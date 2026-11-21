import { useRef, useState } from "react";
import { api } from "../api";

export default function TopBar(p) {
  const [seed, setSeed] = useState(0);
  const [micOn, setMicOn] = useState(false);
  const [micStatus, setMicStatus] = useState("");
  const recorder = useRef(null);
  const chunks = useRef([]);

  const toggleMic = async () => {
    if (recorder.current && recorder.current.state !== "inactive") {
      recorder.current.stop();
      return;
    }
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({audio: true});
    } catch (e) {
      p.notify("mic error: " + e.message);
      return;
    }
    chunks.current = [];
    const mr = new MediaRecorder(stream);
    mr.ondataavailable = (e) => { if (e.data.size) chunks.current.push(e.data); };
    mr.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      setMicOn(false);
      setMicStatus("transcribing…");
      try {
        const blob = new Blob(chunks.current, {type: mr.mimeType || "audio/webm"});
        const data = await api.transcribe(await blob.arrayBuffer());
        p.onRuleText(data.text);
        setMicStatus("transcript in rule box");
      } catch (e) {
        setMicStatus("");
        p.notify("transcribe failed: " + e.message);
      }
    };
    recorder.current = mr;
    mr.start();
    setMicOn(true);
    setMicStatus("recording… click again to stop");
  };

  const pauseLabel = p.liveRunId ? (p.followLive ? "pause" : "resume live") : "pause";

  return (
    <div id="topbar">
      <h3>Commons</h3>
      <label>run
        <select value={p.runId} onChange={(e) => p.onPickRun(e.target.value)} title="pick a saved or live run">
          {p.runs.map((r) => (
            <option key={r.name} value={r.name} style={r.active ? {color: "#2ecc71"} : undefined}>
              {r.name}{r.active ? " ●LIVE" : ""}
            </option>
          ))}
        </select>
      </label>
      <label>seed
        <input type="number" value={seed} style={{width: 60}} title="seed for a new run" onChange={(e) => setSeed(+e.target.value || 0)} />
      </label>
      <button title="start a live run with this seed" onClick={() => p.onStartRun(seed)}>start run</button>
      <button title="play the replay (space)" onClick={p.onPlay}>{p.playing ? "pause" : "play"}</button>
      <button title="pause replay / stop following a live run" onClick={p.onPause}>{pauseLabel}</button>
      <input type="range" min={1} max={p.maxRounds} value={p.cur} style={{flex: 1}}
        title="round slider (left/right arrows)" onChange={(e) => p.onScrub(+e.target.value)} />
      <span id="roundlabel">{p.roundLabel}</span>
      <span id="status">{p.statusText}</span>
      <input type="text" value={p.ruleText} placeholder="type a rule: nobody may take more than 6 fish..."
        style={{flex: 1}} title="rule text — parse to preview, then apply" onChange={(e) => p.onRuleText(e.target.value)} />
      <button title="parse the rule text (preview only, no effect yet)" onClick={p.onParse}>parse</button>
      <button title="apply the parsed rule to the selected live run" disabled={p.applyDisabled} onClick={p.onApply}>apply</button>
      <button id="mic" className={micOn ? "recording" : ""} title="record a rule aloud; the transcript fills the rule box" onClick={toggleMic}>● rec</button>
      <span id="micstatus">{micStatus}</span>
    </div>
  );
}
