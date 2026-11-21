# Commons scene polish + summary agent plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Three fixes to the React scene (`commons/ui/`), from the 16:09/16:10 screenshots and feedback: (1) **center the pond** — in scene view it sits right-of-center with a big empty left area; (2) **visuals follow what the fishers say and do** — boats/bubbles/lake react to `say` and to catch/fine/ban events, not just drift; (3) a **summary box + summary agent** — a "What happened" card that an LLM writes from the run log so far, refreshed asynchronously. Plus: port the label wording just applied to the vanilla page (`2c1e213`) into the React HUD/DataView so the demo UI speaks the same language. Demo-ready before freeze; `dist/` stays committed; vanilla fallback untouched.

**Architecture:** All work in `commons/ui/` + one new endpoint in `commons/server.py` (`POST /summarize {run_id, up_to_round?}` → reads `runs/<run_id>/rounds.jsonl`, one `mistral-medium-latest` call (`reasoning_effort="none"`, ~fast) returns `{"run_id", "round", "summary"}` and appends to `runs/<run_id>/summary.jsonl`; never called inside the round loop, max one in flight — respects the README model contract: large-4 stays reserved for Inspector + final report). Scene engine (`src/scene/engine.js`) gains: centered layout, reaction hooks. New `SummaryBox` component shown in Scene HUD (collapsible card) and DataView.

**Tech Stack:** unchanged (React 18 + Vite + Canvas 2D + Chart.js; server FastAPI). Summary uses the existing `commons/fishers.py` `call_json` helper with `config.FISHER_MODEL`.

## Design spec

- **Centered pond:** lake center at `(W/2, H*0.52)` with radius `min(W,H)*0.40` (bigger than now), HUD overlays the top without pushing the scene; boat ring centered on the lake; composition balanced left/right; on narrow screens center stays `W/2`.
- **Reactive visuals (say/do):**
  - `say`-driven: bubble tint — cooperative words (fair, share, together, all) → green bubble + boat gentle nod; boastful/aggressive words (plenty, mine, take, endless) → amber bubble; bubble pop already exists. Boat leans (rotate ±4°) toward its bubble for 0.5 s when `say` changes.
  - action-driven: `catch > 0` → boat dips (scaleY squash 0.15 s) + fish arcs (exist); `fined > 0` → boat shake + red ring + floating "−N fish" text particle; `banned` → boat **sails to the shore and docks** (target = shoreline point, greyed, 🚫), returns when ban expires; `report != catch` → purple flash (exists) + small ❓ marker above boat for that round; stock crossing K/2 → sky tint shifts a notch.
- **Summary box / summary agent:** `POST /summarize` (above) + `SummaryBox.jsx`: card bottom-left in Scene view ("What happened so far" + 2-4 sentence plain-English summary + round covered), refresh button + auto-refresh every 5 rounds for the selected run, loading spinner, cached per (run, round); in DataView it's a full panel under Inspector. Announce the new endpoint to the team (contracts rule).
- **Label port:** apply the `2c1e213` wording to React: Hud/TopBar buttons ("Start a new village", "Check my rule", "Enforce it", "🎙 Speak a rule", advanced toggle hiding seed with random default + village-nº tooltip), run picker Demo/All-runs optgroups with friendly names, rule preview as one plain sentence ("Understood as: … Not enforced yet." / red "Nobody checks this rule."), "Rule in force:", results table plain-word rule names + "Rounds survived (of 30)" / "False reports" headers, stock chart legend "Healthy level (500)".

## File map

- Edit: `commons/ui/src/scene/engine.js` (centering, reactions), `commons/ui/src/components/Scene.jsx`, `Hud.jsx`, `TopBar.jsx`, `DataView.jsx`, `ResultsTable.jsx`, `StockChart.jsx`, `App.jsx`, `styles.css`, `api.js`
- Create: `commons/ui/src/components/SummaryBox.jsx`
- Edit: `commons/server.py` (add `POST /summarize` only)
- Untouched: `commons/static/index.html` (already relabelled), all existing endpoints, `runs/**` except new `summary.jsonl` files (gitignored under `runs/`)

## Environment setup

