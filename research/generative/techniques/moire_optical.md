# Technique — Moiré & optical interference

**Family scope:** superposed periodic *line/dot* families that beat into moiré
fringes; thin‑film **iridescence** (oil‑slick / soap‑bubble); **prism /
refraction** chromatic‑dispersion warp. Pure op‑art shimmer.

**Stay in your lane — two cousins already exist, do NOT rebuild them:**

| Existing asset | What it owns | What THIS family owns instead |
|---|---|---|
| `genart.interference` | radial **ripple sources** → concentric rings colliding | straight & radial **line gratings** superposed → density‑beat moiré |
| `genart.opart` | warped **square‑cell Vasarely grid** under a lens | line‑family moiré, **iridescence field**, **prism dispersion** |

So: no concentric ring sources, no square‑cell grid. Line screens, thin‑film
rainbows, and glassy chromatic warp only. Slot is `genart` → `bg` (fills the
frame, holds luminance in `[0.02,0.92]` with no bed behind it).

Two render lanes, pick per sub‑family:

- **Vector lane** (line‑moiré): draw two rotated families of straight `line()`s
  under `blendMode(MULTIPLY)` at *full canvas res*. Moiré is a **razor** density
  beat the coarse buffer can never match. Cheap (≤ ~600 short strokes).
- **Buffer lane** (oil‑slick, prism): a coarse `createGraphics` pixel field →
  iridescent LUT / per‑channel dispersion → smooth‑upscale to full canvas. This
  is the `dither`/`interference` idiom; use it for anything colored & continuous.

---

## 1 — Algorithm + math

### Line‑moiré (grating superposition)
A grating of parallel lines at angle θ, period p, has phase
`φ(x,y) = (2π/p)(x·cosθ + y·sinθ)`; ink where the duty window of `cos φ` is dark.
Superpose grating 1 `(θ₁,p₁)` and grating 2 `(θ₂,p₂)`.

- **Rotational moiré** (`p₁=p₂=p`, angle diff `α`): fringes appear with spacing
  `P_moiré = p / (2 sin(α/2)) ≈ p/α` for small α, running at angle
  `(θ₁+θ₂)/2 + 90°`. As `α → 0` the fringe spacing blows up to infinity
  (coincidence); as α opens, bands tighten. **Drift α on `K.t` and the fringes
  breathe from wall‑wide to razor forever** — the whole motion floor for free.
- **Vernier moiré** (`θ₁=θ₂`, `p₁≠p₂`): spacing `P = p₁p₂/|p₁−p₂|`. Sliding one
  grating's phase (`φ += ω·t`) makes the fringes **travel** at velocity
  `P·ω/2π`. A period *mismatch* param feeds this.

The visible fringe is a **local‑ink‑coverage beat**: where the two line sets
coincide they leave wide paper gaps (bright); where they interleave they fill in
(dark). That density beat *is* the moiré — MULTIPLY compositing reproduces it
exactly (transmittance product of two overlaid films).

### Thin‑film iridescence (oil‑slick)
Reflected color of a film of thickness `d`, index `n`, wavelength `λ` is
constructive when `2·n·d·cosθ = (m+½)λ`. Perceived hue therefore **cycles
through the spectrum as `d` grows**, repeating once per interference order `m`.
Model it as a smooth **thickness field** `T(x,y,t) ∈ [0,1]` mapped through a
spectral palette that **repeats `orders` times** across `T`; whiten near order
boundaries (soap‑film silver). Advect `T` + drift it globally so all rainbow
bands crawl.

### Prism / refraction warp
Refraction bends sample coordinates by the gradient of a height field:
`u' = u + κ·∇h`. Dispersion makes `κ` wavelength‑dependent (`n(λ)`), so **each
RGB channel bends by a slightly different amount** → spectral fringes on every
edge. Implement as: build a scalar field, take its local slope as a displacement
`disp`, then read the color phase at `+1.0·disp` (R), `+0.0` (G), `−1.0·disp`
(B). No scene to resample — the field *is* the source.

