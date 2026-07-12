const D = { hue: 190, energy: .6, speed: 1, density: .55, scale: 1, x: .5, y: .5, arms: .5, style: 'phosphor', seed: 0, alpha: 100 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };

const u = Math.min(width, height);
const HW = Math.max(120, Math.floor(width * 0.5)), HH = Math.max(120, Math.floor(height * 0.5));
const bg = [232, 44, 7];
if (!S.tb || S.tw !== HW || S.th !== HH) {
  S.tb = createGraphics(HW, HH); S.tb.colorMode(HSB, 360, 100, 100, 100);
  S.tb.noStroke(); S.tb.fill(bg[0], bg[1], bg[2]); S.tb.rect(0, 0, HW, HH); S.tw = HW; S.th = HH;
}
// seed-driven epicycle coefficients
const N = Math.round(3 + P.density * 8);
if (S.seedUsed !== P.seed || S.n !== N) {
  S.seedUsed = P.seed; S.n = N;
  const fr = i => { const s = Math.sin(i * 127.1 + P.seed * 311.7) * 43758.5453; return s - Math.floor(s); };
  S.fq = []; S.am = []; S.ph = [];
  for (let k = 0; k < N; k++) {
    const sign = fr(k * 3 + 1) < 0.4 ? -1 : 1;
    S.fq.push(sign * (k === 0 ? 1 : Math.round(1 + fr(k * 3 + 2) * 6)));
    S.am.push(1 / (1 + k * (0.5 + fr(k * 3 + 3) * 1.1)));
    S.ph.push(fr(k * 3 + 4) * 6.2831);
  }
  const amsum = S.am.reduce((a, b) => a + b, 0); S.am = S.am.map(a => a / amsum);
  S.hoff = fr(99) * 40;
}
const tb = S.tb;
const style = P.style;
// slow fade of the trail buffer -> glowing decay
tb.push(); tb.noStroke();
const fade = style === 'ink' ? 4.5 : (style === 'blueprint' ? 6 : 2.0);
tb.fill(bg[0], bg[1], style === 'ink' ? 96 : bg[2], fade); tb.rect(0, 0, HW, HH); tb.pop();

const t = K.t * (0.5 + P.speed * 0.9);
const drift = K.t * 0.015; // continuous coefficient drift so the curve never exactly closes -> perpetual novelty
const cx = HW * 0.5, cy = HH * 0.5, R = u * 0.42 * (0.4 + P.scale * 0.75) * (HW / u);
const hb = (P.hue + S.hoff + K.section * 18) % 360;
function tip(tt) {
  let x = cx, y = cy;
  for (let k = 0; k < S.n; k++) {
    const f = S.fq[k] * (1 + 0.04 * Math.sin(drift + k));
    const ang = f * tt + S.ph[k] + drift * (k + 1) * 0.3;
    x += R * S.am[k] * Math.cos(ang); y += R * S.am[k] * Math.sin(ang);
  }
  return [x, y];
}
// draw a short arc of the trace this frame (several substeps for a smooth continuous line)
const steps = 30;
const dt = (0.10 + P.speed * 0.05);
const eg = 0.55 + P.energy * 0.7; // energy -> glow strength
let prev = S.lastTip || tip(t);
tb.noFill();
const seg = [];
for (let s = 1; s <= steps; s++) { const tt = t + (s / steps) * dt; seg.push(tip(tt)); }
// pass 1: wide soft glow (skip for ink)
if (style !== 'ink') {
  tb.strokeWeight(4.5); let pp = prev;
  for (let s = 0; s < seg.length; s++) {
    const p = seg[s], tt = t + ((s + 1) / steps) * dt;
    if (style === 'neon') tb.stroke((hb + tt * 40) % 360, 90, 100, 10 * eg);
    else if (style === 'blueprint') tb.stroke(205, 80, 100, 9 * eg);
    else if (style === 'chrome') tb.stroke((hb) % 360, 12, 100, 10 * eg);
    else tb.stroke((hb) % 360, 60, 100, 12 * eg);
    tb.line(pp[0], pp[1], p[0], p[1]); pp = p;
  }
}
// pass 2: bright thin core
tb.strokeWeight(style === 'ink' ? 1.7 : 1.4); let pc = prev;
for (let s = 0; s < seg.length; s++) {
  const p = seg[s], tt = t + ((s + 1) / steps) * dt;
  const gl = 78 + 22 * Math.sin(tt * 2);
  if (style === 'phosphor') tb.stroke((hb) % 360, 45, gl, 92);
  else if (style === 'neon') tb.stroke((hb + tt * 40) % 360, 92, 100, 90);
  else if (style === 'ink') tb.stroke((hb) % 360, 35, 12, 82);
  else if (style === 'blueprint') tb.stroke(202, 55, 100, 88);
  else tb.stroke((hb) % 360, 8, 100, 90); // chrome
  tb.line(pc[0], pc[1], p[0], p[1]); pc = p;
}
S.lastTip = seg[seg.length - 1];

// composite
push();
if (P.alpha < 100) tint(0, 0, 100, P.alpha);
image(tb, 0, 0, width, height);
pop();

// live clockwork arms on top (the epicycle construction) — a few, semi-transparent
const showArms = P.arms > 0.05;
if (showArms) {
  push(); translate(width * 0.5, height * 0.5);
  const AR = u * 0.42 * (0.4 + P.scale * 0.75);
  let x = 0, y = 0;
  const armAlpha = (style === 'blueprint' ? 55 : 30) * P.arms;
  const armMax = style === 'blueprint' ? S.n : Math.min(S.n, 5);
  for (let k = 0; k < armMax; k++) {
    const f = S.fq[k] * (1 + 0.04 * Math.sin(drift + k));
    const ang = f * t + S.ph[k] + drift * (k + 1) * 0.3;
    const nx = x + AR * S.am[k] * Math.cos(ang), ny = y + AR * S.am[k] * Math.sin(ang);
    noFill(); stroke(style === 'blueprint' ? 205 : hb, style === 'blueprint' ? 60 : 30, 90, armAlpha * 0.7); strokeWeight(1);
    ellipse(x, y, AR * S.am[k] * 2);
    stroke(style === 'blueprint' ? 200 : hb, 40, 100, armAlpha); strokeWeight(1.3); line(x, y, nx, ny);
    x = nx; y = ny;
  }
  // bright drawing head
  const head = 3 + A.treble * 10 + K.pulse * 3;
  noStroke(); fill((hb + 20) % 360, 40, 100, 90); ellipse(x, y, head + 3);
  drawingContext.shadowBlur = 14 + A.rms * 30; drawingContext.shadowColor = 'rgba(180,230,255,0.8)';
  ellipse(x, y, head); drawingContext.shadowBlur = 0;
  pop();
}
