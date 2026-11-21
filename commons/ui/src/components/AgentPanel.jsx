export default function AgentPanel({rounds, cur, index, onClose}) {
  const upto = rounds.slice(0, Math.min(cur, rounds.length));
  const f0 = upto.length ? upto[upto.length - 1].fishers[index] : null;
  if (!f0) return null;
  const rows = upto.map((r) => r.fishers[index]).filter(Boolean);
  const maxCatch = Math.max(1, ...rows.map((f) => Math.max(f.catch, f.report)));
  return (
    <section className="agentpanel">
      <div className="sumhead">
        <b>{f0.name}</b>
        <button title="close" onClick={onClose}>✕</button>
      </div>
      <div className="muted">wealth {f0.wealth} · latest: “{f0.say}”</div>
      <table>
        <thead>
          <tr><th>round</th><th>took</th><th>said</th><th></th><th>note</th></tr>
        </thead>
        <tbody>
          {rows.map((f, i) => (
            <tr key={i} className={f.report !== f.catch ? "lirow" : ""}>
              <td>{upto[i].round}</td>
              <td>{f.catch}</td>
              <td>{f.report}</td>
              <td className="barcell">
                <div className="minibar" style={{width: Math.max(2, (f.catch / maxCatch) * 100) + "%", background: f.report !== f.catch ? "var(--warn)" : "var(--good)"}} />
              </td>
              <td>{f.banned ? "banned" : f.fined > 0 ? "fined " + f.fined : f.report !== f.catch ? "under-reported" : ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
