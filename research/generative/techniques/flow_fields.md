# Technique — Flow / curl-noise fields

Advecting particles, **dye continua**, **ribbon bundles**, **streamline contours**, and
**ASCII glyph grids** through a 2D velocity field. A field family: one shared velocity
kernel, four hard-different *renderers* on top.

> **Differentiation mandate.** `genart.flowfield` already ships the obvious renderer —
> hundreds of particles advected by `θ = noise·2π`, drawn as thin `line()` streaks, in
> `silk / ink / thermal / neon / schematic`. **Do NOT re-author that.** This file documents
> the treatments it does *not* do, each a different rendering *philosophy* (continuum vs.
> mass vs. contour vs. glyph), and each upgrades the field itself from a raw noise-angle to
> a **divergence-free curl field**. Feeds recipes: `curl_smoke`, `diffusion_dye`,
> `flow_ribbons`, `streamline_contours` / `isolines`, `ascii_field`.

---

## 1. Algorithm + math

### 1.1 The velocity field — noise-angle vs. curl (the upgrade)

The legacy flowfield uses the noise value *as the angle*:

```
θ(x,y,t) = noise(x·s, y·s, t) · 2π · turb        v = (cos θ, sin θ)
```

This field is **not** divergence-free. `∇·v ≠ 0` ⇒ it has **sources and sinks**: particles
pile into attractor points and evacuate others (the "combed" marbled look), and dye pumped
through it vanishes into sinks. Fine for streaks, wrong for smoke.

**Curl noise** (Bridson, *Curl-Noise for Procedural Fluid Flow*, 2007) fixes this. Treat a
scalar noise field `ψ` as a **stream function** and take its perpendicular gradient:

```
ψ(x,y,t) = noise(x·s, y·s, t·rate)              (the potential)
v = ∇⊥ψ = ( ∂ψ/∂y , −∂ψ/∂x )
```

By construction `∇·v = ∂²ψ/∂x∂y − ∂²ψ/∂y∂x = 0` → **incompressible**. No sources/sinks:
streamlines never terminate at a point, mass is conserved, you get vortices and rivers, not
combing seams. Finite-difference it (central, step `ε`):

```
vx = ψ(x, y+ε) − ψ(x, y−ε)
vy = −( ψ(x+ε, y) − ψ(x−ε, y) )
θ  = atan2(vy, vx) · turb          // turb bends/twists the streamlines
```

Four `noise()` taps per sample point. This single `θ` kernel drives **all four** renderers
below — the family is unified by its field, divided by its render.

### 1.2 Dye advection (the continuum renderer)

A scalar dye density `D(x,t)` (or per-channel color) is *transported* by `v`:

```
∂D/∂t + (v·∇)D = 0
```

Solve with **semi-Lagrangian backtrace** (Stam, *Stable Fluids*, 1999) — unconditionally
stable, no CFL blow-up: for each grid cell `x`, look one step *upstream* and copy what was
there:

```
x_prev = x − v̂(x)·h                             (v̂ = unit direction, h ≈ 1 cell)
D_new(x) = bilerp(D_old, x_prev) · dissipation   (dissipation < 1 → smoke fades)
```

Semi-Lagrangian is **inherently diffusive** (the bilinear read blurs each step), so you
usually need **no separate blur pass** — a budget gift. Re-inject dye at a moving emitter
each frame (the motion floor). This is `curl_smoke` (rising plume) and `diffusion_dye`
(bleeding pigment, higher dissipation).

### 1.3 Streamline integration (ribbons + contours)

A streamline is the curve everywhere tangent to `v`: `dx/ds = v̂(x)`. March it (Euler is
plenty at this scale):

```
x_{k+1} = x_k + (cos θ_k, sin θ_k)·h_step
```

- **Ribbon**: carry a width `w_k` and emit the two edges offset along the *perpendicular*
  `n = (−sin θ, cos θ)`: `left = x + n·w/2`, `right = x − n·w/2`. Feed as a `TRIANGLE_STRIP`.
  Taper `w` by arclength (fat middle, thin ends) → silk. Braid by adding a per-ribbon
  lateral oscillation with a phase offset so neighbors interleave.
- **Contour**: draw the streamline itself as a thin polyline. Seed many, evenly, and you get
  Tyler Hobbs' *evenly-spaced streamlines* — a topographic flow map (`streamline_contours`).

### 1.4 Isoline variant (marching squares)

