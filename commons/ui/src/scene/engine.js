import { boatTarget } from "./layout.js";
import { sayTint } from "../labels.js";

function lerp(a, b, t) { return a + (b - a) * t; }
function mix(c1, c2, t) {
  return [Math.round(lerp(c1[0], c2[0], t)), Math.round(lerp(c1[1], c2[1], t)), Math.round(lerp(c1[2], c2[2], t))];
}
const css = (c, a) => (a == null ? `rgb(${c[0]},${c[1]},${c[2]})` : `rgba(${c[0]},${c[1]},${c[2]},${a})`);

const SKY_TOP_GOOD = [7, 89, 133], SKY_HOR_GOOD = [186, 230, 253];
const SKY_TOP_BAD = [20, 20, 34], SKY_HOR_BAD = [80, 30, 30];
const LAKE_TOP_GOOD = [125, 211, 252], LAKE_BOT_GOOD = [2, 132, 199];
const LAKE_TOP_BAD = [58, 62, 72], LAKE_BOT_BAD = [28, 30, 36];

export function createScene(canvas) {
  const ctx = canvas.getContext("2d");
  const S = {
    C: null, rec: null,
    time: 0, health: 1, dead: false,
    W: 0, H: 0, dpr: 1,
    boats: [], particles: [], ripples: [], fish: [], confetti: [],
    clouds: [], rain: [],
    shakeUntil: -1, goldenUntil: -1, bannerText: "", bannerUntil: -1,
    stamp: false, confettiDone: false,
    running: false, raf: 0, last: 0, reduced: false,
    onFrame: null, fishTarget: 0,
    safe: {top: 96, bottom: 40, left: 80, right: 80},
  };
  for (let i = 0; i < 4; i++) {
    S.clouds.push({x: Math.random(), y: 0.06 + Math.random() * 0.16, s: 34 + Math.random() * 60, v: 0.003 + Math.random() * 0.005});
  }
  for (let i = 0; i < 130; i++) {
    S.rain.push({x: Math.random(), y: Math.random(), v: 0.9 + Math.random() * 0.7});
  }

  function resize() {
    const win = typeof window !== "undefined" ? window : {devicePixelRatio: 1, innerWidth: 800, innerHeight: 600};
    S.dpr = Math.min(2, win.devicePixelRatio || 1);
    S.W = win.innerWidth || canvas.clientWidth || 800;
    S.H = win.innerHeight || canvas.clientHeight || 600;
    canvas.width = Math.round(S.W * S.dpr);
    canvas.height = Math.round(S.H * S.dpr);
    canvas.style.width = S.W + "px";
    canvas.style.height = S.H + "px";
    ctx.setTransform(S.dpr, 0, 0, S.dpr, 0, 0);
    layoutBoats();
  }

  const center = () => ({x: S.W / 2, y: S.H * 0.52});
  const R0 = () => Math.min(0.47 * S.H, 0.42 * S.W);
  const visHealth = () => (S.C && S.C.F0 ? Math.min(1.15, Math.max(0.03, (S.rec ? S.rec.stock_after : S.C.F0) / S.C.F0)) : S.health);
  const baseR = () => Math.max(60, R0() * Math.sqrt(visHealth()));
  const xScale = () => Math.max(1, Math.min(2.2, (S.W * 0.96) / (2 * R0())));

  function newFish() {
    return {ang: Math.random() * Math.PI * 2, rad: 0.2 + Math.random() * 0.62, sp: 0.15 + Math.random() * 0.35, sz: 3 + Math.random() * 4, ph: Math.random() * 6.28, jumpAt: S.time + 2 + Math.random() * 5};
  }

  function spawnCatch(i, f, c, R) {
    const b = S.boats[i];
    const n = Math.min(Math.max(0, f.catch), 5);
    for (let k = 0; k < n; k++) {
      const a = Math.atan2(b.ty - c.y, b.tx - c.x) + (Math.random() - 0.5) * 0.9;
      const d = R * (0.25 + Math.random() * 0.5);
      S.particles.push({
        type: "fisharc",
        x0: c.x + Math.cos(a) * d, y0: c.y + Math.sin(a) * d * 0.55,
        x1: b.tx, y1: b.ty - 16,
        t: -k * 0.07, dur: 0.45 + Math.random() * 0.2,
      });
    }
  }

  function splash(x, y, color) {
    for (let k = 0; k < 10; k++) {
      S.particles.push({type: "drop", x, y, vx: (Math.random() - 0.5) * 160, vy: -60 - Math.random() * 140, r: 1.2 + Math.random() * 1.6, color: color || "#bae6fd"});
    }
    S.ripples.push({x, y, r: 4, vr: 90, alpha: 0.7, color: "186,230,253"});
  }

  function setConfig(C) { S.C = C; }

  function layoutBoats() {
    const rec = S.rec;
    if (!rec || !S.C || S.W === 0) return;
    const n = rec.fishers.length;
    const c = center(), R = baseR();
    const rx = R * xScale(), ry = R * 0.88;
    const ringRx = Math.max(80, Math.min(rx * 1.24, S.W / 2 - S.safe.left - 62, S.W / 2 - S.safe.right - 62));
    const ringRy = Math.max(56, Math.min(ry * 1.24, c.y - S.safe.top - 80, S.H - S.safe.bottom - 14 - c.y));
    const pts = [];
    for (let i = 0; i < n; i++) {
      const t = boatTarget(i, rec.round, n);
      const f = rec.fishers[i].banned ? 0.93 : t.rad;
      pts.push({x: c.x + Math.cos(t.ang) * ringRx * f, y: c.y + Math.sin(t.ang) * ringRy * f});
    }
    for (let k = 0; k < 4; k++) {
      for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
          const a = pts[i], b = pts[j];
          let dx = b.x - a.x, dy = b.y - a.y;
          const d = Math.hypot(dx, dy), minD = 140;
          if (d > 1e-6 && d < minD) {
            const push = (minD - d) / 2;
            dx /= d; dy /= d;
            a.x -= dx * push; a.y -= dy * push;
            b.x += dx * push; b.y += dy * push;
          }
        }
      }
    }
    for (const p of pts) {
      p.x = Math.max(S.safe.left + 60, Math.min(S.W - S.safe.right - 60, p.x));
      p.y = Math.max(S.safe.top + 74, Math.min(S.H - S.safe.bottom - 12, p.y));
    }
    for (let i = 0; i < n; i++) {
      const b = S.boats[i];
      b.tx = pts[i].x;
      b.ty = pts[i].y;
      if (b.x === 0 && b.y === 0) { b.x = b.tx; b.y = b.ty; }
    }
  }

  function setSafeArea(patch) {
    Object.assign(S.safe, patch);
    layoutBoats();
  }

  function setRound(rec, prev) {
    const old = S.rec;
    S.rec = rec;
    if (!rec || !S.C) return;
    const C = S.C;
    S.health = Math.max(0, Math.min(1, rec.stock_after / C.K));
    const wasDead = S.dead;
    S.dead = rec.stock_after < C.F_DEAD;
    if (S.dead && !wasDead) {
      S.shakeUntil = S.time + 1.0;
      S.stamp = true;
      splash(center().x, center().y, "#64748b");
    }
    const n = rec.fishers.length;
    while (S.boats.length < n) S.boats.push({x: 0, y: 0, tx: 0, ty: 0, phase: Math.random() * 6.28, flashUntil: -1, popAt: -1, lean: 0, leanUntil: -1, shakeUntil: -1, dipUntil: -1, docked: false, tint: ""});
    S.boats.length = n;
    layoutBoats();
    const c = center(), R = baseR();
    for (let i = 0; i < n; i++) {
      const f = rec.fishers[i];
      const b = S.boats[i];
      b.docked = !!f.banned;
      b.name = f.name;
      b.fined = f.fined;
      b.banned = f.banned;
      b.tint = sayTint(f.say);
      const pf = prev && prev.fishers ? prev.fishers[i] : null;
      if (pf && pf.say !== f.say) {
        b.popAt = S.time;
        b.lean = (Math.random() - 0.5) * 0.16;
        b.leanUntil = S.time + 0.6;
      }
      if (pf && prev.round !== rec.round) {
        if (f.catch > 0) {
          spawnCatch(i, f, c, R);
          b.dipUntil = S.time + 0.18;
        }
        if (f.fined > 0 && pf.fined !== f.fined) {
          b.shakeUntil = S.time + 0.45;
          S.particles.push({type: "text", x: b.tx, y: b.ty - 26, vy: -46, text: "−" + f.fined, color: "#f87171", t: 0, dur: 1.1});
        }
        if (f.report !== f.catch) {
          b.flashUntil = S.time + 0.7;
          S.particles.push({type: "text", x: b.tx, y: b.ty - 32, vy: -34, text: "❓", color: "#c4b5fd", t: 0, dur: 1.4});
        }
      }
    }
    const prevRule = prev ? prev.rule : null;
    if (rec.rule && (!prevRule || JSON.stringify(prevRule) !== JSON.stringify(rec.rule))) {
      S.goldenUntil = S.time + 1.4;
      S.bannerText = rec.rule.plain_text;
      S.bannerUntil = S.time + 3.5;
      for (let k = 0; k < 3; k++) {
        S.ripples.push({x: c.x, y: c.y, r: 8 + k * 14, vr: 240 - k * 45, alpha: 0.85, color: "251,191,36"});
      }
    }
    if (!S.dead && rec.round >= 30 && !S.confettiDone) {
      S.confettiDone = true;
      for (let k = 0; k < 160; k++) {
        S.confetti.push({x: Math.random() * S.W, y: -20 - Math.random() * S.H * 0.5, vx: (Math.random() - 0.5) * 2.2, vy: 2 + Math.random() * 3, rot: Math.random() * 6.28, vr: (Math.random() - 0.5) * 9, size: 4 + Math.random() * 5, color: `hsl(${Math.floor(Math.random() * 360)},80%,60%)`});
      }
    }
    S.fishTarget = Math.round(S.health * 40);
    while (S.fish.length < S.fishTarget) S.fish.push(newFish());
    if (S.fish.length > S.fishTarget) S.fish.length = S.fishTarget;
    if (old !== rec && S.reduced) renderOnce();
  }

  function update(dt) {
    for (const b of S.boats) {
      b.x += (b.tx - b.x) * Math.min(1, dt * 2.6);
      b.y += (b.ty - b.y) * Math.min(1, dt * 2.6);
    }
    for (const p of S.particles) {
      if (p.type === "fisharc") {
        p.t += dt / p.dur;
        if (p.t >= 1 && !p.landed) {
          p.landed = true;
          splash(p.x1, p.y1, "#bae6fd");
        }
      } else if (p.type === "drop") {
        p.x += p.vx * dt;
        p.y += p.vy * dt;
        p.vy += 500 * dt;
      } else if (p.type === "text") {
        p.t += dt / p.dur;
        p.y += p.vy * dt;
      }
    }
    S.particles = S.particles.filter((p) => p.type === "fisharc" ? p.t < 1.05 : p.type === "drop" ? p.y < S.H + 20 : p.type === "text" ? p.t < 1 : true);
    for (const r of S.ripples) { r.r += r.vr * dt; r.alpha -= dt * 0.5; }
    S.ripples = S.ripples.filter((r) => r.alpha > 0);
    for (const f of S.fish) {
      f.ang += f.sp * dt;
      if (S.time > f.jumpAt) {
        f.jumpAt = S.time + 3 + Math.random() * 5;
        const c = center(), R = baseR();
        S.particles.push({type: "fisharc", x0: c.x + Math.cos(f.ang) * R * f.rad, y0: c.y + Math.sin(f.ang) * R * f.rad * 0.6, x1: c.x + Math.cos(f.ang + 0.6) * R * f.rad, y1: c.y - R * 0.35, t: 0, dur: 0.7, fish: true});
      }
    }
    for (const cf of S.confetti) {
      cf.x += cf.vx + Math.sin(S.time * 3 + cf.rot) * 0.6;
      cf.y += cf.vy;
      cf.rot += cf.vr * dt;
    }
    S.confetti = S.confetti.filter((cf) => cf.y < S.H + 30);
    for (const cl of S.clouds) {
      cl.x += cl.v * dt;
      if (cl.x > 1.2) cl.x = -0.2;
    }
    for (const r of S.rain) {
      r.y += r.v * dt * 2.2;
      r.x -= dt * 0.25;
      if (r.y > 1.1) { r.y = -0.1; r.x = Math.random() * 1.2; }
    }
  }

  function blobPath(c, R, t) {
    const xs = xScale();
    ctx.beginPath();
    for (let k = 0; k <= 72; k++) {
      const a = (k / 72) * Math.PI * 2;
      const r = R * (1 + 0.05 * Math.sin(3 * a + t * 0.9) + 0.035 * Math.sin(5 * a - t * 1.4) + 0.02 * Math.sin(8 * a + t * 0.6));
      const x = c.x + Math.cos(a) * r * xs;
      const y = c.y + Math.sin(a) * r * 0.88;
      if (k === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
  }

  function drawFish(x, y, sz, ang, color) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(ang);
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.ellipse(0, 0, sz, sz * 0.45, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(-sz, 0);
    ctx.lineTo(-sz * 1.7, -sz * 0.5);
    ctx.lineTo(-sz * 1.7, sz * 0.5);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  }

  function drawBoat(b, t) {
    const y = b.y + Math.sin(t * 2 + b.phase) * 3;
    const x = b.x + Math.cos(t * 1.7 + b.phase) * 2 + (t < b.shakeUntil ? (Math.random() - 0.5) * 5 : 0);
    ctx.save();
    ctx.translate(x, y);
    if (t < b.leanUntil) ctx.rotate(b.lean);
    if (t < b.dipUntil) ctx.scale(1, 0.78);
    if (b.banned) ctx.globalAlpha = 0.45;
    if (b.fined > 0) {
      ctx.strokeStyle = `rgba(248,113,113,${0.6 + 0.4 * Math.sin(t * 6)})`;
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.arc(0, -6, 17, 0, Math.PI * 2);
      ctx.stroke();
    }
    ctx.fillStyle = b.banned ? "#6b7280" : "#92400e";
    ctx.beginPath();
    ctx.moveTo(-14, 0);
    ctx.quadraticCurveTo(0, 11, 14, 0);
    ctx.lineTo(10, -7);
    ctx.lineTo(-10, -7);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = "#fcd34d";
    ctx.beginPath();
    ctx.arc(0, -11, 4.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function draw() {
    const t = S.time;
    const c = center();
    const R = baseR();
    const bad = 1 - S.health;
    const skyTop = S.dead ? SKY_TOP_BAD : mix(SKY_TOP_GOOD, SKY_TOP_BAD, bad);
    const skyHor = S.dead ? SKY_HOR_BAD : mix(SKY_HOR_GOOD, SKY_HOR_BAD, bad);
    const lakeTop = S.dead ? LAKE_TOP_BAD : mix(LAKE_TOP_GOOD, LAKE_TOP_BAD, bad);
    const lakeBot = S.dead ? LAKE_BOT_BAD : mix(LAKE_BOT_GOOD, LAKE_BOT_BAD, bad);

    ctx.clearRect(0, 0, S.W, S.H);
    const sky = ctx.createLinearGradient(0, 0, 0, S.H);
    sky.addColorStop(0, css(skyTop));
    sky.addColorStop(1, css(skyHor));
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, S.W, S.H);

    const sunA = S.dead ? 0.15 : 0.9 * (0.3 + 0.7 * S.health);
    const sun = ctx.createRadialGradient(S.W * 0.82, S.H * 0.16, 4, S.W * 0.82, S.H * 0.16, 90);
    sun.addColorStop(0, `rgba(253,224,71,${sunA})`);
    sun.addColorStop(1, "rgba(253,224,71,0)");
    ctx.fillStyle = sun;
    ctx.fillRect(S.W * 0.82 - 100, S.H * 0.16 - 100, 200, 200);

    ctx.fillStyle = `rgba(255,255,255,${S.dead ? 0.06 : 0.35 * (0.4 + 0.6 * S.health)})`;
    for (const cl of S.clouds) {
      ctx.beginPath();
      ctx.ellipse(cl.x * S.W, cl.y * S.H, cl.s, cl.s * 0.38, 0, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.fillStyle = "#8a7a5c";
    blobPath(c, R * 1.08, t);
    ctx.fill();
    const lg = ctx.createRadialGradient(c.x, c.y - R * 0.3, R * 0.1, c.x, c.y, R);
    lg.addColorStop(0, css(lakeTop));
    lg.addColorStop(1, css(lakeBot));
    blobPath(c, R, t);
    ctx.fillStyle = lg;
    ctx.fill();
    ctx.strokeStyle = css(lakeTop, 0.8);
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.save();
    blobPath(c, R, t);
    ctx.clip();
    for (let w = 0; w < 3; w++) {
      ctx.strokeStyle = `rgba(255,255,255,${0.10 - w * 0.025})`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      for (let x = -20; x <= S.W + 20; x += 14) {
        const y = c.y - R * 0.5 + w * R * 0.32 + Math.sin(x * 0.02 + t * (1.2 + w * 0.4) + w * 2) * 6;
        if (x === -20) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
    for (const f of S.fish) {
      const fx = c.x + Math.cos(f.ang) * R * xScale() * f.rad;
      const fy = c.y + Math.sin(f.ang * 1.3 + f.ph) * R * f.rad * 0.45;
      drawFish(fx, fy, f.sz, f.ang, "rgba(2,40,60,0.55)");
    }
    if (t < S.goldenUntil) {
      const gg = ctx.createRadialGradient(c.x, c.y, 0, c.x, c.y, R * 1.2);
      gg.addColorStop(0, `rgba(251,191,36,${0.35 * (S.goldenUntil - t)})`);
      gg.addColorStop(1, "rgba(251,191,36,0)");
      ctx.fillStyle = gg;
      ctx.fillRect(c.x - R * 1.3, c.y - R * 1.3, R * 2.6, R * 2.6);
    }
    ctx.restore();

    for (const r of S.ripples) {
      ctx.strokeStyle = `rgba(${r.color},${Math.max(0, r.alpha)})`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.ellipse(r.x, r.y, r.r, r.r * 0.55, 0, 0, Math.PI * 2);
      ctx.stroke();
    }

    for (const p of S.particles) {
      if (p.type === "fisharc") {
        const u = Math.max(0, Math.min(1, p.t));
        const mx = (p.x0 + p.x1) / 2, my = Math.min(p.y0, p.y1) - 90;
        const x = lerp(lerp(p.x0, mx, u), lerp(mx, p.x1, u), u);
        const y = lerp(lerp(p.y0, my, u), lerp(my, p.y1, u), u);
        const ang = Math.atan2(2 * (1 - u) * (my - p.y0) + 2 * u * (p.y1 - my), 2 * (1 - u) * (mx - p.x0) + 2 * u * (p.x1 - mx));
        drawFish(x, y, p.fish ? 5 : 4, ang, p.fish ? "rgba(186,230,253,0.9)" : "#fde68a");
      } else if (p.type === "drop") {
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      } else if (p.type === "text") {
        ctx.globalAlpha = Math.max(0, 1 - p.t);
        ctx.fillStyle = p.color;
        ctx.font = "bold 14px system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(p.text, p.x, p.y);
        ctx.globalAlpha = 1;
        ctx.textAlign = "left";
      }
    }
    for (const cf of S.confetti) {
      ctx.save();
      ctx.translate(cf.x, cf.y);
      ctx.rotate(cf.rot);
      ctx.fillStyle = cf.color;
      ctx.fillRect(-cf.size / 2, -cf.size / 2, cf.size, cf.size * 0.6);
      ctx.restore();
    }

    for (const b of S.boats) drawBoat(b, t);

    if (S.dead) {
      ctx.strokeStyle = "rgba(180,200,230,0.35)";
      ctx.lineWidth = 1.2;
      for (const r of S.rain) {
        ctx.beginPath();
        ctx.moveTo(r.x * S.W, r.y * S.H);
        ctx.lineTo(r.x * S.W - 6, r.y * S.H + 16);
        ctx.stroke();
      }
    }

    const vg = ctx.createRadialGradient(S.W / 2, S.H / 2, Math.min(S.W, S.H) * 0.42, S.W / 2, S.H / 2, Math.max(S.W, S.H) * 0.75);
    vg.addColorStop(0, "rgba(0,0,0,0)");
    vg.addColorStop(1, S.dead ? "rgba(0,0,0,0.55)" : "rgba(0,0,0,0.32)");
    ctx.fillStyle = vg;
    ctx.fillRect(0, 0, S.W, S.H);
  }

  function snapshot() {
    return {
      boats: S.boats.map((b) => ({
        x: b.x, y: b.y + Math.sin(S.time * 2 + b.phase) * 3,
        name: b.name, fined: b.fined, banned: b.banned,
        flash: S.time < b.flashUntil,
        docked: b.docked,
        tint: b.tint,
      })),
      center: center(),
      particleCount: S.particles.length,
      banner: S.time < S.bannerUntil ? S.bannerText : null,
      stamp: S.stamp,
      stock: S.rec ? S.rec.stock_after : null,
    };
  }

  function frame(ts) {
    if (!S.running) return;
    const dt = Math.min(0.05, (ts - S.last) / 1000 || 0.016);
    S.last = ts;
    S.time += dt;
    ctx.save();
    if (S.time < S.shakeUntil) {
      ctx.translate((Math.random() - 0.5) * 10, (Math.random() - 0.5) * 10);
    }
    update(dt);
    draw();
    ctx.restore();
    if (S.onFrame) S.onFrame(snapshot());
    S.raf = requestAnimationFrame(frame);
  }

  function renderOnce() {
    update(0.016);
    draw();
    if (S.onFrame) S.onFrame(snapshot());
  }

  return {
    resize,
    setConfig,
    setRound,
    setSafeArea,
    setReduced: (v) => { S.reduced = v; },
    start() {
      if (S.running) return;
      S.running = true;
      S.last = performance.now();
      if (S.reduced) { renderOnce(); return; }
      S.raf = requestAnimationFrame(frame);
    },
    stop() {
      S.running = false;
      cancelAnimationFrame(S.raf);
    },
    renderOnce,
    snapshot,
  };
}
