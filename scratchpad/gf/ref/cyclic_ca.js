const D = { hue: 20, energy: .6, speed: 1, density: .5, scale: 1, x: .5, y: .5, states: .5, style: 'spectrum', seed: 0, alpha: 100 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };

const GW = 150, GH = Math.max(60, Math.round(GW * height / width));
const NST = Math.round(4 + P.states * 8); // number of cyclic states (4..12)
const THR = 1; // neighbor threshold — 1 = Greenberg-Hastings regime, reliably spirals & never freezes
function fr(i){ const s = Math.sin(i*127.1 + P.seed*311.7)*43758.5453; return s - Math.floor(s); }
function step(a, b){
  for (let y = 0; y < GH; y++) for (let x = 0; x < GW; x++) {
    const i = y*GW + x, cur = a[i], nxt = (cur + 1) % NST; let cnt = 0;
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
      if (dx === 0 && dy === 0) continue;
      const nx = (x+dx+GW)%GW, ny = (y+dy+GH)%GH;
      if (a[ny*GW+nx] === nxt) cnt++;
    }
    b[i] = (cnt >= THR) ? nxt : cur;
  }
}
if (!S.g || S.gw !== GW || S.gh !== GH) { S.g = createGraphics(GW, GH); S.g.pixelDensity(1); S.gw = GW; S.gh = GH; }
if (!S.a || S.seedUsed !== P.seed || S.nst !== NST || S.len !== GW*GH) {
  S.seedUsed = P.seed; S.nst = NST; S.len = GW*GH;
  S.a = new Int16Array(GW*GH); S.b = new Int16Array(GW*GH);
  for (let i = 0; i < GW*GH; i++) S.a[i] = Math.floor(fr(i*1.7+3) * NST);
  // pre-run so it opens on organized spiral waves, not the chaotic debris phase
  for (let r = 0; r < 90; r++) { step(S.a, S.b); const t = S.a; S.a = S.b; S.b = t; }
}
// time-based stepping (K.t, never frameCount)
const stepN = Math.floor(K.t * (3 + P.speed * 9));
if (S.step !== stepN) {
  const reps = Math.min(3, Math.max(1, stepN - (S.step || stepN - 1)));
  for (let r = 0; r < reps; r++) { step(S.a, S.b); const t = S.a; S.a = S.b; S.b = t; }
  S.step = stepN;
  // reinject a fresh random patch each section so spirals keep being born
  if (S.sec !== K.section) {
    S.sec = K.section;
    const cx = Math.floor(fr(K.section*5+1)*GW), cy = Math.floor(fr(K.section*5+2)*GH), rad = 8;
    for (let dy = -rad; dy <= rad; dy++) for (let dx = -rad; dx <= rad; dx++) {
      const nx = (cx+dx+GW)%GW, ny = (cy+dy+GH)%GH;
      S.a[ny*GW+nx] = Math.floor(fr(nx*3.1+ny*7.7+K.section) * NST);
    }
  }
}
// render current grid -> coarse buffer
const g = S.g, a = S.a; g.loadPixels(); const px = g.pixels;
const style = P.style, hb = P.hue, expo = 0.6 + P.energy * 0.6 + K.intensity * 0.3 + A.rms * 0.5;
function hsv(h, s, v){ h=((h%360)+360)%360/60; const c=v*s, xx=c*(1-Math.abs(h%2-1)), m=v-c; let r,g2,b2;
  if(h<1){r=c;g2=xx;b2=0}else if(h<2){r=xx;g2=c;b2=0}else if(h<3){r=0;g2=c;b2=xx}else if(h<4){r=0;g2=xx;b2=c}else if(h<5){r=xx;g2=0;b2=c}else{r=c;g2=0;b2=xx}
  return [(r+m)*255,(g2+m)*255,(b2+m)*255]; }
for (let y = 0; y < GH; y++) for (let x = 0; x < GW; x++) {
  const i = y*GW + x, s = a[i], f = s / NST;
  let r, gg, b;
  if (style === 'thermal') { const m = Math.min(1, f*1.1*expo); r=Math.min(255,m*2.3*255); gg=Math.max(0,Math.min(255,(m*2-0.5)*255)); b=Math.max(0,Math.min(255,(m*3.4-2.3)*255)); }
  else if (style === 'duotone') { const c1=[hb,80,90], c2=[(hb+180)%360,70,95]; const c=hsv(c1[0]+(c2[0]-c1[0])*f, 0.35+0.5*f, (0.25+0.7*f)*expo); r=c[0];gg=c[1];b=c[2]; }
  else if (style === 'phosphor') { const v = Math.min(1, (0.15+f)*expo); r=v*60; gg=v*255; b=v*90; }
  else if (style === 'contour') { const nb = a[((y+1)%GH)*GW + x], edge = (nb === (s+1)%NST || nb === (s-1+NST)%NST) ? 1 : 0; const base=0.05+f*0.06; const c=hsv(hb+f*40, 0.6, (base+edge*0.9)*expo); r=c[0];gg=c[1];b=c[2]; }
  else { // spectrum — limited analogous iq cosine band (elegant waves, not garish full rainbow)
    const hr = hb/360, ph = 0.55*f + hr, sh = Math.min(1, (0.40 + 0.6*f) * expo);
    r = (0.5 + 0.5*Math.cos(6.2831*(ph + 0.0))) * sh * 255;
    gg = (0.5 + 0.5*Math.cos(6.2831*(ph + 0.20))) * sh * 255;
    b = (0.5 + 0.5*Math.cos(6.2831*(ph + 0.40))) * sh * 255;
  }
  const o = 4*i; px[o]=r; px[o+1]=gg; px[o+2]=b; px[o+3]=255;
}
g.updatePixels();
push();
if (P.alpha < 100) tint(0, 0, 100, P.alpha);
noSmooth(); image(g, 0, 0, width, height);
pop();
