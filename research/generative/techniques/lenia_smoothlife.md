# Technique — Continuous Cellular Automata (SmoothLife / Lenia)

Family: **field / continuum sim** (COVERAGE.md §A, target `lenia`). A coarse float
grid `A(x) ∈ [0,1]` is convolved with a radial **ring kernel** to get a neighborhood
potential, run through a **smooth growth map**, and integrated in time with a small
`dt`. Gliders and self-propelled organisms (Lenia's *orbium*) emerge from noise.
It is the continuous-space, continuous-state, continuous-time generalization of
Conway's Life — so it belongs next to `genart.cellular` (discrete Life) and
`genart.reaction_diffusion` (Gray-Scott) but must look and behave **hard-different**
from both: no square cells, no ink-blot Turing spots — smooth luminous protoplasm
that *swims*.

Namesakes: **Bert Chan** (Lenia, 2019 — the orbium and the whole creature taxonomy),
**Stephan Rafler** (SmoothLife, 2011). Aesthetic kin: **Jonathan McCabe**
(multi-scale Turing fields), **Sage Jenson / mxsage** (luminous membrane sims),
**Alexander Mordvintsev** (growing neural CA), **Karl Sims** (a-life / RD).

---

## 1 · Algorithm + math

Both variants are the same three steps — *convolve → smooth-threshold → integrate*.
The engine cost is entirely in the convolution; everything else is O(cells).

### Lenia (primary — use this)

- State field `A(x,t) ∈ [0,1]` on an `GW×GH` grid, **toroidal** (wrap edges).
- **Kernel** `K(r)`: radially symmetric, radius `R` cells, normalized so `Σ K = 1`.
  Canonical "exponential bump" core, peaks at `r=0.5`, → 0 at `r=0` and `r=1`:

  ```
  Kc(r) = exp( α − α / (4·r·(1−r)) ),   α = 4,   r = dist/R ∈ (0,1)
  ```

  (Multi-ring kernels weight concentric shells by `β=[b0,b1,…]`; orbium uses `β=[1]`,
  a single bump — that is all you need. A Gaussian ring `Kc(r)=exp(−((r−.5)²)/(2w²))`
  is an easier-to-threshold drop-in.)
- **Potential** (the convolution): `U(x) = Σ_r K(r)·A(x+r)`  → `U ∈ [0,1]`.
- **Growth map** `G(u)`: a bell centered at `μ`, width `σ`, range `[−1,1]`:

  ```
  G(u) = 2·exp( −(u−μ)² / (2σ²) ) − 1
  ```

- **Integrate**: `A(x,t+dt) = clip( A(x,t) + dt·G(U(x)), 0, 1 )`.

**Orbium** (the classic glider, tune around these): `R≈13, μ=0.15, σ=0.015, dt=0.1`,
single-bump kernel. Lower `μ` → the field wants to fill (blobs merge, risk of
saturation); higher `μ` → starves (risk of death). Wider `σ` → chaotic turbulence;
narrow `σ` → crisp, fragile creatures.

### SmoothLife (the "block" flavor — cheaper at large R, honor the namesake)

Only **two** local averages per cell: `m` = mean of `A` over the **inner disk**
(`r<ri`, "self"), `n` = mean over the **outer annulus** (`ri<r<ra`, "neighbors"),
with `ri = ra/3`. Smooth sigmoid transition instead of a bell:

```
σ(x,a,e)   = 1 / (1 + exp(−(x−a)·4/e))          // logistic gate
σm(x,y;m)  = x + (y−x)·σ(m,0.5,em)              // pick birth vs survive interval by m
σn(n,a,b)  = σ(n,a,en)·(1 − σ(n,b,en))          // "alive" band a<n<b
s(n,m)     = σn( n, σm(b1,d1;m), σm(b2,d2;m) )
A' = clip( A + dt·(2·s(n,m) − 1), 0, 1 )
```

Classic params: `ra=12–21, b1=.278, b2=.365, d1=.267, d2=.445, en=.028, em=.147,
dt≈.1–.3`. The win: two disk-averages can be read in **O(1) per pixel** from an
**integral image** (summed-area table) built once per frame in O(N²) — so radius is
*free*, letting you run a 160×90 grid. The look is chunkier/organic-square (SmoothLife's
signature). Ship this as the `mode:'smooth'` path if you want a big-grid variant;
otherwise the sparse-kernel Lenia below is the default because it produces true orbium.

---

## 2 · p5-2D implementation (this engine, within PROBE)

Structure copies `genart.reaction_diffusion` verbatim in shape: coarse `Float32Array`
grid cached in `S` keyed on size+seed; **kernel taps precomputed once**; one sim step
per frame; render into a tiny `createGraphics(GW,GH)` via `loadPixels`; `image()`-upscale
to full canvas (with `P.scale` zoom). No WebGL, no `filter()`, no full-canvas per-pixel.

**Budget being spent (name it):** the convolution is `ntap × GW × GH` multiply-adds/frame.
Default `GW=84, GH≈47` (≈3950 cells, capped) and `R=9` → thresholded bump has **≈175
taps** → **≈0.69M MAC/frame**, one step. Keep `ntap × GW × GH ≤ ~0.8M` for stage-safe
headroom in an 11-layer stack; drop `R` or grid if you exceed. `R≥12` (≈420 taps →
1.7M) is a **solo/feature** setting, still 60fps on this box (PROBE: 3-layer heavy held
60 with headroom) but the heaviest layer in a stack. Grid ≤ 96 wide, **never** run the
kernel on the full canvas — coarse buffer + upscale (PROBE §A: 256² is the ceiling,
128×72–192×108 preferred for heavy per-pixel; we sit comfortably under it).

```js
const D = { energy:.6, scale:1, hue:158, speed:1, density:.5, x:.5, y:.5,
            mu:.15, sigma:.017, R:9, style:'protoplasm', act:'drift', seed:0 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };

const clp=(v,a,b)=>Math.max(a,Math.min(b,v)), TAU=Math.PI*2;
const fr=i=>{const s=Math.sin(i*127.1+(P.seed|0)*311.7)*43758.5453;return s-Math.floor(s);};
if(S.lastBeat==null||K.beat<S.lastBeat)S.lastBeat=K.beat; S.lastBeat=K.beat;   // t0/beat-reset guard

const W=width,H=height,u=Math.min(W,H);
const en=clp(P.energy,0,1), dens=clp(P.density,0,1);

// ---- coarse grid geometry (cap ~4000 cells) ----
const GW=84, GH=clp(Math.round(GW*H/W),24,72), N=GW*GH;

// ---- sparse ring kernel, precomputed ONCE (radius+seed keyed) ----
const Rg=clp(Math.round(P.R),5,14);
const kkey=Rg+'|k';
if(!S.tw || S.kkey!==kkey){
  S.kkey=kkey; const dxs=[],dys=[],ws=[]; let wsum=0;
  for(let dy=-Rg;dy<=Rg;dy++)for(let dx=-Rg;dx<=Rg;dx++){
    const r=Math.hypot(dx,dy)/Rg; if(r<1e-3||r>=1)continue;
    const w=Math.exp(4 - 4/(4*r*(1-r)));           // Lenia bump core (peak r=0.5)
    if(w<0.04)continue;                             // THRESHOLD → sparse tap list
    dxs.push(dx); dys.push(dy); ws.push(w); wsum+=w;
  }
  S.tdx=Int16Array.from(dxs); S.tdy=Int16Array.from(dys);
  S.tw=Float32Array.from(ws.map(w=>w/wsum));        // normalize → U∈[0,1]
  S.ntap=ws.length;
}
const tdx=S.tdx, tdy=S.tdy, tw=S.tw, ntap=S.ntap;

// ---- field buffers, size+seed keyed init (seed a few soft organisms) ----
if(!S.a || S.gw!==GW || S.gh!==GH || S.seedUsed!==(P.seed|0)){
  S.gw=GW; S.gh=GH; S.seedUsed=(P.seed|0); S.mass=0.1;
  S.a=new Float32Array(N); S.a2=new Float32Array(N);
  const nb=3+Math.round(fr(1)*4);
  for(let b=0;b<nb;b++){
    const cx=(fr(b*3+2)*GW)|0, cy=(fr(b*3+3)*GH)|0, rr=Math.round(Rg*(0.7+fr(b*3+4)*0.6));
    for(let dy=-rr;dy<=rr;dy++)for(let dx=-rr;dx<=rr;dx++){
      const d=Math.hypot(dx,dy)/rr; if(d>=1)continue;
      const idx=(((cy+dy)%GH+GH)%GH)*GW+(((cx+dx)%GW+GW)%GW);
      S.a[idx]=clp(S.a[idx]+(1-d)*(0.55+fr(b*7+dx)*0.4),0,1);
    }
  }
  if(!S.buf||S.bkw!==GW||S.bkh!==GH){ if(S.buf&&S.buf.remove)S.buf.remove(); S.buf=createGraphics(GW,GH); S.bkw=GW; S.bkh=GH; }
}
const a=S.a, a2=S.a2, buf=S.buf;

// ---- Lenia params + section/act drift (dramaturgy: species morph over minutes) ----
let mu=clp(P.mu,0.05,0.40), sig=clp(P.sigma,0.008,0.09);
const drift=K.t*0.015 + K.section*0.4;
if(P.act==='bloom')      mu += 0.020*Math.sin(drift*0.7);
else if(P.act==='swarm'){mu += 0.030*Math.sin(drift); sig*=1+0.15*Math.sin(drift*0.6);}
else                     mu += 0.012*Math.sin(drift*0.5);   // drift
mu=clp(mu,0.05,0.40); sig=clp(sig,0.008,0.09);
const dt=clp(P.speed,0.25,3)*0.11;                          // speed = integration rate
const inv2s2=1/(2*sig*sig);
const over=Math.max(0,(S.mass-0.72))*0.06;                  // homeostasis: bleed off overpopulation

// ---- ONE Lenia step: ring convolution → growth bell → integrate (toroidal) ----
let mass=0;
for(let y=0;y<GH;y++){ const row=y*GW;
  for(let x=0;x<GW;x++){
    let s=0;
    for(let k=0;k<ntap;k++){
      let nx=x+tdx[k]; if(nx<0)nx+=GW; else if(nx>=GW)nx-=GW;   // single-add wrap (|tap|<GW)
      let ny=y+tdy[k]; if(ny<0)ny+=GH; else if(ny>=GH)ny-=GH;
      s+=a[ny*GW+nx]*tw[k];
    }
    const g=2*Math.exp(-(s-mu)*(s-mu)*inv2s2)-1;
    let v=a[row+x]+dt*g-over; v=v<0?0:v>1?1:v;
    a2[row+x]=v; mass+=v;
  }
}
S.a.set(a2); S.mass=mass/N;

// ---- perpetual injection so the ecosystem never dies (motion + luminance floor) ----
const spawn=(cx,cy,rr,amp)=>{ for(let dy=-rr;dy<=rr;dy++)for(let dx=-rr;dx<=rr;dx++){
  const d=Math.hypot(dx,dy)/rr; if(d>=1)continue;
  const idx=(((cy+dy)%GH+GH)%GH)*GW+(((cx+dx)%GW+GW)%GW);
  S.a[idx]=clp(S.a[idx]+(1-d)*amp,0,1); }; };
if(S.sec!==K.section){ S.sec=K.section;               // drop a fresh organism each section
  spawn((fr(K.section*2.3+9)*GW)|0,(fr(K.section*2.3+10)*GH)|0, Math.round(Rg*0.9), 0.8+A.bass*0.3); }
if(P.act==='bloom' && K.pulse>0.6)                     // beat-pulsed spawns (population grows)
  spawn((P.x*GW)|0,(P.y*GH)|0, Math.round(Rg*0.7), 0.35+0.4*K.intensity);
if(S.mass<0.02) for(let q=0;q<3;q++)                   // dwindle rescue — never blank
  spawn((fr(K.t*5+q)*GW)|0,(fr(K.t*7+q)*GH)|0, Math.round(Rg*(0.8+0.4*fr(q))), 0.9);

// ---- render field → color into the coarse buffer (RGB 0-255; HSB does NOT apply here) ----
const fld=S.a, bgH=((P.hue%360)+360)%360, glow=0.4+en*1.6;
buf.loadPixels(); const px=buf.pixels;
// iq cosine palette: col = pa + pb*cos(2π(pc*t+pd))  → RGB 0..1
const iq=(t,pa,pb,pc,pd)=>[pa[0]+pb[0]*Math.cos(TAU*(pc[0]*t+pd[0])),
  pa[1]+pb[1]*Math.cos(TAU*(pc[1]*t+pd[1])), pa[2]+pb[2]*Math.cos(TAU*(pc[2]*t+pd[2]))];
for(let y=0;y<GH;y++)for(let x=0;x<GW;x++){
  const i=y*GW+x, f=fld[i];
  // membrane emphasis: local gradient makes cell rims glow (the "swimming" read)
  let xm=x-1;if(xm<0)xm+=GW; let xp=x+1;if(xp>=GW)xp-=GW;
  let ym=y-1;if(ym<0)ym+=GH; let yp=y+1;if(yp>=GH)yp-=GH;
  const grad=Math.min(1,(Math.abs(fld[y*GW+xp]-fld[y*GW+xm])+Math.abs(fld[yp*GW+x]-fld[ym*GW+x]))*3);
  // protoplasm: deep substrate → luminous membrane (near-mono, lum-safe: peak ≈ .82 not white)
  const t=clp(f*glow,0,1), c=iq(bgH/360 + t*0.18,[.10,.14,.18],[.32,.40,.46],[1,1,1],[.0,.10,.20]);
  const rim=grad*0.5*(0.6+en);
  const idx=i*4;
  px[idx]  =clp((c[0]+rim)*255,4,235);   // lum floors/caps keep frame-mean in [.02,.92]
  px[idx+1]=clp((c[1]+rim*0.9)*255,5,235);
  px[idx+2]=clp((c[2]+rim*1.1)*255,8,240);
  px[idx+3]=255;
}
buf.updatePixels();

// ---- composite with P.scale display-zoom (crop centered sub-rect, fill frame) ----
const zoom=clp(P.scale,1,2.6), sw=GW/zoom, sh=GH/zoom;
const sx=clp((GW-sw)*(0.15+P.x*0.7),0,GW-sw), sy=clp((GH-sh)*(0.15+P.y*0.7),0,GH-sh);
noStroke(); image(buf,0,0,W,H,sx,sy,sw,sh);

// ---- audio/beat glow ON TOP of the clk baseline (never multiplies the sim) ----
blendMode(ADD); noStroke();
fill(bgH,55,100, clp((6+18*K.swell+A.bass*26)*en,0,26)); rect(0,0,W,H);
blendMode(BLEND); drawingContext.shadowBlur=0;
```

Why this is inside the gates: the sim **steps every frame** (continuous drift, not
beat-locked → it does **not** re-phase at 8s, so the 320px motion gate is passed
structurally, not by luck); smooth `dt` integration keeps frame-to-frame change gentle
(anti-strobe, well under 0.35); the substrate floor + membrane cap + homeostasis + reseed
pin luminance inside `[0.02,0.92]` at every parameter extreme.

---

## 3 · Parameter surface

Order the JSON `params` so the **first two numerics are `energy` then `scale`** — both
change the render obviously at max (glow blow-out; deep zoom), passing the poke gate.
`mu`/`sigma`/`R` change the *species* but a lone poke can look subtle — never first.

| param | maps to | default | min | max | safe at both extremes because… |
|---|---|---|---|---|---|
| `energy` | membrane glow gain + rim contrast + ADD overlay | .6 | 0 | 1 | at 0 the substrate + field still render (lum floor); at 1 the rim/overlay are capped (`clp…235`, ADD α≤26) → no white-out |
| `scale` | display zoom into the field | 1 | 1 | 2.6 | crop is clamped to the buffer; upscale is `image()` — no cost, no OOB |
| `speed` | `dt` integration rate | 1 | .25 | 3 | `dt≤0.33`; small enough that no single step can flip a cell fully → no strobe |
| `density` | seed-blob & injection count/size | .5 | 0 | 1 | 0 still gets section + rescue spawns; 1 is bounded by grid + homeostasis |
| `hue` | base palette hue | 158 | 0 | 360 | pure recolor; wraps cleanly (never first param — 360→red≈0) |
| `x`,`y` | injection focus + zoom pan | .5 | 0 | 1 | fractions, clamped |
| `mu` | growth center (species/"filling") | .15 | .05 | .40 | low = fills → homeostasis bleeds mass off; high = starves → reseed catches it |
| `sigma` | growth width (crisp↔turbulent) | .017 | .008 | .09 | narrow creatures survive via reseed; wide turbulence stays bounded by clamp |
| `R` | kernel radius, cells (organism size) | 9 | 5 | 14 | tap list rebuilt on change; ≤14 keeps `ntap·N` budget honest |
| `style` | render discipline (see §4) | protoplasm | — | — | enum |
| `act` | multi-min program | drift | — | — | drift / bloom / swarm |
| `seed` | init layout + organism placement | 0 | 0 | 9999 | int; rebuild grid + kernel on change (`S.seedUsed`, `S.kkey`) |

---

## 4 · Palette / tone — ≥3 divergent looks (≥1 non-representational)

Direct `buf.pixels` writes are **raw RGB 0–255** — `colorMode(HSB)` does *not* apply to
pixel arrays (only to `fill()`/`stroke()`), so compute RGB in the buffer loop (iq cosine
or a manual HSB→RGB helper) and reserve HSB `fill()` for the ADD glow overlay. iq cosine
palette: `col = a + b·cos(2π(c·t + d))`, `t = field·energy`. Swap `(a,b,c,d)` per style.

1. **`protoplasm`** *(default, anchor — commit hard, non-cartoon)*. Near-monochrome
   deep-teal substrate → cyan luminous membrane, rim-lit by the local gradient so
   organisms read as glowing cell walls swimming in dark fluid. `a=[.10,.14,.18]
   b=[.32,.40,.46] c=[1,1,1] d=[.0,.10,.20]`. Dark-key, sacred/clinical, bioluminescent.
2. **`thermal`** *(false-color heat, chromatic)*. Ironbow ramp over the field value:
   stops `[6,4,20]→[70,16,120]→[190,40,60]→[245,130,20]→[255,235,140]`, lerp by `f`.
   Reads like a microbiology thermal scan. Warm, high-chroma — the divergent-hot look.
3. **`stain`** *(histology microscopy — representational-adjacent)*. H&E stain: pale
   warm substrate (`~[.86,.80,.82]`), magenta-violet nuclei where `f` is high, cyan
   cytoplasm in the mid-band. Duotone discipline, light-key — the antithesis of #1.
4. **`iso`** *(schematic contour — NON-REPRESENTATIONAL, satisfies the mandate)*.
   Quantize the field into `5+density·7` bands; darken the band edges
   (`|f·bands − round(f·bands)|<0.1`) into iso-lines over a cool false-color ramp — a
   topographic/scientific readout of the potential, abstracted away from "creatures."
   Or push it to marching-squares outlines (see `genart.metaballs`) for pure line-art.
5. **`ink`** *(sumi bleed)*. Warm paper substrate, organisms as dark ink pools
   (`tone=1−f^.75`), gradient adds a faint warm bleed halo — dry, melancholy, tonal.

Every option changes **how form is built** (mass vs. contour vs. stain vs. line), not
just hue. Let `hue` extremes reach desaturated/near-mono; keep peak lum ≤ 0.85 so no
saturated frame whites out.

---

## 5 · Temporal strategy (30s → 5min, never re-phases)

- **Real-time motion floor** — the simulation integrates **every frame** with `dt·speed`.
  This is the continuous drift the engine demands: organisms glide and morph on wall-clock
  time, *not* on `frameCount` or beat count, so it **never re-phases at 8s** (unlike
  beat-locked motion, which PROBE warns freezes on the gate). A single stable orbium still
  *translates* — motion is structural. Belt-and-suspenders: a slow `K.t` hue/palette drift
  (`bgH/360 + …`) and per-section injection guarantee pixel change even if the field settles.
- **`K.section` / `K.intensity` arcs** — `mu` (and `sigma` in swarm) drift by
  `K.section*0.4`, so the **species changes every 8 bars**: spots → gliders → turbulence
  → back. Each section drops a fresh organism; injection amplitude and glow ride
  `K.intensity`. A minute in genuinely looks like a different ecosystem.
- **`K.pulse` / `K.swell` / `A`** on top of the baseline — `bloom` spawns organisms on
  `K.pulse>0.6`; the ADD overlay breathes on `K.swell` and flares on `A.bass`; sparkle can
  ride `A.treble`. **Never** multiply the sim by `A.*` (silence during validation must not
  stop it).
- **`P.act` programs (ship all three):** `drift` = calm ecosystem, gentle `mu` wander,
  section spawns only; `bloom` = population **grows** over minutes via beat-pulsed spawns
  at `x,y`; `swarm` = wide `mu`+`sigma` oscillation → chaotic turbulent regime, dense and
  restless. One asset, three multi-minute dramaturgies selectable at fire time.

---

## 6 · Exemplars + failure modes

**Artists to key the look against:** **Bert Chan** (Lenia — study orbium's smooth
translating glider and the creature zoo; the *default* should feel alive like his sims),
**Stephan Rafler** (SmoothLife — the chunkier organic-block flavor for the `smooth` mode),
**Jonathan McCabe** (multi-scale Turing fields — palette/texture north star for
`protoplasm`/`stain`), **Sage Jenson / mxsage** (dark luminous membrane rendering),
**Alexander Mordvintsev** (growing neural CA — morphogenesis framing), **Karl Sims**
(a-life / RD lineage). `_cards/` is empty at authoring time — cite by name in `desc`/tags.

| failure | symptom | cause | fix (already in the core loop) |
|---|---|---|---|
| **blank / blackout** | mean lum < 0.02, motion 0 | organisms died (`mu` high / `dt` big / no reseed), or `A=0`→pure black | substrate floor in palette (never map to pure black); `S.mass<0.02` triple-reseed; per-section spawn |
| **static at 8s** | motion diff < 0.004 | field froze into a stationary attractor, or beat-locked stepping re-phased | step **every frame** (not on beat); keep `mu` in the gliding regime; `K.t` palette drift; section injection |
| **white-out** | mean lum > 0.92 | low `μ`/high `dt` saturates field to 1 | homeostasis `over` bleeds mass when `S.mass>0.72`; membrane RGB capped `≤235–240`; ADD α≤26 |
| **strobing** | motion diff > 0.35 | `dt` too large (cells flip in one step) or full-field regime flip / injection flash | `dt≤0.33`; injections local + ramped `(1−d)`; no full-frame inversion |
| **perf drop** | fps < 25 in stack | `ntap·GW·GH` too high (`R≥12` on a wide grid, or per-pixel on full canvas) | keep `ntap·N ≤ ~0.8M`, `GW≤96`, threshold taps, ONE step/frame, render in `GW×GH` buffer + upscale |
| **dead grey mush** | alive but ugly, no organisms | `σ` too wide + `μ` mid → featureless boil | narrow `σ` toward 0.015; nudge `μ` to 0.15; smaller `R` sharpens creatures |

**Authoring checklist:** P-block byte-for-byte · kernel + grid cached in `S` keyed on
`R`/size/seed · rebuild on `seed` change (`S.seedUsed`, `S.kkey`) · sim steps every frame ·
`energy,scale` are the first two numeric params · buffer writes are RGB not HSB · restore
`blendMode(BLEND)` + `shadowBlur=0` at the end · tag generously (lenia, smoothlife,
cellular-automata, artificial-life, orbium, organism, protoplasm, emergence, microscopy,
morphogenesis, membrane, generative, abstract, background).
