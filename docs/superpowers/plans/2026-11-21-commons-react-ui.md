# Commons React GUI plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the Commons screen into a React (Vite) GUI with polished, animated visuals, demo-ready before feature freeze 16:45 — with **zero API contract changes** and the current vanilla page (`commons/static/index.html`, already demo-ready at `d887b99`) kept as an automatic fallback, so the demo can never break because of the UI rewrite.

**Architecture:** React 18 + Vite app in `commons/ui/`, built to `commons/ui/dist/` and committed, so the demo machine needs no JS toolchain. `commons/server.py` serves `dist/index.html` at `/` when the build exists and falls back to `commons/static/index.html` otherwise; all API routes (`/api/*`, `/run`, `/parse`, `/rule`, `/state/{id}`, `/transcribe`, `/speak`) are unchanged and registered before any static mount. Chart.js is bundled via npm instead of the CDN — one less runtime internet dependency at demo time. Data flow is identical to the vanilla page: poll `/state/{run_id}` every 1 s for live runs, `/api/runs` for the picker (+ `active` flags), `/api/runs/{id}/inspector`, `/api/batch`.

**Tech Stack:** Node 20+ / npm (sandbox has Node v22.23.5, npm 10.9.9), Vite 5, React 18, `chart.js` + `react-chartjs-2`, hand-written CSS with variables (no Tailwind — keep deps minimal). Backend untouched except the static-serving fallback in `commons/server.py`.

## Risks and gates

- The role file says "vanilla JS, no build step" — this plan overrides it (user request). **Ownership note:** role files say Screen owns only `commons/server.py` and `commons/static/index.html`; the new `commons/ui/` directory needs a one-line OK from the team. Everything stays inside `commons/`; the root `.gitignore` (Engine-owned) is not touched — `commons/ui/.gitignore` ignores `node_modules/`.
- **Go/no-go gate, T-60 min before freeze:** if `npm run build` has not produced a working `dist/` by then, stop and demo the vanilla page. The fallback in `server.py` makes this automatic even if `dist/` is missing.
- `npm install` needs internet once, on the build machine; afterwards the committed `dist/` is served statically.
- Timebox: tasks 1-3 are the critical path; if any of them slips, cut visual polish (Task 9) before cutting components.

## Visual design spec (the "better visuals")

- **Theme:** dark navy background (`#0b1020`), CSS variables, system/Inter font, cards = 12px radius, 1px border, soft shadow. Accents: lake `#38bdf8`, sustainable `#34d399`, warning `#fbbf24`, danger `#f87171`, inspector `#a78bfa`.
- **LakeScene (SVG, animated):** layered wave paths translating on CSS keyframes over a radial-gradient lake whose radius/color scale with stock (blue → grey when `< F_DEAD`); big stock number in the center; a red "LAKE DEAD" stamp when dead; a **ripple burst when a rule is applied** (watch for rule-change rounds); a faint dashed ring at K/2.
- **Boats:** 10 SVG boats on a ring, each bobbing with a staggered animation delay; speech bubble with tail that fades/slides in when `say` changes; banned = 🚫 + grayscale, fined = red pulsing ring; hover tooltip shows wealth/fines/ban; ▶ button speaks the line.
- **Charts (Chart.js, bundled):** stock line with gradient area fill, 300 ms animated transitions, labeled dashed `K/2 = 500` line, rule-applied markers as amber flag triangles with the rule's `plain_text` in the tooltip; catch chart = rounded bars (catch orange vs report purple) + labeled green dashed sustainable 6.25 line.
- **Results table:** sticky header, row hover, the best rule (max avg rounds survived) row highlighted green, inline mini bar for rounds survived, percentages formatted.
- **Inspector panel:** header shows source file + **running mean score vs the 0.30 baseline as a gauge bar** with a tick at baseline; one card per check: round, accused chips (green ✓ when also in true top-3, red otherwise), true top-3 chips, precision/recall, reasons on hover.
- **Topbar:** sticky glassy bar with grouped labeled controls, pulsing LIVE badge on active runs, hint pill bottom-center (auto-dismiss), red error toasts top-right, tooltips on every button, keyboard shortcuts (space = play/pause, ←/→ = scrub).

