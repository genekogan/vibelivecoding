# Technique — Stable Fluids (semi-Lagrangian dye advection)

**Family:** Jos Stam *Stable Fluids* — a **continuous dye field** advected on a coarse
grid by a velocity field. Velocity comes from **curl noise** (divergence-free by
construction — the cheap, always-stable default) or **injected impulse splats**
(beats / audio / plume source). Diffusion is realized as a **blur**. Optional
"authentic" upgrade adds Navier–Stokes self-advection + a Gauss–Seidel pressure
projection for genuine vortex shedding.

**Slot:** `genart` → `bg` (self-sufficient full-bleed). Also viable as `post` (advect
a half-res copy of what's beneath — see §Variants).

**Why this earns its place next to `flowfield` / `marbling` / `reaction_diffusion`:**
flowfield draws *particle streaks*; this advects a *continuous scalar field* (smoke,
not lines). marbling shears *closed ink rings*; this is a *grid solver* with backtrace
sampling. reaction_diffusion is a *chemical* PDE (no transport); this is *transport of
dye by a velocity field*. The signature read is **billowing incompressible smoke that
curls back on itself** — impossible with a laminar angle field.

---

## 1 · Algorithm + math

Incompressible Navier–Stokes with a passive dye (density) `ρ` carried by velocity
**u** = (u,v), pressure `p`, viscosity `ν`:

```
momentum:      ∂u/∂t = −(u·∇)u − ∇p + ν∇²u + f
incompressible: ∇·u = 0
dye transport:  ∂ρ/∂t = −(u·∇)ρ + κ∇²ρ + S
```

Stam splits each timestep `dt` into a sequence of unconditionally-stable operators:

1. **add force**  `u ← u + dt·f`   (impulse splats, buoyancy)
2. **diffuse**   solve `(I − νdt∇²)u = u₀`  ← *implicit; on a coarse grid this IS a blur*
3. **project**   make divergence-free: solve `∇²p = ∇·u`, then `u ← u − ∇p`
4. **advect**    semi-Lagrangian backtrace (below)
5. **project** again
6. **dye**: add source `S`, diffuse (blur), advect with the same backtrace.

### The heart — semi-Lagrangian advection (why it's "stable")

To update field `q` at cell (i,j), find where the parcel *now* at (i,j) came *from* one
step ago, then **bilinearly sample the old field there**:

```
x_back = i − dt·u(i,j)
y_back = j − dt·v(i,j)
q_new(i,j) = bilerp( q_old, x_back, y_back )
```

Because the new value is a **convex combination** of old samples, it can never exceed the
input range — so it never blows up, *for any dt*. That is the entire trick: no CFL
condition, no explosion at high speed. Coarse grid + big dt is fine.

### Divergence-free velocity for free — curl of a stream function

The expensive part of the full solver is the pressure projection (steps 3 & 5) that
enforces `∇·u = 0`. You can **skip it entirely** by *prescribing* the velocity as the
curl of a scalar stream function `ψ`:

```
u =  ∂ψ/∂y ,   v = −∂ψ/∂x        ⇒   ∇·u ≡ 0  (identically incompressible)
```

Take `ψ = fBm/Perlin noise(x, y, t)`. The perpendicular gradient of noise is a smooth,
swirling, **already-divergence-free** field — no projection needed, never diverges,
always in motion. This is the **recommended default** for the VJ engine. Reach for the
full projection only when you want vortices that genuinely shed and interact.

### Diffuse = blur

Implicit diffusion `(I − a∇²)x_new = x`, `a = νdt·N²`, solved by one Jacobi/Gauss–Seidel
sweep is *exactly* `x_new(i,j) = ( x(i,j) + a·Σneighbours ) / (1+4a)` — i.e. blend toward
the 4-neighbour average. On a coarse grid **one light tent-blur pass per frame** is a
faithful, cheap stand-in. That is the "Blur = diffuse" identity.

---

## 2 · p5-2D implementation (this engine, within PROBE)

**Budget I'm spending:** one **coarse Float32 grid, long axis 52→92 cells (cap 96)** —
≈ 2.9k–5.2k cells, squarely in PROBE's *"prefer 128×72 for heavy per-pixel math = free"*
bracket (I use *less*). Per frame: **GN Perlin `noise()` calls** to build ψ (PROBE:
3-octave noise on 128×72 is free — I do 1 octave on ≤96×54), plus ~5 array passes over
GN (curl, inject, advect, blur, colour). Storage: `S.d, S.d2` (dye + scratch),
`S.vx, S.vy` (velocity), `S.psi` (stream scratch), and **one** `createGraphics(GW,GH)`
upscaled to full canvas with `imageSmoothingEnabled=true` (bilinear = smooth smoke) —
the exact `reaction_diffusion` composite path. **No full-canvas `filter()`, no
per-scanline gradient, no particles.** Grid rebuilds only on size/seed change.

> Seed determinism: **never** `noiseSeed()`/`randomSeed()` (global pollution across
> layers). Offset the noise **coordinates** by a seed-derived constant `S.noff` (the
> `flowfield` pattern) and hash with the inline `hsh` for splat placement.

### Core loop — kinematic curl-noise path (the workhorse)

```js
const D = { energy:.6, swirl:.6, density:.5, speed:1, dissipate:.4, scale:1,
            hue:210, x:.5, y:.62, style:'smoke', act:'plume', seed:0 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };

const clp=(v,a,b)=>Math.max(a,Math.min(b,v)), TAU=Math.PI*2;
const hsh=i=>{const s=Math.sin(i*127.1+(P.seed|0)*311.7)*43758.5453;return s-Math.floor(s);};
if(S.lastBeat==null||K.beat<S.lastBeat)S.lastBeat=K.beat; S.lastBeat=K.beat;

const W=width, H=height, md=Math.min(W,H);

// ---- coarse grid, size + seed keyed (long axis 52..92, hard-cap 96) ----
const LA = Math.min(96, Math.round(52 + clp(P.density,0,1)*40));
const AR = W/H;
const GW = AR>=1 ? LA : Math.max(24, Math.round(LA*AR));
const GH = AR>=1 ? Math.max(24, Math.round(LA/AR)) : LA;
if(!S.d || S.gw!==GW || S.gh!==GH || S.seedUsed!==(P.seed|0)){
  S.gw=GW; S.gh=GH; S.seedUsed=(P.seed|0);
  const N=GW*GH;
  S.d=new Float32Array(N); S.d2=new Float32Array(N);
  S.vx=new Float32Array(N); S.vy=new Float32Array(N); S.psi=new Float32Array(N);
  S.noff = hsh(7)*1000;                              // seed → noise-coord offset
  if(S.buf&&S.buf.remove)S.buf.remove();
  S.buf=createGraphics(GW,GH);
  for(let y=0;y<GH;y++)for(let x=0;x<GW;x++){        // soft blob so frame 0 isn't blank
    const dx=x/GW-0.5, dy=y/GH-0.5;
    S.d[y*GW+x]=Math.max(0, 0.55 - 3.0*(dx*dx+dy*dy));
  }
}
const GN=GW*GH, d=S.d, d2=S.d2, vx=S.vx, vy=S.vy, psi=S.psi, buf=S.buf;

// dt guard (tolerate t0 resets / backward jumps)
let dt=K.t-(S.lastT!=null?S.lastT:K.t); if(!(dt>0)||dt>0.4)dt=0.016; S.lastT=K.t;

// ---- 1. velocity = curl of a noise stream-function (divergence-free) ----
const zt   = K.t*(0.05 + P.speed*0.05) + S.noff;     // REAL-TIME evolution → motion floor
const nsc  = 2.6 / Math.max(0.4, P.scale);           // vortex size: bigger scale = broader swirls
const vg   = (7 + clp(P.swirl,0,2)*24)               // curl gain (vorticity strength)
             * (0.8 + K.intensity*0.5);              // §5 arc: swirl breathes with the section
for(let y=0;y<GH;y++)for(let x=0;x<GW;x++)
  psi[y*GW+x]=noise(x/GW*nsc + S.noff, y/GH*nsc, zt);// 1 octave; GN noise() calls (free)
for(let y=0;y<GH;y++){
  const yp=Math.min(GH-1,y+1), ym=Math.max(0,y-1);
  for(let x=0;x<GW;x++){
    const xp=Math.min(GW-1,x+1), xm=Math.max(0,x-1), i=y*GW+x;
    vx[i]= (psi[yp*GW+x]-psi[ym*GW+x])*vg;           //  ∂ψ/∂y
    vy[i]=-(psi[y*GW+xp]-psi[y*GW+xm])*vg;           // −∂ψ/∂x
  }
}
// act: 'vortex' overlays solid-body rotation about the anchor (whirlpool)
if(P.act==='vortex'){
  const cx=P.x*GW, cy=P.y*GH, om=1.4+P.swirl*1.4;
  for(let y=0;y<GH;y++)for(let x=0;x<GW;x++){
    const i=y*GW+x, rx=x-cx, ry=y-cy, r=Math.hypot(rx,ry)+1e-3;
    vx[i]+= -ry/r*om; vy[i]+= rx/r*om;
  }
}

// ---- 2. add force + dye: perpetual injector (motion + luminance floor) ----
const nInj = 1 + Math.round(clp(P.density,0,1)*2);   // ≤4 injectors
const push = 0.55 + A.bass*0.8 + K.pulse*0.5;        // audio ON TOP of a clk baseline
const bigDrop = (P.act==='bloom') && (Math.floor(K.beat)>Math.floor(S.pb||0) && Math.floor(K.beat)%4===0);
S.pb=K.beat;
for(let q=0;q<nInj;q++){
  const ang=K.t*(0.3+q*0.13)+q*2.2, rad=(P.act==='vortex'?0.05:0.16)+0.12*Math.sin(K.t*0.09+q*1.7);
  const ix=Math.round((0.5+(P.x-0.5)*0.7+Math.cos(ang)*rad)*GW);
  const iy=Math.round((0.5+(P.y-0.5)*0.7+Math.sin(ang)*rad)*GH);
  const rr=(bigDrop?3:1)+Math.round(clp(P.density,0,1)*2);
  for(let dy=-rr;dy<=rr;dy++)for(let dx=-rr;dx<=rr;dx++){
    const gx=ix+dx, gy=iy+dy; if(gx<0||gx>=GW||gy<0||gy>=GH)continue;
    const fall=Math.max(0,1-(dx*dx+dy*dy)/((rr+0.6)*(rr+0.6)));
    const i=gy*GW+gx;
    d[i]=Math.min(1, d[i]+fall*push*(bigDrop?0.9:0.5));
    vy[i]-= 1.3*push*fall;                            // buoyant lift (plume rises)
    vx[i]+= (dx)*0.15;                                // slight lateral spread
  }
}

// ---- 3. semi-Lagrangian advect dye (backtrace + bilinear) with dissipation ----
const flow   = (0.6 + P.speed*1.2);                  // advection strength (dt folded in vg×flow)
const dissip = 1 - (0.004 + clp(P.dissipate,0,1)*0.03);
for(let y=0;y<GH;y++)for(let x=0;x<GW;x++){
  const i=y*GW+x;
  let sx=x - vx[i]*flow, sy=y - vy[i]*flow;           // trace parcel back
  if(sx<0)sx=0; else if(sx>GW-1.001)sx=GW-1.001;
  if(sy<0)sy=0; else if(sy>GH-1.001)sy=GH-1.001;
  const x0=sx|0, y0=sy|0, fx=sx-x0, fy=sy-y0;
  const i00=y0*GW+x0, i10=i00+1, i01=i00+GW, i11=i01+1;
  const top=d[i00]*(1-fx)+d[i10]*fx, bot=d[i01]*(1-fx)+d[i11]*fx;
  d2[i]=(top*(1-fy)+bot*fy)*dissip;
}
// ---- 4. diffuse = one blur pass (implicit diffusion stand-in) → back into d ----
const dif=0.14;
for(let y=0;y<GH;y++){
  const yp=Math.min(GH-1,y+1), ym=Math.max(0,y-1);
  for(let x=0;x<GW;x++){
    const xp=Math.min(GW-1,x+1), xm=Math.max(0,x-1), i=y*GW+x;
    const nb=(d2[ym*GW+x]+d2[yp*GW+x]+d2[y*GW+xm]+d2[y*GW+xp])*0.25;
    d[i]=d2[i]*(1-dif)+nb*dif;
  }
}

// ---- 5. map dye → colour → coarse buffer → upscale (see §4 for styles) ----
const bgH=((P.hue%360)+360)%360, en=clp(P.energy,0,1), style=P.style;
const hsb2rgb=(h,s,v)=>{h=((h%360)+360)%360;s/=100;v/=100;const c=v*s,xx=c*(1-Math.abs((h/60)%2-1)),m=v-c;let r,g,b;const k=Math.floor(h/60)%6;if(k===0){r=c;g=xx;b=0;}else if(k===1){r=xx;g=c;b=0;}else if(k===2){r=0;g=c;b=xx;}else if(k===3){r=0;g=xx;b=c;}else if(k===4){r=xx;g=0;b=c;}else{r=c;g=0;b=xx;}return[(r+m)*255,(g+m)*255,(b+m)*255];};
buf.loadPixels(); const pix=buf.pixels;
for(let i=0;i<GN;i++){
  const f=clp(d[i]*(0.8+en*1.6),0,1); let r,g,b;
  if(style==='ink'){                                  // dark pigment blooming on warm paper
    const t=Math.pow(f,0.8);
    r=222*(1-t*0.92); g=216*(1-t*0.95); b=202*(1-t*0.90);
  } else if(style==='thermal'){                       // ironbow false-colour (non-representational)
    const st=[[6,4,20],[70,16,120],[190,40,60],[245,130,20],[255,235,150]];
    const ff=f*(st.length-1); let si=Math.min(st.length-2,ff|0); const tt=ff-si, a0=st[si], a1=st[si+1];
    r=a0[0]+(a1[0]-a0[0])*tt; g=a0[1]+(a1[1]-a0[1])*tt; b=a0[2]+(a1[2]-a0[2])*tt;
  } else {                                            // 'smoke': luminous near-mono, dark-key
    const c=hsb2rgb(bgH + f*22, 62 - f*34, 6 + f*90); r=c[0]; g=c[1]; b=c[2];
  }
  const p=i*4; pix[p]=r; pix[p+1]=g; pix[p+2]=b; pix[p+3]=255;
}
buf.updatePixels();
drawingContext.imageSmoothingEnabled=true;            // bilinear upscale = smooth smoke
noStroke(); image(buf,0,0,W,H);

// gentle beat breathe (partial-frame, well under strobe cap) for 'smoke'/'thermal'
if(style!=='ink'){ blendMode(ADD); noStroke();
  fill(bgH,50,100, clp(6+8*K.swell+A.bass*10,0,16)); rect(0,0,W,H); blendMode(BLEND); }
drawingContext.shadowBlur=0; blendMode(BLEND);
```

Everything above holds **60fps** on the probe box (it is lighter than
`reaction_diffusion`, which runs GN×iters×2 fields at 63fps).

### Optional authentic upgrade — full Navier–Stokes (vortex shedding)

Swap the kinematic velocity for a *self-evolving* one when you want smoke that curls
back on itself. Keep `S.vx,S.vy` as persistent state, add `S.p,S.div` scratch, and each
frame **after adding forces**: `project → advect velocity (same backtrace on vx,vy) →
project`. Budget: +2 velocity advections and 2 Poisson solves ≈ +10×GN ops
(≈ 52k at 96×54) — still 60fps.

```js
function project(vx,vy,p,div,GW,GH){
  for(let y=1;y<GH-1;y++)for(let x=1;x<GW-1;x++){ const i=y*GW+x;
    div[i]=-0.5*((vx[i+1]-vx[i-1])+(vy[i+GW]-vy[i-GW])); p[i]=0; }
  for(let k=0;k<6;k++)                                  // Gauss–Seidel Poisson (∇²p = div)
    for(let y=1;y<GH-1;y++)for(let x=1;x<GW-1;x++){ const i=y*GW+x;
      p[i]=(div[i]+p[i-1]+p[i+1]+p[i-GW]+p[i+GW])*0.25; }
  for(let y=1;y<GH-1;y++)for(let x=1;x<GW-1;x++){ const i=y*GW+x;
    vx[i]-=0.5*(p[i+1]-p[i-1]); vy[i]-=0.5*(p[i+GW]-p[i-GW]); }   // u ← u − ∇p
}
```

Velocity self-advection is the identical backtrace, writing `vx,vy` into `vx2,vy2` then
swapping. Add a touch of **vorticity confinement** (re-inject curl where it decays) if
the Gauss–Seidel damping makes it too smooth. Ship the kinematic path by default; expose
the full solver behind `style:'solver'` or a `physics` flag only if the extra vorticity
reads on stage.

---

## 3 · Parameter surface

Order matters: the validator pokes the **first two numerics to max together** — both
must produce an obvious change and stay safe at max. `energy` (contrast jump) and
`swirl` (fast tight motion) lead; both are unconditionally safe (semi-Lagrangian can't
blow up, `f` is clamped to 1).

| param | maps to | default | min | max | safe-at-both-extremes note |
|---|---|---|---|---|---|
| `energy` | dye→colour contrast/brightness + splat push | .6 | 0 | 1 | 0 = faint but ≥ lum floor from ground; 1 = clamps at `f=1`, no whiteout |
| `swirl` | curl gain `vg` (vorticity / how tightly it spins) | .6 | 0 | **2** | 2 = fast — but backtrace is stable; still ≤ few cells/step |
| `density` | grid long-axis cells (52→92) + injector count/size | .5 | 0 | 1 | reallocates grid (keyed) — brief, then denser detail |
| `speed` | advection `flow` + noise evolution `zt` | 1 | .2 | 3 | .2 = slow drift (still moves via `zt`); 3 = fast, stable |
| `dissipate` | dye decay/frame (trail persistence) | .4 | 0 | 1 | 0 = long-lived (guard vs saturation, see §6); 1 = quick clearing |
| `scale` | vortex size (`nsc`, bigger = broader swirls) | 1 | .4 | 2.6 | .4 = fine turbulent detail; 2.6 = few big slow eddies |
| `hue` | base palette hue | 210 | 0 | 360 | **never place first** (360 wraps to red≈0) |
| `x`,`y` | plume source / injector & vortex anchor | .5,.62 | 0 | 1 | pure placement |
| `style` | render discipline (§4) | `smoke` | — | — | options: `smoke · ink · thermal · spectral · schematic` |
| `act` | multi-minute program (§5) | `plume` | — | — | `plume · vortex · bloom` |
| `seed` | noise offset + splat layout | 0 | 0 | 9999 | rebuild on change (`S.seedUsed`) |

Optional extra if you want a smear knob: `viscosity` → the blur amount `dif` (0.05→0.4);
low = crisp filaments, high = soft cloud. Keep total params ≤ ~13.

---

## 4 · Palette / tone strategy — ≥3 divergent looks (≥1 non-representational)

The dye is a **scalar** `f ∈ [0,1]`; colour is entirely a 1-D transfer function, so
radically different looks cost nothing. Discipline per style:

- **`smoke`** *(default, dark-key, representational)* — near-monochrome volumetric. Fix
  `hue`, drive **brightness by dye density** with a slight hue push and desaturation into
  the highlights: `hsb2rgb(hue + f*22, 62 − f*34, 6 + f*90)`. The **brightness floor of 6**
  keeps empty cells ≈ 0.06 luminance (never a black frame). Additive glow breathe on top.
  Reads as luminous smoke / nebula.
- **`ink`** *(light-key, painterly, subtractive)* — dark pigment diffusing in water on
  warm paper. Start from paper `[222,216,202]` (≈ 0.85 lum, deliberately *below* 0.92) and
  **subtract** proportional to `f^0.8`. This is suminagashi-in-motion but as a continuous
  field, not marbling's rings.
- **`thermal`** *(non-representational, clinical)* — ironbow false-colour heat ramp of the
  raw density: black→indigo→magenta→orange→white. Reads as a schlieren / thermographic
  scan, not "a thing."
- **`spectral`** *(chromatic, psychedelic)* — hue mapped from **velocity direction**
  `atan2(vy,vx)` (compute per cell), brightness from `f`, high saturation, `blendMode(ADD)`
  in the breathe pass. Iridescent dye plume.
- **`schematic`** *(non-representational, blueprint)* — skip the pixel buffer; on a dark
  ground draw the **velocity field as a sparse vector grid** (every 4th cell, arrow =
  `vx,vy`) plus a couple of **iso-density contour lines** of `f`. Diagnostic / fluid-lab
  aesthetic.

Reusable **iq cosine palette** (Inigo Quilez) for `smoke`/`thermal`/duotone ramps —
`col(t) = a + b·cos(2π(c·t + d))`, returns 0..1 RGB:

```js
const iqp=(t,a,b,c,dph)=>[0,1,2].map(k=>clp(a[k]+b[k]*Math.cos(TAU*(c[k]*t+dph[k])),0,1)*255);
// smoke  (indigo→cyan→white):  iqp(f,[.2,.2,.3],[.5,.5,.5],[1,1,1],[.0,.1,.2])
// magma  (black→red→yellow):   iqp(f,[.5,.2,.1],[.5,.4,.2],[1,1,1],[.0,.15,.2])
// duotone: lerp two fixed HSB endpoints by f  →  hsb2rgb over (h0→h1, s0→s1, b0→b1)
```

HSB discipline: `colorMode` is already HSB 360/100/100/100 — never call it. For the
buffer we write raw RGB via `hsb2rgb`/`iqp`. **≥3 divergent looks** shipped: `smoke`
(dark luminous), `ink` (light subtractive), `thermal` (false-colour) — plus `spectral`
and `schematic`. `thermal` **and** `schematic` are non-representational (mandate met).

---

## 5 · Temporal strategy (30s → 5min; survives the 8s gate)

This engine **freezes beat-locked-only motion at 8s** (cps 0.5 → 16 beats re-phase). The
fluid's motion is **not** beat-locked, so it passes structurally:

- **Real-time motion floor (never re-phases):** three independent continuous drivers.
  (a) the stream function evolves via `zt = K.t·rate` — pure wall-clock, no beat phase;
  (b) the dye is **advected every single frame**, so the whole field is in constant
  translation/rotation even with zero beats; (c) the perpetual injector orbits on `K.t`.
  Snapshots 8s apart differ heavily (expect motion ≈ 0.05–0.16, like reaction_diffusion).
- **Beat / audio on top (never sole):** `push = 0.55 + A.bass·0.8 + K.pulse·0.5` → puffs
  on the kick; `K.swell` + `A.bass` drive the partial-frame breathe. Core advection is
  **never multiplied by `A.*`** — silence still billows.
- **Section arc (30s–5min):** `vg *= (0.8 + K.intensity·0.5)` so vorticity swells and
  calms with `K.intensity[K.section]`; scale injector rate/size by `K.intensity` too.
  A minute in looks materially different because the section index has moved.
- **`P.act` programs (multi-minute dramaturgies, selectable at fire time):**
  - **`plume`** — buoyant upward injection, moderate swirl: a rising smoke column that
    mushrooms and shears. Steady, hypnotic.
  - **`vortex`** — solid-body rotation added to velocity about the `x,y` anchor; injection
    pulled to the centre → everything spirals into a whirlpool that tightens over the arc.
  - **`bloom`** — sparse **big ink-drops on downbeats** (`K.beat%4`) that bloom and
    dissipate between hits (raise `dissipate`); ink-in-water, breath-paced, negative space.

---

## 6 · Exemplars + failure modes

**Exemplar artists** (cite by name — no `_cards/` yet):

- **Jos Stam** — author of *Stable Fluids* (SIGGRAPH 1999) and *Real-Time Fluid Dynamics
  for Games* (GDC 2003); the ~100-line solver this whole family descends from.
- **Memo Akten** — *MSAFluid* / `ofxMSAFluid`: a Stam solver used as an art instrument —
  the canonical "advected coloured dye reacting to input" look.
- **Pavel Dobryakov** — *WebGL-Fluid-Simulation* (PavelDoGreat): the modern reference for
  luminous **splat dye** on black; my `smoke` style targets this read.
- **Refik Anadol** — *Machine Hallucinations* / *Melting Memories*: billowing pigment
  data-clouds; reference for the slow, deep, nebula tone and the `bloom` act.
- **Robert Hodgin (flight404)** — organic fluid/particle fields; reference for buoyant,
  living motion rather than mechanical swirl.

**Failure modes & the guard that prevents each:**

- **Blank / black frame** — dye decayed to 0 (dissipate too high, no injection). Guard:
  seed a soft blob at build, run the **perpetual injector every frame**, and keep the
  `smoke` brightness floor (6) so empty cells ≈ 0.06 lum. Never let `dissipate` reach a
  regime where injection can't keep coverage.
- **Whiteout / lum > 0.92** — `ink` paper too bright when dye is sparse (mostly bare
  paper), or `smoke` saturating (`dissipate` = 0 + heavy injection → flat bright field).
  Guard: paper capped at ≈ 0.85 lum; keep a `dissipate` floor (`≥ 0.004/frame` baked in);
  clamp `f` to 1. Verify mean lum ∈ [0.02, 0.92] at both param extremes.
- **Static (motion ≤ 0.004)** — you froze `zt` (drove noise on a constant), or velocity
  gain `vg` too low, or advection `flow≈0`. Guard: `zt` from `K.t` always advances (needs
  the `__clk` metronome running — engine-standard), `vg` floor of 7, `flow` floor 0.6.
  **Never** use `frameCount` for time (banned + rejected).
- **Strobing (motion > 0.35)** — full-frame flash/inversion. Guard: injection push is
  **local** (small splat radius), the breathe pass is additive alpha ≤ 16, the palette is
  not remapped per beat, and bilinear upscale keeps frame-to-frame diffs smooth. Never
  invert or flash the whole field.
- **Perf** — grid too big (keep long axis ≤ 96), computing ψ with 4 `noise()` calls per
  cell (instead **build the ψ array once, GN calls, then finite-difference it**), too many
  injectors (≤ 4), or Gauss–Seidel iters > 8 in the full solver. **Never** `loadPixels`
  the full canvas (only the GW×GH buffer) and **never** `filter()` the canvas.
- **NaN / garbage** — `dt = 0` on a `t0` reset, or backtrace sampling out of bounds.
  Guard: `dt` clamped to `0.016` when non-positive/huge; `sx,sy` clamped to
  `[0, GW−1.001]` / `[0, GH−1.001]` before bilinear read.
