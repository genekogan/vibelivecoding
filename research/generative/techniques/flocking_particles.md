# Technique — Flocking / Particle Systems (emergent clustering)

**Family:** boids / murmuration · particle-life (asymmetric-attraction species) ·
n-body gravity. One shared skeleton — a population of agents integrated each
frame — with three interchangeable **acceleration kernels**. What differs is only
how `accel_i` is computed from the neighborhood; the population array, spatial
hash, trail field, styles, params and clock plumbing are identical.

Lineage: **Craig Reynolds** (Boids, 1987 — separation/alignment/cohesion),
**Robert Hodgin / flight404** (glowing GPU flocks, Magnetosphere, gravitation
studies), **Jeffrey Ventrella** (*Clusters* — particle life), **Jared Tarbell**
(agent line-systems, additive trails), **Sage Jenson** (agent trail-fields).

Covers COVERAGE.md targets **B·boids**, **B·nbody**, **B·particle_fountain**.
Author each as its OWN `genart` asset (own tags/identity) off this skeleton — or
expose `model` as a fourth param for a mega-asset. Do NOT dilute the first-two-
numeric param poke (keep `energy`, `density` first).

---

## 1 · Algorithm + math

Every agent `i` holds position `p_i`, velocity `v_i` (and a species tag `t_i`).
Each frame: compute an acceleration from neighbors, integrate, clamp, wrap.

**Boids** — three steering terms summed over neighbors within radius `r`:

```
separation  s_i = -Σ_j (p_j − p_i)/|p_j − p_i|²      (j within r_sep = r·0.5)
alignment   a_i =  mean_j(v_j) − v_i                  (j within r)
cohesion    c_i =  mean_j(p_j) − p_i                  (j within r)
accel_i     = w_sep·s_i + w_ali·a_i + w_coh·c_i
v_i ← clamp(v_i + accel_i, [v_min, v_max]);  p_i ← wrap(p_i + v_i)
```

Reynolds' insight: steering = `desired − velocity`, each term truncated to a max
force. The three weights are the entire behavioral gamut — cohesion≫separation
clumps, separation≫cohesion disperses, alignment makes the coherent sweep of a
murmuration. `v_min` (a speed floor) keeps the swarm alive (never freezes).

**Particle-life** (Ventrella/Clusters) — `K` species, an **asymmetric** K×K
matrix `M[a][b] ∈ [−1,1]` = the force species `a` feels from species `b`. Force
is a function of distance only:

```
F(r) = (r/r_min − 1)                     for r < r_min   (universal REPULSION, prevents collapse)
     =  M[t_i][t_j] · (1 − |2·rr − 1|)   for r_min ≤ r < r_max,  rr=(r−r_min)/(r_max−r_min)
     =  0                                for r ≥ r_max
accel_i = Σ_j F(r_ij) · (p_j − p_i)/r_ij ;  v_i ← (v_i + accel_i)·friction
```

Asymmetry (`M[a][b] ≠ M[b][a]`) is the whole magic — it makes chasers, fleers,
self-propelled cells and membranes. Friction (`~0.85`) replaces the speed clamp.

**N-body gravity** — `accel_i = Σ_j G·m_j·(p_j−p_i)/(|p_j−p_i|²+ε²)^{3/2}`. The
**softening** `ε²` (`≈(u·0.03)²`) kills the singularity at close approach. True
mutual gravity is O(N²) → viable only at N≤~150. The **budget-friendly** form is
*restricted* n-body: `M` heavy bodies (mutual, O(M²), M≤~8) + up to ~1500 massless
tracers each pulled only by the bodies (O(N·M)) — orbits, slingshots, accretion.

**Spatial hash — the budget-keeper.** Boids and particle-life are O(N²) naively.
Bin agents into a uniform grid of cell size = neighbor radius; each agent scans
only its 9 cells (self + 8). That's O(N·k), k = avg neighbors. Rebuild each frame
by clearing buckets (reuse arrays — never realloc). N-body's *long-range* force
can't be cut off, so it skips the hash and uses the few-bodies trick instead.

