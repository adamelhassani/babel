export default function LakeScene({C, rec, ruleRound, onSpeak}) {
  const n = rec ? rec.fishers.length : C.N;
  const stock = rec ? rec.stock_after : C.K;
  const dead = rec ? rec.stock_after < C.F_DEAD : false;
  const frac = Math.max(0, Math.min(1, stock / C.K));
  const r = 20 + 110 * Math.sqrt(frac);

  return (
    <div id="lakebox">
      <svg viewBox="0 0 260 260" className="lakesvg">
        <defs>
          <radialGradient id="lakegrad" cx="50%" cy="40%" r="65%">
            <stop offset="0%" stopColor={dead ? "#3a3f4a" : "#7dd3fc"} />
            <stop offset="100%" stopColor={dead ? "#23262e" : "#0369a1"} />
          </radialGradient>
          <clipPath id="lakeclip"><circle cx="130" cy="130" r={r} /></clipPath>
        </defs>
        <circle cx="130" cy="130" r={r} fill="url(#lakegrad)" stroke={dead ? "#555" : "#38bdf8"} strokeWidth="2" />
        <g clipPath="url(#lakeclip)">
          <path className="wave w1" fill="rgba(255,255,255,.18)"
            d="M0,150 Q32,140 65,150 T130,150 T195,150 T260,150 T325,150 T390,150 T455,150 T520,150 V260 H0 Z" />
          <path className="wave w2" fill="rgba(255,255,255,.10)"
            d="M0,165 Q32,157 65,165 T130,165 T195,165 T260,165 T325,165 T390,165 T455,165 T520,165 V260 H0 Z" />
        </g>
        {ruleRound != null && <circle key={ruleRound} cx="130" cy="130" r={r} className="ripple" fill="none" stroke="#fbbf24" strokeWidth="3" />}
        <text x="130" y="128" textAnchor="middle" className="stocktext">{Math.round(stock)}</text>
        {dead && <text x="130" y="152" textAnchor="middle" className="deadtext">LAKE DEAD</text>}
      </svg>
      <div id="boats">
        {Array.from({length: n}, (_, i) => {
          const ang = -Math.PI / 2 + (i * 2 * Math.PI) / n;
          const f = rec ? rec.fishers[i] : null;
          return (
            <div key={i} className={"boat" + (f && f.banned ? " banned" : "")}
              style={{left: 170 + 150 * Math.cos(ang), top: 170 + 150 * Math.sin(ang), animationDelay: (i * 0.35) + "s"}}>
              <div className="bubble">{f ? f.say : ""}</div>
              <div className="hull" style={f && f.fined > 0 ? {boxShadow: "0 0 0 2px #f87171"} : undefined}>
                {f && f.banned ? "🚫" : "🛶"}
              </div>
              <div className="name">{f ? f.name : ""}</div>
              <div className="fstat">{f ? (f.banned ? "banned" : f.fined > 0 ? "fined " + f.fined : "") : ""}</div>
              <button className="play" title="speak this line aloud" disabled={!f || !f.say} onClick={() => f && onSpeak(f.say)}>▶</button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