```bash
git checkout commons && git pull --rebase origin commons
cd commons/ui && npm install && npm run build
cd ../.. && export MISTRAL_API_KEY="$MISTRAL_API_KEY" && .venv/bin/python -m commons.server
```

---

### Task 1: Center the pond

**Files:** edit `src/scene/engine.js`

- [ ] **Step 1:** `center()` → `{x: S.W / 2, y: S.H * 0.52}`; `baseR()` → `min(W,H) * 0.40` (min 60); boat ring multipliers stay proportional to R so the ring stays centered; verify no HUD overlap (HUD is absolute overlay, doesn't affect canvas).
- [ ] **Step 2: Verify**

Run: `npm run build`, node engine smoke (fake-canvas script from the scene plan): load `phase0-seed0` round 1, snapshot → assert `center` used by boats is near `(W/2, H*0.52)` (check a boat target's midpoint ≈ center). Browser: pond visually centered, boats ring symmetric.
Expected: pond dead-center, ring symmetric, no empty left side.

### Task 2: Say/do-driven reactions in the engine

**Files:** edit `src/scene/engine.js`, `src/components/Scene.jsx`, `styles.css`

- [ ] **Step 1:** keyword tint in `setRound`: classify `f.say` (cooperative vs boastful) → `boat.tint` (green/amber/none), `boat.leanUntil`, set `boat.docked = f.banned`; banned boats get target at shoreline (`R*1.12` at their angle) instead of ring.
- [ ] **Step 2:** action particles: `fined > 0` (new since prev) → shake boat 0.4 s + red ring + floating text particle "−N"; `report != catch` → purple flash (exists) + ❓ marker particle; `catch > 0` → boat dip (squash timer) + fish arcs (exist).
- [ ] **Step 3:** draw boats with `rotate(lean)` and `scale(1, dip)` transforms; floating text particles rendered on canvas.
- [ ] **Step 4: Verify**

Node engine smoke: feed `seed0-004` rounds (has fines/bans from round 5) → assert some boat gets `docked`/`flashUntil` set and particles spawned. Browser: play `seed0-004` — banned boat visibly sails to shore and greys, fined boat shakes with red ring, bubbles tint by wording.

### Task 3: Summary agent endpoint (server)

**Files:** edit `commons/server.py`

- [ ] **Step 1:** add

```python
class SummarizeBody(BaseModel):
    run_id: str
    up_to_round: int = 0


@app.post("/summarize")
async def summarize(body: SummarizeBody):
    rounds = _read_rounds(body.run_id)
    if body.up_to_round:
        rounds = [r for r in rounds if r["round"] <= body.up_to_round]
    if not rounds:
        raise HTTPException(404, f"run {body.run_id} has no rounds yet")
    text = summarize_rounds(rounds)   # one call_json call, FISHER_MODEL, reasoning none, JSON {"summary": str}
    rec = {"run_id": body.run_id, "round": rounds[-1]["round"], "summary": text}
    try:
        with open(os.path.join(RUNS_DIR, body.run_id, "summary.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
    except OSError:
        pass
    return rec
```

with `summarize_rounds` building a compact prompt from the records (round, stock, catches vs reports, fines, bans, rule changes, notable says) and calling `fishers.call_json(..., model=config.FISHER_MODEL, max_tokens=400, temperature=0.3)`; guard one-in-flight with an `asyncio.Lock`; wrap parser failures in HTTPException 502. Import `from . import fishers` (add) — note `call_json` sends `reasoning_effort="none"` already.
- [ ] **Step 2: Verify**

Run: TestClient with `commons.rules`-style stub of the parser (monkeypatch `fishers.call_json`) → `POST /summarize {"run_id": "phase0-seed0"}` returns 200 with `summary`, appends `runs/phase0-seed0/summary.jsonl` (delete after test); without key → 502. Real key: returns a readable 2-4 sentence summary.
Expected: endpoint works, contract-safe (medium model, not in round loop).

### Task 4: SummaryBox UI (scene + data)

**Files:** create `src/components/SummaryBox.jsx`; edit `api.js` (`summarize(runId, upTo)`), `App.jsx` (state + poll), `Scene.jsx`, `DataView.jsx`, `styles.css`

- [ ] **Step 1:** `SummaryBox` props `{runId, round}` — card with title "What happened so far", body text, "round N" footer, refresh button; auto-refresh when `round` crosses a multiple of 5 (App effect); cache last (runId, round) to avoid refetch; loading spinner; error → toast.
- [ ] **Step 2:** Scene view: collapsible card bottom-left (`<details>`-style toggle), above the view toggle. DataView: full panel next to Inspector.
- [ ] **Step 3: Verify**

Build + browser: select `batch-no-rule-s2` → SummaryBox fills with a summary of the collapse; select a live run mid-flight → summary updates as rounds pass. TestClient: `/summarize` wired.

### Task 5: Port the label wording into the React UI

**Files:** edit `Hud.jsx`, `TopBar.jsx`, `DataView.jsx`, `ResultsTable.jsx`, `StockChart.jsx`, `App.jsx`, `api.js`

- [ ] **Step 1:** Buttons/labels exactly as in `2c1e213`: "Start a new village", "Check my rule", "Enforce it", "🎙 Speak a rule"; `advanced` toggle hiding the seed input (random default 0-9999, tooltip "Village number. The same number gives a similar run.").
- [ ] **Step 2:** Run picker with `Demo` optgroup (the four friendly names) + `All runs`; friendly-name map shared via `src/labels.js` (also used by ResultsTable rule renames; export `FRIENDLY_RUNS`, `RULE_WORDS`, `ruleSentence(rule)`, `optionLabel(id, live)` — mirror of the vanilla implementations, single source in React).
- [ ] **Step 3:** Rule preview as one plain sentence via `ruleSentence` ("Understood as: … Not enforced yet."; red "Nobody checks this rule." when `inspection_prob` is 0); "Rule in force:" banner; results headers "Rounds survived (of 30)" / "False reports"; chart legend "Healthy level (500)".
- [ ] **Step 4: Verify**

Build; TestClient: `/static/index.html` and `/` (React) both contain the new labels where applicable; node test of `ruleSentence` in `src/labels.js` matches vanilla output for the example rule.

### Task 6: Rebuild, verify end-to-end, update runbook

- [ ] **Step 1:** `npm run build`; commit source + `dist`; TestClient smoke: `/` React shell, assets 200, all API endpoints incl. `/summarize` (stubbed) unchanged, vanilla fallback intact.
- [ ] **Step 2:** Node engine smoke re-run (centering assertions + reactions) — must pass.
- [ ] **Step 3:** Update the demo runbook: scene view centered pond; play "No rule (lake dies)" → boats react, lake dies with rain; "Quota with inspections (survives)" + SummaryBox narration; 📊 Data for numbers. Announce `POST /summarize` in the team channel (contracts rule).
- [ ] **Step 4: Verify**

Full smoke + `git status` shows only `commons/ui/**`, `commons/server.py`, plan docs.

---

## Risks

- Summary endpoint must not hammer the API: one call per refresh, 5-round cadence, lock-guarded; medium model only (large-4 contract untouched).
- Centering change is layout-only; re-run the node engine smoke to catch regressions.
- Time: freeze 16:45 — critical path is Tasks 1, 2, 4; Task 3 (summary) can fall back to a static "last events" list (no LLM) if the endpoint is not working 45 min before freeze.

## Verification (whole plan)

- [ ] `npm run build` exits 0; `dist` committed.
- [ ] Node engine smoke: centered layout + reaction flags fire on real run data (`seed0-004` fines/bans, `phase0-seed0` death).
- [ ] TestClient: `/` React, `/static/index.html` vanilla labels, `/api/*` + `/run`, `/parse`, `/rule`, `/state/{id}`, `/summarize` (stubbed + keyless 502), inspector source, batch 27 rows; fallback without `dist`.
- [ ] Browser checklist on the demo Mac: pond centered and larger; boats react to says (tint/lean) and actions (dock on ban, shake on fine, dip on catch, ❓ on lie); SummaryBox narrates the run and updates every 5 rounds; Data view has all panels with new labels; no console errors.

**Definition of done:** pond centered, scene reacts to say/do, summary box narrates via the summary agent, labels consistent between React and vanilla pages, `dist` rebuilt and pushed to `origin commons` before freeze, vanilla fallback intact.