---

## 2 · p5-2D implementation (this engine)

- **Population** lives in `S.ps` as `{x,y,vx,vy,t}` objects, rebuilt only when
  seed / size / count changes. Deterministic layout via a **seeded LCG** (never
  p5 `random()` — global pollution across layers).
- **World is toroidal** (wrap edges) → frame always full, no wall-clumping, good
  luminance. Neighbor distance uses the **minimal-image** shift.
- **Trails**: a single translucent `rect(0,0,width,height)` per frame — high alpha
  = crisp specks, low alpha = long smears. Budget note: **NO full-canvas
  `filter()`** (banned, ~12ms). For a richer bloom you MAY instead self-stamp a
  **half-canvas feedback buffer** in `S` (`width/2 × height/2`, `g.image(g,…)`
  slightly scaled) — but the fade-rect is the cheap default.
- **Budget spent**: agents are the **≤2000-points** pool → cap `N ≤ ~1100` (dots/
  short streaks). In `web` mode, **≤2 links/agent** (~≤1800 thin lines). Additive
  streaks use `stroke` lines (cheap) — reserve the **≤150 heavy ADD shapes** cap
  and `shadowBlur` (≤30 shapes) only if you glow a few *hero* agents.
- The sim advances **per frame** (like `flowfield` advects per frame — accepted
  house practice). Rate rides `P.speed` and `K.intensity`; the **continuous
  motion floor** is the flocking drift itself + a `noise(…, K.t·0.04)` wander
  (samples on real time → never re-phases at 8s).

