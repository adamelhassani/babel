# Commons UI demo-readiness plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make the Commons screen intuitive enough that a stranger can follow the hackathon demo cold — replay a saved lake collapse, start a live run, parse and apply a spoken/typed rule, catch a cheater being banned, then read the results table and the Inspector panel — all visible on one screen, with live/dead states and errors that cannot be missed. Demo-ready before feature freeze 16:45; demo video 17:30; submit 18:00.

**Architecture:** Backend contracts unchanged. One page (`commons/static/index.html`, vanilla JS + Chart.js 4 from CDN, no build step) plus exactly one new endpoint in `commons/server.py`: `POST /parse {text}` → parsed rule JSON *without* applying, so the UI can preview before apply (`POST /rule` stays for one-click apply). All data still comes from `runs/**` via the existing endpoints (`/api/runs`, `/api/runs/{id}/rounds`, `/state/{id}`, `/api/runs/{id}/inspector`, `/api/batch`, `/transcribe`, `/speak`). `GET /api/runs` gains an `active` flag per run so the picker can badge live runs. Role 2 owns only `commons/server.py` and `commons/static/index.html` — every task below touches nothing else (plus this plan file).

**Tech Stack:** Python 3.11+, FastAPI + uvicorn + pydantic (server), vanilla JS + Chart.js 4 CDN (page), node --check for JS syntax, FastAPI TestClient (httpx) for endpoint smoke, manual browser checklist at 1440x900.

## What changes vs what stays

- **Stays:** every existing endpoint and response shape (except `/api/runs` gaining `active`), the round-log contract, Chart.js usage, dark theme, run picker + slider + play/pause, rule markers on the stock chart, fines/bans on boats, mic → `/transcribe` → rule box, ▶ → `/speak`.
- **Changes (page):** one-screen demo grid (lake tall left, charts top-right, results + inspector bottom-right, audio in topbar), start at round 1 with a dismissible hint, LIVE badge + "pause = stop following" semantics, parse → preview → apply rule flow with a persistent current-rule banner, stock number inside the lake + LAKE DEAD label, boat state icons (🚫 banned, red ring fined), error toasts, tooltips on all buttons, keyboard shortcuts (space, ←/→), responsive grid.
- **Changes (server):** `POST /parse`; `/api/runs` returns `{"runs": [{"name": ..., "active": ...}]}`.

## File map

- Edit: `commons/static/index.html` — all UI work (Tasks 2-8)
- Edit: `commons/server.py` — `POST /parse` + `/api/runs` active flag (Task 1)
- Create: `docs/superpowers/plans/2026-11-21-commons-ui-demo.md` — this plan

## Environment setup (do once before Task 1)

```bash
git checkout commons && git pull --rebase origin commons
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"        # fastapi, uvicorn, mistralai, pydantic, pytest, httpx
export MISTRAL_API_KEY="$MISTRAL_API_KEY"  # from the environment only; never write it into a file
.venv/bin/python -m commons.server        # serves http://127.0.0.1:8000
```

---

### Task 1: server.py — parse-only endpoint + live flags in run list

**Files:**
- Edit: `commons/server.py`

- [x] **Step 1: Add `ParseBody` and `POST /parse` next to `POST /rule`**

```python
class ParseBody(BaseModel):
    text: str


@app.post("/parse")
async def parse_only(body: ParseBody):
    try:
        rule = await rulesmod.parse_rule(body.text)
    except Exception as exc:
        raise HTTPException(502, f"rule parser failed: {exc}")
    return {"rule": rule}
```

- [x] **Step 2: Give `/api/runs` an `active` flag**

```python
@app.get("/api/runs")
def list_runs():
    runs = []
    if os.path.isdir(RUNS_DIR):
        for name in sorted(os.listdir(RUNS_DIR)):
            if os.path.isfile(os.path.join(RUNS_DIR, name, "rounds.jsonl")):
                runs.append({"name": name, "active": _run_active(name)})
    return {"runs": runs}
```

(`_run_active` already exists.) Update the page's `init`/`refreshPicker` to read `r.name` / `r.active` (Task 4).

- [x] **Step 3: Verify**

Run:
```bash
.venv/bin/python - <<'EOF'
from fastapi.testclient import TestClient
from commons.server import app
c = TestClient(app)
r = c.get("/api/runs"); assert r.status_code == 200
assert all(set(x) == {"name", "active"} for x in r.json()["runs"])
print([ (x["name"], x["active"]) for x in r.json()["runs"] ])
r = c.post("/parse", json={"text": "quota 6"})
print("parse without key ->", r.status_code)   # expect 502 (no key in this env) or 200 with key
EOF
```
Expected: `/api/runs` lists every run folder with `active: false` (no live runs); `/parse` returns 200 with `{"rule": {...}}` when `MISTRAL_API_KEY` is set, 502 with a clear message otherwise.