---

## 2 — p5‑2D implementation

### 2a. Vector line‑moiré core loop (headline, razor‑sharp)

Budget spent: **≤300 lines × 2 families = ≤600 short `line()` strokes under
MULTIPLY** (well under the 2000‑point cap; strokes are cheaper than ADD ellipses)
+ ≤10 ADD sparkle circles. No buffer, no `filter()`.

```js
const D = { hue:210, energy:.55, density:.5, scale:1, speed:1, x:.5, y:.5, tilt:.5, mismatch:.5, style:'letterpress', act:'rotate', seed:0 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };
const W=width, H=height, u=Math.min(W,H), TAU=Math.PI*2;
const cl=(v,a,b)=>v<a?a:v>b?b:v, md=(a,n)=>((a%n)+n)%n;
const fr=i=>{const s=Math.sin(i*127.1+P.seed*311.7)*43758.5453;return s-Math.floor(s);};
const st=P.style, ink=(st==='letterpress');

// ground — keep paper value <=0.88 so a sparse grating never blows past lum 0.92
if(ink)                   background(0,0,88);
else if(st==='blueprint') background(212,82,15);
else                      background(md(P.hue,360),12,90);

const spd=P.speed, en=cl(P.energy,0,1);
const ax=cl(P.x,.12,.88)*W, ay=cl(P.y,.12,.88)*H;
const R = Math.hypot(W,H)*0.75;

// density = line count (FIRST poke param, structural); scale = zoom
const nAcross = 12 + cl(P.density,0,1)*66;
let period = (u/nAcross)/cl(P.scale,.3,3);
period = Math.max(period, 2*R/300);        // floor => coverage guaranteed, perf capped
const duty = cl(0.20 + en*0.28, .12, .55); // ink fraction (energy = SECOND poke, contrast)
const lw   = Math.max(0.6, period*duty);

// inter-grating angle drives fringe spacing; breathes on K.t (never rephases)
const secBoost = 0.6 + 0.8*(K.intensity!=null?K.intensity:.6);
const aBreath  = 0.5 + 0.5*Math.sin(K.t*0.05*spd);
let alpha = 0.02 + (0.03 + en*0.30)*secBoost*(0.35+0.65*aBreath) + (A.lowmid||0)*0.05;
let baseAng = md(P.tilt*TAU + K.t*0.03*spd, TAU);   // whole rig drifts
let slide   = K.t*spd*0.55;                          // family-2 phase travel
if(P.act==='slide'){ alpha=0.02; slide=K.t*spd*1.1; }               // near-coincident vernier crawl
else if(P.act==='pulse'){ const j=Math.floor(K.beat*spd); alpha=0.05+0.22*fr(j*2+3)+K.pulse*0.06; }

const p2 = period*(1 + (P.mismatch-0.5)*0.14);      // period mismatch -> vernier beat
const nL = Math.min(300, Math.ceil(R/Math.min(period,p2)));

push();
translate(ax, ay);
blendMode(MULTIPLY);
strokeCap(SQUARE);
strokeWeight(lw);
if(ink) stroke(0,0,10,100); else stroke(md(P.hue,360),60,42,82);
push(); rotate(baseAng);                             // family 1
for(let i=-nL;i<=nL;i++){ const x=i*period; line(x,-R,x,R); }
pop();
if(!ink) stroke(md(P.hue+28,360),60,42,82);
push(); rotate(baseAng+alpha);                       // family 2 (rotated + phase-slid)
const off=md(slide*period,p2);
for(let i=-nL;i<=nL;i++){ const x=i*p2+off; line(x,-R,x,R); }
pop();
blendMode(BLEND);
pop();

// treble sparkle riding the field (audio ON TOP of the K.t floor, few shapes)
if((A.treble||0)>0.06){ blendMode(ADD); noStroke();
  const n=Math.floor(10*A.treble);
  for(let s=0;s<n;s++){ const a=fr(s*3.3+Math.floor(K.beat*2))*TAU;
    fill(ink?0:md(P.hue,360),0,100,40*A.treble);
    circle(ax+Math.cos(a)*u*0.3, ay+Math.sin(a)*u*0.3, u*0.006); }
  blendMode(BLEND);
}
```