Alternatively contour the **potential** `ψ` directly: sample `ψ` on a grid, and for `L`
quantized levels run marching squares → topographic isolines that *flow* as `ψ` drifts.
This is the `isolines` recipe; it reads as a living contour map, not particles.

### 1.5 ASCII sampling (the glyph renderer)

On a character grid, sample `θ` at each cell and pick a glyph from a **direction ramp**
(`- \ | /` for 4 sectors, extend to 8) — glyph *choice* encodes direction, no per-glyph
rotation needed. Modulate brightness by `|v|` or by a dye field sampled at the cell. Pure
data-viz of the field → non-representational (`ascii_field`, Gysin lineage).

---

## 2. p5-2D implementation (this engine, within PROBE)

All four renderers share the curl helper `ang(x,y)`. **Budget named per renderer.**

### 2.A Dye buffer — flagship (`curl_smoke` / `diffusion_dye`)

**Budget spent: per-pixel buffer at 128×72** (9,216 cells ≪ 65k cap; sits exactly on the
PROBE "128×72 domain-warp = free" line), **single-octave curl = 4 `noise()`/cell ≈ 37k/frame**
(PROBE blesses 3-octave domainwarp at 128×72 and multi-pass Gray-Scott at 60fps, so this is
in budget). Ceiling **160×90**; do **not** exceed 192×108. Upscaled to full canvas by one
`image()` — smoothing gives the silky continuum.