### Task 2: One-screen demo layout

**Files:**
- Edit: `commons/static/index.html`

- [x] **Step 1: New grid.** Replace `.panels{display:grid;grid-template-columns:380px 1fr 1fr;...}` with:

```css
.panels{display:grid;grid-template-columns:400px 1fr 1fr;gap:8px;padding:8px}
.panel.lake{grid-row:span 2}
@media (max-width:1250px){.panels{grid-template-columns:1fr 1fr}}
@media (max-width:820px){.panels{grid-template-columns:1fr}.panel.lake{grid-row:auto}}
```

- [x] **Step 2: Reorder panels.** Lake panel gets `class="panel lake"` and spans two rows; stock chart and catch chart fill the top-right; Results and Inspector go in the second row under the charts; delete the Audio panel from the grid and move the mic button into the topbar next to the rule box (`<button id="mic" title="record a rule aloud">● rec</button> <span id="micstatus"></span>`).

- [x] **Step 3: Verify**

Run: `.venv/bin/python -m commons.server`, open `http://127.0.0.1:8000` at 1440x900.
Expected: lake + both charts + results + inspector all visible without scrolling; audio controls visible in the topbar; narrowing the window to 800px stacks panels in one column.

### Task 3: First-load experience (start at round 1 + hint)

**Files:**
- Edit: `commons/static/index.html`

- [x] **Step 1:** In `loadRun`, set `cur = 1` (not `rounds.length`) and `slider.value = 1`.
- [x] **Step 2:** Add a hint toast element `<div id="hint">▶ play, or scrub the round slider. Pick another run top-left.</div>` shown on load, hidden on first play/slider input (and auto-hide after 8 s). Style: fixed bottom-center, dark pill, `transition: opacity .4s`.
- [x] **Step 3: Verify**

Reload the page.
Expected: round 1 of `phase0-seed0` shown (full blue lake, stock 600→517 in chart), hint visible; press play → hint disappears and rounds advance.

### Task 4: Live-run affordances (LIVE badge, pause = stop following)

**Files:**
- Edit: `commons/static/index.html`

- [x] **Step 1:** `refreshPicker`/`init` read `{"name","active"}` from `/api/runs`; render option label as `name + (active ? " ●LIVE" : "")` with a green dot span.
- [x] **Step 2:** Add `let followLive = true;`. In `poll()`, only auto-advance (`cur = rounds.length`) when `followLive` is true. The pause button toggles `followLive` and its label between "pause" and "resume live"; play button behavior unchanged for replay.
- [x] **Step 3: Verify**

`POST /run {"seed": 0}`, watch the slider follow the live run with a LIVE badge on the picker; click pause → slider freezes at the current round while the run continues (badge stays); click again → following resumes. Switching the picker to a saved run clears the badge and stops following.

### Task 5: Rule flow — parse, preview, apply

**Files:**
- Edit: `commons/static/index.html` (uses new `POST /parse`)

- [x] **Step 1:** Topbar rule controls become: `<input id="ruletext">` + `<button id="parsebtn" title="parse the rule text">parse</button>` + `<button id="applyrule" title="apply the parsed rule to the live run" disabled>apply</button>`.
- [x] **Step 2:** `parseRule()`: POST `/parse {text}` → `showRule(rule, pending=true)` in the rulebox (yellow "preview — not applied" tag), enable apply button. `applyRule()`: POST `/rule {run_id, text}` → `showRule(rule, pending=false)` (green "applied") + status; disable apply until the text changes.
- [x] **Step 3:** Persistent current-rule banner: in `render()`, if `rec.rule`, show `rec.rule.plain_text` as a separate line in the rulebox area labelled "in effect"; keep it distinct from any pending preview.
- [x] **Step 4: Verify**

With the key set: type the quota sentence → parse → rulebox shows `quota_per_fisher: 6, inspection_prob: 0.3, ...` marked preview, and the run log still shows `rule: null`; click apply → `/rule` 200, fields marked applied, gold marker appears on the stock chart at the next logged round. Without the key: parse → red toast with the 502 detail (Task 7).

### Task 6: Lake and boat state clarity

**Files:**
- Edit: `commons/static/index.html`

- [x] **Step 1:** Lake: add `<text id="laketext">` inside the SVG showing the stock number (e.g. "517"), and a `<text id="lakedead">` "LAKE DEAD" in red shown when `stock_after < F_DEAD`; circle keeps grey fill.
- [x] **Step 2:** Boats: banned → hull becomes 🚫 and boat dims (existing `.banned`); fined → red ring (`box-shadow:0 0 0 2px #e74c3c;border-radius:50%` on the hull); bubble font 11px, clamp 4 lines; every button gets a `title` tooltip (start run, play, pause, parse, apply, mic, ▶).
- [x] **Step 3: Verify**

