import { useEffect, useRef } from "react";
import { createScene } from "../scene/engine";
import { sayTint } from "../labels.js";
import Hud from "./Hud";
import SummaryBox from "./SummaryBox";

export default function Scene(props) {
  const {C, rec} = props;
  const rootRef = useRef(null);
  const canvasRef = useRef(null);
  const sceneRef = useRef(null);
  const boatEls = useRef([]);
  const bannerRef = useRef(null);
  const stampRef = useRef(null);
  const prevRecRef = useRef(null);

  useEffect(() => {
    const sc = createScene(canvasRef.current);
    sc.onFrame = (snap) => {
      boatEls.current.forEach((el, i) => {
        if (!el || !snap.boats[i]) return;
        const b = snap.boats[i];
        el.style.transform = `translate(${b.x}px, ${b.y}px) translate(-50%, -100%)`;
        el.classList.toggle("flash", b.flash);
      });
      if (bannerRef.current) {
        if (snap.banner) {
          bannerRef.current.textContent = "⚖ " + snap.banner;
          bannerRef.current.className = "scenebanner show";
        } else {
          bannerRef.current.className = "scenebanner";
        }
      }
      if (stampRef.current) stampRef.current.className = snap.stamp ? "scenestamp show" : "scenestamp";
    };
    sc.setReduced(window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    sc.resize();
    const ro = new ResizeObserver(() => sc.resize());
    ro.observe(canvasRef.current);
    window.addEventListener("resize", sc.resize);
    sc.start();
    sceneRef.current = sc;
    return () => { ro.disconnect(); window.removeEventListener("resize", sc.resize); sc.stop(); };
  }, []);

  useEffect(() => {
    if (C && sceneRef.current) sceneRef.current.setConfig(C);
  }, [C]);

  useEffect(() => {
    const sc = sceneRef.current;
    if (sc && rec) {
      sc.setRound(rec, prevRecRef.current);
      prevRecRef.current = rec;
    }
  }, [rec]);

  useEffect(() => {
    const root = rootRef.current;
    const sc = sceneRef.current;
    if (!root || !sc) return;
    const hud = root.querySelector(".hud");
    const sum = root.querySelector(".summarybox");
    sc.setSafeArea({
      top: (hud ? hud.offsetHeight : 0) + 8,
      bottom: sum ? sum.offsetHeight + 56 : 40,
    });
  });

  const fishers = rec ? rec.fishers : [];

  return (
    <div className="sceneview" ref={rootRef}>
      <canvas ref={canvasRef} className="scenecanvas" />
      <div className="sceneboats">
        {fishers.map((f, i) => (
          <div
            key={i}
            className={"sceneboat" + (f.banned ? " banned" : "")}
            ref={(el) => { boatEls.current[i] = el; }}
          >
            <div className={"bubble " + sayTint(f.say)} key={f.say} title={f.say}
              onClick={(e) => e.currentTarget.classList.toggle("open")}>{f.say}</div>
            <div className="hullrow">
              <span className="hull" style={f.fined > 0 ? {boxShadow: "0 0 0 2px #f87171"} : undefined}>
                {f.banned ? "🚫" : "🛶"}
              </span>
              <span className="name">{f.name}</span>
              <button className="play" title="speak this line aloud" disabled={!f.say} onClick={() => props.onSpeak(f.say)}>▶</button>
            </div>
            <div className="fstat">{f.banned ? "banned" : f.fined > 0 ? "fined " + f.fined : ""}</div>
          </div>
        ))}
      </div>
      <div ref={bannerRef} className="scenebanner" />
      <div ref={stampRef} className="scenestamp">LAKE DEAD</div>
      <SummaryBox compact summary={props.summary} onRefresh={props.refreshSummary} />
      <Hud {...props} />
    </div>
  );
}