```js
const D = { density:.55, energy:.6, speed:1, scale:1, hue:24, turb:.6, diffuse:.3, x:.5, y:.72, style:'smoke', act:'plume', seed:0 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };
const W = width, H = height, u = Math.min(W,H), TAU = 6.28318530718;
const clp = (v,a,b)=> v<a?a:v>b?b:v;

// coarse dye grid, aspect-matched, size-keyed cache
const GW = Math.min(160, 128), GH = Math.max(2, Math.round(GW*H/W)), GN = GW*GH;
if (!S.d || S.gw!==GW || S.gh!==GH){
  S.gw=GW; S.gh=GH; S.d=new Float32Array(GN); S.d2=new Float32Array(GN);
  if (S.buf && S.buf.remove) S.buf.remove();
  S.buf = createGraphics(GW,GH); S.buf.pixelDensity(1);
}
// iq-cosine palette LUT (256 RGB bytes), rebuilt only on style/hue/seed change
const lkey = P.style+':'+Math.round(P.hue)+':'+(P.seed|0);
if (S.lkey!==lkey){ S.lkey=lkey; S.lut = buildLUT(P.style, P.hue, P.seed); }

// --- shared curl velocity kernel (seed folded into noise coord, NOT noiseSeed) ---
const zt   = K.t*(0.04 + P.speed*0.05) + (P.seed|0)*0.13;   // real-time field drift (never re-phases)
const sp   = 0.010 / clp(P.scale,0.3,3);                    // swirl size
const turb = 0.7 + P.turb*2.2 + A.lowmid*1.4;               // vortex strength (audio ON TOP)
const eps  = 1.3;
const ns   = (x,y)=> noise(x*sp, y*sp, zt);
const ang  = (x,y)=> Math.atan2( ns(x,y+eps)-ns(x,y-eps), -(ns(x+eps,y)-ns(x-eps,y)) ) * turb;

// --- act dramaturgy + wandering emitter (perpetual injection = motion floor) ---
const intn = K.intensity!=null?K.intensity:.6;
let dissip = clp(0.990 - P.diffuse*0.014, 0.972, 0.994);    // <1 so it clears; ≥0.972 never blanks
let emit   = 0.30 + P.density*0.55 + A.bass*0.6 + K.pulse*0.22*P.energy;
let ex = clp(P.x,0,1), ey = clp(P.y,0,1), er = 0.045 + P.density*0.05;
if (P.act==='gust')      emit *= 0.6 + (K.section%2?0.9:0.2) + K.pulse*0.5;
else if (P.act==='bloom'){ dissip = clp(dissip-0.006,0.965,0.99); er *= 1.6; }
ex += Math.cos(K.t*0.23)*0.05; ey += Math.sin(K.t*0.19)*0.035;   // slow orbit → plume wanders

const cw = W/GW, chh = H/GH, step = 0.8 + P.speed*1.4;      // backtrace ≈ 1–2 cells (CFL-safe)
const src=S.d, dst=S.d2;
// --- semi-Lagrangian advect (backtrace in grid coords, bilinear read) ---
for (let gy=0; gy<GH; gy++){
  const py=(gy+0.5)*chh;
  for (let gx=0; gx<GW; gx++){
    const a = ang((gx+0.5)*cw, py);
    let sx = clp(gx - Math.cos(a)*step, 0, GW-1.001);
    let sy = clp(gy - Math.sin(a)*step, 0, GH-1.001);
    const x0=sx|0, y0=sy|0, fx=sx-x0, fy=sy-y0, i00=y0*GW+x0;
    const t0=src[i00]+(src[i00+1]-src[i00])*fx;
    const t1=src[i00+GW]+(src[i00+GW+1]-src[i00+GW])*fx;
    dst[gy*GW+gx]=(t0+(t1-t0)*fy)*dissip;
  }
}
// --- inject emitter (radial falloff) into dst ---
const cxg=ex*GW, cyg=ey*GH, rg=Math.max(1,er*GW), r2=rg*rg;
for (let dy=-rg; dy<=rg; dy++) for (let dx=-rg; dx<=rg; dx++){
  const q=dx*dx+dy*dy; if (q>r2) continue;
  const x=(cxg+dx)|0, y=(cyg+dy)|0; if (x<0||x>=GW||y<0||y>=GH) continue;
  const i=y*GW+x; dst[i]=Math.min(1.5, dst[i] + emit*(1-q/r2)*0.5);
}
// --- render dye through LUT → buffer bytes → upscale ---
S.buf.loadPixels();
const pix=S.buf.pixels, lut=S.lut, bri=0.55+P.energy*0.6;
for (let i=0;i<GN;i++){
  let d=dst[i]*bri; if(d>1)d=1; const li=(d*255)|0, l=li*3, j=i<<2;
  pix[j]=lut[l]; pix[j+1]=lut[l+1]; pix[j+2]=lut[l+2]; pix[j+3]=255;
}
S.buf.updatePixels();
S.d=dst; S.d2=src;                    // ping-pong swap
image(S.buf, 0,0, W,H);               // smoothing upscale = silky continuum

// --- iq cosine palette; base tone guarantees luminance floor, cap avoids whiteout ---
function buildLUT(style, hue, seed){
  const L=new Uint8ClampedArray(768), TAU=6.28318530718;
  const iq=(t,a,b,c,d)=>[a[0]+b[0]*Math.cos(TAU*(c[0]*t+d[0])),
                         a[1]+b[1]*Math.cos(TAU*(c[1]*t+d[1])),
                         a[2]+b[2]*Math.cos(TAU*(c[2]*t+d[2]))];
  const base=[0.04,0.05,0.08];        // dark blue-grey floor (lum≈0.05 > 0.02) — never black frame
  for (let i=0;i<256;i++){ const t=i/255; let c;
    if (style==='thermal')      c=iq(t,[.5,.35,.3],[.5,.45,.4],[1,1,1],[.0,.20,.38]);   // blue→red→white heat
    else if (style==='oilslick')c=iq(t,[.5,.5,.5],[.45,.45,.45],[1,1,1],[.0,.33,.66]);  // iridescent
    else if (style==='ink'){ const g=t*0.85; c=[g,g,g*1.02]; }                          // near-mono sumi
    else /* smoke: warm dye */  c=iq(t,[.5,.32,.28],[.5,.42,.42],[1,1,1],[.02,.12+hue/3600,.24]);
    L[i*3]  = clp(base[0]+c[0]*t,0,0.96)*255;
    L[i*3+1]= clp(base[1]+c[1]*t,0,0.96)*255;
    L[i*3+2]= clp(base[2]+c[2]*t,0,0.96)*255;
  }
  return L;
}
```

*Multi-color dye:* carry a second field `Hgrid` (hue/age) advected by the *same* backtrace,
and index the LUT 2D — or run 3 float channels (RGB dye). Both stay in the 160×90 budget;
prefer single-density + LUT (cheapest, and gorgeous).

### 2.B Ribbon bundles (`flow_ribbons`)

**Budget: ≤40 filled `TRIANGLE_STRIP` shapes** (≪ 150 heavy-shape cap; each ribbon is one
thin shape, not ¼-canvas), ≤ 40×48 field evals. Reuse `ang()` from §2.A.

