import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import Scene from "./components/Scene";
import DataView from "./components/DataView";
import Toast from "./components/Toast";
import Hint from "./components/Hint";

export default function App() {
  const [C, setC] = useState(null);
  const [view, setView] = useState("scene");
  const [runs, setRuns] = useState([]);
  const [runId, setRunId] = useState("");
  const [rounds, setRounds] = useState([]);
  const [cur, setCur] = useState(1);
  const [liveRunId, setLiveRunId] = useState(null);
  const [followLive, setFollowLive] = useState(true);
  const [batch, setBatch] = useState(null);
  const [inspector, setInspector] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);
  const [showHint, setShowHint] = useState(true);
  const [playing, setPlaying] = useState(false);
  const [ruleText, setRuleText] = useState("");
  const [preview, setPreview] = useState(null);
  const [summary, setSummary] = useState(null);
  const pollCount = useRef(0);
  const roundsRef = useRef([]);
  const lastSummaryRound = useRef(0);

  useEffect(() => { roundsRef.current = rounds; }, [rounds]);

  const refreshSummary = useCallback(async () => {
    if (!runId) return;
    const rr = roundsRef.current;
    const upTo = rr.length ? rr[rr.length - 1].round : 0;
    setSummary((s) => ({...(s || {}), loading: true}));
    try {
      const r = await api.summarize(runId, upTo);
      lastSummaryRound.current = r.round;
      setSummary({round: r.round, text: r.summary, loading: false});
    } catch (e) {
      setSummary((s) => ({...(s || {}), loading: false}));
      notify("summary failed: " + e.message);
    }
  }, [runId, notify]);

  const notify = useCallback((msg) => setToastMsg(msg), []);
  const hideHint = useCallback(() => setShowHint(false), []);

  const loadRun = useCallback(async (id) => {
    try {
      const data = await api.rounds(id);
      setRounds(data.rounds);
      setCur(1);
      setRunId(id);
      setInspector(null);
      setSummary(null);
      lastSummaryRound.current = 0;
      try {
        const r = await api.summarize(id, data.rounds.length ? data.rounds[data.rounds.length - 1].round : 0);
        lastSummaryRound.current = r.round;
        setSummary({round: r.round, text: r.summary, loading: false});
      } catch (e) { /* summary is best-effort */ }
    } catch (e) {
      notify("load failed: " + e.message);
    }
  }, [notify]);

  useEffect(() => {
    (async () => {
      try {
        setC(await api.constants());
        const r = await api.runs();
        setRuns(r.runs);
        const names = r.runs.map((x) => x.name);
        const initial = names.includes("phase0-seed0") ? "phase0-seed0" : names[0];
        if (initial) await loadRun(initial);
        const b = await api.batch().catch(() => null);
        if (b) setBatch(b);
      } catch (e) {
        notify("init error: " + e.message);
      }
    })();
  }, [loadRun, notify]);

  useEffect(() => {
    const t = setInterval(async () => {
      pollCount.current++;
      try {
        const r = await api.runs();
        setRuns(r.runs);
      } catch (e) { /* transient */ }
      if (liveRunId) {
        try {
          const s = await api.state(liveRunId);
          setRounds(s.rounds);
          if (s.rounds.length && followLive) setCur(s.rounds.length);
          if (!s.active) {
            setLiveRunId(null);
            setFollowLive(true);
          }
        } catch (e) { /* transient */ }
      }
      if (runId) {
        try {
          setInspector(await api.inspector(runId));
        } catch (e) {
          setInspector("waiting");
        }
      }
      if (pollCount.current % 5 === 0) {
        try { setBatch(await api.batch()); } catch (e) { /* keep old */ }
        const rr = roundsRef.current;
        if (runId && rr.length) {
          const lastRound = rr[rr.length - 1].round;
          if (lastRound !== lastSummaryRound.current && (lastRound % 5 === 0 || rr.length <= 6)) {
            try {
              const r = await api.summarize(runId, lastRound);
              lastSummaryRound.current = r.round;
              setSummary({round: r.round, text: r.summary, loading: false});
            } catch (e) { /* summary is best-effort */ }
          }
        }
      }
    }, 1000);
    return () => clearInterval(t);
  }, [liveRunId, runId, followLive]);

  useEffect(() => {
    if (!playing || !rounds.length) return;
    const delay = view === "scene" ? 1100 : 700;
    const t = setInterval(() => {
      setCur((c) => {
        if (c >= rounds.length) {
          setPlaying(false);
          return c;
        }
        return c + 1;
      });
    }, delay);
    return () => clearInterval(t);
  }, [playing, rounds.length, view]);

  useEffect(() => {
    const h = (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
      if (e.code === "Space") { e.preventDefault(); hideHint(); setPlaying((p) => !p); }
      if (e.key === "ArrowRight" && rounds.length) { e.preventDefault(); setPlaying(false); hideHint(); setCur((c) => Math.min(rounds.length, c + 1)); }
      if (e.key === "ArrowLeft" && rounds.length) { e.preventDefault(); setPlaying(false); hideHint(); setCur((c) => Math.max(1, c - 1)); }
    };
    document.addEventListener("keydown", h);
    return () => document.removeEventListener("keydown", h);
  }, [rounds.length, hideHint]);

  useEffect(() => {
    if (!showHint) return;
    const t = setTimeout(() => setShowHint(false), 8000);
    return () => clearTimeout(t);
  }, [showHint]);

  const rec = rounds.length ? rounds[Math.min(cur, rounds.length) - 1] : null;
  const ruleRound = rec && rec.rule
    ? (cur >= 2 && rounds[cur - 2].rule && JSON.stringify(rounds[cur - 2].rule) === JSON.stringify(rec.rule) ? null : rec.round)
    : null;

  const onStartRun = async (seed) => {
    try {
      const r = await api.startRun(seed);
      setLiveRunId(r.run_id);
      setFollowLive(true);
      hideHint();
      const rl = await api.runs();
      setRuns(rl.runs);
      await loadRun(r.run_id);
    } catch (e) {
      notify("start failed: " + e.message);
    }
  };

  const onParse = async () => {
    const text = ruleText.trim();
    if (!text) return;
    try {
      const r = await api.parse(text);
      setPreview({rule: r.rule, applied: false});
    } catch (e) {
      notify("parse failed: " + e.message);
    }
  };

  const onApply = async () => {
    const text = ruleText.trim();
    if (!runId || !text) return;
    try {
      const r = await api.applyRule(runId, text);
      setPreview({rule: r.rule, applied: true});
    } catch (e) {
      notify("rule failed: " + e.message);
    }
  };

  const onRuleText = (t) => {
    setRuleText(t);
    setPreview(null);
  };

  const onPickRun = (id) => {
    setLiveRunId(null);
    setFollowLive(true);
    setPlaying(false);
    hideHint();
    loadRun(id);
  };

  const onSpeak = async (text) => {
    if (!text) return;
    try {
      const r = await api.speak(text);
      if (!r.ok) throw new Error(await r.text());
      const url = URL.createObjectURL(await r.blob());
      const a = new Audio(url);
      a.onended = () => URL.revokeObjectURL(url);
      a.play();
    } catch (e) {
      notify("speak failed: " + e.message);
    }
  };

  if (!C) return <div className="loading">loading…</div>;

  const controls = {
    C, rec, rounds, cur, batch, inspector, preview, ruleRound,
    runs, runId, onPickRun, onStartRun,
    playing, onPlay: () => { hideHint(); setPlaying((p) => !p); },
    onPause: () => { setPlaying(false); if (liveRunId) setFollowLive((f) => !f); },
    liveRunId, followLive,
    maxRounds: Math.max(1, rounds.length),
    onScrub: (v) => { setPlaying(false); hideHint(); setCur(v); },
    roundLabel: rec ? "round " + rec.round + " / " + rounds.length : "",
    statusText: rec ? (rec.stock_after < C.F_DEAD ? "lake dead" : "stock " + rec.stock_after) : "",
    ruleText, onRuleText, onParse, onApply,
    applyDisabled: !preview || preview.applied,
    notify, onSpeak,
    summary, refreshSummary,
  };

  return (
    <div>
      {view === "scene" ? <Scene {...controls} /> : <DataView {...controls} />}
      <button className="viewtoggle" title="switch between scene and data views"
        onClick={() => setView((v) => (v === "scene" ? "data" : "scene"))}>
        {view === "scene" ? "📊 Data" : "🌊 Scene"}
      </button>
      <Hint visible={showHint} />
      <Toast msg={toastMsg} onDone={() => setToastMsg(null)} />
    </div>
  );
}
