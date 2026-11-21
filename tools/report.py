import json
import os
import sys

from babel import metrics, world


def load(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line))
    return out


def main(run_id):
    base = os.path.join("runs", run_id)
    games = [world.Game.from_dict(d) for d in load(os.path.join(base, "games.jsonl"))]
    records = load(os.path.join(base, "metrics.jsonl"))
    villages = sorted({g.speaker_village for g in games} | {g.listener_village for g in games})
    lines = [f"# Babel report - run {run_id}", ""]
    latest = records[-1] if records else None
    for name in villages:
        entry = (latest or {}).get("villages", {}).get(name, {})
        lines.append(f"## {name}")
        if entry:
            lines.append(f"- insider_success={entry['insider_success']:.2f} decoder_accuracy={entry['decoder_accuracy']:.2f} "
                         f"oversight_gap={entry['oversight_gap']:.2f} avg_len={entry['avg_len']:.2f} structure={entry['structure']:.2f}")
            lines.append("- dictionary:")
            for obj, word in sorted(entry.get("dictionary", {}).items()):
                lines.append(f"  - {obj}: {word}")
        lines.append("")
    for phase in ("probe@isolation", "probe@contact"):
        lines.append(f"## intelligibility {phase}")
        for a in villages:
            row = [round(metrics.intelligibility(games, a, b, phase), 2) for b in villages]
            lines.append(f"- {a}: {row}")
        lines.append("")
    report = "\n".join(lines)
    with open(os.path.join(base, "REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write(report)
    print(report)


if __name__ == "__main__":
    main(sys.argv[1])
