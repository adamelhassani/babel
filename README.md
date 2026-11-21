# Commons

A test bench for how AI agents behave when they share a limited resource, and which rules stop them draining it.

Ten agent fishers share one lake. Each round each fisher decides how many fish to take (`catch`) and what to tell the village (`report`), plus a short public statement (`say`). Fish regrow only if enough are left. A human states a rule in plain words; it is parsed into JSON, enforced (quota, inspections, fines, bans, tax, closed rounds, transparency), and the village plays on. An AI inspector (mistral-large-4) reads only public information and names the 3 fishers it believes under-reported the most.

## Layout

```
commons/
  config.py       constants, model names, runs dir
  world.py        stock update, rule enforcement
  fishers.py      personas, prompts, shared async client + call_json
  rules.py        rule JSON schema + mistral-large-4 parser
  run.py          one run, background registry, JSONL logging
  batch.py        9 rule scenarios x 3 seeds -> runs/batch/results.csv
  metrics.py      gini, CSV rows, summaries (from logs only)
  inspector.py    top-3 under-reporter checks -> runs/<id>/inspector.jsonl
  report.py       mistral-large-4 report -> runs/batch/report.md
  audio.py        Voxtral TTS (speak) + transcription (transcribe)
  server.py       FastAPI app (127.0.0.1:8000) + static UI
  static/index.html
instructions/     team plan and role files
runs/             sample logs (tracked) + live logs (gitignored)
```

## Setup

```bash
git checkout commons
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
export MISTRAL_API_KEY="..."   # env only, never committed (.env is gitignored)
```

## Run

```bash
.venv/bin/python -m commons.server                  # UI at http://127.0.0.1:8000
.venv/bin/python -m commons.run                     # rule acceptance test (3 seeds x 30 rounds)
.venv/bin/python -m commons.run phase0              # no-rule baseline
.venv/bin/python -m commons.batch                   # all scenarios -> runs/batch/results.csv
.venv/bin/python -m commons.inspector runs/phase0-seed0
.venv/bin/python -m commons.report runs             # -> runs/batch/report.md
```

Every round is appended to `runs/<run_id>/rounds.jsonl`; the UI and all metrics read from those logs, so any run replays with no API calls.
