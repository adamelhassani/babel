import argparse
import asyncio
import csv
import json
import os
import time
from collections import defaultdict

from . import config, fishers

REPORT_SYSTEM = (
    "You are a fisheries scientist writing a short report from experiment logs. "
    'Reply with JSON only: {"report": "<markdown report, under 250 words>"}'
)

SAMPLE_LIMIT = 10


def load_results(results_csv):
    with open(results_csv, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def aggregate(rows):
    by_rule = defaultdict(list)
    for row in rows:
        by_rule[row["rule_name"]].append(row)
    out = {}
    for name, rs in by_rule.items():
        n = len(rs)
        out[name] = {
            "seeds": n,
            "rounds_survived": sum(int(r["rounds_survived"]) for r in rs) / n,
            "final_stock": sum(float(r["final_stock"]) for r in rs) / n,
            "share_lying": sum(float(r["share_lying"]) for r in rs) / n,
            "share_over_quota": sum(float(r["share_over_quota"]) for r in rs) / n,
            "gini": sum(float(r["gini"]) for r in rs) / n,
        }
    return out


def find_run_dirs(runs_dir):
    return [
        os.path.join(runs_dir, d)
        for d in sorted(os.listdir(runs_dir))
        if os.path.isfile(os.path.join(runs_dir, d, "rounds.jsonl"))
    ]


def rule_dirs(rule_name, run_dirs):
    prefix = f"batch-{rule_name}-s"
    dirs = [d for d in run_dirs if os.path.basename(d).startswith(prefix)]
    if rule_name == "no-rule":
        dirs += [d for d in run_dirs if os.path.basename(d).startswith("phase0-")]
    return dirs


def sample_statements(run_dir, limit=SAMPLE_LIMIT):
    says = []
    seen = set()
    with open(os.path.join(run_dir, "rounds.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            for f in rec["fishers"]:
                s = (f.get("say") or "").strip()
                if s and s not in seen:
                    seen.add(s)
                    says.append(s)
                    if len(says) >= limit:
                        return says
    return says


def build_user_prompt(results_csv, runs_dir):
    rows = load_results(results_csv)
    aggs = aggregate(rows)
    with open(results_csv, encoding="utf-8") as fh:
        csv_text = fh.read()
    run_dirs = find_run_dirs(runs_dir)
    lines = [
        f"Results from runs/batch/results.csv ({len(rows)} runs):",
        csv_text,
        "Averages per rule over seeds:",
    ]
    for name in sorted(aggs):
        a = aggs[name]
        lines.append(
            f"- {name}: rounds_survived={a['rounds_survived']:.1f} final_stock={a['final_stock']:.1f} "
            f"share_lying={a['share_lying']:.3f} share_over_quota={a['share_over_quota']:.3f} gini={a['gini']:.3f}"
        )
    lines.append("Sample fisher statements per rule (up to 10 each, from that rule's local runs):")
    for name in sorted(aggs):
        dirs = rule_dirs(name, run_dirs)
        says = []
        for d in dirs:
            says.extend(sample_statements(d, SAMPLE_LIMIT - len(says)))
            if len(says) >= SAMPLE_LIMIT:
                break
        lines.append(f"- {name}: {json.dumps(says[:SAMPLE_LIMIT])}")
    lines.append(
        "Write the report (markdown, under 250 words): which rule kept the lake alive, which failed and why, "
        "how often fishers lied under each rule, and one surprising observation."
    )
    return "\n".join(lines)


async def make_report(results_csv, runs_dir):
    config.REASONING_EFFORT = "low"
    config.FISHER_TIMEOUT_S = 180
    user = build_user_prompt(results_csv, runs_dir)
    data = await fishers.call_json(
        [{"role": "system", "content": REPORT_SYSTEM}, {"role": "user", "content": user}],
        model=config.LARGE_MODEL,
        max_tokens=6000,
    )
    return data.get("report", "")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs_dir", nargs="?", default=config.RUNS_DIR)
    args = parser.parse_args()
    results_csv = os.path.join(args.runs_dir, "batch", "results.csv")
    if not os.path.isfile(results_csv):
        print(f"MISSING: {results_csv}")
        return
    if not config.MISTRAL_API_KEY:
        print("BLOCKED: MISTRAL_API_KEY is not set in the environment")
        return
    start = time.time()
    report = asyncio.run(make_report(results_csv, args.runs_dir))
    elapsed = time.time() - start
    out_path = os.path.join(args.runs_dir, "batch", "report.md")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(report + "\n")
    words = len(report.split())
    print(f"wrote {out_path} ({words} words, {elapsed:.1f}s)")
    print("---")
    print(report)


if __name__ == "__main__":
    main()
