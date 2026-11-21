import { useState } from "react";
import { useMic } from "../hooks";
import { DEMO_RUNS, optionLabel } from "../labels.js";

export default function TopBar(p) {
  const [seed, setSeed] = useState(() => Math.floor(Math.random() * 10000));
  const [showAdv, setShowAdv] = useState(false);
  const mic = useMic(p.notify, p.onRuleText);
  const pauseLabel = p.liveRunId ? (p.followLive ? "pause" : "resume live") : "pause";

  const demoRuns = p.runs.filter((r) => DEMO_RUNS.includes(r.name));
  const otherRuns = p.runs.filter((r) => !DEMO_RUNS.includes(r.name));
  const runOpt = (r) => (
    <option key={r.name} value={r.name} style={r.active ? {color: "#2ecc71"} : undefined}>
      {optionLabel(r.name, r.active)}
    </option>
  );

  return (
    <div id="topbar">
      <h3>Commons</h3>
      <label>run
        <select value={p.runId} onChange={(e) => p.onPickRun(e.target.value)} title="pick a saved or live run">
          <optgroup label="Demo">{demoRuns.map(runOpt)}</optgroup>
          <optgroup label="All runs">{otherRuns.map(runOpt)}</optgroup>
        </select>
      </label>
      <button title="show advanced options" onClick={() => setShowAdv((v) => !v)}>advanced</button>
      {showAdv && (
        <label>village nº
          <input type="number" value={seed} style={{width: 70}}
            title="Village number. The same number gives a similar run."
            onChange={(e) => setSeed(+e.target.value || 0)} />
        </label>
      )}
      <button title="start a new village" onClick={() => p.onStartRun(seed)}>Start a new village</button>
      <button title="play the replay (space)" onClick={p.onPlay}>{p.playing ? "pause" : "play"}</button>
      <button title="pause replay / stop following a live run" onClick={p.onPause}>{pauseLabel}</button>
      <input type="range" min={1} max={p.maxRounds} value={p.cur} style={{flex: 1}}
        title="round slider (left/right arrows)" onChange={(e) => p.onScrub(+e.target.value)} />
      <span id="roundlabel">{p.roundLabel}</span>
      <span id="status">{p.statusText}</span>
      <input type="text" value={p.ruleText} placeholder="type a rule: nobody may take more than 6 fish..."
        style={{flex: 1}} title="rule text — check it, then enforce" onChange={(e) => p.onRuleText(e.target.value)} />
      <button title="check what the rule means (preview only, no effect yet)" onClick={p.onParse}>Check my rule</button>
      <button title="enforce the parsed rule on the selected live run" disabled={p.applyDisabled} onClick={p.onApply}>Enforce it</button>
      <button id="mic" className={mic.micOn ? "recording" : ""} title="record a rule aloud; the transcript fills the rule box" onClick={mic.toggle}>🎙 Speak a rule</button>
      <span id="micstatus">{mic.micStatus}</span>
    </div>
  );
}