```js
const NR = Math.round(6 + P.density*34), L = 48, sPx = u*0.010*(0.6+P.speed*1.2);
const hsh = i=>{ const s=Math.sin(i*127.1+(P.seed|0)*311.7)*43758.5453; return s-Math.floor(s); };
blendMode(ADD); noStroke();
for (let r=0;r<NR;r++){
  let x=(P.x+(hsh(r)*2-1)*0.34)*W, y=(P.y+(hsh(r+99)*2-1)*0.30)*H + Math.sin(K.t*0.5+r)*u*0.02;
  const hue=(P.hue+(hsh(r+7)-0.5)*40+K.t*3+360)%360, braid=Math.sin(r*1.7)*(P.braid||.4);
  beginShape(TRIANGLE_STRIP);
  for (let k=0;k<=L;k++){
    const t=k/L, a=ang(x,y)+braid*Math.sin(k*0.4+K.t*2)*0.5;
    const w=u*0.006*(0.3+P.scale)*(0.4+Math.sin(Math.PI*t))*(1+P.energy);
    const nx=-Math.sin(a), ny=Math.cos(a);
    fill(hue,70,92,(10+P.energy*22)*(0.3+Math.sin(Math.PI*t)*0.7));
    vertex(x+nx*w,y+ny*w); vertex(x-nx*w,y-ny*w);
    x+=Math.cos(a)*sPx; y+=Math.sin(a)*sPx;
  }
  endShape();
}
blendMode(BLEND);
```

Re-integrating every frame from wandering seeds is the motion floor — ribbons breathe and
re-braid continuously with `K.t`; no beat lock needed.

### 2.C Streamline contours (`streamline_contours` / `isolines`)

**Budget: ≤ ~1800 polyline vertices** (`NS·L ≤ 1800`, under the 2000-point free budget) as
`beginShape()` lines — *or* the isoline variant on a **96×54** marching grid (PROBE: marching
squares 96×54 = free).

```js
// (a) evenly-spawned long streamlines as fine ink contours (Tyler Hobbs look)
const NS = Math.round(10 + P.density*28), L = 60, sPx = u*0.008;
noFill(); strokeWeight(1.0 + P.energy*1.1);
for (let s=0;s<NS;s++){
  let x=hsh(s*2)*W, y=hsh(s*2+1)*H;
  stroke((P.hue+K.t*4)%360, 14, 88, 34+P.energy*30);   // near-mono ink-on-cream
  beginShape();
  for (let k=0;k<L;k++){ vertex(x,y); const a=ang(x,y); x+=Math.cos(a)*sPx; y+=Math.sin(a)*sPx;
    if (x<0||x>W||y<0||y>H) break; }
  endShape();
}
```

For the topographic **isoline** style, sample `ψ = ns(px,py)` on a 96×54 grid, march `levels`
(4–16) quantized thresholds, draw the crossing segments; as `zt` drifts the whole contour map
flows. Quantize `levels` gently (lerp the level offset over `K.section`) so contours don't
pop → avoids strobe.

### 2.D ASCII-sampled flow (`ascii_field`)

**Budget: ≤ ~1800 `text()` draws** via a hard counter (ascii_rain proves 2500 glyphs @60fps).
**Direction encoded by glyph choice → zero per-glyph `rotate()`** (rotating each glyph is the
perf trap; cap that mode at ≤800). Non-representational by nature.

```js
const DIR=['-','\\','|','/'], cell=Math.max(10,u*0.024*P.scale);
const cols=Math.min(150,(W/cell|0)+1), rows=Math.min(90,(H/cell|0)+1);
textAlign(CENTER,CENTER); textFont('monospace'); textSize(cell*0.9); noStroke();
let budget=1800;
for (let gy=0; gy<rows&&budget>0; gy++) for (let gx=0; gx<cols&&budget>0; gx++){
  const px=(gx+0.5)*cell, py=(gy+0.5)*cell, a=ang(px,py);
  const sector=((Math.round(a/(Math.PI/4))%4)+4)%4;             // → - \ | /
  const m=Math.sin(a*2+K.t+gx*0.1)*0.5+0.5;                     // flow shimmer
  fill((P.hue)%360, 40, 26+m*64, 90); text(DIR[sector], px, py); budget--;
}
```

---

## 3. Parameter surface

Map onto the **universal seven** first; family extras after. Every range holds at both
extremes (validator pokes to max). **Order the `params` object so the first two numerics are
`density` then `energy`** (both obviously change the render at max — never put `hue` first; 360
wraps to red≈0 and trips the params gate).

