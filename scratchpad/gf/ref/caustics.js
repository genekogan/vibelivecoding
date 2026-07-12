const D = { hue: 195, energy: .62, speed: 1, density: .5, scale: 1, x: .5, y: .5, sharp: .6, style: 'pool', seed: 0, alpha: 100 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };

const BW = 240, BH = Math.max(60, Math.round(BW * height / width));
if (!S.g || S.bw !== BW || S.bh !== BH) { S.g = createGraphics(BW, BH); S.g.pixelDensity(1); S.bw = BW; S.bh = BH; }
if (S.seedUsed !== P.seed) { S.seedUsed = P.seed;
  const fr = i => { const s = Math.sin(i*127.1 + P.seed*311.7)*43758.5453; return s - Math.floor(s); };
  S.o1 = fr(1)*20; S.o2 = fr(2)*20; S.hoff = fr(3);
}
const sd = P.seed | 0;
function hsh(ix,iy){ let h=(ix*374761393+iy*668265263+sd*2147483647)|0; h=(h^(h>>13))*1274126177|0; return ((h^(h>>16))>>>0)/4294967295; }
function vn(x,y){ const ix=Math.floor(x),iy=Math.floor(y),fx=x-ix,fy=y-iy,u=fx*fx*(3-2*fx),v=fy*fy*(3-2*fy); const a=hsh(ix,iy),b=hsh(ix+1,iy),c=hsh(ix,iy+1),d=hsh(ix+1,iy+1); return a+(b-a)*u+(c-a)*v+(a-b-c+d)*u*v; }
function fbm(x,y){ return 0.6*vn(x,y)+0.3*vn(x*2.03+5.1,y*2.03-3.2)+0.15*vn(x*4.1-2.3,y*4.1+7.7); }

const t = K.t * (0.10 + P.speed*0.16);
const zoom = 3.0/(0.4+P.scale*1.1);
const pw = 2.5 + P.sharp*7;         // caustic vein sharpness
const expo = 0.5 + P.energy*1.0 + K.intensity*0.3 + A.rms*0.6;
const hb = (P.hue + S.hoff*30 + K.section*10)%360, style = P.style;
const g = S.g; g.loadPixels(); const px = g.pixels;
for (let j=0;j<BH;j++){ for (let i=0;i<BW;i++){
  const nx=(i/BW-0.5)*zoom*(BW/BH)+S.o1, ny=(j/BH-0.5)*zoom+S.o2;
  // two warped phase fields whose interference forms focusing caustic ridges
  const wx=fbm(nx+t*0.4, ny), wy=fbm(nx-2.7, ny+t*0.35);
  const a1=Math.sin((nx+1.5*wx)*3.3 + t*1.1);
  const a2=Math.sin((ny+1.5*wy)*3.1 - t*0.9);
  const a3=Math.sin((nx+ny+1.2*(wx+wy))*2.2 + t*0.7);
  let ridge=(Math.abs(a1)+Math.abs(a2)+Math.abs(a3))/3;      // 0..1, low where lines cross -> focus
  let caust=Math.pow(1-ridge, pw)*1.6;                        // bright thin veins
  caust=Math.min(1.4, caust*expo);
  let r,gg,b;
  if (style==='thermal'){ const m=Math.min(1,caust); r=Math.min(255,m*2.4*255); gg=Math.max(0,Math.min(255,(m*2.0-0.5)*255)); b=Math.max(0,Math.min(255,(0.15+m*0.3)*255)); }
  else if (style==='mercury'){ const base=0.10+0.12*wx; const v=Math.min(1,base+caust); r=v*225; gg=v*232; b=v*245; }
  else if (style==='blueprint'){ const band=Math.abs(((ridge*8)%1)-0.5); const line=band<0.08?1:0; const base=0.04+wx*0.06; r=(base*0.4+line*0.3)*255; gg=(base*0.7+line*0.8)*255; b=(base*1.5+caust*0.6+line)*255; if(b>255)b=255; }
  else if (style==='sunset'){ const water=[0.10,0.03,0.06]; const c=[1.0,0.75,0.35]; const v=Math.min(1,caust); r=Math.min(255,(water[0]+c[0]*v)*255); gg=Math.min(255,(water[1]+c[1]*v)*255); b=Math.min(255,(water[2]+c[2]*v)*255); }
  else { // pool (deep blue-teal water + white-cyan caustics)
    const depth=0.06+0.10*(0.5+0.5*wx); const water=[depth*0.15, depth*0.9, depth*1.2];
    const v=Math.min(1,caust); const cr=0.55+0.45*v, cg=0.85+0.15*v, cb=1.0;
    r=Math.min(255,(water[0]+cr*v*0.95)*255); gg=Math.min(255,(water[1]+cg*v)*255); b=Math.min(255,(water[2]*0.8+cb*v)*255);
  }
  const o=4*(j*BW+i); px[o]=r; px[o+1]=gg; px[o+2]=b; px[o+3]=255;
}}
g.updatePixels();
push();
if (P.alpha<100) tint(0,0,100,P.alpha);
image(g,0,0,width,height);
pop();
