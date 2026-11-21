export default function InspectorPanel({inspector, runId}) {
  if (!inspector || inspector === "waiting" || !(inspector.checks || []).length) {
    return (
      <div className="muted emptyinsp">
        <span className="spinner" /> Inspector is analyzing {runId}… (one check every 5 rounds, arrives asynchronously)
      </div>
    );
  }
  const checks = inspector.checks;
  const last = checks[checks.length - 1];
  const baseline = last.baseline != null ? Number(last.baseline) : 0.3;
  const mean = checks.reduce((s, c) => s + (Number(c.precision) || 0), 0) / checks.length;

  let sum = 0;
  return (
    <div>
      <div className="insphead">
        <span>source: {inspector.source || ""}</span>
        <span className="gauge" title={"running mean score " + mean.toFixed(3) + " vs baseline " + baseline}>
          <span className="gaugefill" style={{width: Math.min(100, mean * 100) + "%"}} />
          <span className="gaugetick" style={{left: Math.min(100, baseline * 100) + "%"}} />
          <span className="gaugelabel">mean {mean.toFixed(3)} {mean >= baseline ? "▲ above" : "▼ below"} baseline {baseline}</span>
        </span>
      </div>
      <table>
        <thead>
          <tr><th>round</th><th>accused</th><th>true top 3</th><th>prec</th><th>recall</th><th>mean so far</th></tr>
        </thead>
        <tbody>
          {checks.map((c, i) => {
            sum += Number(c.precision) || 0;
            const lied = new Set(c.truly_lied || []);
            return (
              <tr key={i}>
                <td>{c.round}</td>
                <td className="chips">
                  {(c.accused || []).map((n) => (
                    <span key={n} className={"chip" + (lied.has(n) ? " hit" : "")} title={c.reasons && c.reasons[n] ? c.reasons[n] : undefined}>
                      {n}{lied.has(n) ? " ✓" : ""}
                    </span>
                  ))}
                </td>
                <td className="chips">
                  {(c.truly_lied || []).map((n) => <span key={n} className="chip true">{n}</span>)}
                </td>
                <td>{(Number(c.precision) || 0).toFixed(2)}</td>
                <td>{(Number(c.recall) || 0).toFixed(2)}</td>
                <td>{(sum / (i + 1)).toFixed(2)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
