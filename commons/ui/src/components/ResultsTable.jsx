const NUM_COLS = ["rounds_survived", "final_stock", "total_catch", "gini", "share_over_quota", "share_lying"];

export default function ResultsTable({batch}) {
  if (!batch || !batch.rows || !batch.rows.length) {
    return <div className="muted">no runs/batch/results.csv yet</div>;
  }
  const byRule = {};
  for (const row of batch.rows) {
    if (!byRule[row.rule_name]) byRule[row.rule_name] = [];
    byRule[row.rule_name].push(row);
  }
  const avg = Object.entries(byRule).map(([rule, rows]) => {
    const o = {rule_name: rule, n: rows.length};
    for (const c of NUM_COLS) o[c] = rows.reduce((s, r) => s + (parseFloat(r[c]) || 0), 0) / rows.length;
    return o;
  }).sort((a, b) => b.rounds_survived - a.rounds_survived);
  const maxRounds = avg.length ? avg[0].rounds_survived : 1;

  return (
    <table>
      <thead>
        <tr><th>rule</th><th>runs</th><th>rounds</th><th></th><th>final stock</th><th>catch</th><th>gini</th><th>over quota</th><th>lying</th></tr>
      </thead>
      <tbody>
        {avg.map((o, i) => (
          <tr key={o.rule_name} className={i === 0 ? "best" : ""}>
            <td>{o.rule_name}</td>
            <td>{o.n}</td>
            <td>{o.rounds_survived.toFixed(1)}</td>
            <td className="barcell"><div className="minibar" style={{width: Math.max(2, (o.rounds_survived / maxRounds) * 100) + "%"}} /></td>
            <td>{o.final_stock.toFixed(0)}</td>
            <td>{o.total_catch.toFixed(0)}</td>
            <td>{o.gini.toFixed(3)}</td>
            <td>{(o.share_over_quota * 100).toFixed(0)}%</td>
            <td>{(o.share_lying * 100).toFixed(0)}%</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