| Param | Role in this family | Safe min / max |
|---|---|---|
| `density` | emitter amount (dye) · ribbon/streamline count · glyph grid fill | 0.1 / 1 |
| `energy` | brightness / glow / stroke weight / ribbon alpha | 0 / 1 |
| `speed` | field drift `zt` + advection step + churn (beats-relative) | 0.2 / 3 |
| `scale` | swirl size (potential spatial freq `sp`) | 0.3 / 3 |
| `hue` | base palette hue / streak color | 0 / 360 |
| `x`,`y` | emitter anchor / field bias | 0 / 1 |
| **`turb`** | curl angle multiplier = vortex strength (0 = laminar drift → 1.5 = chaotic) | 0 / 1.5 |
| **`diffuse`** | dissipation + bleed (dye only; higher = softer, faster-clearing) | 0 / 1 |
| **`braid`** | ribbon lateral interleave amplitude | 0 / 1 |
| **`levels`** | contour/isoline count (int) | 4 / 16 |
| **`warp`** | add a 2nd noise octave to `ψ` for finer detail (≤2 octaves) | 0 / 1 |
| `style` | renderer/palette discipline (see §4) — the anchor | — |
| `seed` | int, folded into noise coord + `hsh` (no `noiseSeed`/`random` global pollution) | 0 / 9999 |
| `act` | multi-minute program (see §5) | — |

`turb=0` must still move (laminar drift from `zt`), `turb=1.5` must not NaN or freeze —
`atan2` is bounded, so it can't. `scale` is always `clp`'d before dividing (no ÷0).

---

## 4. Palette / tone strategy

- **Dye buffer → iq cosine LUT in raw RGB bytes** (see `buildLUT` in §2.A). Write bytes
  straight into `buf.pixels` — this *bypasses* `colorMode(HSB)` cleanly (pixels[] are raw
  RGBA), which is exactly what you want for a 256-entry ramp. iq form:
  `color(t) = a + b·cos(2π·(c·t + d))` per channel. Classic constants:
  `a=b=[.5,.5,.5], c=[1,1,1]`, and `d` picks the ramp — `[0,.33,.66]`=full spectrum
  (oil-slick), `[.0,.12,.24]`=warm ember (smoke), `[.0,.20,.38]`=blue→red heat (thermal).
  **Always add a dark base tone** (`[.04,.05,.08]`) so empty cells hold luminance ≥ 0.02, and
  **clamp the top to ~0.96** so a dense flood never whites out past 0.92.
- **Vector styles (ribbons / contours / ASCII) → HSB discipline.** Derive hue from `P.hue`
  plus a small spread by streamline index or by `θ`; keep saturation *low* (10–20) for the
  ink-on-cream contour look, *high* (70–92) with `ADD` for silk/neon ribbons.
- **Duotone / near-monochrome** is the sophistication move: one hue, luminance does all the
  work. The `ink` and `topo-contour` styles must be genuinely near-mono (S ≤ 15), not a
  desaturated color.

**≥3 divergent looks, ≥1 non-representational** — proposed style set for this family:

1. **`smoke`** — soft mass-conserving curl plume, warm iq ember ramp, `image()`-upscaled
   continuum. (representational-ish: reads as smoke/dye.)
2. **`silk-ribbon`** — filled `ADD` `TRIANGLE_STRIP` bundles, duotone with bright core.
   (abstract-organic.)
3. **`topo-contour`** — evenly-spaced streamlines / marching-squares isolines, near-mono
   ink-on-cream, schematic. **(non-representational.)**
4. **`ascii-flow`** — dot-matrix directional glyphs, green-phosphor or amber mono.
   **(non-representational, Gysin.)**
   Plus cross-cutting palette swaps: **`thermal`** (false-color heat) and **`oilslick`**
   (iq full-spectrum iridescence) apply to the dye buffer without changing the algorithm.

---

## 5. Temporal strategy (30s → 5min; the engine FREEZES beat-locked-only motion at 8s)

**Continuous drift = the non-negotiable motion floor.** Every renderer here evolves on
`K.t` regardless of beats, so nothing re-phases at the 8s gate:

- **Field drift:** `zt = K.t·rate + seed`. The potential slides forever → streamlines,
  contours, and glyphs churn even with zero dye and zero beat.
- **Dye:** a **perpetual wandering emitter** (orbit `ex,ey` on `cos/sin(K.t·…)`) + `dissip<1`
  keeps a moving bright front. Advection never reaches a static steady state.
