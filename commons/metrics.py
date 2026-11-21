"""Metrics for Babel runs: catch-inequality gini and CSV row building.

`gini` is computed on each fisher's TOTAL FISH CAUGHT over the run
(always non-negative), not on wealth.
"""

import csv
import json
import os
import re

from . import config

CSV_COLUMNS = [
    "rule_name", "start_round", "seed", "rounds_survived", "final_stock",
    "total_catch", "gini", "share_over_quota", "share_lying", "min_wealth",
]


def gini(values):
    """Gini coefficient of a list of numbers (0 = perfectly equal).
    For non-negative values (e.g. total fish caught) it is in [0, 1]."""
    vals = [float(v) for v in values]
    n = len(vals)
    if n == 0:
        return 0.0
    mean = sum(vals) / n
    if mean == 0:
        return 0.0
    diff = sum(abs(a - b) for a in vals for b in vals)
    return diff / (2 * n * n * mean)


def run_row(rule_name, start_round, seed, res):
    return {
        "rule_name": rule_name,
        "start_round": start_round,
        "seed": seed,
        "rounds_survived": len(res["stocks"]),
        "final_stock": round(res["final_stock"], 2),
        "total_catch": res["total_catch_sum"],
        "gini": round(gini(res["caught_totals"]), 4),
        "share_over_quota": round(res["over_quota_share"], 4),
        "share_lying": round(res["lie_share"], 4),
        "min_wealth": res["min_wealth"],
    }


def row_from_log(run_dir, rule_name, start_round, seed):
    """Build a CSV row purely from a saved runs/<run_id>/rounds.jsonl log."""
    path = os.path.join(run_dir, "rounds.jsonl")
    recs = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    caught = {}
    lies = 0
    over_q = 0
    fisher_rounds = 0
    total_catch = 0
    for r in recs:
        total_catch += r["total_catch"]
        quota = (r["rule"] or {}).get("quota_per_fisher")
        for f in r["fishers"]:
            fisher_rounds += 1
            caught[f["name"]] = caught.get(f["name"], 0) + f["catch"]
            if f["report"] != f["catch"]:
                lies += 1
            if quota is not None and f["catch"] > quota:
                over_q += 1
    last = recs[-1]
    return {
        "rule_name": rule_name,
        "start_round": start_round,
        "seed": seed,
        "rounds_survived": len(recs),
        "final_stock": round(last["stock_after"], 2),
        "total_catch": total_catch,
        "gini": round(gini(list(caught.values())), 4),
        "share_over_quota": round(over_q / fisher_rounds, 4) if fisher_rounds else 0.0,
        "share_lying": round(lies / fisher_rounds, 4) if fisher_rounds else 0.0,
        "min_wealth": min(f["wealth"] for f in last["fishers"]),
    }


_RUN_DIR_RE = re.compile(r"^batch-(?P<name>.+)-s(?P<seed>\d+)$")


def regenerate(results_csv=None, runs_dir=None):
    """Rebuild the batch CSV from saved run logs. No API calls."""
    results_csv = results_csv or os.path.join(config.RUNS_DIR, "batch", "results.csv")
    runs_dir = runs_dir or config.RUNS_DIR
    rows = []
    for entry in sorted(os.listdir(runs_dir)):
        m = _RUN_DIR_RE.match(entry)
        if not m:
            continue
        run_dir = os.path.join(runs_dir, entry)
        if not os.path.isfile(os.path.join(run_dir, "rounds.jsonl")):
            continue
        name = m.group("name")
        seed = int(m.group("seed"))
        with open(os.path.join(run_dir, "rounds.jsonl"), encoding="utf-8") as fh:
            first_rule_round = next(
                (json.loads(l)["round"] for l in fh if l.strip() and json.loads(l).get("rule")),
                1,
            )
        rows.append(row_from_log(run_dir, name, first_rule_round, seed))
    rows.sort(key=lambda r: (r["rule_name"], r["seed"]))
    write_csv(results_csv, rows)
    return rows


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def summarize(rows):
    """Average rows per rule_name over seeds."""
    groups = {}
    for r in rows:
        groups.setdefault(r["rule_name"], []).append(r)
    out = []
    for name, rs in groups.items():
        n = len(rs)
        out.append({
            "rule_name": name,
            "start_round": rs[0]["start_round"],
            "n_seeds": n,
            "rounds_survived": round(sum(r["rounds_survived"] for r in rs) / n, 2),
            "final_stock": round(sum(r["final_stock"] for r in rs) / n, 1),
            "total_catch": round(sum(r["total_catch"] for r in rs) / n, 1),
            "gini": round(sum(r["gini"] for r in rs) / n, 4),
            "share_over_quota": round(sum(r["share_over_quota"] for r in rs) / n, 4),
            "share_lying": round(sum(r["share_lying"] for r in rs) / n, 4),
            "min_wealth": round(sum(r["min_wealth"] for r in rs) / n, 1),
        })
    return out


if __name__ == "__main__":
    rows = regenerate()
    print(f"regenerated {os.path.join(config.RUNS_DIR, 'batch', 'results.csv')} with {len(rows)} rows (gini on total fish caught)")
