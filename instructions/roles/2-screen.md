# Role 2: Screen

**Owner:** ________

**You own:** `commons/server.py`, `commons/static/index.html`. Do not edit other files.

**You consume:** the round log, the engine functions, the audio functions and the Inspector output. All are defined in `../README.md` under Contracts.

| By | Task | Done when |
|---|---|---|
| 14:30 | Step 1: replay page | `runs/phase0-seed0/rounds.jsonl` plays back with all four visuals |
| 15:30 | Step 2: live run and rule box | You type a rule, see it parsed, apply it, and the run changes |
| 16:15 | Step 3: results table, Inspector panel, audio buttons | All three appear with real data |
| 17:30 | Record the demo video | Uploaded with the submission |

## Step 1 prompt

```
Build the Commons screen. Own only commons/server.py and
commons/static/index.html. Do not edit other files.
A FastAPI app serving one page that replays
runs/phase0-seed0/rounds.jsonl:
- a lake drawn as a circle sized by stock, turning grey when dead
- ten boats, each with the fisher's name and latest `say` as a bubble
- a stock chart over rounds with a dashed line at 500
- per-fisher bars of catch against report, with a line at 6.25
- a run picker listing folders in runs/, a round slider, play and pause
Vanilla JS and Chart.js from CDN, no build step.
Run it, open it, and show me a screenshot or describe what renders.
Commit only my files and push to origin commons.
```

## Step 2 prompt (after sync 1 at 14:30)

```
Wire the screen to the engine. Endpoints in server.py:
- POST /run {seed} -> run_id, calls commons.run.start_run
- POST /rule {run_id, text} -> parsed rule JSON, calls parse_rule then
  apply_rule
- GET /state/{run_id} -> all rounds so far, polled every second
On the page: a "start run" button, a rule text box, the parsed rule shown
as readable fields, an "apply" button, and a marker on the stock chart at
the round each rule took effect. Show fines and bans on the boats.
```

## Step 3 prompt (after sync 2 at 15:30)

```
Add three panels:
- Results: a table from runs/batch/results.csv averaged by rule, sorted
  by rounds survived.
- Inspector: read runs/<run_id>/inspector.jsonl; show who was accused,
  who truly lied, and precision and recall. It arrives late and
  asynchronously, so poll for it.
- Audio: a microphone button that records a clip, posts it to
  POST /transcribe (calls commons.audio.transcribe) and puts the text in
  the rule box; and a play button on each bubble using POST /speak.
```

## Demo video checklist (start by 16:50)

1. Start a run with no rule. Let the lake fall for four or five rounds. Show the "fair shares" bubbles against the catch bars.
2. Speak or type the quota-and-inspection rule. Show the parsed rule. Apply it.
3. Show the stock recovering, and a fisher being caught and banned.
4. Show the Inspector panel and the results table.
5. Keep it under three minutes. Never show `.env`, a terminal with the key, or the browser's network tab.

If the live run misbehaves while recording, use replay mode on a saved test B run.
