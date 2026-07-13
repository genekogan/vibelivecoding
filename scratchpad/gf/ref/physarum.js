const D = { hue: 185, energy: .6, speed: 1, density: .55, scale: 1, x: .5, y: .5, turn: .5, style: 'bioluminescent', seed: 0, alpha: 100 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };

const GW = 300, GH = Math.max(80, Math.round(GW * height / width));
const N = Math.round(3000 + P.density * 6000);
function fr(i){ const s = Math.sin(i*127.1 + P.seed*311.7)*43758.5453; return s - Math.floor(s); }
if (!S.g || S.gw !== GW || S.gh !== GH) { S.g = createGraphics(GW,GH); S.g.pixelDensity(1); S.gw=GW; S.gh=GH; S.trail=null; }
if (!S.trail || S.seedUsed !== P.seed || S.n !== N) {
  S.seedUsed = P.seed; S.n = N;
  S.trail = new Float32Array(GW*GH); S.tmp = new Float32Array(GW*GH);
  S.ax = new Float32Array(N); S.ay = new Float32Array(N); S.ah = new Float32Array(N);
  // spread agents UNIFORMLY across the whole field (a central disk collapses into one blob)
  for (let k=0;k<N;k++){ S.ax[k]=fr(k*2+1)*GW; S.ay[k]=fr(k*2+2)*GH; S.ah[k]=fr(k*3+7)*6.283; }
}
const trail=S.trail, tmp=S.tmp, ax=S.ax, ay=S.ay, ah=S.ah;
const SD = 4 + P.scale*4;                // sensor distance (smaller = finer veins)
const SA = 0.5;                          // sensor angle
const TA = 0.25 + P.turn*0.7;            // turn angle
const SP = 0.7 + P.speed*0.9;            // move speed
const dep = 5.0;                         // deposit
const decay = 0.90;
function sample(x,y){ let ix=Math.floor(x)%GW, iy=Math.floor(y)%GH; if(ix<0)ix+=GW; if(iy<0)iy+=GH; return trail[iy*GW+ix]; }
const steps = 1 + (K.fps>45?1:0);
for (let s=0;s<steps;s++){
  for (let k=0;k<S.n;k++){
    const x=ax[k], y=ay[k], h=ah[k];
    const c=sample(x+Math.cos(h)*SD, y+Math.sin(h)*SD);
    const l=sample(x+Math.cos(h-SA)*SD, y+Math.sin(h-SA)*SD);
    const r=sample(x+Math.cos(h+SA)*SD, y+Math.sin(h+SA)*SD);
    let nh=h;
    if (c>l && c>r) {} else if (l>r) nh=h-TA; else if (r>l) nh=h+TA; else nh=h+(fr(k+ (s*0.11))-0.5)*TA;
    ah[k]=nh;
    let nx=x+Math.cos(nh)*SP, ny=y+Math.sin(nh)*SP;
    if(nx<0)nx+=GW; if(nx>=GW)nx-=GW; if(ny<0)ny+=GH; if(ny>=GH)ny-=GH;
    ax[k]=nx; ay[k]=ny;
    const idx=(Math.floor(ny)*GW+Math.floor(nx));
    trail[idx]+=dep;
  }
  // diffuse (3x3 box) + decay
  for (let y=0;y<GH;y++){ const yu=((y-1+GH)%GH)*GW, yd=((y+1)%GH)*GW, yc=y*GW;
    for (let x=0;x<GW;x++){ const xl=(x-1+GW)%GW, xr=(x+1)%GW;
      const sum=trail[yc+xl]+trail[yc+x]+trail[yc+xr]+trail[yu+xl]+trail[yu+x]+trail[yu+xr]+trail[yd+xl]+trail[yd+x]+trail[yd+xr];
      tmp[yc+x]=(sum/9)*decay; } }
  trail.set(tmp);
}
// render
const g=S.g; g.loadPixels(); const px=g.pixels;
const style=P.style, hb=P.hue, expo=0.7+P.energy*0.9+K.intensity*0.3+A.rms*0.5;
const norm=1/(14 + (1-P.density)*10);
function hsv(h,s,v){ h=((h%360)+360)%360/60; const c=v*s,xx=c*(1-Math.abs(h%2-1)),m=v-c; let r,g2,b2; if(h<1){r=c;g2=xx;b2=0}else if(h<2){r=xx;g2=c;b2=0}else if(h<3){r=0;g2=c;b2=xx}else if(h<4){r=0;g2=xx;b2=c}else if(h<5){r=xx;g2=0;b2=c}else{r=c;g2=0;b2=xx} return [(r+m)*255,(g2+m)*255,(b2+m)*255]; }
for (let i=0;i<GW*GH;i++){
  let v=Math.min(1.15, trail[i]*norm*expo); const o=4*i; let r,gg,b;
  if (style==='coral'){ const c=hsv(18+v*30, 0.85, Math.min(1,0.1+v)); r=c[0];gg=c[1];b=c[2]; }
  else if (style==='ink'){ const p=0.93-v*0.85; r=p*250;gg=p*244;b=p*232; }
  else if (style==='blueprint'){ const base=0.05; r=(base*30+v*40); gg=(base*70+v*160); b=(base*150+v*255); if(b>255)b=255; }
  else if (style==='thermal'){ const m=Math.min(1,v); r=Math.min(255,m*2.4*255); gg=Math.max(0,Math.min(255,(m*2-0.5)*255)); b=Math.max(0,Math.min(255,(m*3.4-2.3)*255)); }
  else { const c=hsv(hb+v*90, 0.75-v*0.25, Math.min(1,0.06+v*1.05)); r=c[0];gg=c[1];b=c[2]; } // bioluminescent
  px[o]=r; px[o+1]=gg; px[o+2]=b; px[o+3]=255;
}
g.updatePixels();
push();
if (P.alpha<100) tint(0,0,100,P.alpha);
image(g,0,0,width,height);
pop();