Why MULTIPLY: black line × paper = line; where two families overlap vs interleave
the *local paper coverage* swings → the macroscopic light/dark beat. Keep
`duty ≈ 0.25–0.4` — at duty→0.5 every region is half‑covered and the beat washes
out. Native stroke AA anti‑aliases the fringe, which also *tames* strobing.

### 2b. Buffer lane — thickness field → iridescent LUT (oil‑slick / prism)

Budget spent: **176‑px long‑side coarse buffer = ~17k px/frame** (< the 256²=65k
cap), **3‑wave sum‑of‑sines + a 2‑term domain warp per pixel** (`dither` runs 4
waves at 180px → verified 59.5 fps), **one 256‑entry LUT** rebuilt only on
style/hue change, smooth‑upscaled. No feedback, no `filter()`.

```js
const D = { hue:295, scale:1, energy:.6, density:.5, speed:1, x:.5, y:.5, orders:.5, style:'oilfilm', act:'flow', seed:0 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };
const TAU=6.28318530718, cl=(v,a,b)=>v<a?a:v>b?b:v;
const fr=i=>{const q=Math.sin(i*127.1+P.seed*311.7)*43758.5453;return q-Math.floor(q);};
const st=P.style;

// coarse buffer keyed on aspect bucket
const asp=width/height, LS=176; let bw,bh;
if(asp>=1){ bw=LS; bh=Math.max(8,Math.round(LS/asp)); } else { bh=LS; bw=Math.max(8,Math.round(LS*asp)); }
const bkey=bw+'x'+bh;
if(!S.buf||S.bkey!==bkey){ if(S.buf&&S.buf.remove)S.buf.remove(); S.buf=createGraphics(bw,bh); S.buf.pixelDensity(1); S.bkey=bkey; }
const g=S.buf;

// iridescent LUT (256) keyed style+hue — iq cosine spectral sweep + soap-white edges
const lkey=st+'|'+Math.round(P.hue);
if(S.lkey!==lkey){ S.lkey=lkey; const N=256;
  const Rr=new Uint8Array(N),Gg=new Uint8Array(N),Bb=new Uint8Array(N), h0=P.hue/360;
  for(let i=0;i<N;i++){ const t=i/(N-1); let r,gc,b;
    if(st==='oilfilm'){                                   // full spectral cycle, RGB phase 1/3 apart
      r =.5+.5*Math.cos(TAU*(t+h0+0.00));
      gc=.5+.5*Math.cos(TAU*(t+h0+0.33));
      b =.5+.5*Math.cos(TAU*(t+h0+0.67));
      const wh=Math.pow(Math.abs(Math.cos(TAU*t)),10)*0.55;// soap-silver flash at each order edge
      r=r*(1-wh)+wh; gc=gc*(1-wh)+wh; b=b*(1-wh)+wh;
    } else if(st==='thermal'){ const m=t, h=(250-235*m+360)%360, c=color(h,90-30*m,25+70*m);
      r=c.levels[0]/255; gc=c.levels[1]/255; b=c.levels[2]/255;
    } else { const v=0.14+0.78*(0.5+0.5*Math.cos(TAU*t)); r=gc=b=v; }   // silver / near-mono
    Rr[i]=r*255|0; Gg[i]=gc*255|0; Bb[i]=b*255|0;
  }
  S.R=Rr; S.Gc=Gg; S.B=Bb;
}

// seeded 3-wave thickness field
if(S.seedUsed!==P.seed){ S.seedUsed=P.seed; const Wv=[]; let sw=0;
  for(let i=0;i<3;i++){ const ang=fr(i*9)*TAU, f=1.4+fr(i*9+1)*2.6, w=.6+fr(i*9+5)*.5;
    Wv.push({fx:Math.cos(ang)*f, fy:Math.sin(ang)*f, ph:fr(i*9+2)*TAU, sp:(fr(i*9+3)*.6+.2)*(fr(i*9+4)<.5?-1:1), w}); sw+=w; }
  S.Wv=Wv; S.sw=sw;
}
const Wv=S.Wv, norm=0.5/S.sw;
const spd=cl(P.speed,.2,4), en=cl(P.energy,0,1), sc=cl(P.scale,.3,3);
const ordersN = 1.2 + cl(P.orders,0,1)*3.5 + sc*0.6;    // rainbow band count (scale = FIRST poke)
const warpAmt = 0.10 + en*0.16;                          // domain-warp depth (energy = SECOND poke)
const drift = K.t*spd*0.06 + K.section*0.04;             // global thickness drift = motion floor
const boil  = K.t*spd*0.40;                              // field advection
const oil=(st==='oilfilm'), prism=(st==='prism'), R=S.R,Gc=S.Gc,B=S.B;

g.loadPixels(); const px=g.pixels, invW=1/(bw-1), invH=1/(bh-1); let idx=0;
for(let yy=0;yy<bh;yy++){ const ny=yy*invH;
  for(let xx=0;xx<bw;xx++){ const nx=xx*invW;
    const wx=nx*4 + warpAmt*Math.sin(ny*7.0+boil);       // domain warp -> organic slick blobs
    const wy=ny*4 + warpAmt*Math.sin(nx*7.0+boil*1.1);
    let T=0; for(let i=0;i<3;i++){ const w=Wv[i]; T+=Math.sin(wx*w.fx+wy*w.fy+w.ph+boil*w.sp)*w.w; }
    T=0.5+T*norm;                                         // thickness proxy 0..1
    if(prism){                                            // chromatic dispersion: RGB read at 3 phases
      const base=(T+drift)*ordersN, disp=(T-0.5)*(0.06+en*0.10);
      const pr=base+disp, pg=base, pb=base-disp;
      px[idx]  =(0.14+0.82*(0.5+0.5*Math.cos(TAU*pr)))*255|0;
      px[idx+1]=(0.14+0.82*(0.5+0.5*Math.cos(TAU*pg)))*255|0;
      px[idx+2]=(0.14+0.82*(0.5+0.5*Math.cos(TAU*pb)))*255|0;
    } else {
      let ph=(T+drift)*ordersN; ph-=Math.floor(ph);       // wrap into LUT -> repeating orders
      let li=(ph*255)|0; if(li<0)li=0; else if(li>255)li=255;
      px[idx]=R[li]; px[idx+1]=Gc[li]; px[idx+2]=B[li];
    }
    px[idx+3]=255; idx+=4;
  }
}
g.updatePixels();
drawingContext.imageSmoothingEnabled=true;
image(g,0,0,width,height);
blendMode(BLEND);
```