```js
// ── flocking_particles · BOIDS core (murmuration) ───────────────────────────
const D = { energy:.6, density:.5, speed:1, scale:1, hue:210,
            sep:1.6, ali:1.0, coh:1.0, reach:.5, wander:.4, trail:.5,
            x:.5, y:.5, style:'murmur', act:'murmur', seed:0 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };
const u = Math.min(width, height), key = width+'x'+height, st = P.style;
const fr = i => { const q = Math.sin(i*127.1 + P.seed*311.7)*43758.5453; return q - Math.floor(q); };

// population — seed + size + density keyed (budget: ≤~1100 of the 2000-point pool)
const N = Math.floor(220 + P.density*880);
if (S.seedUsed!==P.seed || S.key!==key || !S.ps || S.ps.length!==N){
  S.seedUsed=P.seed; S.key=key;
  let z=(P.seed*2654435761+12345)>>>0;
  S.rnd=()=>{ z=(z*1664525+1013904223)>>>0; return z/4294967296; };
  S.ps=[];
  for (let i=0;i<N;i++){ const a=S.rnd()*6.2832;
    S.ps.push({ x:S.rnd()*width, y:S.rnd()*height, vx:Math.cos(a), vy:Math.sin(a), t:(S.rnd()*6)|0 }); }
}
const ps=S.ps, rnd=S.rnd;

// arc + act dramaturgy (30s–5min; never re-phases — K.t / K.section driven)
const intn = (K.intensity!=null?K.intensity:0.6);
let cohMul=1, sepMul=1, spdMul=1, follow=0, tgtx=P.x*width, tgty=P.y*height;
if (P.act==='startle'){ sepMul = 1 + K.pulse*2.2 + A.bass*1.6; spdMul = 1 + K.pulse*0.6; }        // predator dash on the beat
else if (P.act==='settle'){ follow=0.9; tgtx=(0.5+0.4*Math.sin(K.t*0.045))*width; tgty=(0.5+0.34*Math.cos(K.t*0.037))*height; } // migrate to a wandering target
else { cohMul = 0.8 + K.swell*0.5; }                          // 'murmur' — breathe cohesion on the bar

// steering constants — all resolution-relative (scale by u = min(w,h))
const rad = u*(0.035 + P.reach*0.11) * P.scale, rad2 = rad*rad;
const sepR2 = (rad*0.5)*(rad*0.5);
const vmax = u*(0.004 + P.speed*0.009) * (0.7+intn*0.6) * spdMul, vmin = vmax*0.16; // speed FLOOR keeps it alive
const wCoh=(0.3+P.coh*1.0)*cohMul, wAli=0.4+P.ali*1.3, wSep=(0.6+P.sep*1.6)*sepMul;
const wanderAmt = vmax*(0.05+P.wander*0.45), forceCap = vmax*0.9;                    // clamp accel → stability
const hw=width*0.5, hh=height*0.5;

// spatial hash — cell = neighbor radius; reused buckets; O(N·k) not O(N²)
const cell=Math.max(6,rad), cols=Math.max(1,Math.ceil(width/cell)), rows=Math.max(1,Math.ceil(height/cell));
let grid=S.grid;
if (!grid || S.gc!==cols || S.gr!==rows){ grid=S.grid=new Array(cols*rows); S.gc=cols; S.gr=rows; for (let i=0;i<grid.length;i++) grid[i]=[]; }
for (let i=0;i<grid.length;i++) grid[i].length=0;             // reuse arrays — no GC churn
const cellOf=(x,y)=>((((Math.floor(x/cell)%cols)+cols)%cols) + (((Math.floor(y/cell)%rows)+rows)%rows)*cols);
for (let i=0;i<N;i++){ const p=ps[i]; grid[cellOf(p.x,p.y)].push(i); }

// trail field — ONE translucent rect (never full-canvas filter). alpha hi=crisp, lo=smears
noStroke(); blendMode(BLEND);
if (st==='murmur') fill((P.hue+15)%360, 30, 13, 58 - K.pulse*8);      // dusk, near-opaque → crisp specks
else if (st==='ink') fill(38, 8, 93, 40);                            // paper
else if (st==='web') fill(210, 60, 9, 24);                           // blueprint dark
else if (st==='thermal') fill(250, 40, 4, 12+P.trail*8);             // long heat smears
else fill((P.hue+200)%360, 55, 4, 9+P.trail*10);                     // plasma / neon
rect(0,0,width,height);

const additive = (st==='plasma'||st==='neon'||st==='thermal');
blendMode(additive?ADD:BLEND);

// ONE pass — neighbor sums (hash) → steer → integrate → draw
for (let i=0;i<N;i++){
  const p=ps[i];
  const cx=(((Math.floor(p.x/cell)%cols)+cols)%cols), cy=(((Math.floor(p.y/cell)%rows)+rows)%rows);
  let sx=0,sy=0, ax=0,ay=0, gx=0,gy=0, cnt=0, lc=0;
  for (let ox=-1;ox<=1;ox++) for (let oy=-1;oy<=1;oy++){
    const b=grid[((((cx+ox)%cols)+cols)%cols) + (((((cy+oy)%rows)+rows)%rows)*cols)];
    for (let k=0;k<b.length;k++){
      const j=b[k]; if (j===i) continue; const q=ps[j];
      let dx=q.x-p.x, dy=q.y-p.y;                             // minimal-image (toroidal)
      if (dx>hw)dx-=width; else if (dx<-hw)dx+=width;
      if (dy>hh)dy-=height; else if (dy<-hh)dy+=height;
      const d2=dx*dx+dy*dy; if (d2>rad2||d2<1e-4) continue;
      gx+=dx; gy+=dy; ax+=q.vx; ay+=q.vy;                     // cohesion + alignment sums
      if (d2<sepR2){ const inv=1/d2; sx-=dx*inv; sy-=dy*inv; }// separation ~ 1/d
      cnt++;
      if (st==='web' && lc<2 && j>i && d2<rad2*0.36){ stroke(200,55,85,26); strokeWeight(0.8); line(p.x,p.y,p.x+dx,p.y+dy); lc++; }
    }
  }
  let accx=0, accy=0;
  if (cnt>0){ const inv=1/cnt;
    accx += gx*inv*wCoh*0.02 + ((ax*inv)-p.vx)*wAli*0.35 + sx*wSep*3.0;
    accy += gy*inv*wCoh*0.02 + ((ay*inv)-p.vy)*wAli*0.35 + sy*wSep*3.0;
  }
  if (follow>0){ accx += (tgtx-p.x)*follow*0.012; accy += (tgty-p.y)*follow*0.012; }
  const wa = noise(p.x*0.0018, p.y*0.0018, K.t*0.04 + S.seedUsed*0.01)*12.566;   // curl wander = MOTION FLOOR
  accx += Math.cos(wa)*wanderAmt; accy += Math.sin(wa)*wanderAmt;
  const am=Math.hypot(accx,accy); if (am>forceCap){ const s=forceCap/am; accx*=s; accy*=s; } // force cap
  p.vx+=accx; p.vy+=accy;
  let sp=Math.hypot(p.vx,p.vy);
  if (sp>vmax){ const s=vmax/sp; p.vx*=s; p.vy*=s; sp=vmax; }
  else if (sp<vmin && sp>1e-4){ const s=vmin/sp; p.vx*=s; p.vy*=s; sp=vmin; }
  if (!isFinite(p.x)||!isFinite(p.y)||!isFinite(p.vx)){ p.x=rnd()*width; p.y=rnd()*height; p.vx=rnd()-0.5; p.vy=rnd()-0.5; } // NaN guard
  p.x=(p.x+p.vx+width)%width; p.y=(p.y+p.vy+height)%height;   // toroidal wrap

  const sn=Math.min(1, sp/vmax);                              // normalized speed → color
  if (st==='murmur'){ noStroke(); fill((P.hue+20)%360, 22, 8+sn*10, 55); const r=(1.1+P.energy*1.6)*P.scale; ellipse(p.x,p.y,r,r); }
  else if (st==='ink'){ noStroke(); const j=fr(i); fill(220,14,12,28+j*40); const r=(1.3+j*1.7+P.energy*1.4)*P.scale; ellipse(p.x,p.y,r,r); }
  else if (st==='web'){ noStroke(); fill(196,50,95,70); const r=1.6*P.scale; ellipse(p.x,p.y,r,r); }
  else { // plasma / neon / thermal — additive streak, hue by speed / heading
    let h; if (st==='thermal') h=(250 - sn*250 + 360)%360;
    else if (st==='neon') h=(P.hue + K.t*8 + sn*80)%360;
    else h=(P.hue + K.t*10 + Math.atan2(p.vy,p.vx)*28 + 360)%360;
    const al=Math.min(34, 13 + P.energy*15 + K.pulse*6);      // ADD alpha ≤34 (contract cap)
    stroke((h+360)%360, st==='thermal'?86:78, Math.min(100,55+sn*45+A.rms*40), al);
    strokeWeight((0.8+P.energy*1.5)*P.scale);
    const tl=2.2+P.energy*3; line(p.x,p.y, p.x-p.vx*tl, p.y-p.vy*tl);
  }
}
blendMode(BLEND); drawingContext.shadowBlur=0;
```

