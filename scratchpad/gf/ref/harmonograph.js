const D = { hue: 165, energy: .62, speed: 1, density: .5, scale: 1, x: .5, y: .5, detune: .5, style: 'phosphor', seed: 0, alpha: 100 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };

const u = Math.min(width, height);
const HW = Math.max(140, Math.floor(width*0.5)), HH = Math.max(140, Math.floor(height*0.5));
const bg = [230, 42, 6];
if (!S.tb || S.tw !== HW || S.th !== HH) { S.tb = createGraphics(HW,HH); S.tb.colorMode(HSB,360,100,100,100); S.tb.noStroke(); S.tb.fill(bg[0],bg[1],bg[2]); S.tb.rect(0,0,HW,HH); S.tw=HW; S.th=HH; }
if (S.seedUsed !== P.seed) { S.seedUsed = P.seed;
  const fr = i => { const s = Math.sin(i*127.1 + P.seed*311.7)*43758.5453; return s - Math.floor(s); };
  // clean small-integer ratio (rose/knot), with a tiny detune epsilon so the figure PRECESSES
  const ratios = [[2,3],[3,4],[3,5],[4,5],[2,5],[5,6],[3,7]];
  const rr = ratios[Math.floor(fr(1)*ratios.length)];
  S.fx = rr[0]; S.fy = rr[1];
  S.p = [fr(5)*6.28, fr(6)*6.28, fr(7)*6.28, fr(8)*6.28];
  S.a = [0.62+fr(9)*0.28, 0.30+fr(10)*0.28, 0.62+fr(11)*0.28, 0.30+fr(12)*0.28];
  S.hoff = fr(13)*40;
}
const tb = S.tb, style = P.style;
const fade = style==='ink' ? 3.5 : (style==='blueprint' ? 4.5 : 1.7);
tb.push(); tb.noStroke(); tb.fill(bg[0], bg[1], style==='ink'?96:bg[2], fade); tb.rect(0,0,HW,HH); tb.pop();

const t = K.t*(0.35 + P.speed*0.6);
const cx = HW*0.5, cy = HH*0.5, R = u*0.38*(0.4+P.scale*0.8)*(HW/u);
const hb = (P.hue + S.hoff + K.section*16)%360;
const eps = 0.018 + P.detune*0.09;   // detune between paired pendulums -> the rose PRECESSES (never closes = motion floor)
function pt(tt){
  const f0=S.fx, f1=S.fx+eps, f2=S.fy, f3=S.fy+eps*1.3;
  const x = cx + R*(S.a[0]*Math.sin(f0*tt+S.p[0]) + S.a[1]*Math.sin(f1*tt+S.p[1]));
  const y = cy + R*(S.a[2]*Math.sin(f2*tt+S.p[2]) + S.a[3]*Math.sin(f3*tt+S.p[3]));
  return [x,y];
}
const steps = 34, step = (0.10 + P.speed*0.05), eg = 0.55 + P.energy*0.7;
const seg = []; for (let s=1;s<=steps;s++) seg.push(pt(t + (s/steps)*step));
let prev = S.last || pt(t);
tb.noFill();
// pass 1 wide glow (not ink)
if (style!=='ink'){ tb.strokeWeight(4.2); let pp=prev;
  for (let s=0;s<seg.length;s++){ const p=seg[s], tt=t+((s+1)/steps)*step;
    if (style==='neon') tb.stroke((hb+tt*30)%360,90,100,11*eg);
    else if (style==='blueprint') tb.stroke(205,80,100,9*eg);
    else if (style==='chalk') tb.stroke(hb,15,100,10*eg);
    else tb.stroke(hb,60,100,12*eg);
    tb.line(pp[0],pp[1],p[0],p[1]); pp=p; } }
// pass 2 bright core
tb.strokeWeight(style==='ink'?1.7:1.4); let pc=prev;
for (let s=0;s<seg.length;s++){ const p=seg[s], tt=t+((s+1)/steps)*step; const gl=78+22*Math.sin(tt*1.5);
  if (style==='phosphor') tb.stroke(hb,45,gl,92);
  else if (style==='neon') tb.stroke((hb+tt*30)%360,92,100,90);
  else if (style==='ink') tb.stroke(hb,32,12,82);
  else if (style==='blueprint') tb.stroke(202,55,100,88);
  else tb.stroke(hb,12,100,90); // chalk
  tb.line(pc[0],pc[1],p[0],p[1]); pc=p; }
S.last = seg[seg.length-1];

push();
if (P.alpha<100) tint(0,0,100,P.alpha);
image(tb,0,0,width,height);
pop();
// bright drawing head
push(); translate(width*0.5,height*0.5); const h=pt(t); const hx=(h[0]-cx)*(width/HW), hy=(h[1]-cy)*(height/HH);
noStroke(); fill((hb+20)%360,40,100,90);
drawingContext.shadowBlur=12+A.rms*24; drawingContext.shadowColor='rgba(200,255,235,0.8)';
ellipse(hx,hy,4+A.treble*8); drawingContext.shadowBlur=0; pop();
