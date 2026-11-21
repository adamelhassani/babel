export default function RuleBar({preview, rec}) {
  return (
    <>
      <div className="rulebox">
        {preview && (
          <>
            <span><b style={{color: preview.applied ? "#2ecc71" : "#fbbf24"}}>
              {preview.applied ? "applied ✓" : "preview — not applied yet"}
            </b></span>
            {Object.entries(preview.rule).map(([k, v]) => (
              <span key={k}><b>{k}: </b>{String(v)}</span>
            ))}
          </>
        )}
      </div>
      <div id="currule">{rec && rec.rule ? "in effect: " + rec.rule.plain_text : "no rule in effect"}</div>
    </>
  );
}
