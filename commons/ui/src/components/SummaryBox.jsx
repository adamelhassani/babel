export default function SummaryBox({summary, onRefresh, compact}) {
  const loading = summary && summary.loading && !summary.text;
  return (
    <div className={compact ? "summarybox compact" : "summarybox"}>
      <div className="sumhead">
        <b>What happened so far</b>
        <button title="refresh the summary (summary agent)" onClick={onRefresh}>↻</button>
      </div>
      {loading ? (
        <div className="muted"><span className="spinner" /> summarizing…</div>
      ) : (
        <div className="sumtext">{summary && summary.text ? summary.text : <span className="muted">no summary yet — press ↻</span>}</div>
      )}
      {summary && summary.round ? <div className="sumround">up to round {summary.round}</div> : null}
    </div>
  );
}
