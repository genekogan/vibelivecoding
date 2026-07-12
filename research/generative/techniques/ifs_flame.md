# Technique — Iterated Function Systems & the Fractal Flame

**Family:** chaos-game point accumulation onto a persistent density buffer, tone-mapped
with **log-density + gamma** and colored by a structural **color coordinate**.
Covers Barnsley fern, Sierpinski gasket, Heighway dragon (linear IFS) and the
**Draves fractal flame / Electric Sheep** generalization (affine + nonlinear variations).

**Differentiate hard from `genart.attractor`.** That asset is a *Clifford strange
attractor*: a single deterministic map, splatted with `blendMode(ADD)` alpha ellipses,
colored by iteration index. This family is fundamentally different in BOTH algorithm and
render: a **weighted set of contractive maps** chosen by a chaos game, a **nonlinear
variation** stage (the flame signature), a **real log-density histogram** (not additive
alpha splats — the histogram is what gives flames their luminous depth), and **structural
color** (an averaged color coordinate indexing a palette, not `i%360`). Author it so a
side-by-side reads as a different instrument, not a reskin.

Slot: **`genart` → `bg`** (owns the frame, validated with no bed behind → must fill the
canvas and hold luminance in [0.02, 0.92]).

---

## 1. Algorithm + math

### The chaos game (all IFS variants)
An IFS is a finite set of **contractive** affine maps `F_i`, each fired with probability
`p_i` (`Σ p_i = 1`). Iterate a single point; after burn-in the orbit lands on and densely
paints the system's attractor (Barnsley's *collage theorem*: the attractor is the union
`∪ F_i(attractor)`).

```
affine:  F_i(x,y) = ( a_i·x + b_i·y + c_i ,  d_i·x + e_i·y + f_i )
loop:    pick i with prob p_i ;  (x,y) ← F_i(x,y) ;  plot (x,y)
```

Contractive = the linear part `[[a,b],[d,e]]` has spectral radius < 1 (roughly `a·e−b·d`
small and rows short). Non-contractive → the orbit diverges to infinity → blank render.

**Concrete map sets (exact coefficients — use these literally):**

- **Barnsley fern** (4 maps, `x'=a x+b y+c, y'=d x+e y+f`):

  | p | a | b | c | d | e | f |
  |---|---|---|---|---|---|---|
  | .01 | 0 | 0 | 0 | .16 | 0 | 0 | (stem) |
  | .85 | .85 | .04 | 0 | −.04 | .85 | 1.6 | (successively smaller fronds) |
  | .07 | .20 | −.26 | 0 | .23 | .22 | 1.6 | (left leaflet) |
  | .07 | −.15 | .28 | 0 | .26 | .24 | .44 | (right leaflet) |

  Attractor bounds ≈ `x∈[−2.8, 2.75], y∈[0, 10]`.

- **Sierpinski gasket** (3 maps, equal `p=1/3`): `F_i(x,y) = ((x+V_ix)/2, (y+V_iy)/2)`
  toward vertices `V = (0,0), (1,0), (0.5, 0.866)`. Bounds = that triangle.

- **Heighway dragon** (2 maps, `p=.5`): `F1: a=.5,b=−.5,d=.5,e=.5`; `F2: a=−.5,b=−.5,c=1,d=.5,e=−.5`.

### The fractal flame generalization (Draves 1992)
Each map gets a **nonlinear variation** `V` applied *after* its affine, and carries a
**color index** `col_i ∈ [0,1]`. Per iteration:

```
1. pick map i by prob
2. affine:      (px,py) = F_i(x,y)
3. variation:   (px,py) = blend( (px,py) , V_m(px,py) , warp )   // warp∈[0,1]
4. color coord: c ← (c + col_i) / 2                              // Draves color scheme
5. accumulate:  hist[bin]++ ,  csum[bin] += c                    // density + color
```

Canonical variations (input `(x,y)`, `r²=x²+y²`, `r=√r²`, `θ=atan2(x,y)`):

