import { useEffect, useRef, useState } from "react";
import { createScene } from "../scene/engine";
import { sayTint } from "../labels.js";
import Hud from "./Hud";
import SidePanel from "./SidePanel";

export default function Scene(props) {
  const {C, rec} = props;
  const [sideOpen, setSideOpen] = useState(true);
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
    sc.setPace(props.speed || 1);
    sc.resize();
    const ro = new ResizeObserver(() => sc.resize());
    ro.observe(canvasRef.current);
    window.addEventListener("resize", sc.resize);
    sc.start();
    sceneRef.current = sc;
    return () => { ro.disconnect(); window.removeEventListener("resize", sc.resize); sc.stop(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (C && sceneRef.current) sceneRef.current.setConfig(C);
  }, [C]);

  useEffect(() => {
    if (sceneRef.current) sceneRef.current.setPace(props.speed || 1);
  }, [props.speed]);

  useEffect(() => {
    const sc = sceneRef.current;
    if (sc && rec) {
      sc.setRound(rec, prevRecRef.current, !props.animated);
      prevRecRef.current = rec;
    }
  }, [rec, props.animated]);

  useEffect(() => {
    const root = rootRef.current;
    const sc = sceneRef.current;
    if (!root || !sc) return;
    const hud = root.querySelector(".hud");
    const side = root.querySelector(".sidepanel");
    const hudH = hud ? hud.offsetHeight : 0;
    root.style.setProperty("--hudh", (hudH + 2) + "px");
    const sideW = side && !side.classList.contains("collapsed") ? side.offsetWidth : 0;
    sc.setSafeArea({
      top: hudH + 8,
      right: sideW ? sideW + 24 : 80,
      bottom: 40,
    });
  });

  const fishers = rec ? rec.fishers : [];
  const accused = props.latestCheck && props.latestCheck.accused ? new Set(props.latestCheck.accused) : new Set();

  return (
    <div className="sceneview" ref={rootRef}>
      <canvas ref={canvasRef} className="scenecanvas" />
      <div className="sceneboats">
        {fishers.map((f, i) => (
          <div
            key={i}
            className={"sceneboat" + (f.banned ? " banned" : "") + (props.selected === i ? " selected" : "")}
            ref={(el) => { boatEls.current[i] = el; }}
            onClick={() => props.onSelectFisher(i)}
            title="click for this fisher's history"
          >
            <div className={"bubble " + sayTint(f.say)} key={f.say} title={f.say}
              onClick={(e) => { e.stopPropagation(); e.currentTarget.classList.toggle("open"); }}>{f.say}</div>
            <div className="hullrow">
              <span className="hull" style={{
                background: `hsl(${(i * 47) % 360}, 45%, 30%)`,
                ...(f.fined > 0 ? {boxShadow: "0 0 0 2px #f87171"} : {}),
              }}>
                {f.banned ? "🚫" : "🛶"}
              </span>
              <span className="name">{f.name}</span>
              {accused.has(f.name) && <span className="accused" title="accused by the Inspector">❗</span>}
              <button className="play" title="speak this line aloud" disabled={!f.say}
                onClick={(e) => { e.stopPropagation(); props.onSpeak(f.say); }}>▶</button>
            </div>
            <div className={"cstat" + (f.report !== f.catch ? " lie" : "")}>took {f.catch} · said {f.report}</div>
            <div className="fstat">{f.banned ? "banned" : f.fined > 0 ? "fined " + f.fined : ""}</div>
          </div>
        ))}
      </div>
      <div ref={bannerRef} className="scenebanner" />
      <div ref={stampRef} className="scenestamp">LAKE DEAD</div>
      <SidePanel {...props} sideOpen={sideOpen} onToggleSide={() => setSideOpen((v) => !v)} />
      <Hud {...props} />
    </div>
  );
}
