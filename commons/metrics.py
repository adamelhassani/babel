"""Metrics for Babel runs: wealth gini and CSV row building."""

import csv
import os

from . import config

CSV_COLUMNS = [
    "rule_name", "start_round", "seed", "rounds_survived", "final_stock",
    "total_catch", "gini", "share_over_quota", "share_lying", "min_wealth",
]


def gini(values):
    """Gini coefficient of a list of numbers (0 = perfectly equal)."""
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
        "gini": round(gini(res["final_wealths"]), 4),
        "share_over_quota": round(res["over_quota_share"], 4),
        "share_lying": round(res["lie_share"], 4),
        "min_wealth": res["min_wealth"],
    }


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