```
0 linear        (x, y)
1 sinusoidal    (sin x, sin y)
2 spherical     (x/r², y/r²)
3 swirl         (x·sin r² − y·cos r²,  x·cos r² + y·sin r²)
4 horseshoe     ((x−y)(x+y)/r,  2xy/r)
5 polar         (θ/π,  r−1)
6 handkerchief  (r·sin(θ+r),  r·cos(θ−r))
7 disc          (θ/π·sin(π r),  θ/π·cos(π r))
```

`warp` linearly blends affine↔variation, so `warp=0` gives a crisp linear IFS (a clean
Sierpinski gasket) and `warp=1` gives full flame swirl from the *same* code path.

### Log-density + gamma tone map (the flame's signature)
Density spans many orders of magnitude (dense core vs. faint tendrils). Naive linear
mapping crushes the tendrils to black. Draves' fix — map **log** of the count, then gamma:

```
norm  = log(1 + n·exposure) / log(1 + nMax·exposure)   // n = hist[bin], nMax = running max
value = norm ^ (1/gamma)                                // gamma ≈ 2.4 lifts faint detail
rgb   = palette[ csum[bin]/n ] · value                  // structural color × brightness
```

`nMax` tracked per frame gives **auto-exposure** → luminance self-stabilizes regardless of
coefficients/density (a robust luminance gate, see §6).

---

## 2. p5-2D implementation

Realtime constraint: a true flame needs millions of samples, but we only get ~2000
iterations/frame. Solution = a **persistent Float32 histogram with rolling exponential
decay**. Each frame decays the old histogram (`× 0.86–0.985`) and adds ~2000 fresh chaos
samples, so density accumulates to an effective `iters/(1−decay) ≈ 15k–130k` samples —
enough for log-density depth — while continuously **following coefficient drift** (never
freezes, never re-phases). Tone-map the histogram into a **coarse `createGraphics` buffer**
and `image()`-upscale to the full canvas (upscale smoothing = free bloom).

**Budget accounting (every cost tied to a PROBE line):**
- Coarse grid long-axis **200** (→ `200×112` on 16:9 ≈ 22k px, `200×200` = 40k px square) —
  under the **≤256² per-pixel** cap (`pix_256x256` = 59.2fps).
- **~2000 pure-JS chaos iterations/frame** (900 + density·2100). These are typed-array
  writes, **not** `beginShape(POINTS)` p5 draws — they don't spend the 2000-*p5-points*
  budget; that cap is for draw calls. Cheaper.
- **3 array passes** over the grid (decay+max, then tonemap) ≈ 3×40k = 120k ops/frame.
- **One full-frame `image()` upscale** + one optional ADD bloom pass (`feedback_fullcanvas`
  self-stamp was free, so one extra image draw is fine).
- **No full-canvas `filter()`** (banned, ~12ms). Bloom = the upscale + one translucent ADD redraw.

