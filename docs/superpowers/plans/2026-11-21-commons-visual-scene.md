# Commons "living scene" visual overhaul plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Turn the Commons UI from a dashboard into a living visual scene. Default view = a full-viewport animated lake scene (canvas): when you press **play/start**, boats sail to new spots each round, fish arc out of the water into boats with splashes, the lake visibly shrinks/desaturates as stock drops, a rule apply sends a golden ripple across the water, and the lake dying triggers rain + screen shake + a LAKE DEAD stamp. The existing charts/tables/inspector move behind a **"Data"** toggle so demo numbers stay one click away. Demo-ready before freeze 16:45; the committed `commons/ui/dist` keeps working at all times and the vanilla page stays as ultimate fallback.

**Why (from the 15:51 screenshot):** current layout is a 3-column panel grid — flat gradient circle for the lake, boats frozen on a static ring, an empty Inspector panel ("not ready yet"), charts in cards. It reads as a dashboard, not a scene.

**Architecture:** Same React app (`commons/ui/`), same API contract, same server. New default view `Scene` (a `<canvas>` + rAF engine in `src/scene/`), with the current panels moved into `DataView` behind a view toggle. A single `scene/engine.js` owns animation state (boat positions/targets, particles, fish, ripples, weather); components only feed it the current round record (`rec`) and user intents (play/pause/scrub). Canvas caps `devicePixelRatio` at 2, pauses when the tab is hidden, and `prefers-reduced-motion` renders a static frame. No new runtime deps — plain Canvas 2D, no WebGL.

**Tech Stack:** unchanged — React 18 + Vite 5 + Chart.js (charts only in Data view now); Canvas 2D for the scene; CSS for HUD/glass overlay.

## Scene design spec

- **Sky/surroundings:** vertical gradient that shifts with lake health (stock/K): healthy = deep blue sky + sun + drifting clouds; mid = hazy teal; dying = storm grey with rain streaks; dead = near-black red horizon + vignette. Vignette + subtle grain overlay always.
- **Lake:** organic blob (radial radius modulated by layered sine noise, slowly morphing), not a perfect circle; radial gradient fill darkening with depth; moving wave highlights; shoreline sand ring; **fish silhouettes** under the surface, count ∝ stock (cap ~40), swimming on slow Lissajous paths, occasionally jumping.
- **Boats:** 10 boats that **sail** — on each round change every boat picks a new target angle/radius around the lake and eases toward it (0.8 s, easeOutCubic), bobbing on the wave field, leaving fading wake trails. Speech bubble pops above the boat with a spring scale-in when `say` changes. Banned = 🚫 + grayscale; fined = red pulse ring. Hover/click boat → name + wealth + catch tooltip card.
- **Catch animation:** for each fisher with `catch > 0` on round change, spawn `catch` (cap 5) fish-arc particles: quadratic bezier from a random lake point to the boat, splash droplets on landing, ripple ring. `report != catch` → the boat's bubble flashes purple briefly (the "lie" tell).
- **Round flow:** play advances `cur` every ~1.2 s with a soft zoom pulse on the lake and the stock number in the HUD counting to the new value; scrubbing the slider just re-renders the scene state for that round.
- **Rule applied:** golden ripple rings expanding from the lake center + floating banner with the rule's `plain_text` (fades after 3 s).
- **Lake dead:** desaturate whole scene, rain starts, slight screen shake for 1 s, big red "LAKE DEAD" stamp scales in; stock counter red.
- **Survived 30 rounds:** confetti burst + "THE LAKE LIVES" banner.
- **HUD (overlay, glassy, minimal):** run picker (with ●LIVE), seed + start run, play/pause, round slider + `round X/N`, stock readout, rule input + parse + apply + mic, view toggle (🌊 Scene / 📊 Data), toast, hint. Rule preview chip floats bottom-left.
- **Data view:** exactly the current grid (lake mini-map optional, StockChart, CatchChart, ResultsTable, InspectorPanel, RuleBar) — used for the numbers in the demo script. Inspector "not ready" state gets a nicer empty state (spinner + text).

## File map

- Create: `commons/ui/src/scene/engine.js` (rAF loop, particle/fish/ripple/wave systems, boat movers, weather), `commons/ui/src/scene/layout.js` (boat target positions per round, seeded), `commons/ui/src/components/Scene.jsx` (canvas + HUD overlay), `commons/ui/src/components/Hud.jsx`, `commons/ui/src/components/DataView.jsx`
- Edit: `commons/ui/src/App.jsx` (view state `scene|data`, default `scene`; pass `rec` + intents to Scene; render DataView on toggle), `commons/ui/src/styles.css` (scene/HUD styles, view toggle, empty-state), `commons/ui/src/components/{LakeScene,TopBar,RuleBar}.jsx` (move into DataView / slim down; LakeScene kept as mini-map in Data view)
- Untouched: `commons/server.py`, all endpoints, vanilla `commons/static/index.html`, `runs/**`

## Environment setup (same as React plan)

