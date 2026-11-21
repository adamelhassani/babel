# Commons: team instructions

Start here. Then open your role file in `roles/`. The full plan is in `PLAN.md`.

## What we are building

A test bench for how AI agents behave when they share a limited resource, and which rules stop them draining it.

- Ten agent fishers share one lake. Each round each decides how many fish to take and what to report.
- A human states a rule, typed or spoken. It is parsed, enforced, and the village plays on.
- An AI Inspector (Mistral Large 4) reads only what fishers say and report, and names who it thinks is lying.

**One-sentence pitch:** "When AI agents share a limited resource they overuse it and lie about it. Commons lets you test which rules stop that, and whether an AI inspector can catch them, before you deploy."

**Already proven (phase 0):** with no rule the lake died in round 6 or 7 in 3 of 3 runs, catches were about twice the sustainable level, and about 70% of reports were false.

## Roles

| Role | Owner | File |
|---|---|---|
| 1 Engine | ________ | `roles/1-engine.md` |
| 2 Screen | ________ | `roles/2-screen.md` |
| 3 Voice, Inspector, pitch | ________ | `roles/3-voice-inspector-pitch.md` |

## Deadlines

| Time | What |
|---|---|
| 14:30 | Sync 1: engine functions handed to Screen |
| 15:30 | Sync 2: audio and Inspector output handed to Screen |
| 16:15 | Sync 3: full run-through together |
| 16:45 | Feature freeze |
| 17:30 | Demo video recorded |
| 18:00 | Submit |

## Contracts (do not change without telling everyone)

**Round log**, one JSON line per round in `runs/<run_id>/rounds.jsonl`:

```
{"run_id", "round", "stock_before", "stock_after", "total_catch",
 "sustainable_catch": 62.5, "rule": null | {...},
 "fishers": [{"name", "catch", "report", "say", "wealth", "fined",
              "banned"}]}
```

**Rule JSON:**

```
{"quota_per_fisher": int|null, "inspection_prob": 0..1,
 "fine_multiplier": float, "ban_rounds": int, "tax_rate": 0..1,
 "closed_every": int|null, "transparency": bool, "plain_text": str}
```

**Engine functions** (Engine provides, Screen calls):
`parse_rule(text) -> dict`, `start_run(seed, rule=None) -> run_id`, `apply_rule(run_id, rule)`.

**Audio functions** (Voice provides, Screen calls):
`transcribe(bytes) -> str`, `speak(text, voice) -> bytes`.

**Inspector output**, `runs/<run_id>/inspector.jsonl`, one line per check:
`{"round", "accused": [names], "truly_lied": [names], "precision", "recall"}`.

**Batch results**, `runs/batch/results.csv`:
`rule_name, seed, rounds_survived, final_stock, total_catch, gini, share_over_quota, share_lying`.

## Models

| Use | Model | Settings |
|---|---|---|
| Fishers, rule parser | `mistral-medium-latest` | `reasoning_effort="none"`, about 0.5 s per call |
| Inspector, final report | `mistral-large-4` | `reasoning_effort="low"`, `max_tokens=6000`, timeout 180 s, one call at a time, never inside the round loop |
| Speech to text | `voxtral-mini-transcribe-3-0` | |
| Text to speech | `voxtral-mini-tts-3-0` | |

Import the client with `from mistralai.client import Mistral`.

## Git rules

- Everyone works on the `commons` branch.
- Edit only the files your role owns.
- `git pull --rebase origin commons` before each step. Commit only your files and push after each step passes.
- Never run `git add .` or `git add -A`. Never commit `.env`, `.venv/` or `runs/` (except logs named in a role file).
- The API key lives only in `.env` or the environment. Never paste it into a prompt, a chat or a file that is committed.

## If we fall behind, cut in this order

1. Agents SDK backend
2. Fishers' lines spoken aloud
3. The Inspector
4. Spoken rule input (keep typed)

Never cut: a live run where a rule changes the outcome, the results table, the demo video.