```js
const D = { energy:.6, scale:1, density:.55, speed:1, hue:22, gamma:2.4, persist:.5, warp:.7, x:.5, y:.5, system:'flame', style:'electricsheep', seed:0, act:'breathe' };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };

// --- coarse accumulation grid (long axis 200; keyed on canvas aspect only → survives resize) ---
const LA = 200;
let cw, ch;
if (width >= height){ cw = LA; ch = Math.max(64, Math.round(LA*height/width)); }
else { ch = LA; cw = Math.max(64, Math.round(LA*width/height)); }
if (S.gridKey !== cw+'x'+ch){
  S.gridKey = cw+'x'+ch; S.cw=cw; S.ch=ch;
  S.hist = new Float32Array(cw*ch);
  S.csum = new Float32Array(cw*ch);
  if (S.buf) S.buf.remove();
  S.buf = createGraphics(cw,ch); S.buf.pixelDensity(1);
}
cw=S.cw; ch=S.ch; const N4=cw*ch;

// --- seeded LCG (free-runs; reseed only on P.seed change → seed-deterministic look) ---
if (S.seedUsed !== P.seed){
  S.seedUsed = P.seed;
  let z=(P.seed*2654435761 ^ 0x9e3779b9)>>>0;
  S.rnd=()=>{ z=(z*1664525+1013904223)>>>0; return z/4294967296; };
  S.ox=S.rnd()*2-1; S.oy=S.rnd()*2-1; S.oc=S.rnd();
}
const rnd=S.rnd;

// --- build the IFS map set on system/seed change ---
if (S.sysKey !== P.system+'|'+P.seed){
  S.sysKey = P.system+'|'+P.seed;
  const M=[];
  if (P.system==='fern'){
    M.push({p:.01,a:0,b:0,c:0,d:.16,e:0,f:0,v:0,col:.05});
    M.push({p:.85,a:.85,b:.04,c:0,d:-.04,e:.85,f:1.6,v:0,col:.34});
    M.push({p:.07,a:.2,b:-.26,c:0,d:.23,e:.22,f:1.6,v:0,col:.62});
    M.push({p:.07,a:-.15,b:.28,c:0,d:.26,e:.24,f:.44,v:0,col:.9});
    S.dom={x0:-2.8,x1:2.75,y0:0,y1:10};
  } else if (P.system==='sierpinski'){
    const V=[[0,0],[1,0],[.5,.866]];
    for (let i=0;i<3;i++) M.push({p:1/3,a:.5,b:0,c:V[i][0]*.5,d:0,e:.5,f:V[i][1]*.5,v:0,col:i/3+.12});
    S.dom={x0:0,x1:1,y0:0,y1:.866};
  } else if (P.system==='dragon'){
    M.push({p:.5,a:.5,b:-.5,c:0,d:.5,e:.5,f:0,v:0,col:.18});
    M.push({p:.5,a:-.5,b:-.5,c:1,d:.5,e:-.5,f:0,v:0,col:.72});
    S.dom={x0:-.45,x1:1.25,y0:-.45,y1:1.05};
  } else { // 'flame' — random contractive affines + a variation each
    const k=2+(rnd()*3|0);
    for (let i=0;i<k;i++){ const s=.35+rnd()*.5;
      M.push({p:1/k, a:(rnd()*2-1)*s,b:(rnd()*2-1)*s,c:(rnd()*2-1)*.6,
                     d:(rnd()*2-1)*s,e:(rnd()*2-1)*s,f:(rnd()*2-1)*.6,
                     v:1+(rnd()*7|0), col:i/k+rnd()*.1}); }
    S.dom={x0:-1.7,x1:1.7,y0:-1.7,y1:1.7};
  }
  let acc=0; for (const m of M){ acc+=m.p; m.cp=acc; }
  S.maps=M; S.mapAcc=acc;
}
const maps=S.maps, dom=S.dom;

// --- palette LUT (256×3 float) on hue/style/seed change (built ONCE, never per-pixel) ---
if (S.palKey !== P.style+'|'+Math.round(P.hue)+'|'+P.seed){
  S.palKey = P.style+'|'+Math.round(P.hue)+'|'+P.seed;
  S.pal=new Float32Array(256*3); const h0=P.hue/360, TAU=6.28318, st=P.style;
  for (let i=0;i<256;i++){ const t=i/255; let r,g,b;
    if (st==='thermal'){ r=Math.min(1,t*1.8); g=Math.max(0,Math.min(1,(t-.35)*1.7)); b=Math.max(0,(t-.75)*3.4); }
    else if (st==='ink'){ r=g=b=t; }                                   // resolved vs paper in tonemap
    else if (st==='noir'){ r=.5*t+.12*t*t; g=.66*t; b=Math.min(1,.8*t+.22); }
    else if (st==='duotone'){ if(t<.5){const u=t*2; r=.9*u; g=.14*u; b=.34*u;} else {const u=(t-.5)*2; r=.1+.2*u; g=.1+.42*u; b=.1+.85*u;} }
    else { r=.5+.5*Math.cos(TAU*(h0+t+.00)); g=.5+.5*Math.cos(TAU*(h0+t+.33)); b=.5+.5*Math.cos(TAU*(h0+t+.67)); } // electricsheep: iq cosine
    S.pal[i*3]=r; S.pal[i*3+1]=g; S.pal[i*3+2]=b; }
}
const pal=S.pal;

// --- temporal drift program (K.t floor — continuous seconds, never re-phases) ---
const intn=(K.intensity!=null?K.intensity:.6);
let driftAmp=.18, rotRate=.05;
if (P.act==='storm'){ driftAmp=.34*(.5+intn); rotRate=.14; }
else if (P.act==='bloom'){ driftAmp=.09; rotRate=.03; }
const T=K.t*P.speed;
const morph=(P.system==='flame')?driftAmp:0;              // only flame morphs coeffs; IFS keep exact shape
// rotate whole attractor about its own centre (hoisted: 2 trig/frame, applied per point)
const rot=(P.system==='fern')?Math.sin(K.t*.3)*.06:K.t*rotRate*P.speed;
const cr=Math.cos(rot), sr=Math.sin(rot);
const dcx=(dom.x0+dom.x1)/2, dcy=(dom.y0+dom.y1)/2, dw=dom.x1-dom.x0, dh=dom.y1-dom.y0;

// --- rolling decay + running max (pass 1 over the grid) ---
const decay=0.86+P.persist*0.125;
const hist=S.hist, csum=S.csum;
let nMax=0;
for (let i=0;i<N4;i++){ const v=hist[i]*decay; hist[i]=v; csum[i]*=decay; if(v>nMax)nMax=v; }

// --- chaos game (pure-JS math; ~2000 iters, never touches p5) ---
const iters=Math.floor((900+P.density*2100)*(0.7+intn*0.5)+A.bass*400);
let x=S.ox,y=S.oy,cc=S.oc; const eps=1e-9;
for (let it=0; it<iters; it++){
  const rr=rnd()*S.mapAcc; let m=maps[0];
  for (let j=0;j<maps.length;j++){ if(rr<=maps[j].cp){ m=maps[j]; break; } }
  let a=m.a,b=m.b,c=m.c,d=m.d,e=m.e,f=m.f;
  if (morph){ const ph=m.col*6.28; a+=Math.sin(T*.11+ph)*morph; e+=Math.cos(T*.09+ph)*morph; c+=Math.sin(T*.07+ph)*morph*.5; f+=Math.cos(T*.13+ph)*morph*.5; }
  let px=a*x+b*y+c, py=d*x+e*y+f;
  if (m.v && P.warp>0.001){
    const r2=px*px+py*py+eps, r=Math.sqrt(r2), th=Math.atan2(px,py); let vx=px,vy=py;
    switch(m.v){
      case 1: vx=Math.sin(px); vy=Math.sin(py); break;
      case 2: vx=px/r2; vy=py/r2; break;
      case 3: vx=px*Math.sin(r2)-py*Math.cos(r2); vy=px*Math.cos(r2)+py*Math.sin(r2); break;
      case 4: vx=(px-py)*(px+py)/r; vy=2*px*py/r; break;
      case 5: vx=th/Math.PI; vy=r-1; break;
      case 6: vx=r*Math.sin(th+r); vy=r*Math.cos(th-r); break;
      case 7: vx=(th/Math.PI)*Math.sin(Math.PI*r); vy=(th/Math.PI)*Math.cos(Math.PI*r); break;
    }
    px+=(vx-px)*P.warp; py+=(vy-py)*P.warp;
  }
  x=px; y=py; cc=(cc+m.col)*0.5;
  if (!(x>-1e4&&x<1e4&&y>-1e4&&y<1e4)){ x=rnd()*2-1; y=rnd()*2-1; cc=rnd(); continue; } // NaN/divergence respawn
  if (it<8) continue;                                                                    // cheap burn-in
  // rotate about attractor centre, then domain-map → grid with user scale/anchor
  const rx=x-dcx, ry=y-dcy;
  let gx=((rx*cr-ry*sr)+dcx-dom.x0)/dw, gy=((rx*sr+ry*cr)+dcy-dom.y0)/dh;
  gy=1-gy;                                                                               // flip to image space
  gx=(gx-0.5)/P.scale+P.x; gy=(gy-0.5)/P.scale+P.y;
  const ix=(gx*cw)|0, iy=(gy*ch)|0;
  if (ix>=0&&ix<cw&&iy>=0&&iy<ch){ const bi=iy*cw+ix; const nv=hist[bi]+1; hist[bi]=nv; csum[bi]+=cc; if(nv>nMax)nMax=nv; }
}
S.ox=x; S.oy=y; S.oc=cc;

// --- log-density + gamma tone map → coarse buffer (pass 2) ---
const expo=0.5+P.energy*2.2+K.pulse*0.22+A.rms*1.1;      // beat bump is PARTIAL → no strobe
const invG=1/Math.max(0.3,P.gamma);
const logMax=Math.log(1+nMax*expo)+1e-3;
const st=P.style, ink=(st==='ink');
const bgR=ink?216:6, bgG=ink?213:4, bgB=ink?206:12;      // dark-but-not-black / paper (never pure white)
const buf=S.buf; buf.loadPixels(); const q=buf.pixels;
for (let i=0;i<N4;i++){ const n=hist[i]; let R,G,B;
  if (n<1e-3){ R=bgR; G=bgG; B=bgB; }
  else { let br=Math.log(1+n*expo)/logMax; if(br>1)br=1; br=Math.pow(br,invG);
    if (st==='thermal'){ const k=(br*255)|0; R=pal[k*3]*255; G=pal[k*3+1]*255; B=pal[k*3+2]*255; }
    else if (ink){ const val=1-br*0.9; R=bgR*val; G=bgG*val; B=bgB*val; }               // DARK flame on paper (light-key)
    else { let k=((csum[i]/n)*255)|0; if(k<0)k=0; if(k>255)k=255; R=pal[k*3]*255*br; G=pal[k*3+1]*255*br; B=pal[k*3+2]*255*br; }
  }
  const p4=i*4; q[p4]=R; q[p4+1]=G; q[p4+2]=B; q[p4+3]=255;
}
buf.updatePixels();

// --- upscale full-frame (no rotation here → no corner gaps) + optional cheap bloom ---
image(buf,0,0,width,height);
if (!ink){ blendMode(ADD); tint(255,30+P.energy*26); image(buf,0,0,width,height); noTint(); blendMode(BLEND); }
drawingContext.shadowBlur=0;
```

