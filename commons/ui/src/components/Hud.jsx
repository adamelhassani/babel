import { useState } from "react";
import { useMic } from "../hooks";

export default function Hud(p) {
  const [seed, setSeed] = useState(0);
  const mic = useMic(p.notify, p.onRuleText);
  const pauseLabel = p.liveRunId ? (p.followLive ? "pause" : "resume live") : "pause";

  return (
    <div className="hud">
      <h3>Commons</h3>
      <select value={p.runId} onChange={(e) => p.onPickRun(e.target.value)} title="pick a saved or live run">
        {p.runs.map((r) => (
          <option key={r.name} value={r.name} style={r.active ? {color: "#2ecc71"} : undefined}>
            {r.name}{r.active ? " ●LIVE" : ""}
          </option>
        ))}
      </select>
      <input type="number" value={seed} style={{width: 56}} title="seed for a new run" onChange={(e) => setSeed(+e.target.value || 0)} />
      <button title="start a live run with this seed" onClick={() => p.onStartRun(seed)}>start run</button>
      <button title="play the scene (space)" onClick={p.onPlay}>{p.playing ? "pause" : "play"}</button>
      <button title="pause / stop following a live run" onClick={p.onPause}>{pauseLabel}</button>
      <input type="range" min={1} max={p.maxRounds} value={p.cur} className="hudslider"
        title="round slider (left/right arrows)" onChange={(e) => p.onScrub(+e.target.value)} />
      <span className="hudlabel">{p.roundLabel}</span>
      <span className="hudlabel stock" key={p.statusText}>{p.statusText}</span>
      <input type="text" value={p.ruleText} placeholder="type a rule: nobody may take more than 6 fish..." className="hudrule"
        title="rule text — parse to preview, then apply" onChange={(e) => p.onRuleText(e.target.value)} />
      <button title="parse the rule text (preview only, no effect yet)" onClick={p.onParse}>parse</button>
      <button title="apply the parsed rule to the selected live run" disabled={p.applyDisabled} onClick={p.onApply}>apply</button>
      <button className={mic.micOn ? "recording" : ""} title="record a rule aloud; the transcript fills the rule box" onClick={mic.toggle}>● rec</button>
      <span className="hudlabel">{mic.micStatus}</span>
      {p.preview && (
        <span className={"previewchip " + (p.preview.applied ? "applied" : "")}>
          {p.preview.applied ? "applied ✓" : "preview — not applied yet"}
        </span>
      )}
    </div>
  );
}