```bash
git checkout commons && git pull --rebase origin commons
cd commons/ui && npm install && npm run build
cd ../.. && .venv/bin/python -m commons.server   # http://127.0.0.1:8000
```

---

### Task 1: View scaffold — Scene default + DataView toggle

**Files:** edit `App.jsx`, `styles.css`; create `components/DataView.jsx`, `components/Scene.jsx` (stub)

- [x] **Step 1:** `App.jsx`: add `const [view, setView] = useState("scene")`. Render `<Scene .../>` when `view === "scene"`, else `<DataView .../>` with the existing panels (StockChart, CatchChart, ResultsTable, InspectorPanel, RuleBar, LakeScene mini). Add a toggle button in the HUD/topbar: `🌊 Scene` / `📊 Data`.
- [x] **Step 2:** `Scene.jsx` stub renders a full-viewport `<canvas>` + HUD for now; `DataView.jsx` hosts the current panel grid unchanged.
- [x] **Step 3: Verify**

Run: `npm run build` && restart server && open page.
Expected: page loads into the scene view (canvas full screen), toggle switches to the current dashboard grid and back; `/api/*` calls unchanged (check server log / TestClient smoke).

### Task 2: Scene engine core (rAF loop, waves, blob lake, sky/weather)

**Files:** create `src/scene/engine.js`, flesh out `Scene.jsx`

- [x] **Step 1:** `engine.js`: `createScene(canvas)` returning `{start, stop, resize, setRound(rec, C), setHealth(stockFrac), burst(kind, x, y), shake(), setDead(bool)}`. Internals: rAF loop with dt clamp, `devicePixelRatio` cap 2, `document.hidden` pause, reduced-motion → single static render. Systems: sky gradient by health, clouds (3-5 drifting ellipses), rain (streak particles when dead), lake blob (radius = f(stock) with per-angle sine noise animated over time), wave highlight bands, vignette + grain (precomputed noise canvas, low alpha).
- [x] **Step 2:** `Scene.jsx`: canvas sized to window (`ResizeObserver`), engine driven by props: on `rec` change call `engine.setRound(rec)`; health from `rec.stock_after / C.K`.
- [x] **Step 3: Verify**

Run: `npm run build`, open page, pick `phase0-seed0`, scrub slider to round 6.
Expected: animated water, morphing shoreline, sky darkens and rain starts at round 6 (stock 7.28 < 50), LAKE DEAD handled in Task 5; no console errors; CPU reasonable (check via `top` on the dev machine, not required in CI).

### Task 3: Moving boats + wakes + bubbles + states

**Files:** `src/scene/engine.js`, `src/scene/layout.js`, `Scene.jsx`

- [x] **Step 1:** `layout.js`: deterministic per-round boat targets — `boatTarget(i, round, seed)` → angle/radius jitter around the lake ring (seeded by round number so replay is stable).
- [x] **Step 2:** engine boat system: each boat has pos + target; on round change, assign new targets; integrate with easeOutCubic over 0.8 s; bob = sin(t*2 + i) * 3px on wave height at boat pos; wake = fading trail of small ellipses behind boats.
- [x] **Step 3:** render boats as small SVG-ish paths on canvas (hull + fisher dot); speech bubble drawn in DOM overlay (absolutely positioned divs synced from engine boat screen positions each frame — engine exposes `boatScreenPos(i)`) with CSS spring pop on `say` change; banned 🚫/grayscale; fined red pulse ring; ▶ speak button per boat (reuse `onSpeak`).
- [x] **Step 4: Verify**

Run: build, open page on `seed0-004` (has fines/bans from round 5), press play.
Expected: each round boats visibly sail to new positions with wakes; bubbles pop; fined boat shows red ring, banned boat 🚫; ▶ works.

### Task 4: Catch/lie animations + particles

**Files:** `src/scene/engine.js`, `Scene.jsx`

- [x] **Step 1:** on `setRound(rec)` compare with previous rec: for each fisher, spawn min(catch, 5) fish-arc particles (bezier lake→boat), splash droplets + ripple at landing; if `report != catch`, flash the boat bubble purple for 0.6 s.
- [x] **Step 2:** particle system: gravity droplets, fading ripples (expanding stroked circles), golden motes on rule apply, confetti on survive-30, splash on fish jump.
- [x] **Step 3:** fish silhouettes: count = round(stockFrac * 40), Lissajous swim paths under translucent surface layer; 1 fish jumps every ~4 s.
- [x] **Step 4: Verify**

Build, play `phase0-seed0` rounds 1-3.
Expected: on each round advance, fish arcs + splashes per catching boat, purple flash on liars (most fishers in phase 0), fish visible under water, count shrinking as stock drops.

### Task 5: Drama events — rule ripple, death, victory + HUD

**Files:** `src/scene/engine.js`, `Scene.jsx`, `Hud.jsx`, `styles.css`