Key patterns lifted from house style: seeded LCG + cached `createGraphics` buffer keyed in
`S` (as in `genart.dla`); auto-exposure so the luminance gate self-stabilizes; every knob
read from `P` each frame.

---

## 3. Parameter surface

Order matters — the params gate pokes the **first two numerics to max together** and
demands an obvious change. Lead with **energy** (exposure) then **scale** (zoom); both are
dramatic at max, neither wraps like `hue`.

| param | default | min | max | maps to | notes / why safe at both extremes |
|---|---|---|---|---|---|
| `energy` | .6 | 0 | 1 | **exposure** (log gain) + iteration count | 0 → dim thin flame (still visible, auto-exposed); 1 → blazing full bloom. **First numeric.** |
| `scale` | 1 | .4 | 2.4 | flame zoom vs grid | .4 → small centred; 2.4 → fills/overspills frame (clipped cleanly by grid bounds). **Second numeric — nearly doubles size at max.** |
| `density` | .55 | .1 | 1 | iters/frame 1110→3000 | .1 → sparse sparkle; 1 → dense solid — both bounded (≤3000 pure-JS iters). |
| `speed` | 1 | .2 | 3 | drift + rotation rate | .2 → glacial; 3 → churning. Only rate — shape stays valid. |
| `hue` | 22 | 0 | 360 | palette base hue (electricsheep/noir/duotone) | 360 wraps to 0 — **never first.** |
| `gamma` | 2.4 | 1.2 | 4.5 | tone-map gamma | 1.2 → hard core-only contrast; 4.5 → faint tendrils lifted. Both hold luminance (auto-exposed). |
| `persist` | .5 | 0 | 1 | histogram decay 0.86→0.985 | 0 → crisp/live (follows drift instantly); 1 → long luminous smear trails. |
| `warp` | .7 | 0 | 1 | affine↔variation blend | 0 → crisp linear IFS (clean gasket/fern); 1 → full nonlinear flame swirl. |
| `x`,`y` | .5,.5 | .2 | .8 | attractor anchor fraction | clamped band keeps it on-frame. |
| `system` | `flame` | — | — | IFS family | `flame · fern · sierpinski · dragon` — one asset covers all four. |
| `style` | `electricsheep` | — | — | palette/tone discipline | see §4 (≥5 looks). |
| `seed` | 0 | 0 | 9999 | int — flame affines + variation assignment + palette phase | rebuilds `S.maps`/`S.pal` on change. |
| `act` | `breathe` | — | — | multi-minute program | `breathe · bloom · storm` (see §5). |