## File map

- Create: `commons/ui/package.json`, `commons/ui/vite.config.js`, `commons/ui/index.html`, `commons/ui/.gitignore` (`node_modules/`), `commons/ui/src/main.jsx`, `commons/ui/src/App.jsx`, `commons/ui/src/api.js`, `commons/ui/src/styles.css`, `commons/ui/src/hooks.js`, `commons/ui/src/components/{TopBar,LakeScene,StockChart,CatchChart,ResultsTable,InspectorPanel,RuleBar,Toast,Hint}.jsx`
- Create (build output, committed): `commons/ui/dist/**`
- Edit: `commons/server.py` — serve `commons/ui/dist` at `/` when present, else the current `commons/static/index.html` (Task 2 only)
- Edit: this plan's checkboxes as tasks complete

## Environment setup (do once before Task 1)

```bash
git checkout commons && git pull --rebase origin commons
node --version        # expect >= 20 (sandbox: v22.23.5, npm 10.9.9)
cd commons/ui && npm install && npm run build && ls dist/index.html
cd ../.. && .venv/bin/python -m commons.server   # http://127.0.0.1:8000
```

---

### Task 1: Scaffold the Vite + React app

**Files:**
- Create: `commons/ui/package.json`, `commons/ui/vite.config.js`, `commons/ui/index.html`, `commons/ui/.gitignore`, `commons/ui/src/main.jsx`

- [ ] **Step 1: `package.json`**

```json
{
  "name": "commons-ui",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "chart.js": "^4",
    "react": "^18",
    "react-chartjs-2": "^5",
    "react-dom": "^18"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4",
    "vite": "^5"
  }
}
```

- [ ] **Step 2: `vite.config.js`**

```js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "./",
  build: { outDir: "dist" },
});
```

- [ ] **Step 3:** `commons/ui/index.html` (Vite entry, `<div id="root">` + `<script type="module" src="/src/main.jsx">`), `commons/ui/.gitignore` containing `node_modules/`, and `src/main.jsx` rendering `<App/>` into `#root` and importing `./styles.css`.

- [ ] **Step 4: Verify**

Run: `cd commons/ui && npm install && npm run build && ls dist/index.html dist/assets | head`
Expected: install succeeds, `dist/index.html` and hashed JS/CSS assets exist.

### Task 2: server.py — serve the React build with vanilla fallback

**Files:**
- Edit: `commons/server.py`

- [ ] **Step 1:** Add near the top:

```python
DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "dist")
DIST_INDEX = os.path.join(DIST_DIR, "index.html")
```

- [ ] **Step 2:** Replace the `GET /` handler and the `/static` mount with (keep all API routes above them):

```python
@app.get("/")
def index():
    if os.path.isfile(DIST_INDEX):
        return FileResponse(DIST_INDEX)
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


if os.path.isdir(DIST_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
```

- [ ] **Step 3: Verify**

Run: `.venv/bin/python - <<'EOF' ... TestClient ... EOF` asserting: with `dist/` present `GET /` returns the React HTML (contains `id="root"`); after `mv commons/ui/dist /tmp/dist-bak`, `GET /` returns the vanilla page (contains `chart.js@4` CDN tag); restore `dist`. All `/api/*`, `/run`, `/parse`, `/rule`, `/state/{id}` responses unchanged.
Expected: both branches 200, API smoke passes in both.

### Task 3: API client + hooks

**Files:**
- Create: `commons/ui/src/api.js`, `commons/ui/src/hooks.js`

- [ ] **Step 1:** `api.js` — thin fetch wrappers: `getConstants, listRuns, getRounds(runId), getState(runId), getInspector(runId), getBatch, postRun(seed), postParse(text), postRule(runId, text), postTranscribe(bytes), postSpeak(text)`; non-OK responses throw with the response body text.
- [ ] **Step 2:** `hooks.js` — `useRuns()` (picker data incl. `active`, refreshed on an interval), `useRounds(runId)` (initial load; returns `{rounds, cur, setCur}`), `useLivePoll(liveRunId, followLive)` (1 s interval on `/state/{id}`, auto-advance `cur` only when `followLive`, clears `liveRunId` when `active` false), `useInspector(runId)`, `useBatch()` (refresh every 5 s).
- [ ] **Step 3: Verify**

