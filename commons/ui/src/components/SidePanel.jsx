import SummaryBox from "./SummaryBox";
import AgentPanel from "./AgentPanel";
import { ruleSentence } from "../labels.js";

export default function SidePanel(p) {
  const {C, rec, rounds, cur, feed, inspector, latestCheck, selected, onSelectFisher, summary, refreshSummary, sideOpen, onToggleSide} = p;
  const checks = inspector && inspector.checks && rec
    ? inspector.checks.filter((c) => c.round <= rec.round)
    : [];
  const mean = checks.length ? checks.reduce((s, c) => s + (Number(c.precision) || 0), 0) / checks.length : null;
  const baseline = checks.length && checks[checks.length - 1].baseline != null ? Number(checks[checks.length - 1].baseline) : 0.3;
  const lied = latestCheck ? new Set(latestCheck.truly_lied || []) : new Set();

  return (
    <div className={"sidepanel" + (sideOpen ? "" : " collapsed")}>
      <button className="sidecollapse" title={sideOpen ? "hide info panel" : "show info panel"} onClick={onToggleSide}>
        {sideOpen ? "›" : "‹"}
      </button>
      {sideOpen && (
        <div className="sidebody">
          <section className="sstats">
            <h3>Live</h3>
            {rec ? (
              <>
                <div className="statrow"><span>Round</span><b>{rec.round} / {rounds.length}</b></div>
                <div className="statrow">
                  <span>Stock</span>
                  <b className={rec.stock_after < C.F_DEAD ? "bad" : ""}>{rec.stock_after}</b>
                  <span className="muted">healthy ~{C.F0} · dead &lt;{C.F_DEAD}</span>
                </div>
                <div className="statrow">
                  <span>Catch</span>
                  <b>{rec.total_catch}</b>
                  <span className="muted">sustainable {C.SUSTAINABLE_CATCH}</span>
                </div>
                <div className="ruleline">
                  <b>Rule in force:</b> {rec.rule ? (rec.rule.plain_text || ruleSentence(rec.rule)) : "none"}
                </div>
              </>
            ) : <div className="muted">no run loaded</div>}
          </section>

          {selected != null && (
            <AgentPanel rounds={rounds} cur={cur} index={selected} onClose={() => onSelectFisher(selected)} />
          )}

          <section className="sfeed">
            <h3>Event feed</h3>
            {feed.length === 0 && <div className="muted">nothing yet</div>}
            {feed.map((it, i) => (
              <div key={i} className={"feeditem " + it.kind}>
                <span className="fr">r{it.round}</span>{it.text}
              </div>
            ))}
          </section>

          <section className="sinsp">
            <h3>Inspector</h3>
            {!latestCheck && (
              <div className="muted emptyinsp"><span className="spinner" />waiting for the first check (every 5 rounds)…</div>
            )}
            {latestCheck && (
              <>
                <div className="muted">
                  last check: round {latestCheck.round} · precision {(Number(latestCheck.precision) || 0).toFixed(2)} · recall {(Number(latestCheck.recall) || 0).toFixed(2)}
                </div>
                {mean != null && (
                  <span className="gauge" title={"running mean " + mean.toFixed(3) + " vs baseline " + baseline}>
                    <span className="gaugefill" style={{width: Math.min(100, mean * 100) + "%"}} />
                    <span className="gaugetick" style={{left: Math.min(100, baseline * 100) + "%"}} />
                    <span className="gaugelabel">mean {mean.toFixed(3)} vs baseline {baseline}</span>
                  </span>
                )}
                <div className="chips">
                  {(latestCheck.accused || []).map((n) => (
                    <span key={n} className={"chip" + (lied.has(n) ? " hit" : "")} title={latestCheck.reasons && latestCheck.reasons[n] ? latestCheck.reasons[n] : undefined}>
                      {n}{lied.has(n) ? " ✓" : ""}
                    </span>
                  ))}
                </div>
              </>
            )}
          </section>

          <SummaryBox summary={summary} onRefresh={refreshSummary} />
        </div>
      )}
    </div>
  );
}