**Optional extra — `sym` (int 1–6):** replicate each plotted point around `n` rotations for
dihedral flame-mandalas. Cost: `n×` the bin writes → drop `iters` by `1/n` to stay in budget.

---

## 4. Palette / tone strategy

Color is written as **raw RGB into `buf.pixels[]`** (we bypass the HSB `fill()` path
deliberately — per-pixel `fill()` is the banned per-scanline pattern; a 256-entry LUT built
**once** on change is the sanctioned move). Structural color = `palette[ csum/n ]`, i.e. the
map-averaged color coordinate, NOT iteration index — this is what makes flame color read as
*material*, coherent across the whole structure.

**iq cosine palette** (the electricsheep engine): `col(t) = 0.5 + 0.5·cos(2π(t + phase))`
per channel with channel phases `(0, .33, .67)` and a `hue/360` offset → a smooth full
spectrum, hue-rotatable by one param.

Five divergent `style` looks (≥3 required, ≥1 non-representational, ≥1 non-glow/light-key):

1. **`electricsheep`** *(default)* — classic Draves: full-spectrum iq-cosine structural
   color, log-density bloom on near-black, saturated luminous tendrils. The signature.
2. **`thermal`** — **non-representational** false-color heat ramp (black→red→amber→white)
   indexed on **log-density itself** (ignores structural color). Hot dense core, cool edges.