### Swap kernel A — particle-life (replace the boids `accel` accumulation)

```js
// setup once per seed: K species + asymmetric matrix M[a][b] ∈ [-1,1]
if (S.matSeed!==P.seed){ S.matSeed=P.seed; const KS=Math.max(2,P.species|0); S.KS=KS; S.M=[];
  for (let a=0;a<KS;a++){ S.M[a]=[]; for (let b=0;b<KS;b++) S.M[a][b]=fr(a*13+b*7+1)*2-1; } }
const KS=S.KS, M=S.M, rMin=rad*0.30, invRange=1/(rad-rMin), fScale=vmax*0.9;
// …inside the neighbor loop, INSTEAD of the boids sums:
const d=Math.sqrt(d2);
let f;
if (d<rMin) f=(d/rMin-1)*1.1;                                  // universal repulsion (no collapse → luminance safe)
else { const rr=(d-rMin)*invRange; f=M[p.t][q.t]*(1-Math.abs(2*rr-1)); }  // triangle attraction, peak mid-range
accx += (dx/d)*f; accy += (dy/d)*f;
// …after loop: integrate with FRICTION (no alignment/cohesion, keep vmax + NaN guard)
p.vx=(p.vx+accx*fScale)*0.86; p.vy=(p.vy+accy*fScale)*0.86;
// color by species: fill(p.t/KS*360, 70, 90, …)
```

