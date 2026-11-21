export default function Hint({visible}) {
  return (
    <div id="hint" className={visible ? "show" : ""}>
      ▶ play or scrub the round slider · pick a run top-left · parse + apply a rule
    </div>
  );
}
