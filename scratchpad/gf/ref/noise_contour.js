const D = { hue: 150, energy: .6, speed: 1, density: .55, scale: 1, x: .5, y: .5, levels: .5, style: 'topographic', seed: 0, alpha: 100 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };

const BW = 220, BH = Math.max(60, Math.round(BW * height / width));
if (!S.g || S.bw !== BW || S.bh !== BH) { S.g = createGraphics(BW, BH); S.g.pixelDensity(1); S.bw = BW; S.bh = BH; }
if (S.seedUsed !== P.seed) { S.seedUsed = P.seed;
  const fr = i => { const s = Math.sin(i*127.1 + P.seed*311.7)*43758.5453; return s - Math.floor(s); };
  S.o1 = fr(1)*20; S.o2 = fr(2)*20; S.hoff = fr(3);
}
const sd = P.seed | 0;
function hsh(ix,iy){ let h=(ix*374761393+iy*668265263+sd*2147483647)|0; h=(h^(h>>13))*1274126177|0; return ((h^(h>>16))>>>0)/4294967295; }
function vn(x,y){ const ix=Math.floor(x),iy=Math.floor(y),fx=x-ix,fy=y-iy,u=fx*fx*(3-2*fx),v=fy*fy*(3-2*fy); const a=hsh(ix,iy),b=hsh(ix+1,iy),c=hsh(ix,iy+1),d=hsh(ix+1,iy+1); return a+(b-a)*u+(c-a)*v+(a-b-c+d)*u*v; }
function fbm(x,y){ return 0.55*vn(x,y)+0.28*vn(x*2.05+5.1,y*2.05-3.2)+0.13*vn(x*4.1-2.3,y*4.1+7.7)+0.06*vn(x*8.2+1.1,y*8.2-4.4); }

const t = K.t * (0.05 + P.speed*0.09);
const zoom = 2.4/(0.4+P.scale*1.1);
const L = Math.round(6 + P.levels*20);      // contour levels
const lw = 0.10 + (1-P.energy)*0.05;         // line half-width in band space
const expo = 0.7 + P.energy*0.5 + K.intensity*0.25 + A.rms*0.4;
const hb = (P.hue + S.hoff*30 + K.section*8)%360, style = P.style;
const g = S.g; g.loadPixels(); const px = g.pixels;
function hsv(h,s,v){ h=((h%360)+360)%360/60; const c=v*s,xx=c*(1-Math.abs(h%2-1)),m=v-c; let r,g2,b2; if(h<1){r=c;g2=xx;b2=0}else if(h<2){r=xx;g2=c;b2=0}else if(h<3){r=0;g2=c;b2=xx}else if(h<4){r=0;g2=xx;b2=c}else if(h<5){r=xx;g2=0;b2=c}else{r=c;g2=0;b2=xx} return [(r+m)*255,(g2+m)*255,(b2+m)*255]; }
for (let j=0;j<BH;j++){ for (let i=0;i<BW;i++){
  const nx=(i/BW-0.5)*zoom*(BW/BH)+S.o1 + t*0.15, ny=(j/BH-0.5)*zoom+S.o2 - t*0.05;
  let f = fbm(nx, ny + Math.sin(t*0.6)*0.15);   // 0..1 elevation, drifting
  const band = f*L, frac = band - Math.floor(band), lvl = Math.floor(band)/L;
  const online = (frac < lw || frac > 1-lw) ? 1 : 0;
  let r,gg,b;
  if (style === 'blueprint') { const base=0.05+lvl*0.10; const c=online?[190,255,255]:[base*30,base*90,base*150]; r=c[0]*(online?0.9:1); gg=c[1]*(online?0.95:1); b=c[2]; if(!online){r=base*40;gg=base*90;b=base*150;} else {r=90;gg=200;b=255;} }
  else if (style === 'thermal') { const m=Math.min(1,lvl*1.1*expo); let rr=Math.min(1,m*2.2),g2=Math.max(0,Math.min(1,m*2-0.5)),bb=Math.max(0,Math.min(1,m*3.3-2.2)); if(online){rr=Math.min(1,rr+0.3);g2=Math.min(1,g2+0.3);bb=Math.min(1,bb+0.3);} r=rr*255;gg=g2*255;b=bb*255; }
  else if (style === 'ink') { const paper=0.90-lvl*0.15; const v=online?0.10:paper; r=v*250;gg=v*244;b=v*230; }
  else if (style === 'neon') { const c=hsv(hb+lvl*80, 0.8, online?1.0:(0.12+lvl*0.25)*expo); r=c[0];gg=c[1];b=c[2]; }
  else { // topographic elevation ramp (blue valley -> green -> tan -> white peak)
    let cr,cg,cb;
    if(f<0.35){ const u2=f/0.35; cr=0.10+0.05*u2; cg=0.30+0.35*u2; cb=0.45+0.25*u2; }
    else if(f<0.6){ const u2=(f-0.35)/0.25; cr=0.15+0.45*u2; cg=0.65-0.05*u2; cb=0.35-0.20*u2; }
    else if(f<0.82){ const u2=(f-0.6)/0.22; cr=0.60+0.25*u2; cg=0.60-0.05*u2; cb=0.15+0.10*u2; }
    else { const u2=(f-0.82)/0.18; cr=0.85+0.15*u2; cg=0.55+0.45*u2; cb=0.25+0.70*u2; }
    const sh = expo; cr*=sh; cg*=sh; cb*=sh;
    if(online){ cr*=0.35; cg*=0.35; cb*=0.35; } // dark contour line
    r=Math.min(255,cr*255); gg=Math.min(255,cg*255); b=Math.min(255,cb*255);
  }
  const o=4*(j*BW+i); px[o]=r; px[o+1]=gg; px[o+2]=b; px[o+3]=255;
}}
g.updatePixels();
push();
if (P.alpha<100) tint(0,0,100,P.alpha);
image(g,0,0,width,height);
pop();