### Swap kernel B — restricted n-body (skip the hash entirely)

```js
// setup once per seed: M heavy bodies
if (S.bodySeed!==P.seed){ S.bodySeed=P.seed; const MB=2+((P.bodies|0)); S.bodies=[];
  for (let m=0;m<MB;m++) S.bodies.push({ x:(0.3+fr(m*5+1)*0.4)*width, y:(0.3+fr(m*5+2)*0.4)*height,
    vx:(fr(m*5+3)-0.5)*0.4, vy:(fr(m*5+4)-0.5)*0.4, mass:0.6+fr(m*5+5)*1.4 }); }
const bodies=S.bodies, G=0.35*(0.5+P.energy), soft=(u*0.03)*(u*0.03);
for (let m=0;m<bodies.length;m++){ const bm=bodies[m]; let fx=0,fy=0;   // mutual gravity, O(M²)
  for (let n=0;n<bodies.length;n++){ if(n===m)continue; const bn=bodies[n];
    let dx=bn.x-bm.x,dy=bn.y-bm.y; const dd=dx*dx+dy*dy+soft, inv=bn.mass/(dd*Math.sqrt(dd)); fx+=dx*inv; fy+=dy*inv; }
  bm.vx+=fx*G; bm.vy+=fy*G; }
for (const b of bodies){ b.x=(b.x+b.vx+width)%width; b.y=(b.y+b.vy+height)%height; }
// …per tracer, INSTEAD of neighbor sums (no hash needed — only the few bodies):
let gxx=0,gyy=0;
for (let m=0;m<bodies.length;m++){ const b=bodies[m]; let dx=b.x-p.x,dy=b.y-p.y;
  const dd=dx*dx+dy*dy+soft, inv=b.mass/(dd*Math.sqrt(dd)); gxx+=dx*inv; gyy+=dy*inv; }
p.vx=(p.vx+gxx*G)*0.995; p.vy=(p.vy+gyy*G)*0.995;              // faint drag stabilizes orbits
```

---

## 3 · Parameter surface

First two numerics **`energy`, `density`** (the params gate pokes both to max →
must obviously change: brighter/faster + crowded). All maxes verified safe by the
clamps (vmax, forceCap, softening, universal repulsion, NaN guard).

