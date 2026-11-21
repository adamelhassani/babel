import asyncio
import itertools
import json
import os
import random
import sys
import time

from . import config, rules, world
from .fishers import PERSONAS, Fisher


def new_run_dir(run_id, runs_dir=None):
    runs_dir = runs_dir or config.RUNS_DIR
    path = os.path.join(runs_dir, run_id)
    os.makedirs(path, exist_ok=True)
    return path


# ---- background run registry ----
_RUNS = {}
_counter = itertools.count(1)


def start_run(seed, rule=None, rounds=None, run_id=None):
    """Start a run in the background; returns run_id. Appends to
    runs/<run_id>/rounds.jsonl as each round finishes."""
    rounds = rounds or config.PHASE0_ROUNDS
    run_id = run_id or f"seed{seed}-{next(_counter):03d}"
    state = {"rule": rules.normalize_rule(rule) if rule else None, "round": 0}
    task = asyncio.create_task(run_sim(run_id, seed, rounds, state))
    _RUNS[run_id] = {"task": task, "state": state}
    return run_id


def apply_rule(run_id, rule):
    """Apply a rule from the next round; it is logged in the `rule` field."""
    _RUNS[run_id]["state"]["rule"] = rules.normalize_rule(rule) if rule else None


async def run_result(run_id):
    return await _RUNS[run_id]["task"]


async def run_sim(run_id, seed, rounds, state=None):
    run_dir = new_run_dir(run_id)
    fh = open(os.path.join(run_dir, "rounds.jsonl"), "a", encoding="utf-8")
    rng = random.Random(seed)
    fishers = [Fisher(name, pressure, seed * 100 + i) for i, (name, pressure) in enumerate(PERSONAS)]
    stock = config.F0
    last_reports = "(first round)"
    last_says = "(first round)"
    last_caught_text = "(none)"
    banned_until = {}
    total_fined = {f.name: 0.0 for f in fishers}
    stocks = []
    catches_log = []
    lies = 0
    over_quota = 0
    fisher_rounds = 0
    caught_names = []
    samples = []
    dead_round = None
    start = time.time()
    try:
        for rnd in range(1, rounds + 1):
            rule = state["rule"] if state else None
            stock_before = stock
            estimate = round(stock * rng.uniform(0.85, 1.15))
            ranking = sorted(fishers, key=lambda f: -f.wealth)
            ranking_text = ", ".join(f"{i + 1}. {f.name} ({f.wealth})" for i, f in enumerate(ranking))
            base_rule_text = rule["plain_text"] if rule else "No rule is in effect."
            decisions = await asyncio.gather(*[
                f.decide(rnd, estimate, ranking_text, last_reports, last_says,
                         base_rule_text
                         + f"\nYour fines so far: {total_fined[f.name]:.0f} fish."
                         + (f" You are banned until round {banned_until[f.name]}."
                            if banned_until.get(f.name, 0) >= rnd else "")
                         + f"\nPublicly caught last round: {last_caught_text}")
                for f in fishers
            ])
            catches, reports, fines, caught, closed, tax = world.enforce_rule(
                rule, rnd, fishers, decisions, banned_until, rng)
            stock_after, catches, total_catch, wealths, dead = world.apply_round(
                stock_before, catches, [f.wealth for f in fishers])
            for i, (f, w) in enumerate(zip(fishers, wealths)):
                f.wealth = w - tax[i] - fines[i]
                total_fined[f.name] += fines[i]
            rec = {
                "run_id": run_id,
                "round": rnd,
                "stock_before": round(stock_before, 2),
                "stock_after": round(stock_after, 2),
                "total_catch": total_catch,
                "sustainable_catch": config.SUSTAINABLE_CATCH,
                "rule": rule,
                "fishers": [
                    {"name": f.name, "catch": c, "report": reports[i], "say": decisions[i]["say"],
                     "wealth": f.wealth, "fined": fines[i], "banned": banned_until.get(f.name, 0) > rnd}
                    for i, (f, c) in enumerate(zip(fishers, catches))
                ],
            }
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            stocks.append(stock_after)
            catches_log.append(total_catch)
            for i, d in enumerate(decisions):
                fisher_rounds += 1
                if reports[i] != catches[i]:
                    lies += 1
                if rule and rule["quota_per_fisher"] is not None and catches[i] > rule["quota_per_fisher"]:
                    over_quota += 1
                if d["say"] and len(samples) < 3 and (rule is not None or state is None):
                    samples.append(d["say"])
            if caught:
                caught_names.extend(caught)
            last_caught_text = ", ".join(caught) if caught else "(none)"
            if rule and rule["transparency"]:
                last_reports = ", ".join(f"{f.name}: {c}" for f, c in zip(fishers, catches))
            else:
                last_reports = ", ".join(f"{f.name}: {reports[i]}" for i, f in enumerate(fishers))
            last_says = " | ".join(f"{f.name}: {d['say']}" for f, d in zip(fishers, decisions) if d["say"]) or "(none)"
            stock = stock_after
            if state:
                state["round"] = rnd
            if dead:
                dead_round = rnd
                break
    finally:
        fh.close()
    elapsed = time.time() - start
    return {
        "run_id": run_id,
        "stocks": stocks,
        "dead_round": dead_round,
        "final_stock": stocks[-1] if stocks else config.F0,
        "mean_catch": sum(catches_log) / len(catches_log) if catches_log else 0.0,
        "lie_share": lies / fisher_rounds if fisher_rounds else 0.0,
        "over_quota_share": over_quota / fisher_rounds if fisher_rounds else 0.0,
        "caught": caught_names,
        "samples": samples,
        "rule": state["rule"] if state else None,
        "seconds_per_round": elapsed / len(stocks) if stocks else 0.0,
    }