Replay `seed0-004` (rule from round 5): scrub across round 5 → fined/banned boats show states; replay `phase0-seed0` to round 6 → grey lake with "LAKE DEAD" and stock 7.

### Task 7: Error toasts

**Files:**
- Edit: `commons/static/index.html`

- [x] **Step 1:** Add `<div id="toast"></div>` fixed top-right; helper `function toast(msg){ const t=$("toast"); t.textContent=msg; t.style.display="block"; clearTimeout(t._h); t._h=setTimeout(()=>t.style.display="none",5000); }` with red styling.
- [x] **Step 2:** Replace every `$("status").textContent = "... failed: " + ...` error path (startRun, applyRule, parse, toggleMic, speakLine) with `toast(...)`; keep short info in `#status`.
- [x] **Step 3: Verify**

Without `MISTRAL_API_KEY`: click parse → red toast "rule parser failed: ..." appears top-right for 5 s; status line stays clean.

### Task 8: Keyboard shortcuts

**Files:**
- Edit: `commons/static/index.html`

- [x] **Step 1:** Add

```js
document.addEventListener("keydown", e => {
  if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
  if (e.code === "Space") { e.preventDefault(); timer ? pause() : play(); }
  if (e.key === "ArrowRight" && rounds.length) { cur = Math.min(rounds.length, cur + 1); pause(); render(); }
  if (e.key === "ArrowLeft" && rounds.length) { cur = Math.max(1, cur - 1); pause(); render(); }
});
```

- [x] **Step 2: Verify**

Run: `node --check` on the extracted inline script (see Verification), then in the browser: space toggles play/pause, ←/→ scrub one round at a time; typing in the rule box is unaffected.

### Task 9: Demo runbook + pre-demo checklist (no code)

- [ ] **Runbook (under 3 minutes, mirrors `instructions/roles/2-screen.md` checklist):** 1) pick `phase0-seed0`, press play — lake collapses by round 6; read a "fair shares" bubble beside its real catch bar. 2) Start a live run (seed 0). 3) Speak or type the quota-and-inspection rule → parse → preview → apply; watch the stock recover and a boat get banned. 4) Switch to `batch-quota6-30pct-3x-2ban-s0` → Inspector panel (accused vs true top 3, running mean vs 0.30). 5) Results table sorted by rounds survived. Never show `.env`, a terminal with the key, or the browser network tab.
- [ ] **Pre-demo checklist at freeze (16:45):** server running on the demo machine; key exported in that shell; Chart.js CDN reachable; mic permission pre-granted; runs present: `phase0-seed0`, `seed0-004`, `batch-*`; fallback if a live run misbehaves: replay `seed0-004`.

---

## Verification (whole plan)

- [ ] Extract inline JS and syntax-check:

```bash
python3 -c "
import re
html = open('commons/static/index.html').read()
open('/tmp/inline.js','w').write(re.search(r'<script>(.*)</script>', html, re.S).group(1))
" && node --check /tmp/inline.js
```
Expected: no output (syntax OK).

- [ ] Endpoint smoke:

```bash
.venv/bin/python - <<'EOF'
from fastapi.testclient import TestClient
from commons.server import app
c = TestClient(app)
assert c.get("/").status_code == 200
assert all(set(x) == {"name", "active"} for x in c.get("/api/runs").json()["runs"])
assert len(c.get("/api/batch").json()["rows"]) == 27
assert c.get("/api/runs/phase0-seed0/rounds").json()["rounds"][0]["round"] == 1
assert c.get("/api/runs/batch-no-rule-s2/inspector").json()["source"] == "inspector_agent.jsonl"
print("smoke OK")
EOF
```
Expected: `smoke OK`.

- [ ] Browser checklist at 1440x900 (no scroll): all panels visible; reload shows round 1 + hint; play advances; live run gets LIVE badge and slider follows, pause freezes; parse → preview → apply shows fields and chart marker; banned/fined boats visible in `seed0-004`; phase0-seed0 round 6 shows grey lake + LAKE DEAD; results table sorted by rounds survived desc; inspector panel shows source + running mean vs baseline 0.30; error toast appears on a failed call.

**Definition of done:** the full runbook in Task 9 is executed twice end-to-end using only the mouse, with no explanations needed; `git status` shows only `commons/server.py`, `commons/static/index.html`, and this plan changed; all committed and pushed to `origin commons` before 16:45.
