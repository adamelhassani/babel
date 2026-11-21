# Role 1: Engine

**Owner:** ________

**You own:** `commons/config.py`, `commons/world.py`, `commons/rules.py`, `commons/fishers.py`, `commons/run.py`, `commons/batch.py`, `commons/metrics.py`, `commons/__init__.py`, `pyproject.toml`, `.gitignore`. Nobody else edits these; others ask you for changes.

**You provide to Screen by 14:30:** `parse_rule(text) -> dict`, `start_run(seed, rule=None) -> run_id`, `apply_rule(run_id, rule)`.

| By | Task | Done when |
|---|---|---|
| 14:30 | Step 1: rules, parser, tests A and B — DONE | Lake survives 30 rounds in at least 2 of 3 runs of test A |
| 15:30 | Step 2: batch runner — DONE | `runs/batch/results.csv` has six rules x 3 seeds |
| 16:15 | Step 3: Agents SDK backend | Works behind a flag, or skipped after 30 minutes |
| 16:45 | Fixes only | |

## Step 1 prompt

```
Phase 0 passed. Do this step only, then stop.

Build commons/rules.py and extend world.py and run.py:
- Rule JSON: quota_per_fisher (int|null), inspection_prob (0..1),
  fine_multiplier (float), ban_rounds (int), tax_rate (0..1),
  closed_every (int|null), transparency (bool), plain_text (str).
- Enforcement each round, in this order: banned fishers catch 0; on a
  closed round everyone catches 0; each fisher over quota is inspected
  with inspection_prob, and if caught pays fine_multiplier x fish over
  quota and is banned for ban_rounds; tax is taken from each catch; if
  transparency is true, fishers see true catches instead of reports.
- Fishers are shown plain_text, their own fines and bans, and who was
  publicly caught last round.
- parse_rule(text) -> dict: mistral-medium-latest (reasoning none) turns
  one sentence into the rule JSON in under 2 seconds. No mistral-large-4.
- start_run(seed, rule=None) -> run_id runs in the background and appends
  to runs/<run_id>/rounds.jsonl as each round finishes.
  apply_rule(run_id, rule) takes effect from the next round and is logged
  in the `rule` field.

TEST, 3 seeds x 30 rounds each, concurrently:
 A) Parse and apply from round 1: "Nobody may take more than 6 fish. Three
    in ten boats are inspected. Cheats pay three times the excess and sit
    out two rounds."
 B) No rule for rounds 1-3, then the same rule from round 4.
Print per run: stock per round, outcome, mean total catch, share over
quota, share lying, fishers caught, three statements from after the rule.
Print the parsed JSON once.

PASS if the lake survives 30 rounds in at least 2 of 3 runs of test A.
Report pass or fail and stop. Do not tune.
Commit only my files, force-add runs/<one test B run>/rounds.jsonl for the
demo, and push to origin commons.
```

**If test A fails:** raise `inspection_prob` to 0.5 in the test sentence and rerun once. If the lake survives but fishers never cheat, that is fine.

## Step 2 prompt

```
Build commons/batch.py and commons/metrics.py.
Rules to run, each x 3 seeds x 30 rounds, all concurrently where the rate
limit allows:
 1. no rule
 2. quota 6, no inspections
 3. quota 6, 30% inspections, fine 3x, 2-round ban
 4. 30% tax on every catch
 5. lake closed every 3rd round
 6. transparency only (true catches are public)
Write runs/batch/results.csv with columns: rule_name, seed,
rounds_survived, final_stock, total_catch, gini, share_over_quota,
share_lying. Print a summary table averaged over seeds.
Force-add runs/batch/results.csv, commit my files, push.
```

## Step 3 prompt (bonus, 30-minute limit)

```
Add an optional Mistral Agents backend for fishers behind
config.USE_AGENTS (default False). Read
docs.mistral.ai/studio/agents/overview and inspect the installed package
before importing anything. Each fisher becomes one agent whose session
holds its history. The log format and all function signatures must not
change. Run one 10-round game with the flag on and show the output.
If it is not working in 30 minutes, stop and leave the flag off.
```

For the pitch, note where Agents are used and how, even if only in a short demo run.
