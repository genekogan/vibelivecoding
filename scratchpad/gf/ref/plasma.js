const D = { hue: 268, energy: .62, speed: 1, density: .55, scale: 1, x: .5, y: .5, warp: .6, style: 'nebula', seed: 0, alpha: 100 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };

const BW = 280, BH = Math.max(64, Math.round(BW * height / width));
if (!S.g || S.bw !== BW || S.bh !== BH) { S.g = createGraphics(BW, BH); S.g.pixelDensity(1); S.bw = BW; S.bh = BH; }
if (S.seedUsed !== P.seed) {
  S.seedUsed = P.seed;
  const fr = i => { const s = Math.sin(i * 127.1 + P.seed * 311.7) * 43758.5453; return s - Math.floor(s); };
  S.o1 = fr(1) * 20; S.o2 = fr(2) * 20; S.o3 = fr(3) * 20; S.o4 = fr(4) * 20; S.hoff = fr(5);
}
const sd = (P.seed | 0);
function hsh(ix, iy) { let h = (ix * 374761393 + iy * 668265263 + sd * 2147483647) | 0; h = (h ^ (h >> 13)) * 1274126177 | 0; return ((h ^ (h >> 16)) >>> 0) / 4294967295; }
function vn(x, y) { const ix = Math.floor(x), iy = Math.floor(y), fx = x - ix, fy = y - iy; const u = fx * fx * (3 - 2 * fx), v = fy * fy * (3 - 2 * fy); const a = hsh(ix, iy), b = hsh(ix + 1, iy), c = hsh(ix, iy + 1), d = hsh(ix + 1, iy + 1); return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v; }
function fbm(x, y) { return 0.58 * vn(x, y) + 0.28 * vn(x * 2.02 + 5.1, y * 2.02 - 3.2) + 0.14 * vn(x * 4.05 - 2.3, y * 4.05 + 7.7); }

const t = K.t * (0.06 + P.speed * 0.10);
const zoom = 2.6 / (0.35 + P.scale * 1.15);
const W = 0.6 + P.warp * 3.4;
const sec = K.section, hb = (P.hue + S.hoff * 40 + sec * 23) % 360;
const expo = 0.55 + P.energy * 0.9 + K.intensity * 0.35 + A.rms * 0.7;
const style = P.style;
const g = S.g; g.loadPixels(); const px = g.pixels;
// iq cosine palette (rgb 0..1) tuned per hue base
function pal(m) {
  const hr = hb / 360;
  const r = 0.5 + 0.5 * Math.cos(6.2831 * (1.0 * m + hr + 0.00));
  const gg = 0.5 + 0.5 * Math.cos(6.2831 * (1.0 * m + hr + 0.33));
  const b = 0.5 + 0.5 * Math.cos(6.2831 * (1.0 * m + hr + 0.66));
  return [r, gg, b];
}
for (let j = 0; j < BH; j++) {
  for (let i = 0; i < BW; i++) {
    const nx = (i / BW - 0.5) * zoom * (BW / BH) + S.o1;
    const ny = (j / BH - 0.5) * zoom + S.o2;
    const qx = fbm(nx, ny + t * 0.6), qy = fbm(nx + 3.3, ny - t * 0.5 + 1.7);
    const rx = fbm(nx + W * qx + 1.7, ny + W * qy + 9.2 - t * 0.3);
    const ry = fbm(nx + W * qx + 8.3 + t * 0.25, ny + W * qy + 2.8);
    let val = fbm(nx + W * rx, ny + W * ry);
    const grad = qx - qy; // for iridescence / shading
    let r, gg, b;
    if (style === 'thermal') {
      const m = Math.min(1, val * expo * 1.3);
      r = Math.min(1, m * 2.2); gg = Math.min(1, Math.max(0, m * 2.0 - 0.55)); b = Math.min(1, Math.max(0, m * 3.2 - 2.1));
    } else if (style === 'ink') {
      const shade = Math.pow(Math.min(1, Math.max(0, (val - 0.28) * 2.1 * expo)), 1.3);
      const paper = 0.92 - shade * 0.9; r = paper * 0.98; gg = paper * 0.95; b = paper * 0.88;
    } else if (style === 'iridescent') {
      const hh = (val * 2.4 + grad * 1.5 + t * 0.2) % 1;
      const c = pal(hh); const sh = 0.35 + 0.65 * val * expo; r = c[0] * sh; gg = c[1] * sh; b = c[2] * sh;
    } else if (style === 'blueprint') {
      const band = Math.abs(((val * 9) % 1) - 0.5); const line = band < 0.09 ? 1 : 0;
      const base = 0.05 + val * 0.10; r = base * 0.4 + line * 0.35; gg = base * 0.7 + line * 0.85; b = base * 1.6 + line * 1.0;
    } else { // nebula
      const c = pal(val * 1.15 + grad * 0.25);
      const sh = Math.pow(Math.min(1, val * expo + 0.06), 1.25);
      const fil = Math.max(0, Math.abs(grad) - 0.14) * 2.4 * (0.4 + P.density) * val; // bright wispy filaments on steep gradient
      r = Math.min(1, c[0] * sh + fil * 0.9); gg = Math.min(1, c[1] * sh + fil); b = Math.min(1, c[2] * sh + fil * 0.8);
    }
    const o = 4 * (j * BW + i);
    px[o] = Math.max(0, Math.min(255, r * 255)); px[o + 1] = Math.max(0, Math.min(255, gg * 255)); px[o + 2] = Math.max(0, Math.min(255, b * 255)); px[o + 3] = 255;
  }
}
g.updatePixels();
push();
if (P.alpha < 100) tint(0, 0, 100, P.alpha);
image(g, 0, 0, width, height);
pop();
// faint audio-reactive scanline shimmer on the treble (partial, never full-frame — won't strobe)
if (P.density > 0.05 && (A.treble > 0.02 || A.rms > 0.02)) {
  push(); blendMode(ADD); noStroke();
  const glow = (A.treble * 0.5 + A.rms * 0.4) * P.density * P.energy;
  fill((hb + 30) % 360, 30, 100, glow * 22);
  rect(0, 0, width, height);
  blendMode(BLEND); pop();
}
