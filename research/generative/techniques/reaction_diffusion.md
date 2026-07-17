# Technique — Reaction–Diffusion (excitable media): BZ spiral waves & FitzHugh–Nagumo

Family label: `reaction_diffusion`. This file documents the **traveling-wave / excitable-media**
branch — **Belousov–Zhabotinsky** (rotating spirals + expanding target rings) and
**FitzHugh–Nagumo** (spiral defects, cardiac fibrillation). Engine: p5.js **2D**, coarse
`createGraphics` buffer + upscale. No WebGL/GLSL, no `createCanvas`, no full-canvas `filter()`.

## 0. Scope — DO NOT re-skin the Gray-Scott asset

`assets/visual/genart/genart.reaction_diffusion.json` already ships **Gray-Scott**
(styles `ink/neon/topo/thermal`, acts `flow/bloom/mitosis`). Gray-Scott makes **stationary
Turing morphology** — spots, stripes, mazes, mitotic splits — that *creeps* slowly. Read it as
the reference implementation for buffer plumbing, then build something the Gray-Scott asset
**cannot do**: a medium that is *always sweeping*.

| | Gray-Scott (shipped) | BZ / FHN (this file) |
|---|---|---|
| Morphology | spots, mazes, mitosis | **rotating spirals, target rings, defect turbulence** |
| Motion character | slow morph in place | **wavefronts propagate across the frame every frame** |
| Steady state | freezes into a pattern | **never settles — perpetual rotation** |
| Signature look | coral / fingerprint | petri-dish chemistry, cardiac optical-mapping, schlieren |

The rotating wavefront is the money shot *and* it makes the motion gate trivial (an excitable
medium is moving in every pixel neighborhood on every frame — no beat-lock needed).

## 1. Algorithm + math

