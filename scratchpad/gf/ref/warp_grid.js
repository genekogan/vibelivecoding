const D = { hue: 210, energy: .6, speed: 1, density: .5, scale: 1, x: .5, y: .5, warp: .6, style: 'wire', seed: 0, alpha: 100 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };

const u = Math.min(width, height);
const GX = Math.round(10 + P.density * 26), GY = Math.round(6 + P.density * 16);
if (S.seedUsed !== P.seed) { S.seedUsed = P.seed;
  const fr = i => { const s = Math.sin(i*127.1 + P.seed*311.7)*43758.5453; return s - Math.floor(s); };
  S.o1 = fr(1)*20; S.o2 = fr(2)*20; S.hoff = fr(3)*60;
}
const sd = P.seed | 0;
function hsh(ix,iy){ let h=(ix*374761393+iy*668265263+sd*2147483647)|0; h=(h^(h>>13))*1274126177|0; return ((h^(h>>16))>>>0)/4294967295; }
function vn(x,y){ const ix=Math.floor(x),iy=Math.floor(y),fx=x-ix,fy=y-iy,uu=fx*fx*(3-2*fx),vv=fy*fy*(3-2*fy); const a=hsh(ix,iy),b=hsh(ix+1,iy),c=hsh(ix,iy+1),d=hsh(ix+1,iy+1); return a+(b-a)*uu+(c-a)*vv+(a-b-c+d)*uu*vv; }
function fbm(x,y){ return 0.6*vn(x,y)+0.3*vn(x*2.03+5.1,y*2.03-3.2)+0.15*vn(x*4.1-2.3,y*4.1+7.7); }

const t = K.t*(0.10 + P.speed*0.18);
const amp = u * 0.05 * (0.3 + P.warp*2.6) * (0.6 + K.intensity*0.7);
const marginX = width*0.06, marginY = height*0.06;
const cw = (width-2*marginX)/(GX-1), ch = (height-2*marginY)/(GY-1);
const style = P.style, hb = (P.hue + S.hoff + K.section*14)%360;
const expo = 0.5 + P.energy*0.7 + A.rms*0.5;

// compute displaced vertices
const VX = [], VY = [], VD = [];
for (let j=0;j<GY;j++){ for (let i=0;i<GX;i++){
  const bx = marginX + i*cw, by = marginY + j*ch;
  const fx = i*0.28 + S.o1, fy = j*0.30 + S.o2;
  const dx = fbm(fx + t*0.5, fy) - 0.5, dy = fbm(fx + 5.3, fy - t*0.4) - 0.5;
  const disp = Math.sqrt(dx*dx+dy*dy);
  VX.push(bx + dx*amp*2); VY.push(by + dy*amp*2); VD.push(disp);
}}
function idx(i,j){ return j*GX+i; }

push();
if (P.alpha < 100) drawingContext.globalAlpha = P.alpha/100;
if (style === 'ink') { background(38, 12, 96); } else if (style === 'blueprint') { background(215, 70, 22); } else { background(hb, 40, 7); }

if (style === 'solid') {
  noStroke();
  for (let j=0;j<GY-1;j++){ for (let i=0;i<GX-1;i++){
    const a=idx(i,j),b=idx(i+1,j),c=idx(i+1,j+1),d=idx(i,j+1);
    const shade = 0.30 + Math.min(1,(VD[a]+VD[c])*1.3)*0.7;
    fill((hb + (VD[a]*160))%360, 60, Math.min(100, shade*100*expo), 96);
    quad(VX[a],VY[a],VX[b],VY[b],VX[c],VY[c],VX[d],VY[d]);
  }}
} else if (style === 'dot') {
  noStroke();
  for (let k=0;k<VX.length;k++){ const s=2.5+VD[k]*12*P.scale; fill((hb+VD[k]*150)%360, 75, Math.min(100,(50+VD[k]*180)*expo), 96); ellipse(VX[k],VY[k], s+A.treble*6); }
} else { // wire / blueprint / ink — grid lines, cheap two-pass glow (NO per-line shadowBlur)
  const wire = style==='wire';
  // pass 1: wide soft glow (wire only)
  if (wire){ blendMode(ADD); strokeWeight(3.4);
    for (let j=0;j<GY;j++){ for (let i=0;i<GX;i++){ const a=idx(i,j);
      if (i<GX-1){ const b=idx(i+1,j); const d=(VD[a]+VD[b])*0.5; stroke((hb+d*170)%360,80,100,10); line(VX[a],VY[a],VX[b],VY[b]); }
      if (j<GY-1){ const c=idx(i,j+1); const d=(VD[a]+VD[c])*0.5; stroke((hb+d*170)%360,80,100,10); line(VX[a],VY[a],VX[c],VY[c]); }
    }}
    blendMode(BLEND);
  }
  // pass 2: crisp core
  for (let j=0;j<GY;j++){ for (let i=0;i<GX;i++){ const a=idx(i,j);
    if (i<GX-1){ const b=idx(i+1,j); const d=(VD[a]+VD[b])*0.5;
      if (style==='blueprint'){ stroke(200,55,100,75); strokeWeight(1); }
      else if (style==='ink'){ stroke(hb,30,12,82); strokeWeight(0.8+d*3); }
      else { stroke((hb+d*170)%360,70,Math.min(100,(60+d*130)*expo),92); strokeWeight(1+d*2.2); }
      line(VX[a],VY[a],VX[b],VY[b]); }
    if (j<GY-1){ const c=idx(i,j+1); const d=(VD[a]+VD[c])*0.5;
      if (style==='blueprint'){ stroke(200,55,100,75); strokeWeight(1); }
      else if (style==='ink'){ stroke(hb,30,12,82); strokeWeight(0.8+d*3); }
      else { stroke((hb+d*170)%360,70,Math.min(100,(60+d*130)*expo),92); strokeWeight(1+d*2.2); }
      line(VX[a],VY[a],VX[c],VY[c]); }
  }}
}
if (P.alpha < 100) drawingContext.globalAlpha = 1;
pop();