**Buffer‑lane hazard — grating aliasing.** If you ever try to draw *actual fine
gratings* into this buffer (e.g. `cos(nx·80)`), any frequency above ~`bw/4`
aliases and you get random speckle instead of a clean beat. Rule: the buffer
lane carries **smooth low‑frequency fields** (thickness, dispersion) only. Fine
razor gratings go through the **vector lane (2a)** at full res.

---

## 3 — Parameter surface

Order params so the **first two numerics poke to an obvious change** (validator
maxes both together). `hue` never first (360 wraps to red≈0).

| Param | Lane | Range (safe both ends) | Maps to |
|---|---|---|---|
| `density` | vector **(1st)** | 0–1 → 12…78 lines across | line count / grating fineness |
| `energy` | both **(2nd)** | 0–1 | fringe contrast, duty, α amplitude, warp depth, dispersion |
| `scale` | buffer **(1st)** / vector | 0.3–3 | zoom (period ÷) / rainbow‑order base |
| `speed` | both | 0.2–4 | α‑drift + slide + boil rate (beats‑relative) |
| `hue` | both | 0–360 | ink tint / spectral base (ignored by `letterpress`) |
| `x`,`y` | both | 0.1–0.9 | rig anchor / warp center |
| `orders` | buffer | 0–1 → 1.2…4.7 cycles | iridescence band count |
| `tilt` | vector | 0–1 → 0…2π | base grating rotation |
| `mismatch` | vector | 0–1 (0.5=matched) | period ratio → vernier beat |
| `style` | both | see §4 | render philosophy |
| `act` | both | see §5 | multi‑minute dramaturgy |
| `seed` | both | 0–9999 int | hash‑seeded layout (rebuild on change) |