Run: `npm run build` then TestClient smoke against the running server (same script as Task 2 Step 3) plus a manual `npm run dev` sanity check that the page renders the topbar with the run picker populated.
Expected: build OK; picker lists all `runs/*` folders with LIVE badges when a run is active.

### Task 4: TopBar + Toast + Hint components

**Files:**
- Create: `commons/ui/src/components/TopBar.jsx`, `Toast.jsx`, `Hint.jsx`; wire into `App.jsx`

- [ ] **Step 1:** TopBar: run picker (options `name + (active ? " ●LIVE" : "")`), seed input, start run, play, pause ("resume live" toggle when following a live run), round slider + `round X / N` label, status (stock / lake dead), rule text input, parse, apply (disabled until a preview exists), mic record button + mic status.
- [ ] **Step 2:** Toast (red, top-right, auto-dismiss 5 s, `toast(msg)` via context or simple event bus) and Hint (bottom pill, auto-dismiss 8 s, hidden on first interaction). All buttons keep their `title` tooltips; keyboard shortcuts (space, ←/→) in a `useEffect` keydown listener.
- [ ] **Step 3: Verify**

Run: `npm run build`, restart server, open page at 1440x900.
Expected: sticky topbar with all controls; hint visible then fades; starting a run shows ●LIVE and the slider follows; pause freezes the view ("resume live"); a failed `/parse` (unset key) shows a red toast.

### Task 5: LakeScene — animated lake + boats

**Files:**
- Create: `commons/ui/src/components/LakeScene.jsx`