3. **`ink`** — **light-key, non-glow**: near-monochrome graphite/sumi bloom, **dark flame on
   warm paper** (tone map subtracts brightness from paper instead of adding). Inverts the
   whole family off dark-key and satisfies the gamut spread.
4. **`noir`** — desaturated blue-white phosphor / oscilloscope-X-ray. Clinical, austere.
5. **`duotone`** — two-ink risograph split at `c=0.5` (warm ink vs. blue ink), flat and
   graphic rather than glowing.

HSB discipline: the LUT stays inside a controlled ramp — `thermal`/`ink`/`noir` are
near-monochrome or duotone (no rainbow-vomit), `electricsheep` is the only full-spectrum
option and even it is anchored by `hue`. Big flat fills are impossible here — the log-density
gradient textures every region.

---

## 5. Temporal strategy (30s – 5min)

This engine **freezes beat-locked-only motion at the 8s gate** (cps 0.5 → 16 beats re-phase
→ reads static). Our continuous motion floor is **real-time `K.t` seconds**, monotonic and
non-repeating:

- **Coefficient drift (flame):** each map's `a,e,c,f` wander on `sin/cos(K.t·speed·small)` —
  the flame slowly *morphs shape* forever. Because the histogram is a **rolling-decay
  accumulation**, the render tracks the drift in real time (never converges to a frozen
  frame). This alone clears the motion gate (cousin `genart.attractor` scored 0.0096 with the
  same drift approach; floor is 0.004).