| param | maps to | default | min–max | note |
|---|---|---|---|---|
| `energy` | streak brightness / dot size / force gain / ADD alpha | .6 | 0–1 | **first** — obvious at max |
| `density` | agent count N (220…1100) | .5 | 0–1 | **second** — crowd at max |
| `speed` | `vmax`, sim rate | 1 | .2–2.5 | clamped → no explosion |
| `scale` | neighbor radius + agent size + zoom | 1 | .4–2.2 | big = one giant flock |
| `hue` | base hue (never first — 360 wraps to red≈0) | 210 | 0–360 | |
| `sep` | separation weight | 1.6 | 0–3 | max = disperse (safe) |
| `ali` | alignment weight | 1.0 | 0–3 | max = coherent sweep |
| `coh` | cohesion weight | 1.0 | 0–3 | max = tight clumps (safe — floor keeps them moving) |
| `reach` | neighbor radius fraction | .5 | 0–1 | folds into `rad` |
| `wander` | curl-noise floor amount | .4 | 0–1 | keeps it alive at low neighbor counts |
| `trail` | fade-rect persistence | .5 | 0–1 | low=long smears |
| `x`,`y` | migrate/home target anchor | .5,.5 | 0–1 | used by `act='settle'` / n-body center |
| `species` | *(particle-life)* K species | 4 | 2–6 | matrix rebuilt on seed |
| `bodies` | *(n-body)* heavy masses | 3 | 1–6 | O(M²) mutual, keep ≤6 |
| `style` | render discipline (options) | 'murmur' | murmur·plasma·ink·thermal·web | ≥3 divergent |
| `act` | multi-minute program (options) | 'murmur' | murmur·startle·settle | dramaturgy |
| `seed` | LCG layout + matrix + body seed | 0 | 0–9999 | int, deterministic |

**Danger corners (all guarded):** `coh`≫`sep` → collapse to a point → near-black
(guard: `vmin` floor + universal short-range repulsion + a dusk field so the
frame mean stays >0.02). `sep`+`speed` max + no `forceCap` → NaN explosion →
blank (guard: force cap + speed clamp + NaN respawn + `ε²` softening).

---

## 4 · Palette / tone strategy

Engine is **HSB 360/100/100/100** (already set — never `colorMode`). Color the
agents from a *scalar* — normalized speed `sn`, heading `atan2(vy,vx)`, local
density `cnt`, or species `t` — so the palette tracks the emergent structure
(fast flock edges glow hot; dense cores read as shadow).

- **Near-monochrome murmuration** (anchor, non-glow): tiny dark specks
  `fill((hue+20)%360, ~22, 8+sn*10, 55)` on a dusk field. Clusters darken by
  overlap — the classic starling-cloud-over-Rome read. Abstracted-representational.
- **Additive plasma / neon** (chromatic glow): `blendMode(ADD)`, hue by heading or
  speed, `alpha≤34`. Speed→hue makes velocity legible as color.
- **Thermal false-color** (non-representational): `h=(250 − sn·250)` — slow=blue,
  fast=white-hot. Reads as a heat map of the flow, not birds.
- **Sumi ink / duotone**: dark dry specks on paper (`fill(38,8,93)` field), size
  jitter via `fr(i)`, no glow — calligraphic. Or two flat poster inks by species.
- **Blueprint schematic `web`** (non-representational): nodes + ≤2 bounded neighbor
  links + optional velocity arrows on a dark grid — the flock as a diagram.

**iq cosine palette in HSB** (rich divergent band from one scalar `t∈0..1`):

```js
const pal = t => { const T=6.2832;
  return [ ((P.hue + 60*Math.cos(T*t*0.9) + 30)%360+360)%360,
           Math.max(20,Math.min(100, 55 + 35*Math.cos(T*(t*0.7+0.25)))),
           Math.max(20,Math.min(100, 55 + 40*Math.cos(T*(t*1.1+0.5)))) ]; };
// fill(...pal(sn), alpha) — three cosines, offset phase/freq → thermal, oil-slick, spectral bands
```

Categorical (particle-life): fix each species a hue `t_i/K·360` at S~70 B~90 for a
readable, divergent poster palette — the membranes between species become visible.

---

## 5 · Temporal strategy (30s – 5min)

This engine **FREEZES beat-locked-only motion at 8s** (cps 0.5 → 16 beats
re-phases). Flocking is inherently non-periodic, so the sim itself carries the
motion gate — but reinforce with a real-time floor and layer rhythm on top:

- **Motion floor (never re-phases):** the flocking drift + the
  `noise(x,y, K.t·0.04)` wander (real-time argument). At low neighbor counts the
  wander alone keeps every agent moving → motion-diff always > 0.004.