- **Ribbons / contours:** re-integrated **every frame** from wandering seeds.

**Beat layer (on top, never the sole motion):** `K.pulse` → emitter injection kick + core
brightness (partial, local — never a full-frame flash); `K.swell` → breathe turbulence.

**Minute-scale arcs:** `K.section`/`K.intensity` drift the **emitter orbit radius**,
**dissipation**, **turbulence**, and **contour `levels`** so the piece is visibly different a
minute in. Ramp overall `bri` with `K.intensity`.

**`P.act` programs (2–3 multi-minute dramaturgies):**

| act | behavior |
|---|---|
| `plume` / `flow` | steady rising/river flow, emitter drifts slowly |
| `gust` | periodic surges synced to `K.section` parity + `K.pulse` (velocity & inject spike) |
| `bloom` / `calm` | low turbulence, higher dissipation, big soft emitter — laminar and slow |
| `vortex` (opt.) | add a rotational bias `θ += atan2(y−cy, x−cx)+π/2` → the field spins about the anchor |

**Audio (blend ON TOP, never multiply core motion):** `A.bass` → emitter amount + velocity
gain; `A.lowmid` → `turb`; `A.treble` → glyph/ribbon sparkle; `A.rms` → brightness. During
validation `A.*` may be all zeros — the `K.t` floor alone must pass the motion gate.

---

## 6. Exemplars + failure modes

### Exemplar artists (cite by name — `_cards/` not yet populated)

- **Robert Bridson** — *Curl-Noise for Procedural Fluid Flow* (2007): the divergence-free
  construction this whole family rests on.
- **Jos Stam** — *Stable Fluids* (1999): the semi-Lagrangian backtrace that makes the dye
  buffer stable at any step.
- **Tyler Hobbs** — *Flow Fields* essay: the canonical generative-art treatment; evenly-spaced
  off-grid streamlines, the `topo-contour` discipline.
- **Robert Hodgin (flight404)** — *Meander* / curl-noise particle+dye rivers: the reference for
  elegant, mass-conserving flow with dye.
- **Anders Hoff (inconvergent)** — *Fractures* / hatched streamline fields: the fine
  ink-contour look.
- **Sage Jenson (mxsage)** — Physarum agent-trail fields: adjacent, for dye-trail texture.
- **Memo Akten** — optical-flow / fluid dye pieces.
- **Zach Lieberman** & **Brion Gysin** — glyph/type flow and permutation grids: the
  `ascii-flow` lineage.
- **Vera Molnár / Manfred Mohr** — plotter-schematic discipline for the contour styles.

### Failure modes (each maps to a validation gate)

| Failure | Cause | Fix |
|---|---|---|
| **Blank / near-black frame** (lum < 0.02) | dye all dissipated (dissip too low, no emitter); LUT base is pure black; buffer never `image()`d | dissip ≥ 0.972; **dark base tone in LUT** (`~0.05`); perpetual emitter; verify `image(buf,0,0,W,H)` |
| **White-out** (lum > 0.92) | emitter floods, dissip≈1, LUT tops at 1.0 | cap `emit`, keep dissip < 1, **clamp LUT top to 0.96** |
| **Static** (motion < 0.004) | field on `frameCount` (banned) or beat-only; dye reached steady state | drive `zt` from `K.t`; keep the wandering emitter; re-integrate ribbons/contours each frame |
| **Strobing** (motion > 0.35) | full-frame flash on `K.pulse`; `levels` popping; whole-dye brightness × pulse | keep pulse effects **local/partial** (emitter, cores); lerp `levels` over `K.section`; never global invert |
| **Perf drop** (< 25fps) | dye grid > 192×108; multi-octave curl on full grid; rotating > 800 glyphs; > 150 filled ribbons; any full-canvas `filter()` | grid ≤ 160×90; single-octave (`warp` adds ≤ 1 more); glyph budget counter; ribbons ≤ 40; **never `filter()`** |
| **Combing / dye vanishing into points** | used raw noise-angle field (has sinks) | use the **curl** kernel (`atan2` of ∇⊥ψ) — divergence-free, no sinks |
| **Seed non-determinism / layer bleed** | `noiseSeed()` / p5 `random()` (global) | fold seed into the noise **coordinate** + inline `hsh()`; rebuild caches on `S.seedUsed !== P.seed` |