- [ ] **Step 1:** SVG lake: radial gradient fill, radius ∝ sqrt(stock/K), animated wave layers (two `<path>`s with CSS `@keyframes` translateX loop), stock number centered, "LAKE DEAD" stamp when `stock_after < F_DEAD`, ripple burst when the selected round is a rule-change round (compare with previous round's `rule`).
- [ ] **Step 2:** Boats: 10 positioned on a ring, bobbing (`@keyframes bob`, staggered `animation-delay`), bubble with tail + fade-in on `say` change, 🚫/grayscale when banned, red pulse ring when fined, hover tooltip with wealth/fines, ▶ speaks via `postSpeak` + `Audio`.
- [ ] **Step 3: Verify**

Replay `phase0-seed0`: waves animate, round 1 → full blue lake with "600"; scrub/play to round 6 → grey lake + LAKE DEAD. Replay `seed0-004`: rule round shows ripple + gold chart marker; fined/banned boats show states.

### Task 6: Charts (StockChart, CatchChart)

**Files:**
- Create: `commons/ui/src/components/StockChart.jsx`, `CatchChart.jsx`

- [ ] **Step 1:** Register Chart.js components (`Chart.register(...registerables)`) in `main.jsx` or a `charts.js` module; use `react-chartjs-2` `<Line>`/`<Bar>`.
- [ ] **Step 2:** StockChart: gradient area fill under the stock line, dashed labeled `K/2 = 500` dataset, rule-applied markers as amber triangles (points only) with `plain_text` in tooltip, y 0..K, animated 300 ms.
- [ ] **Step 3:** CatchChart: rounded bars catch vs report, green dashed sustainable 6.25 line (from `/api/constants` `PER_FISHER_SUSTAINABLE`), y 0..C_MAX.
- [ ] **Step 4: Verify**

Open the page on `phase0-seed0`: both charts render and update when scrubbing; legend readable on dark theme.

### Task 7: ResultsTable + InspectorPanel

**Files:**
- Create: `commons/ui/src/components/ResultsTable.jsx`, `InspectorPanel.jsx`

- [ ] **Step 1:** ResultsTable from `/api/batch`: group by `rule_name`, average numeric columns over seeds, sort by avg rounds survived desc, best row highlighted, mini bar for rounds survived, % formatting. (Read columns by name — the CSV has extra `start_round`/`min_wealth` columns.)
- [ ] **Step 2:** InspectorPanel from `/api/runs/{id}/inspector` (source `inspector_agent.jsonl` preferred — server already handles it): header with source + running mean score gauge vs baseline (tick at 0.30); per-check cards with accused chips (✓ green when in truly_lied) next to true top-3 chips, precision/recall, reasons on hover; "not ready yet" state on 404.
- [ ] **Step 3: Verify**

Pick `batch-quota6-30pct-3x-2ban-s0`: inspector shows 6 checks, mean 0.500 vs baseline 0.3; results table sorted with `no-rule`-style worst at the bottom and best highlighted.

### Task 8: RuleBar — parse / preview / apply + in-effect banner

**Files:**
- Create: `commons/ui/src/components/RuleBar.jsx`

- [ ] **Step 1:** Port the vanilla logic: parse → `POST /parse` → preview chips with amber "preview — not applied yet" tag + apply enabled; apply → `POST /rule` → green "applied ✓"; in-effect banner from the current round's `rule.plain_text`; apply disabled when the text changes; mic transcript fills the input and resets the preview.
- [ ] **Step 2: Verify**

With the key: type the quota sentence → parse → preview fields, log still `rule: null` → apply → applied tag + gold marker on stock chart next round. Without key: parse → toast with the 502 detail.

### Task 9: Polish pass (visuals) + responsive

**Files:**
- Edit: `commons/ui/src/styles.css`, components as needed

- [ ] **Step 1:** Apply the theme variables, card styling, animations (waves, bob, ripple, fade-ins, LIVE pulse), hover states, focus rings, `prefers-reduced-motion` respect.
- [ ] **Step 2:** Responsive: grid `400px 1fr 1fr` → 2 cols ≤1250px → 1 col ≤820px; lake panel spans 2 rows on wide screens.
- [ ] **Step 3: Verify**

Run: `npm run build`, reload at 1440x900 and at 900px width.
Expected: all panels visible without scrolling at 1440x900; single column at 900px; animations smooth; no console errors.

### Task 10: Build, commit dist, fallback check, runbook

**Files:**
- Edit: `commons/server.py` (already done in Task 2), `docs/superpowers/plans/2026-11-21-commons-ui-demo.md` (mark superseded sections), this plan

- [ ] **Step 1:** `npm run build`; commit `commons/ui/` source **and** `commons/ui/dist/` (demo machine needs no npm).
- [ ] **Step 2:** Verify fallback once more with TestClient: `dist` present → React HTML at `/`; `dist` temporarily moved → vanilla page at `/`; all API routes unchanged in both.
- [ ] **Step 3:** Update the demo runbook (Task 9 of the previous plan) to the React UI: same 5 steps, now with animated lake, gauge, and cards.
- [ ] **Step 4: Verify**

Run the full TestClient smoke (page + `/api/runs` shape + `/api/batch` + inspector source + `/parse` 502 without key) and the browser checklist: one screen at 1440x900, play/pause, LIVE badge, parse→apply, toasts, keyboard, results, inspector gauge.
Expected: all green; `git status` shows only `commons/ui/**`, `commons/server.py`, and the two plan docs.

---

## Verification (whole plan)

- [ ] `cd commons/ui && npm install && npm run build` — exits 0, `dist/index.html` exists.
- [ ] TestClient smoke (both with and without `dist/` present): `/` 200 in both modes (React vs vanilla), `/api/runs` returns `{name, active}` objects, `/api/batch` 27 rows, `/api/runs/batch-no-rule-s2/inspector` source `inspector_agent.jsonl`, `/parse` 502 without key, `/state/phase0-seed0` 6 rounds.
- [ ] Browser checklist at 1440x900, no scrolling: topbar + hint; lake with waves/stock/LAKE DEAD; boats with bubbles and states; both charts with labeled lines and rule flags; results table sorted with best highlighted; inspector cards with mean-vs-0.30 gauge; play/pause/follow LIVE; parse→preview→apply; mic; toasts; keyboard; responsive at 900px.

**Definition of done:** React build is served at `/` from committed `dist/`, all panels render from the live endpoints with the visuals above, the vanilla page still works as fallback, the API contract is byte-identical, and everything is committed and pushed to `origin commons` before 16:45. If the go/no-go gate fails, the vanilla page from `d887b99` is the demo.