- **Beat accents (partial amplitude — never a full-frame flash):** `K.pulse`
  drives a separation spike (`act='startle'` predator dash) or brightens streaks
  by ≤6 alpha; `K.swell` breathes cohesion/`rad` so the flock tightens & loosens
  on the bar. Keep additive brightness partial → stays under the 0.35 strobe cap.
- **Section arc:** `K.intensity` scales `vmax` and force; over the 8-section arc
  the swarm builds sparse-laminar → dense-agitated → back. `K.section` can bump
  `species` weighting or flip cohesion sign at boundaries.
- **`P.act` multi-minute programs:**
  - `murmur` — steady flocking, gentle bar-synced radius breathing.
  - `startle` — periodic beat-driven scatter-and-regroup (uses `K.pulse` hard).
  - `settle` — a slow **migrating target** (`sin(K.t·0.045)`) the flock follows
    across the frame over minutes, like a season migration.
  - *(particle-life)* `evolve` — slowly rotate/mutate `M` over minutes
    (`M[a][b] += 0.0006·sin(K.t·0.02 + a·b)`) so cluster morphology transforms —
    the single strongest multi-minute dramaturgy in the family.
  - *(n-body)* `collapse` — bodies spiral into a merge, then re-seed on a section
    boundary — accretion → dispersal cycle.
- **Slow hue drift** (`K.t·8..10`) over minutes so the palette never sits still.

---

## 6 · Exemplar artists + failure modes

**Artists** (no `_cards/` yet — cited by name):
- **Craig Reynolds** — canonical Boids; separation/alignment/cohesion is the spine.
- **Robert Hodgin (flight404)** — the aesthetic north star: glowing additive
  flocks, magnetosphere, gravitation/solar particle work → `plasma`/`thermal`.
- **Jeffrey Ventrella** — *Clusters*, origin of particle-life asymmetric attraction.
- **Jared Tarbell** — *Substrate*/*Sand Traveler* agent line-systems, additive trails.
- **Sage Jenson (mxsage)** — Physarum agent trail-fields (adjacent trail render).
- **Andy Lomas** — *Aggregation* accretive growth (n-body/clustering cousin).
- **Casey Reas / Ben Fry** — Processing agent-sketch lineage.
- Murmuration reference: **Dennis Hlynsky** (bird-path video), the STARFLAG /
  Cavagna starling data for real flock statistics.

**Failure modes** (with the exact gates):
- **Blank / all-black (lum < 0.02):** velocities exploded to NaN (force uncapped)
  or total collapse (coh≫sep). Fix: `forceCap`, `vmax` clamp, `ε²` softening,
  universal short-range repulsion, NaN respawn, and a dusk field so the frame
  mean holds > 0.02 even if every agent clumps.
- **Static (motion-diff < 0.004):** too few / too small agents, or the flock hit a
  laminar equilibrium, or motion is *only* beat-locked and re-phased at 8s. Fix:
  enough N + size, the `K.t` wander floor, the `vmin` speed floor, slow
  target/matrix drift.
- **Strobing (motion-diff > 0.35):** full-frame flash (multiplying whole-field
  brightness by `K.pulse`), fade-rect alpha too high blinking the frame, or mass
  en-masse respawn each frame. Fix: partial beat amplitude, smooth trail fade,
  respawn agents individually.
- **Luminance too white (> 0.92):** additive overload — too many/too-bright
  streaks. Fix: `alpha ≤ 34`, cap N, keep the field dark under ADD.
- **Perf (< 25fps):** forgot the spatial hash → O(N²) (810k checks at N=900); or
  reallocating buckets each frame (GC churn); or unbounded `web` links. Fix: hash
  with reused arrays (`length=0`), cap N ≤ ~1100, use `d2` not `sqrt`, ≤2
  links/agent, no full-canvas filter, ADD-alpha discipline. N-body skips the hash
  (few bodies), so it scales to ~1500 tracers freely.
```