- **Attractor rotation:** whole shape rotates about its own centre at `K.t·rotRate` (fern
  gets a gentle ±0.06rad *sway* instead of a full spin — an upright fern shouldn't tumble).
  Applies to fern/sierpinski/dragon too, so even the fixed-coefficient IFS never freeze.
- **`K.section` / `K.intensity` arcs (30s–5min):** `intensity` scales both `exposure` and
  `iters` → the flame breathes brighter/busier through the musical arc without intervention.
- **`P.act` programs:**
  - `breathe` — gentle coefficient wobble + slow rotation (ambient backdrop).
  - `bloom` — low drift, slow rotation; exposure ramps with section (a flower opening).
  - `storm` — high drift amplitude + fast rotation scaled by intensity (violent churn at peak).
- **Beat/audio on top (never the sole motion):** `K.pulse` and `A.bass` add a **partial**
  exposure bump (`+0.22·pulse`) and a few hundred extra iterations — a luminous throb on the
  kick. Kept partial so a full-frame flash can't trip the 0.35 strobe ceiling; the rolling
  decay smooths transients further.

---

## 6. Exemplar artists + failure modes

**Exemplars** *(no artist cards on disk yet — cited by name):*
- **Scott Draves** — *Fractal Flames* (1992) & *Electric Sheep*: the log-density + gamma +
  structural-color + variations algorithm this file implements. The canonical reference.
- **Michael Barnsley** — *Fractals Everywhere*, the fern, the IFS/collage-theorem foundation.
- **Wacław Sierpiński** — the gasket; the textbook chaos-game demonstrator.
- **Benoît Mandelbrot** — the fractal-geometry lineage (escape-time cousin, aesthetic context).
- **Karl Sims** — evolved genotype→phenotype aesthetics (the genetic layer of Electric Sheep).
- **Jared Tarbell** (Complexification) — the point-accumulation-on-a-substrate sensibility.
- **Paul Bourke** — reference IFS/attractor implementations & galleries (technical exemplar).
- **Apophysis / JWildfire** community — the flame-editor variation vocabulary.

**Failure modes & mitigations:**

| mode | cause | fix (already in the core loop) |
|---|---|---|
| **Blank render** (lum < 0.02) | non-contractive maps → orbit diverges; empty histogram | keep affines contractive (`s∈[.35,.85]`); NaN/`|x,y|>1e4` respawn; dark-but-not-black bg floor (6,4,12) keeps lum ≥ ~0.03 even when sparse |
| **Static freeze** (motion < 0.004) | no `K.t` drift, or `__clk` stopped (`K.t=0`) | coefficient drift + attractor rotation are always-on and `K.t`-driven; requires the `__clk` metronome running (engine invariant) |
| **Luminance out of [0.02,0.92]** | thin flame on pure black (low), or paper mode all-paper (high) | **auto-exposure** (`nMax`-normalized log) self-stabilizes; ink paper capped at 216 (lum ≈ 0.83 < 0.92) |
| **Strobing > 0.35** | exposure/gamma slammed by the beat → full-frame flash | beat bump is partial (`+0.22·K.pulse`); rolling decay damps transients; never invert the whole frame |
| **NaN poisoning** | `spherical`/`swirl` ÷ `r²` at `r=0` propagates NaN through the persistent orbit | `r²+=1e-9` epsilon; finite-check respawn each iteration |
| **Degenerate collapse** (line/point) | wrong cumulative-probability pick or bad `p` sum | `cp` cumulative table + `rnd()*mapAcc`; the exact fern/sierpinski coefficients above are validated |
| **Perf creep** (< 25fps) | too many iters, grid > 256², or per-pixel palette recompute | `iters ≤ 3000` (density-capped), grid long-axis 200, palette LUT built once per change, no `filter()` |

---

**Proposed `style` looks for assets in this family (≥3):**
`electricsheep` (default — full-spectrum Draves flame, log-density bloom on black) ·
`thermal` (non-representational density-mapped heat false-color) ·
`ink` (light-key sumi/graphite bloom, dark flame on warm paper) ·
plus `noir` (desaturated phosphor/X-ray) and `duotone` (two-ink riso split).