- [x] **Step 1:** rule-change detection (same logic as `ruleMarkerRounds`): golden ripple rings + floating banner with `plain_text` (DOM overlay, 3 s fade).
- [x] **Step 2:** dead: `setDead(true)` → desaturate (draw scene to offscreen then apply grey overlay, or lerp palette), rain on, 1 s shake, red LAKE DEAD stamp (CSS scale-in). Recovery impossible (log ends) — fine.
- [x] **Step 3:** survive 30 rounds (no dead): confetti + "THE LAKE LIVES" banner.
- [x] **Step 4:** `Hud.jsx`: glass overlay top bar with run picker (●LIVE), seed+start, play/pause, slider, round + animated stock counter, rule input + parse + apply + mic, view toggle, toast mount, hint. Rule preview chip bottom-left. All existing TopBar logic moves here in compact form; TopBar stays for Data view.
- [x] **Step 5: Verify**

Build; script the demo: start run seed 0 (keyless fallback OK), type quota rule → parse → apply → golden ripple + banner appears; watch a live run to death or 30 rounds for the corresponding event.
Expected: events fire at the right rounds; HUD controls all work in scene view.

### Task 6: Data view polish + empty states

**Files:** `DataView.jsx`, `InspectorPanel.jsx`, `ResultsTable.jsx`, `styles.css`

- [x] **Step 1:** InspectorPanel empty state: spinner + "Inspector is analyzing… (it runs every 5 rounds, asynchronously)" instead of bare text.
- [x] **Step 2:** ResultsTable: keep; add a small note row count "9 rules × 3 seeds".
- [x] **Step 3: Verify**

Build; toggle to Data on `phase0-seed0` (no inspector output).
Expected: inspector shows the friendly waiting state; results table unchanged.

### Task 7: Performance + accessibility pass

**Files:** `engine.js`, `styles.css`, `Scene.jsx`

- [x] **Step 1:** rAF single loop, dt clamp 50 ms, particle caps (droplets ≤ 300, ripples ≤ 40, confetti ≤ 200), skip rendering when `document.hidden`, `prefers-reduced-motion` → static frame + no shake.
- [x] **Step 2:** keyboard shortcuts work in scene view (space/arrows), buttons focusable, HUD has aria-labels.
- [x] **Step 3: Verify**

Run: `npm run build`; open scene, play a full 6-round replay, open devtools Performance roughly or just observe smoothness on the Mac; toggle reduced-motion in OS settings → scene renders static, still readable.
Expected: smooth 60 fps on a laptop; static mode works; no console errors.

### Task 8: Rebuild dist, verify end-to-end, update runbook

**Files:** `commons/ui/dist/**` (rebuilt), plan docs, runbook

- [x] **Step 1:** `npm run build`; commit source + `dist`.
- [x] **Step 2:** TestClient smoke unchanged: `/` serves React shell, `/assets/*` 200, API endpoints identical, vanilla fallback intact when `dist` moved away.
- [x] **Step 3:** Update the demo runbook (in `2026-11-21-commons-ui-demo.md` Task 9): 1) scene view, press play on `phase0-seed0` → boats sail, fish arcs, lake dies with rain; 2) start live run, speak/type rule, parse, apply → golden ripple, lake recovers; 3) toggle 📊 Data → inspector gauge + results table for the numbers; keep under 3 min.
- [x] **Step 4: Verify**

Run the full TestClient smoke script from the React plan + live server check that `/` and assets serve; `git status` shows only `commons/ui/**` + plan docs.
Expected: all green.

---

## Risks

- **Time:** freeze is 16:45. Tasks 1-4 are the critical path (scene + boats + catch anims); Task 5 drama is next; 6-7 are polish. If time runs out, cut confetti/rain before cutting boat movement.
- **Performance on the demo machine:** canvas 2D at 1440x900 is fine on any modern laptop; caps + hidden-tab pause guard it. Keep `dist` committed so no rebuild is needed at demo time.
- **Don't break the numbers:** Data view must keep charts/results/inspector exactly as they are — the pitch needs them. Scene view is additive.
- **Fallbacks:** vanilla page + previous `dist` remain in git history; server fallback unchanged.

## Verification (whole plan)

- [x] `cd commons/ui && npm install && npm run build` exits 0.
- [x] TestClient: `/` = React shell with `dist`, `/assets/*.js|css` 200, `/api/runs` `{name,active}`, `/api/batch` 27 rows, inspector source `inspector_agent.jsonl`, `/parse` 502 without key; vanilla fallback when `dist` moved away.
- [ ] Browser checklist on the demo Mac (needs a real browser — engine verified headless in node against real run data): scene loads full-viewport animated; play on `phase0-seed0` → boats sail each round, fish arcs + splashes on catches, purple lie flashes, rain + shake + LAKE DEAD at round 6; start live run + parse/apply rule → golden ripple + banner; 📊 Data toggle shows charts/results/inspector; HUD controls all work; keyboard shortcuts; no console errors; smooth motion (or static under reduced-motion).

**Definition of done:** pressing play makes the scene visibly alive (boats moving, water animating, catch splashes, death/victory drama), the Data toggle preserves every demo number, `dist` rebuilt + committed + pushed to `origin commons` before 16:45, and the vanilla fallback still works.