Extreme safety: at `density=1 scale=3` the vector `period` floors at `2R/300`
so it never explodes the line count or vanishes below coverage. At `energy=1`
duty caps 0.55 (beat still present) and warp caps 0.26 (field stays coherent).
`orders` max 4.7 keeps rainbow bands resolvable in a 176‑px buffer. α always has
a `+0.02` floor so the two gratings never fully coincide into flat gray.

---

## 4 — Palette / tone strategy

Everything is HSB 360/100/100/100 (never call `colorMode`). Rebuild LUTs only on
`style|hue` change. **iq cosine palette** is the spine of the colored looks:

```
color(t) = a + b·cos( 2π·(c·t + d) )     // a=b=0.5, c=cycles, d=RGB phase offset
// spectral rainbow: dR=0.00  dG=0.33  dB=0.67   (used verbatim in 2b's oilfilm LUT)
```

Ship **≥3 divergent looks**, **≥1 non‑representational**:

- **`letterpress`** *(vector, non‑representational, the anchor)* — value‑88 paper,
  value‑10 ink, MULTIPLY. Hard, austere, razor moiré. No hue. Bridget‑Riley / Soto
  black‑and‑white op. This alone satisfies the non‑rep requirement.
- **`oilfilm`** *(buffer)* — the iq spectral cosine with 1/3 RGB phase offsets +
  a `pow(|cos|,10)` soap‑silver flash at each order edge. Petrol‑on‑wet‑asphalt
  rainbow; `hue` rotates where the spectrum starts.
- **`prism`** *(buffer)* — per‑channel dispersion read (§2b). Glassy chromatic
  fringes on every field edge; `energy` widens the split. Cruz‑Diez / Pantone.
- **`blueprint` / `schematic`** *(vector or buffer, non‑rep extra)* — cyan ink on
  dark ground, low duty, contour‑only. Technical, cold.
- **`thermal`** *(buffer)* — indigo→cyan→magenta→gold heat ramp of the thickness
  field. False‑color, clinical.
- **`riso`** *(vector)* — two colored inks (`hue`, `hue+28`) misregistered under
  MULTIPLY → duotone print moiré.

Mood range: `letterpress`/`blueprint` read austere & clinical; `oilfilm`
sensual & psychedelic; `thermal` eerie. Let `hue` extremes reach desaturated /
near‑mono (the `else` LUT branch = silver) so it isn't all brights.

---

## 5 — Temporal strategy (30 s – 5 min, never re‑phases)

This engine **freezes beat‑locked‑only motion at 8 s** (cps 0.5 → 16 beats
re‑phase). Every drift below is on **`K.t`** (real seconds), so nothing rewinds:

- **Motion floor (`K.t`)** — vector: α breathes `sin(K.t·0.05·spd)`, whole rig
  rotates `K.t·0.03·spd`, family‑2 phase slides `K.t·spd·0.55`. Buffer: thickness
  drift `K.t·spd·0.06` (all rainbow bands crawl seamlessly) + field boil
  `K.t·spd·0.40`. Any one of these clears the 0.004 motion gate solo. **Never**
  drive the primary rotation off `K.beat` — that re‑phases and reads static at 8 s;
  reserve `K.pulse`/`K.beat` for accents only.
