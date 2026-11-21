import { ruleSentence } from "../labels.js";

export default function RuleBar({preview, rec}) {
  return (
    <>
      <div className="rulebox">
        {preview && (
          <span>
            <b style={{color: preview.applied ? "#2ecc71" : undefined}}>
              {preview.applied ? "Enforced ✓ " : "Understood as: "}
            </b>
            {ruleSentence(preview.rule)}
            {preview.applied ? "." : ". Not enforced yet."}
            {!preview.applied && preview.rule.inspection_prob <= 0 && (
              <b style={{color: "#f87171"}}> Nobody checks this rule.</b>
            )}
          </span>
        )}
      </div>
      <div id="currule">{rec && rec.rule ? "Rule in force: " + rec.rule.plain_text : "no rule in effect"}</div>
    </>
  );
}
