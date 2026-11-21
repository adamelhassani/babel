import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "./api";
import { ruleSentence } from "./labels";
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
  const [speed, setSpeed] = useState(1);
  const [selected, setSelected] = useState(null);
  const [ruleText, setRuleText] = useState("");
  const animateRef = useRef(false);
  const [preview, setPreview] = useState(null);
  const [summary, setSummary] = useState(null);
  const pollCount = useRef(0);
  const roundsRef = useRef([]);
  const lastSummaryRound = useRef(0);
  const inspMiss = useRef(0);

  useEffect(() => { roundsRef.current = rounds; }, [rounds]);

  const notify = useCallback((msg) => setToastMsg(msg), []);
  const hideHint = useCallback(() => setShowHint(false), []);

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

  const loadRun = useCallback(async (id) => {
    try {
      const data = await api.rounds(id);
      setRounds(data.rounds);
      setCur(1);
      setRunId(id);
      setInspector(null);
      setSummary(null);
      lastSummaryRound.current = 0;
      inspMiss.current = 0;
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
      if (document.hidden) return;
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
        const isLive = liveRunId === runId;
        if (isLive || pollCount.current % 5 === 0) {
          if (!isLive && inspMiss.current > 2) {
            // saved run without inspector output: backed off, retry every 30 s
            if (pollCount.current % 30 !== 0) { /* skip */ }
            else {
              try { setInspector(await api.inspector(runId)); inspMiss.current = 0; }
              catch (e) { inspMiss.current++; setInspector("waiting"); }
            }
          } else {
            try { setInspector(await api.inspector(runId)); inspMiss.current = 0; }
            catch (e) { inspMiss.current++; setInspector("waiting"); }
          }
        }
      }
      if (pollCount.current % 10 === 0) {
        try { setBatch(await api.batch()); } catch (e) { /* keep old */ }
      }
      if (pollCount.current % 5 === 0 && runId) {
        const rr = roundsRef.current;
        if (rr.length) {
          const lastRound = rr[rr.length - 1].round;
          if (lastRound % 5 === 0 && lastRound !== lastSummaryRound.current) {
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
    const delay = (view === "scene" ? 1900 : 700) / speed;
    const t = setInterval(() => {
      animateRef.current = true;
      setCur((c) => {
        if (c >= rounds.length) {
          setPlaying(false);
          return c;
        }
        return c + 1;
      });
    }, delay);
    return () => clearInterval(t);
  }, [playing, rounds.length, view, speed]);

  useEffect(() => {
    const h = (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
      if (e.code === "Space") { e.preventDefault(); hideHint(); setPlaying((p) => !p); }
      if (e.key === "ArrowRight" && rounds.length) { e.preventDefault(); setPlaying(false); hideHint(); animateRef.current = false; setCur((c) => Math.min(rounds.length, c + 1)); }
      if (e.key === "ArrowLeft" && rounds.length) { e.preventDefault(); setPlaying(false); hideHint(); animateRef.current = false; setCur((c) => Math.max(1, c - 1)); }
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

  const feed = useMemo(() => {
    if (!C || !rounds.length) return [];
    const items = [];
    const seen = rounds.slice(0, Math.min(cur, rounds.length));
    let deadAnnounced = false;
    for (let i = 0; i < seen.length; i++) {
      const r = seen[i];
      const prev = i > 0 ? seen[i - 1] : null;
      if (r.rule && (!prev || !prev.rule || JSON.stringify(prev.rule) !== JSON.stringify(r.rule))) {
        items.push({round: r.round, kind: "rule", text: "Rule in force: " + (r.rule.plain_text || ruleSentence(r.rule))});
      }
      items.push({round: r.round, kind: "catch", text: "total catch " + r.total_catch + " vs sustainable " + C.SUSTAINABLE_CATCH});
      for (const f of r.fishers) {
        const pf = prev && prev.fishers ? prev.fishers.find((x) => x.name === f.name) : null;
        if (f.fined > 0 && (!pf || pf.fined !== f.fined)) items.push({round: r.round, kind: "fine", text: f.name + " fined " + f.fined});
        if (f.banned && (!pf || !pf.banned)) items.push({round: r.round, kind: "ban", text: f.name + " banned this round"});
        if (f.report !== f.catch) items.push({round: r.round, kind: "lie", text: f.name + " caught " + f.catch + " but reported " + f.report});
      }
      if (r.stock_after < C.F_DEAD && !deadAnnounced) {
        deadAnnounced = true;
        items.push({round: r.round, kind: "dead", text: "the lake died (stock " + r.stock_after + " < " + C.F_DEAD + ")"});
      }
    }
    if (inspector && inspector.checks && rec) {
      for (const c of inspector.checks) {
        if (c.round <= rec.round) {
          items.push({round: c.round, kind: "insp", text: "Inspector accused " + (c.accused || []).join(", ") + " (precision " + (Number(c.precision) || 0).toFixed(2) + ", recall " + (Number(c.recall) || 0).toFixed(2) + ")"});
        }
      }
    }
    return items.slice(-80).reverse();
  }, [C, rounds, cur, inspector, rec]);

  const latestCheck = useMemo(() => {
    if (!inspector || !inspector.checks || !rec) return null;
    const cs = inspector.checks.filter((c) => c.round <= rec.round);
    return cs.length ? cs[cs.length - 1] : null;
  }, [inspector, rec]);

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
    animateRef.current = false;
    setSelected(null);
    loadRun(id);
  };

  const onReplay = () => {
    setPlaying(false);
    animateRef.current = false;
    hideHint();
    setCur(1);
  };

  const onSpeed = (v) => setSpeed(v);

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
    playing, onPlay: () => { hideHint(); animateRef.current = true; setPlaying((p) => !p); },
    onPause: () => { setPlaying(false); if (liveRunId) setFollowLive((f) => !f); },
    onReplay, speed, onSpeed,
    selected, onSelectFisher: (i) => setSelected((s) => (s === i ? null : i)),
    feed, latestCheck, animated: animateRef.current,
    liveRunId, followLive,
    maxRounds: Math.max(1, rounds.length),
    onScrub: (v) => { setPlaying(false); hideHint(); animateRef.current = false; setCur(v); },
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