An **excitable medium** has three phases per cell: *rest* → (kicked past a threshold) *excited*
→ *refractory* (can't re-fire) → rest. Couple neighbors by diffusion/averaging and a broken
wavefront curls into a **spiral**; a periodic point source emits **concentric target rings**;
crank excitability and spirals **break up into defect turbulence** (the cardiac-fibrillation look).

### 1a. BZ — Turner 3-reagent excitable CA (PRIMARY; cheapest, self-spiraling)

The classic Belousov–Zhabotinsky cellular model (A. R. Turner 2003, popularized by
Softology). Three reagent fields `a,b,c ∈ [0,1]`. Each step, take the Moore-9 average
(cell + 8 neighbors) of each reagent, then react:

```
ā, b̄, c̄  = 3×3 neighborhood mean of a, b, c
a' = ā + ā·(α·b̄ − γ·c̄)
b' = b̄ + b̄·(β·c̄ − α·ā)
c' = c̄ + c̄·(γ·ā − β·b̄)         then clamp each to [0,1]
```

α,β,γ ≈ 1. The **average is the diffusion**; the multiplicative reaction is the excitability.
From uniform random noise it self-organizes into spirals + targets in ~40–120 steps — **no
fragile initial condition needed** (this is why it's the primary engine). Visualize reagent `a`.
Higher α ⇒ thinner, faster, more turbulent waves; γ tunes wavelength/decay.

### 1b. FitzHugh–Nagumo — the named excitable PDE (2-variable, cleaner single rotors)

`u` = activator/voltage (diffuses), `v` = slow recovery/refractory (does **not** diffuse):

```
∂u/∂t = Du·∇²u + u − u³/3 − v
∂v/∂t = ε·(u + a − b·v)
```

Explicit-Euler discretization on the coarse grid (dx = 1, 4-neighbor Laplacian):

```
lap = u[x-1] + u[x+1] + u[y-1] + u[y+1] − 4·u
u' = u + dt·( Du·lap + u − u³/3 − v )      // clamp u to [-2,2] — the cubic blows up otherwise
v' = v + dt·( ε·(u + a − b·v) )
```

Constants: `Du=1, dt=0.13, a=0.7, b=0.8`, `ε ∈ [0.02, 0.11]` (small ε ⇒ slow recovery ⇒
the spiral rotates; large ε ⇒ pulses die to uniform). **CFL stability: `Du·dt/dx² ≤ 0.25`** —
`1·0.13/1 = 0.13` ✓. FHN does **not** spiral from noise; you must break a wavefront. The
textbook **cross-field seed** guarantees one rotor (tile it for more):

```
u = (x < GW/2) ? 1 : -1         // a half-plane wavefront…
v = (y / GH) − 0.5              // …crossed by a refractory gradient ⇒ the free end curls
```

FHN gives crisper single-armed rotors and the cleanest fibrillation breakup; it costs a seed
choreography and NaN-guarding. (Even more robust if you want it: **Barkley's model** — same
shape, only `u` diffuses, `du = (1/ε)·u·(1−u)·(u−(v+b)/a)` — rock-solid spirals, one array.)

**Choose:** BZ CA for hands-off spirals-from-noise and cheapest cost; FHN when you want
deliberate single rotors and a sharp cardiac look. Both drop into the same buffer harness below.

## 2. p5-2D implementation

**Budget spent (PROBE field-sim tier):** one coarse `createGraphics(GW,GH)` buffer at
**128×72 default, capped 160×90** (per-pixel buffer budget is 128×72→192×108); 3 `Float32Array`
reagents ping-ponged; **1–4 CA steps/frame**; upscaled to full canvas with `image()`. This is
the same shape as `genart.reaction_diffusion`, which validated at **63.3 fps** — comfortable.
Pixel writes go straight to `buf.pixels` as **raw RGBA (colorMode is IGNORED for pixel bytes)** —
compute RGB 0–255 directly; only `fill()/rect()` overlays use the engine HSB. **No full-canvas
`filter()`**; the only overlay is one ADD rect at alpha ≤ 14.

Core loop (BZ engine, `chemical` style default):

```js
// __SLOT__ · genart bg · BZ excitable-media spiral field (2D coarse buffer + upscale)
const D = { energy:.6, scale:1, hue:20, speed:1, density:.5, excite:.5, coupling:.5, cores:3, x:.5, y:.5, style:'chemical', act:'spiral', seed:0 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };

const clp=(v,a,b)=>Math.max(a,Math.min(b,v)), W=width, H=height, u=Math.min(W,H);
if(S.lastBeat==null||K.beat<S.lastBeat)S.lastBeat=K.beat; S.lastBeat=K.beat;   // tolerate t0 reset
const hsh=i=>{const s=Math.sin(i*127.1+(P.seed|0)*311.7)*43758.5453;return s-Math.floor(s);};

// --- coarse grid, size + seed keyed (128x72 default, cap 160x90) ---
const LS=124;
const GW=clp(Math.round(LS*W/Math.max(W,H)),40,160)|0;
const GH=clp(Math.round(LS*H/Math.max(W,H)),24,90)|0;
const N=GW*GH, key=GW+'x'+GH+'_'+(P.seed|0);
if(!S.a||S.key!==key){
  S.key=key;
  S.a=new Float32Array(N); S.b=new Float32Array(N); S.c=new Float32Array(N);
  S.a2=new Float32Array(N); S.b2=new Float32Array(N); S.c2=new Float32Array(N);
  for(let i=0;i<N;i++){ S.a[i]=hsh(i*3+1); S.b[i]=hsh(i*3+2); S.c[i]=hsh(i*3+3); }  // random => self-spirals
  if(S.buf&&S.buf.remove)S.buf.remove();
  S.buf=createGraphics(GW,GH); S.buf.pixelDensity(1);
  S.burn=26;   // one-time burn-in so the FIRST visible frame is already organizing (no TV-static strobe)
}
let a=S.a,b=S.b,c=S.c,a2=S.a2,b2=S.b2,c2=S.c2; const buf=S.buf;

// --- excitability from params + slow section drift (dramaturgy over minutes) ---
const drift=K.t*0.015 + K.section*0.5;
let excite=clp(P.excite + 0.12*Math.sin(drift*0.6), 0, 1);
if(P.act==='fibrillation') excite=clp(0.74+0.18*Math.sin(drift),0.5,1);        // spirals break up
else if(P.act==='target')  excite=clp(0.40+0.10*Math.sin(drift*0.7),0.25,0.7); // lazy pacemaker rings
const al=0.8+excite*0.9;                       // alpha: higher => thinner/faster/turbulent
const be=1.0, ga=1.0+(P.coupling-0.5)*0.4;     // gamma: wave wavelength / decay

// --- perpetual pacemaker injection: motion floor + never-uniform guard ---
const beat=K.pulse*0.7 + A.bass*0.6;           // baseline (K) carries it; audio only ADDS
const nPace = P.act==='target' ? 1 : Math.max(1, Math.round(P.cores*P.density*3)|0);
for(let q=0;q<nPace;q++){
  const ang=K.t*(0.18+q*0.07)+q*2.4, rad=0.18+0.14*Math.sin(K.t*0.05+q);
  const cx=Math.floor((0.5+(P.x-0.5)*0.5+Math.cos(ang)*rad)*GW);
  const cy=Math.floor((0.5+(P.y-0.5)*0.5+Math.sin(ang)*rad)*GH);
  const rr=1+Math.round(P.density*2), amp=0.6+beat*0.5;
  for(let dy=-rr;dy<=rr;dy++)for(let dx=-rr;dx<=rr;dx++){
    if(dx*dx+dy*dy>rr*rr)continue;
    const x=((cx+dx)%GW+GW)%GW, y=((cy+dy)%GH+GH)%GH, i=y*GW+x;
    b[i]=Math.min(1,b[i]+amp*0.4); c[i]=Math.min(1,c[i]+amp*0.2);   // excited + refractory tail => a wavefront
  }
}

// --- step the medium (BZ 3-reagent CA, Moore-9 average, toroidal wrap) ---
// MOTION FLOOR: >=1 step EVERY frame => wavefronts always propagate, never re-phases at 8s.
const steps = Math.max(1, Math.round((1 + P.speed*1.3)*(0.6+0.6*K.intensity)) + (S.burn||0));
let sa=a,sb=b,sc=c,da=a2,db=b2,dc=c2;
for(let it=0; it<steps; it++){
  for(let y=0;y<GH;y++){
    const ym=(y-1+GH)%GH, yp=(y+1)%GH, r0=ym*GW, r1=y*GW, r2=yp*GW;
    for(let x=0;x<GW;x++){
      const xm=(x-1+GW)%GW, xp=(x+1)%GW, i=r1+x;
      const av=(sa[r0+xm]+sa[r0+x]+sa[r0+xp]+sa[r1+xm]+sa[i]+sa[r1+xp]+sa[r2+xm]+sa[r2+x]+sa[r2+xp])/9;
      const bv=(sb[r0+xm]+sb[r0+x]+sb[r0+xp]+sb[r1+xm]+sb[i]+sb[r1+xp]+sb[r2+xm]+sb[r2+x]+sb[r2+xp])/9;
      const cv=(sc[r0+xm]+sc[r0+x]+sc[r0+xp]+sc[r1+xm]+sc[i]+sc[r1+xp]+sc[r2+xm]+sc[r2+x]+sc[r2+xp])/9;
      let na=av+av*(al*bv-ga*cv);            // reagent A  (visualized)
      let nb=bv+bv*(be*cv-al*av);            // reagent B
      let nc=cv+cv*(ga*av-be*bv);            // reagent C
      da[i]=na<0?0:na>1?1:na; db[i]=nb<0?0:nb>1?1:nb; dc[i]=nc<0?0:nc>1?1:nc;
    }
  }
  const ta=sa;sa=da;da=ta; const tb=sb;sb=db;db=tb; const tc=sc;sc=dc;dc=tc;   // ping-pong
}
if(sa!==S.a){ S.a.set(sa); S.b.set(sb); S.c.set(sc); }
S.burn=0;
const fld=S.a;

// --- field -> RGB straight into buffer pixels (RAW RGBA — colorMode does NOT apply here) ---
const gain=1.1+P.energy*2.4, st=P.style;
buf.loadPixels(); const px=buf.pixels;
for(let y=0;y<GH;y++)for(let x=0;x<GW;x++){
  const i=y*GW+x; let f=clp(fld[i]*gain-0.05,0,1), r,g,bl;
  if(st==='chemical'){        // ferroin BZ: dark reduced body -> orange -> cool oxidation crest
    const s=[[26,6,16],[150,52,18],[214,96,30],[176,232,255]], ff=f*3; let k=ff|0; if(k>2)k=2; const t=ff-k;
    r=s[k][0]+(s[k+1][0]-s[k][0])*t; g=s[k][1]+(s[k+1][1]-s[k][1])*t; bl=s[k][2]+(s[k+1][2]-s[k][2])*t;
  } else if(st==='cardiac'){  // optical-mapping voltage: black rest -> red plateau -> white depolarization crest
    const s=[[4,2,12],[90,8,34],[240,90,30],[255,244,200]], ff=f*3; let k=ff|0; if(k>2)k=2; const t=ff-k;
    r=s[k][0]+(s[k+1][0]-s[k][0])*t; g=s[k][1]+(s[k+1][1]-s[k][1])*t; bl=s[k][2]+(s[k+1][2]-s[k][2])*t;
  } else {                    // schlieren (abstract): wavefront EDGES as bright iso-lines on near-black
    const xm=(x-1+GW)%GW,xp=(x+1)%GW,ym=(y-1+GH)%GH,yp=(y+1)%GH;
    const gx=fld[y*GW+xp]-fld[y*GW+xm], gy=fld[yp*GW+x]-fld[ym*GW+x];
    const e=clp(Math.hypot(gx,gy)*gain*3.5,0,1), base=10+f*10;   // base>0 keeps mean-lum off the floor
    r=base+e*230; g=base+e*224; bl=base+e*242;
  }
  const j=i*4; px[j]=clp(r,0,255); px[j+1]=clp(g,0,255); px[j+2]=clp(bl,0,255); px[j+3]=255;
}
buf.updatePixels();

// --- composite: upscale to full frame; P.scale = display zoom on a centered sub-rect ---
const zoom=clp(P.scale,1,2.8), sw=GW/zoom, sh=GH/zoom;
const sx=clp((GW-sw)*(0.15+P.x*0.7),0,GW-sw), sy=clp((GH-sh)*(0.15+P.y*0.7),0,GH-sh);
noStroke(); drawingContext.imageSmoothingEnabled=true;      // soft = flowing waves
image(buf,0,0,W,H,sx,sy,sw,sh);

// --- finishing (PARTIAL-frame only — no full-frame flash, keeps motion-diff < 0.35) ---
if(st!=='schlieren'){
  blendMode(ADD);
  fill((((P.hue%360)+360)%360), st==='cardiac'?60:45, 100, clp((6+10*K.swell+A.bass*18)*0.5,0,14));
  rect(0,0,W,H);   // gentle breath/bass glow, alpha<=14 so frame-mean luminance stays stable
}
blendMode(BLEND); drawingContext.shadowBlur=0; noStroke();
```

**FHN swap** — replace the injection + step block above with this (visualize `u`, seed once at build):

```js
// at (re)build, INSTEAD of random noise — cross-field IC guarantees a rotating spiral:
for(let y=0;y<GH;y++)for(let x=0;x<GW;x++){ const i=y*GW+x; S.u[i]=(x<GW*0.5)?1:-1; S.v[i]=(y/GH)-0.5; }
// (allocate S.u,S.v,S.u2,S.v2 Float32Array(N) alongside the reagents; tile the IC in x for >1 rotor)

const Du=1.0, dt=0.13, eps=0.02+0.09*excite, aa=0.7, bb=0.8;   // small eps => slow recovery => rotation
let sU=S.u,sV=S.v,dU=S.u2,dV=S.v2;
for(let it=0; it<steps; it++){
  for(let y=0;y<GH;y++){
    const ym=(y-1+GH)%GH,yp=(y+1)%GH,r0=ym*GW,r1=y*GW,r2=yp*GW;
    for(let x=0;x<GW;x++){
      const xm=(x-1+GW)%GW,xp=(x+1)%GW,i=r1+x, uv=sU[i],vv=sV[i];
      const lap=sU[r1+xm]+sU[r1+xp]+sU[r0+x]+sU[r2+x]-4*uv;           // 4-neighbor Laplacian
      let nu=uv+dt*(Du*lap + uv - uv*uv*uv/3 - vv);
      let nv=vv+dt*(eps*(uv + aa - bb*vv));
      dU[i]=nu<-2?-2:nu>2?2:nu; dV[i]=nv;     // CLAMP u — the cubic NaNs -> black frame otherwise
    }
  }
  const tu=sU;sU=dU;dU=tu; const tv=sV;sV=dV;dV=tv;
}
if(sU!==S.u){ S.u.set(sU); S.v.set(sV); }
// then map for coloring:  f = clp((S.u[i]+2)/4, 0, 1)
```

## 3. Parameter surface

Universal seven mapped where natural + excitable-media extras. **First two numerics = `energy`,
`scale`** (both change the render obviously at max ⇒ params gate passes; `scale` zoom is a
guaranteed visible delta, mirroring the shipped RD asset's proven order). Every range is safe at
**both** extremes (the validator pokes to max).

| param | maps to | default | min | max | both-extremes safe? |
|---|---|---|---|---|---|
| `energy` | contrast/gain + glow amplitude | .6 | 0 | 1 | 0 = low-contrast smoky; 1 = crisp crest, capped at gain 3.5 (no whiteout) |
| `scale` | **display zoom** (crop sub-rect) | 1 | 1 | 2.8 | 2.8 ≈ 3× magnify — obvious change for gate #2 |
| `hue` | palette tint/anchor + glow | 20 | 0 | 360 | warm-anchored ramp in chemical/cardiac; **fully drives** schlieren/iridescent |
| `speed` | sim steps/frame + wave rate | 1 | .2 | 4 | .2 still ≥1 step (floor); 4 = fast turbulent advance |
| `density` | pacemaker count + inject radius | .5 | 0 | 1 | 0 = single lazy source; 1 = many wave sources |
| `excite` | **excitability** (BZ α / FHN ε) | .5 | 0 | 1 | 0 ⇒ α=0.8 still excitable (fat lazy waves); 1 ⇒ fibrillation, clamped bounded |
| `coupling` | **wavelength** (BZ γ / FHN Du:ε) | .5 | 0 | 1 | γ∈[0.8,1.2] — tight vs broad spirals, both alive |
| `cores` | spiral/pacemaker seed count (int) | 3 | 1 | 8 | with `density` sets source count; tiny stamps, ≤~24 total |
| `x`,`y` | seed bias + zoom pan | .5 | 0 | 1 | — |
| `style` | color look (§4) | `chemical` | — | — | `chemical` / `cardiac` / `schlieren` (+`iridescent`/`riso`) |
| `act` | multi-minute program (§5) | `spiral` | — | — | `spiral` / `target` / `fibrillation` |
| `seed` | init RNG (rebuild on change) | 0 | 0 | 9999 | — |

Two levers own the whole gamut: **`excite`** (lazy fat target waves ↔ shredding fibrillation)
and **`coupling`** (tight fine spirals ↔ broad slow scrolls).

## 4. Palette / tone strategy

Pixel bytes are **raw RGBA — `colorMode(HSB)` does not touch `buf.pixels`** — so write RGB 0–255
directly (multi-stop lerp or the iq cosine palette). Reserve HSB for the `fill()/rect()` ADD
overlay only. Ship **≥3 divergent looks**, **≥1 non-representational**:

1. **`chemical`** (default, representational) — the ferroin BZ petri dish: dark reduced maroon body
   → orange mid → **cool cyan-white oxidation crest**. Warm mass, cool moving wavefronts. This is
   the family's signature and reads instantly as "chemistry."
2. **`cardiac`** (evocative/clinical) — optical-mapping voltage false-color: black rest → red
   plateau → **white depolarization crest** with a dark refractory wake. Sharp, medical, ominous —
   pairs naturally with `act:'fibrillation'`. (Distinct from the shipped `thermal` ironbow: this
   is a crest+wake voltage ramp, not a smooth heat gradient.)
3. **`schlieren`** (NON-representational, abstract) — color only the **gradient magnitude**
   (wavefront edges) as thin bright iso-lines on near-black, like phase-contrast microscopy /
   schlieren photography. Austere, monochrome, graphic. Tint the lines by `P.hue` (fully
   hue-driven) so it spans ice-blue → sodium-amber → sacred violet.

Bonus options for range: **`iridescent`** — oil-slick, fully hue-driven via iq cosine palette;
**`riso`** — quantize `f` to 3 bands, two mis-registered inks (fluoro pink + teal) + halftone.

iq cosine palette (returns RGB 0–255; `t = f` or `f + K.t*0.05` for drift):

```js
// color = a + b·cos(2π(c·t + d)) — Inigo Quilez. Tune a,b,c,d for the ramp; hp = P.hue/360 rotates it.
const cosPal=(t,hp)=>{ const A=[.5,.5,.5],B=[.5,.5,.5],C=[1,1,1],Dp=[hp,hp+.33,hp+.67];
  return [0,1,2].map(k=>clp((A[k]+B[k]*Math.cos(6.28318*(C[k]*t+Dp[k])))*255,0,255)); };
// iridescent: const [r,g,bl]=cosPal(f + K.t*0.05, P.hue/360);
```

Discipline: keep a **dark refractory ground** in every representational look so frame-mean
luminance sits mid-band ([0.02, 0.92]); let hue extremes reach desaturated/near-mono/dark-key,
not only brights (schlieren carries the austere end).

## 5. Temporal strategy

**The integrator IS the motion floor.** `steps = max(1, …)` runs **every frame regardless of
beat**, so wavefronts propagate continuously and the pattern **never re-phases** — this is the
one field family where beat-lock freezing at 8s is a non-issue by construction. Everything below
is layered *on top* of that always-on rotation; audio only ADDS, never gates.

- **Real-time `K.t` floor:** pacemakers orbit slowly (`ang = K.t*…`), excitability breathes
  (`0.12·sin(K.t·0.015)`), spirals rotate. Continuous drift, zero beat dependence.
- **`K.section` / `K.intensity` arcs (30 s–5 min):** `steps` scales with `K.intensity`
  (`0.6+0.6·K.intensity`) so the medium quickens through hot sections; `excite` drifts on
  `K.section` so the regime wanders — a few lazy rotors early, dense turbulent sheet at peak.
- **`K.pulse` / `A.bass`:** inject a fresh excitation blob on the beat (spawns a new target ring /
  breaks a new spiral). Baseline carries motion in silence; audio sharpens crests.
- **`P.act` — three multi-minute programs (genuinely different dramaturgies):**
  - **`spiral`** — moderate excitability, a few stable counter-rotating rotors slowly precessing.
  - **`target`** — one central pacemaker fires periodically ⇒ concentric expanding rings; hypnotic,
    calm, radially symmetric.
  - **`fibrillation`** — excitability pinned high ⇒ spirals continuously **break up into defect
    turbulence** (cardiac fibrillation); violent, dense, ever-churning. The peak-energy setting.

## 6. Exemplars + failure modes

**Exemplars** (no `_cards/` yet — cited by name): **Boris Belousov & Anatol Zhabotinsky** (the
oscillating reaction, 1950s–60s); **Richard FitzHugh & Jinichi Nagumo** (excitable-membrane model,
1961–62) and **Dwight Barkley** (fast spiral-wave model); **Alan Turing** (morphogenesis, 1952 —
family root); **Karl Sims** (pioneering "Reaction-Diffusion" evolved sims, 1990s); **Jonathan
McCabe** ("Origins of Form" / multi-scale Turing — the canonical RD-family fine-art palette
discipline); **Andrew Adamatzky** (BZ / reaction-diffusion "computers" — excitable-media imagery &
lineage); **Sage Jenson (mxsage)** (RD-family emergent fields, contemporary VJ motion aesthetic);
**Casey Reas** ("Process" / "Software Structures" — emergent-field composition); **Jason Rampe /
Softology "Visions of Chaos"** (practical BZ + multi-scale implementations to study).

**Failure modes** (each mapped to the gate it trips):

| symptom | gate | cause | fix |
|---|---|---|---|
| blank / near-black | luminance < 0.02, motion ≈ 0 | field decayed to uniform (excite too low, no injection, all reagents equalized) | perpetual pacemaker floor; keep `al ≥ 0.8`; `base>0` luminance floor in schlieren; never let the medium flat-line |
| whiteout | luminance > 0.92 | gain too high / crest fills frame | cap `gain ≤ ~3.5`; keep crest a thin fraction; dark refractory ground under it |
| **static** | motion < 0.004 | steps floored to 0, a settled fixed point, or beat-only motion re-phasing at 8s | `steps = max(1,…)` EVERY frame — the integrator is the floor; slow `excite` drift; never gate steps on beat alone |
| **strobing** | motion > 0.35 | whole-frame wave inversion per frame, or a full-canvas beat flash | keep wavefronts LOCAL (spirals/rings, not full-frame pulses); ADD glow alpha ≤ 14; no post flash; the burn-in seed avoids t≈0 TV-static |
| NaN → black (FHN) | luminance / deploy | explicit-Euler cubic blow-up (dt too large, CFL violated) | clamp `u ∈ [-2,2]` each step; keep `Du·dt/dx² ≤ 0.25`; on NaN, reseed |
| fps < 25 | fps | grid too large / too many steps | 128×72 default, ≤ 160×90, `steps ≤ 4`, one reagent visualized, Moore-9 unrolled (no inner-loop alloc) |
| aliased / janky spirals | quality | wavelength < ~6 cells on the coarse grid | raise `coupling` (fatter waves) or lower `excite`; don't chase detail past 160×90 |

**Ship checklist:** P-block verbatim · `__SLOT__` only token · all rhythm from `K` (no
`frameCount`) · `A` blended on top of the clk baseline · state under `S` only, size+seed-keyed
buffer · raw-RGBA pixel writes, HSB only for overlays · `blendMode(BLEND)` + `shadowBlur=0`
restored at end · ≥3 styles (`chemical`/`cardiac`/`schlieren`) with schlieren non-representational ·
3 acts (`spiral`/`target`/`fibrillation`) · tags: reaction-diffusion, belousov-zhabotinsky, bz,
excitable-media, fitzhugh-nagumo, spiral-wave, target-wave, fibrillation, cardiac, chemical,
morphogenesis, wavefront, generative, abstract, background.