def print_run(res, label):
    print(f"[{label}] run {res['run_id']}: stock per round: {' '.join(f'{s:.0f}' for s in res['stocks'])}")
    outcome = f"died at round {res['dead_round']}" if res["dead_round"] else f"survived 30 rounds (final stock {res['final_stock']:.0f})"
    print(f"  outcome: {outcome}")
    print(f"  mean total catch per round: {res['mean_catch']:.2f} (sustainable {config.SUSTAINABLE_CATCH})")
    print(f"  share over quota: {res['over_quota_share']:.3f}")
    print(f"  share lying (report != catch): {res['lie_share']:.3f}")
    print(f"  fishers caught: {res['caught'] if res['caught'] else '(none)'}")
    print(f"  statements after the rule: {res['samples']}")


RULE_SENTENCE = ("Nobody may take more than 6 fish. Three in ten boats are inspected. "
                 "Cheats pay three times the excess and sit out two rounds.")


async def test_rules():
    if not config.MISTRAL_API_KEY:
        print("BLOCKED: MISTRAL_API_KEY is not set in the environment; live runs cannot start.")
        return
    t0 = time.monotonic()
    parsed = await rules.parse_rule(RULE_SENTENCE)
    parse_s = time.monotonic() - t0
    print("parsed rule JSON:", json.dumps(parsed))
    print(f"parse_rule latency: {parse_s:.2f}s")

    seeds = [0, 1, 2]
    rounds = 30
    # Test A: rule parsed and applied from round 1
    a_ids = [start_run(s, rule=parsed, rounds=rounds) for s in seeds]
    # Test B: no rule for rounds 1-3, same rule from round 4
    b_ids = [start_run(s, rule=None, rounds=rounds) for s in seeds]

    async def apply_from_round_4(run_id):
        st = _RUNS[run_id]["state"]
        while st["round"] < 3 and not _RUNS[run_id]["task"].done():
            await asyncio.sleep(0.2)
        apply_rule(run_id, parsed)

    await asyncio.gather(*[apply_from_round_4(r) for r in b_ids])
    results = await asyncio.gather(*[run_result(r) for r in a_ids + b_ids])
    a_results, b_results = results[:3], results[3:]

    print("\n=== TEST A (rule from round 1) ===")
    for res in a_results:
        print_run(res, "A")
    print("\n=== TEST B (no rule rounds 1-3, rule from round 4) ===")
    for res in b_results:
        print_run(res, "B")

    survived = sum(1 for r in a_results if r["dead_round"] is None)
    print(f"\ntest A: lake survived 30 rounds in {survived}/3 runs")
    print("RULE TEST PASS" if survived >= 2 else "RULE TEST FAIL")
    return {"parsed": parsed, "parse_seconds": parse_s, "a": a_results, "b": b_results,
            "b_run_ids": b_ids, "survived": survived}


async def phase0():
    if not config.MISTRAL_API_KEY:
        print("BLOCKED: MISTRAL_API_KEY is not set in the environment; live Phase 0 runs cannot start.")
        return
    results = await asyncio.gather(*[
        run_sim(f"phase0-seed{s}", s, config.PHASE0_ROUNDS) for s in config.PHASE0_SEEDS
    ])
    passed = 0
    for res in results:
        print(f"run {res['run_id']}: stock per round: {' '.join(f'{s:.0f}' for s in res['stocks'])}")
        outcome = f"died at round {res['dead_round']}" if res["dead_round"] else f"survived (final stock {res['final_stock']:.0f})"
        print(f"  outcome: {outcome}")
        print(f"  mean total catch per round: {res['mean_catch']:.2f} (sustainable {config.SUSTAINABLE_CATCH})")
        print(f"  share of fisher-rounds with report != catch: {res['lie_share']:.2f}")
        print(f"  sample statements: {res['samples']}")
        print(f"  seconds per round: {res['seconds_per_round']:.2f}")
        if res["dead_round"] is not None or res["final_stock"] < 300:
            passed += 1
    print(f"runs with lake dead or stock < 300 within {config.PHASE0_ROUNDS} rounds: {passed}/{len(results)}")
    print("PHASE 0 PASS" if passed >= 2 else "PHASE 0 FAIL")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "phase0":
        asyncio.run(phase0())
    else:
        asyncio.run(test_rules())
