"""Batch runner: 9 rule scenarios x 3 seeds x 30 rounds, at most 6 runs
concurrently. Writes runs/batch/results.csv and prints Part 1 (rescue test
C/D per-run detail) and Part 2 (summary averaged over seeds).

Scenarios:
 1 no-rule | 2 quota6 no inspections | 3 quota6 30% insp 3x fine 2-round ban
 4 30% tax | 5 closed every 3rd round | 6 transparency only
 7 rule 3 late (from round 4) | 8 scenario C (emergency from round 4)
 9 scenario D (emergency from round 4, relax to rule 3 when stock first > 500)
"""

import asyncio
import json
import os
import time

from . import config, metrics, rules
from . import run as runmod

SEEDS = [0, 1, 2]
ROUNDS = 30
MAX_CONCURRENT = 6
RESULTS_CSV = os.path.join(config.RUNS_DIR, "batch", "results.csv")

ORIGINAL_SENTENCE = ("Nobody may take more than 6 fish. Three in ten boats are inspected. "
                     "Cheats pay three times the excess and sit out two rounds.")
EMERGENCY_SENTENCE = ("Emergency: nobody may take more than 3 fish. Half of all boats are "
                      "inspected. Cheats pay three times the excess and sit out three rounds.")


def rule(quota=None, p=0.0, fm=1.0, br=0, tax=0.0, closed=None, transp=False, text="No rule is in effect."):
    return rules.normalize_rule({
        "quota_per_fisher": quota, "inspection_prob": p, "fine_multiplier": fm,
        "ban_rounds": br, "tax_rate": tax, "closed_every": closed,
        "transparency": transp, "plain_text": text,
    })


async def run_scenario(sem, name, base_rule, start_round, seed, relax_rule=None, relax_threshold=None):
    async with sem:
        rid = runmod.start_run(seed, rule=base_rule if start_round == 1 else None,
                               rounds=ROUNDS, run_id=f"batch-{name}-s{seed}")
        entry = runmod._RUNS[rid]
        st = entry["state"]
        if start_round > 1:
            while st["round"] < start_round - 1 and not entry["task"].done():
                await asyncio.sleep(0.2)
            runmod.apply_rule(rid, base_rule)
        if relax_rule is not None:
            while not entry["task"].done():
                if st["round"] >= start_round and st.get("stock", 0) > relax_threshold:
                    runmod.apply_rule(rid, relax_rule)
                    print(f"  [{rid}] stock rose above {relax_threshold} at round {st['round']} -> relaxed rule applied", flush=True)
                    break
                await asyncio.sleep(0.2)
        res = await runmod.run_result(rid)
    return metrics.run_row(name, start_round, seed, res), res, rid


async def main():
    if not config.MISTRAL_API_KEY:
        print("BLOCKED: MISTRAL_API_KEY is not set in the environment; live runs cannot start.")
        return
    t0 = time.monotonic()
    original = await rules.parse_rule(ORIGINAL_SENTENCE)
    emergency = await rules.parse_rule(EMERGENCY_SENTENCE)
    print("original rule:", json.dumps(original), flush=True)
    print("emergency rule:", json.dumps(emergency), flush=True)

    scenarios = [
        ("no-rule", None, 1, None, None),
        ("quota6-no-insp", rule(quota=6, text="Nobody may take more than 6 fish."), 1, None, None),
        ("quota6-30pct-3x-2ban", original, 1, None, None),
        ("tax30", rule(tax=0.3, text="30% tax on every catch."), 1, None, None),
        ("closed-every-3", rule(closed=3, text="The lake is closed every 3rd round."), 1, None, None),
        ("transparency", rule(transp=True, text="Everyone sees the true catches."), 1, None, None),
        ("rule3-late", original, 4, None, None),
        ("C-emergency", emergency, 4, None, None),
        ("D-emergency-relax", emergency, 4, original, 500),
    ]

    sem = asyncio.Semaphore(MAX_CONCURRENT)
    tasks = []
    for name, base_rule, start_round, relax_rule, relax_threshold in scenarios:
        for seed in SEEDS:
            tasks.append(run_scenario(sem, name, base_rule, start_round, seed, relax_rule, relax_threshold))

    rows = []
    detail = {}
    for coro in asyncio.as_completed(tasks):
        row, res, rid = await coro
        rows.append(row)
        detail.setdefault(row["rule_name"], []).append((res, rid))
        print(f"done {row['rule_name']} seed{row['seed']} ({row['rounds_survived']} rounds, final stock {row['final_stock']})", flush=True)

    metrics.write_csv(RESULTS_CSV, sorted(rows, key=lambda r: (r["rule_name"], r["seed"])))
    print(f"\nwrote {RESULTS_CSV} ({len(rows)} rows)", flush=True)

    print("\n=== PART 1 - RESCUE TEST (C and D, per run) ===")
    for name in ("C-emergency", "D-emergency-relax"):
        print(f"\n-- scenario {name} --")
        for res, rid in sorted(detail[name], key=lambda x: x[1]):
            runmod.print_run(res, name)

    print("\n=== PART 2 - BATCH SUMMARY (averaged over seeds) ===")
    print(f"{'rule_name':24s} {'start':>5s} {'surv':>5s} {'final_stock':>11s} {'tot_catch':>9s} {'gini':>6s} {'over_q':>7s} {'lying':>6s} {'min_wealth':>10s}")
    for s in metrics.summarize(rows):
        print(f"{s['rule_name']:24s} {s['start_round']:>5d} {s['rounds_survived']:>5.1f} {s['final_stock']:>11.1f} "
              f"{s['total_catch']:>9.1f} {s['gini']:>6.3f} {s['share_over_quota']:>7.3f} {s['share_lying']:>6.3f} {s['min_wealth']:>10.1f}")

    print(f"\nwall time: {time.monotonic() - t0:.1f}s")
    print("DONE")


if __name__ == "__main__":
    asyncio.run(main())