- **Arc (`K.section` / `K.intensity`)** — `secBoost` scales α amplitude &
  fringe contrast so the piece tightens/loosens over the 8‑bar arc; add
  `K.section·0.04` to the thickness drift so each section reveals new orders.
  Over 5 min the fringe density and rainbow‑band count ride the musical arc.
- **Audio on top** — `A.lowmid` opens α (fringes bloom on the groove), `A.bass`
  bumps contrast, `A.treble` sparkles (vector) / boosts order count. Baseline
  must carry motion with `A.*` all zero (validation runs silent).
- **`P.act` programs (multi‑minute):**
  - vector `rotate` — α breathes, rig spins slowly (default).
  - vector `slide` — α pinned ≈0, one grating phase‑crawls → vernier fringes
    sweep across the frame like a tide.
  - vector `pulse` — α snaps to a seeded angle each beat (`K.pulse` kick) →
    the fringe pattern re‑locks rhythmically.
  - buffer `flow` — steady advected slick (default).
  - buffer `bloom` — `orders`/warp swell on `K.intensity`; rainbow densifies then
    thins over each section.
  - buffer `boil` — faster field churn, bands roil in place.

---

## 6 — Exemplars + failure modes

**Exemplar artists** (roster; `_cards/` empty, so cite by name):
- **Jesús Rafael Soto** & **Ludwig Wilding** — superimposed line screens →
  vibrating moiré; the literal reference for the vector lane.
- **Bridget Riley** & **Victor Vasarely** — op‑art shimmer / kinetic lineage
  (`opart` owns the warped grid; here it's the line‑family read).
- **Carlos Cruz‑Diez** (*Physichromie*) & **Felipe Pantone** — chromatic
  interference / spectral dispersion → the `prism` look.
- **Marcel Duchamp** (*Rotoreliefs*) — rotating optical discs → the continuous
  α‑rotation dramaturgy.
- Thin‑film / soap‑bubble & petrol‑sheen physics → the `oilfilm` iridescence
  (non‑representational spectral option).

**Failure modes (family‑specific cause → fix):**
- **Blank / flat gray** — gratings fully coincide (`α=0` *and* matched period) →
  keep the `+0.02` α floor and let `mismatch` detune; OR you left `MULTIPLY` on
  with nothing drawn (whole canvas darkens each frame) → always restore
  `blendMode(BLEND)`; OR forgot `updatePixels()`/`image(g,…)`.
- **Static at 8 s** — you drove rotation off `K.beat` (re‑phases at 16 beats).
  Move the primary drift to `K.t`; beats are accents only.
- **Luminance out of [0.02,0.92]** — letterpress paper too bright + too few lines
  → cap paper value ≤ 0.88 and keep `density` producing ink; oilfilm LUT with no
  brightness floor goes < 0.02 → keep the `0.14 +` floor in every channel.
- **Strobing > 0.35** — fine gratings rotating fast make the *whole field* flash
  light/dark together; α collapsing toward 0 makes one giant fringe fill the
  frame. Slow α‑drift (`≤0.05·K.t`), hold the α floor so fringe spacing never
  covers the frame, cap `speed`, moderate `duty`. Prism: bound `disp` so channels
  don't full‑frame swap. Native stroke AA already softens the beat — don't defeat
  it with `imageSmoothingEnabled=false` on the vector lane.
- **Perf** — vector `nL` capped at 300 (period floored at `2R/300`); buffer
  `LS ≤ 192` and sum‑of‑**sines** per pixel (never `noise()` per pixel — heavier);
  LUT rebuilt only on style/hue change; **no full‑canvas `filter()`**.
- **Buffer speckle** — a grating finer than ~`bw/4` aliased in the buffer. Keep
  the buffer lane to smooth low‑freq fields; push razor gratings to the vector lane.
