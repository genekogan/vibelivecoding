# Technique — Growth systems II: venation & dielectric breakdown

**Family:** branching-network growth. Four members share one skeleton — *seed → repeatedly
add the next element where a field/force says to → record parent pointers → draw the tree*:

| member | where the next node goes | in catalog? |
|---|---|---|
| differential growth | repel+subdivide a **closed contour** | ✅ `genart.diff_growth` (a *loop*, not a tree) |
| DLA | sticky **random walk** hits the aggregate | ✅ `genart.dla` |
| **space-colonization venation** | node grows toward the mean direction of nearby **auxin attractors** | ⬜ **this file** |
| **dielectric-breakdown lightning** | boundary cell added with prob ∝ **potential^η** (Laplacian) | ⬜ **this file** |

`diff_growth` and `dla` are done — **this file specs the two open members: venation and
lightning.** They are the *tree* members (parent pointers, thickness by flow), where diff_growth
is a repelling loop and dla is an undirected sticky blob. All four reuse the same house
machinery: a persistent `createGraphics` accumulation buffer stamped **incrementally** (few draws
/frame — proven by `dla` at 60fps), seed-deterministic LCG (no p5 `random()`), epoch-based regrow,
and a `K.t` re-image drift as the never-static motion floor.

Read alongside: `assets/prompts/author-brief.md` (gates), `research/generative/PROBE.md` (budgets),
`assets/CONTRACT.md §Visual contract`. Exemplars for both live in the same lineage — **Nervous
System** (Hyphae/Xylem), **Adam Runions / Prusinkiewicz lab** (the venation algorithm itself),
**Jared Tarbell** (Substrate), **Andy Lomas** (Aggregation), and the **Niemeyer–Pietronero–Wiesmann**
DBM model for lightning.

---

## 1. Algorithm + math

### 1a. Space-colonization venation (Runions et al. 2005; Nervous System's Hyphae/Xylem)

State: a set of **vein nodes** `V` (each with a parent index → a tree) and a cloud of **auxin
attractors** `A` (points scattered in the domain). Two length constants: **influence radius `dᵢ`**
(how far an attractor can "see" a node) and **kill radius `d_k`** (how close a node must get to
consume an attractor). Segment step `D` (how far a node grows per iteration; typically `d_k ≈ 2D`).

One growth iteration:

1. **Associate.** For every attractor `a ∈ A`, find its nearest vein node `v` with `|a−v| < dᵢ`.
   (Open venation = nearest single node → pure tree. Closed venation = every node within `dᵢ`
   → anastomosis/loops, the reticulate leaf mesh.)
2. **Grow.** For each node `v` that at least one attractor picked, sum the *unit* directions to
   those attractors and normalize: `n̂ = normalize( Σ (a−v)/|a−v| )`. Spawn `v' = v + D·n̂`,
   parent = `v`. (Averaging directions is why veins bend *toward clusters* of attractors, then
   split when two clusters pull opposite ways — that split is the branch.)
3. **Kill.** Remove any attractor with `min_v |a−v| < d_k` (it's been reached).
4. Repeat until attractors are exhausted or the node budget is hit.

**Thickness (Murray's law).** Vein width ∝ flow. Give each new tip flow=1 and propagate up the
parent chain (`flow[par] += 1`); stroke weight `w = w₀ · flow^(1/γ)`, γ≈2–3 (γ→∞ = uniform
filament). This is what makes the petiole a fat trunk and the veinlets hairline.

### 1b. Dielectric-breakdown lightning (DBM — Niemeyer/Pietronero/Wiesmann 1984)

The physically-faithful member. Solve Laplace's equation `∇²φ = 0` on a grid: aggregate cells
pinned `φ=0`, a source boundary pinned `φ=1`. Growth candidates = empty cells 4-adjacent to the
aggregate. Add candidate `i` with probability

```
p_i = φ_i^η / Σ_j φ_j^η
```

**η is the whole knob.** η=1 → Laplacian/branchy; η→0 → DLA-like blob; **η≈3–8 → straight,
sparse, whip-like bolts** (higher η starves side-channels of probability). Fractal dimension drops
as η rises.

Full relaxation-to-convergence every step is too slow for a VJ frame, so run **DBM-lite**: keep a
persistent `φ` field, do **2–4 Jacobi sweeps/frame** (`φᵢⱼ = ¼(φ₋ + φ₊ + φ↑ + φ↓)`, occupied
pinned 0, boundary pinned 1), grow **G cells/frame** by the weighted pick. The field lags slightly
— that lag reads as organic wobble. Record each grown cell's parent (the adjacent occupied cell it
attached to) → connected channels.

**Strike overlay (the flash).** DBM gives the *creeping Lichtenberg tree*; the dramatic *bolt* is a
**midpoint-displacement** polyline (Drilian's classic): given A→B, midpoint `M=(A+B)/2` displaced
perpendicular by `±rand·|A−B|·rough`; recurse to depth 5–7 (32–128 segments); at each split, with
prob `fork`, spawn a reduced side-bolt. Trace a leaf-to-root path through the DBM tree and draw the
bolt *along* it on beats — genuine structure, scripted drama.

---

## 2. p5-2D implementation (this engine, within PROBE budgets)

Both are **genart / `bg`** (full-bleed, no bed behind — must fill frame, hold luminance in
[0.02,0.92]). Both use the **persistent accumulation buffer** idiom from `dla`: stamp only the
**new** elements each frame, so per-frame draw cost is a handful of shapes — and because it's few,
you can afford `drawingContext.shadowBlur` on them (**≤30 shapes/frame** budget). The buffer holds
the whole grown figure; you `image()` it each frame with a slow `K.t` transform for the drift floor.

**Budgets spent (named):**
- **Persistent full-canvas `createGraphics` stamped incrementally** — the `feedback_fullcanvas` /
  `dla` pattern, verified 60fps. Only a few new stamps/frame.
- **Venation nodes ≤1600** (default ~700) — under the **2000-point** budget; nearest-attractor
  search via a **spatial-hash `Map`** (the `diff_growth` idiom), cell = `dᵢ`, so each attractor
  checks ~9 buckets → ~O(attractors·10) ≈ ≤8k dist-checks/frame. Trivial.
- **DBM grid 96×54** (`marching_96x54` free; ≤128×72 ceiling), Float32 `φ` + Uint8 `occ` + Int32
  `par`. 2–4 sweeps × 5k cells ≈ ≤20k ops/frame. Trivial.
- **Bolt = ONE stroked polyline** with shadowBlur set once (1 shape) → bloom within budget.
- **NO full-canvas `filter()`.** Glow = shadowBlur on the few new stamps + the single-polyline bolt.

### Shared header + palette LUT + spatial hash (author once, reuse in both)

```js
const D = { hue:150, energy:.55, speed:1, density:.5, scale:1, x:.5, y:.5, style:'hyphae', seed:0 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };
const u = Math.min(width, height), st = P.style;
const clp = (v,a,b)=>Math.max(a,Math.min(b,v));
const intn = (K.intensity!=null?K.intensity:.6);

// iq cosine palette -> 'rgb()' string (bypasses HSB cleanly, like dla uses drawingContext).
// Build a 256-LUT ONCE per (seed,style,hue); index by depth/flow/heat 0..1.
function iqRGB(t,a,b,c,d){ const f=i=>Math.round(255*clp(a[i]+b[i]*Math.cos(6.2832*(c[i]*t+d[i])),0,1));
  return 'rgb('+f(0)+','+f(1)+','+f(2)+')'; }
if (S.lutKey !== st+P.seed+((P.hue/360)|0)){ S.lutKey = st+P.seed+((P.hue/360)|0);
  const ph = P.hue/360;                              // hue rotates the palette phase
  const A4=[.5,.5,.5], B4=[.5,.5,.5], C4=[1,1,1], D4=[ph,ph+.33,ph+.66]; // <- swap per style
  S.lut = []; for(let i=0;i<256;i++) S.lut.push(iqRGB(i/255,A4,B4,C4,D4));
}
// thermal (HSB-native, for the thermal style): heat 0..1 -> [h,s,b]
const thermal = h => [ (232-232*h), (90-20*h), (30+70*h) ];
```

### Venation core loop (space colonization)

```js
// --- persistent buffer + epoch regrow (soft fade, never hard-clear -> no strobe) ---
const period = 40;                                  // regrow a fresh figure every ~40s
const epoch = Math.floor(K.t/period);
const key = width+'x'+height+'|'+P.seed+'|'+epoch+'|'+st;
if (S.key !== key){
  S.key = key;
  let z = ((P.seed*2654435761) ^ (epoch*40503) ^ 0xB5) >>> 0;
  S.rnd = ()=>{ z=(z*1664525+1013904223)>>>0; return z/4294967296; };
  if (!S.buf || S.bufKey!==width+'x'+height){ if(S.buf)S.buf.remove();
    S.buf = createGraphics(width,height); S.buf.colorMode(HSB,360,100,100,100); S.bufKey=width+'x'+height; }
  // ground: never pure black (luminance gate). B in [6..14] + vignette.
  S.buf.background(st==='cyanotype'?214:(st==='leaf'?70:222), st==='hyphae'?30:45, st==='leaf'?16:8);
  // attractors scattered in an organic blob around the anchor
  const NA = Math.floor(80 + P.density*320);        // 80..400 auxin sources
  S.attr=[]; const cx=P.x*width, cy=P.y*height, R=u*0.42*clp(P.scale,.4,2.2);
  for(let i=0;i<NA;i++){ const a=S.rnd()*6.2832, rr=R*Math.sqrt(S.rnd());
    S.attr.push({x:cx+Math.cos(a)*rr, y:cy+Math.sin(a)*rr*0.82}); }
  S.nodes=[{x:cx, y:cy+R*0.9, par:-1, flow:1}];      // root at the base of the blob
  S.di = u*0.14; S.dk = u*0.028; S.seg = u*0.014;    // influence / kill / step
  S.done=false;
}
image(S.buf, 0,0);                                   // (drift transform optional; see §5)

// --- grow a few iterations/frame; stop when attractors gone or node cap hit ---
const cap = Math.floor(400 + P.density*1200);        // <=1600 nodes
const iters = S.done ? 0 : Math.max(1, Math.round((1+P.speed*2)*(0.6+intn) + A.bass*3));
for (let it=0; it<iters && !S.done; it++){
  const nodes=S.nodes, attr=S.attr, di=S.di, dk=S.dk, cs=di;
  // hash nodes into buckets keyed on influence-radius cells
  const g=new Map(); for(let i=0;i<nodes.length;i++){ const p=nodes[i];
    const k=(Math.floor(p.x/cs))+','+(Math.floor(p.y/cs)); let b=g.get(k); if(!b){b=[];g.set(k,b);} b.push(i); }
  const pull=new Map();                              // nodeIdx -> {dx,dy}
  for(let ai=attr.length-1; ai>=0; ai--){ const a=attr[ai];
    let best=-1, bd=di*di; const bx=Math.floor(a.x/cs), by=Math.floor(a.y/cs);
    for(let ox=-1;ox<=1;ox++)for(let oy=-1;oy<=1;oy++){ const b=g.get((bx+ox)+','+(by+oy)); if(!b)continue;
      for(let jj=0;jj<b.length;jj++){ const j=b[jj], p=nodes[j], d2=(p.x-a.x)**2+(p.y-a.y)**2;
        if(d2<bd){bd=d2;best=j;} } }
    if(best<0) continue;
    if(bd < dk*dk){ attr.splice(ai,1); continue; }   // consumed
    const p=nodes[best], d=Math.sqrt(bd); let e=pull.get(best)||{dx:0,dy:0};
    e.dx+=(a.x-p.x)/d; e.dy+=(a.y-p.y)/d; pull.set(best,e);
  }
  if(pull.size===0 || nodes.length>=cap){ S.done=true; break; }
  pull.forEach((e,idx)=>{ if(nodes.length>=cap) return;
    const m=Math.hypot(e.dx,e.dy)||1, p=nodes[idx];
    const nx=p.x+e.dx/m*S.seg, ny=p.y+e.dy/m*S.seg;
    const ni=nodes.length; nodes.push({x:nx,y:ny,par:idx,flow:1});
    // Murray flow up the chain + stamp the NEW segment into the buffer
    let k=idx, guard=0; while(k>=0 && guard++<600){ nodes[k].flow++; k=nodes[k].par; }
    stampSeg(S.buf, p, nodes[ni]);                   // few/frame -> shadowBlur affordable
  });
}

function stampSeg(buf, a, b){
  const w = 0.6 + Math.pow(a.flow, 0.4)*0.9;         // Murray thickness
  buf.push();
  if(st==='hyphae'||st==='neon'){ buf.drawingContext.shadowBlur=6;
    buf.drawingContext.shadowColor = S.lut[Math.min(255, a.flow*4|0)]; }
  const col = (st==='cyanotype') ? 'rgb(225,240,255)'
            : (st==='leaf') ? 'rgb('+(70+a.flow)+',120,60)'
            : S.lut[Math.min(255, 40 + a.flow*3 | 0)];
  buf.strokeCap(ROUND); buf.stroke(col); buf.strokeWeight(w);
  buf.line(a.x,a.y,b.x,b.y); buf.drawingContext.shadowBlur=0; buf.pop();
}

// --- MOTION FLOOR: sap pulse + tip shimmer drawn LIVE over the buffer (never re-phases) ---
noStroke();
const tips = S.nodes;
blendMode(ADD);
for(let i=Math.max(1,tips.length-140); i<tips.length; i++){ const p=tips[i];
  const pulse = 0.5+0.5*Math.sin(K.t*2.4 - i*0.05);  // continuous travelling sap
  fill((P.hue+i*0.2)%360, 40, 100, (6+pulse*10)*(0.5+P.energy) + A.treble*30);
  circle(p.x, p.y, u*0.006*(0.6+pulse)); }
blendMode(BLEND);
```

### Lightning core loop (DBM-lite creep + midpoint-bolt strike)

```js
const COLS=96, ROWS=54;
const key = width+'x'+height+'|'+P.seed+'|'+Math.floor(K.t/45)+'|'+st;
if (S.key !== key){
  S.key = key; let z=((P.seed*2654435761)^0x9E)>>>0; S.rnd=()=>{z=(z*1664525+1013904223)>>>0;return z/4294967296;};
  if(!S.buf||S.bufKey!==width+'x'+height){ if(S.buf)S.buf.remove();
    S.buf=createGraphics(width,height); S.buf.colorMode(HSB,360,100,100,100); S.bufKey=width+'x'+height; }
  S.buf.background(st==='thermal'?250:(st==='schematic'?214:230), 55, st==='schematic'?14:7);
  S.occ=new Uint8Array(COLS*ROWS); S.phi=new Float32Array(COLS*ROWS); S.par=new Int32Array(COLS*ROWS).fill(-1);
  S.cand=[]; S.flash=0; S.leaf=0;
  const sx=Math.floor(P.x*COLS), sy=2;                // seed near top -> grows down/out
  S.occ[sy*COLS+sx]=1; addCand(sx,sy);
  for(let x=0;x<COLS;x++){ S.phi[(ROWS-1)*COLS+x]=1; } // bottom edge = source (φ=1)
}
image(S.buf,0,0);
function addCand(x,y){ const nb=[[1,0],[-1,0],[0,1],[0,-1]];
  for(const[dx,dy]of nb){ const nx=x+dx, ny=y+dy; if(nx<0||nx>=COLS||ny<0||ny>=ROWS)continue;
    const i=ny*COLS+nx; if(!S.occ[i] && S.cand.indexOf(i)<0) S.cand.push(i); } }

// --- relax φ a few sweeps/frame (Jacobi), occupied pinned 0, source edge pinned 1 ---
const sweeps=2, phi=S.phi, occ=S.occ;
for(let s=0;s<sweeps;s++) for(let y=1;y<ROWS-1;y++) for(let x=1;x<COLS;x++){ const i=y*COLS+x;
  if(occ[i]) { phi[i]=0; continue; }
  phi[i]=0.25*(phi[i-1]+phi[i+1]+phi[i-COLS]+phi[i+COLS]); }

// --- grow G cells weighted by φ^η ---
const eta = clp(P.eta!=null?P.eta:3, 0.5, 8);         // straightness knob
const G = Math.max(1, Math.round((1+P.speed*2)*(0.5+intn) + A.bass*3));
const cw = width/COLS, ch = height/ROWS;
for(let gi=0; gi<G && S.cand.length; gi++){
  let sum=0; const wts=S.cand.map(i=>{ const w=Math.pow(Math.max(1e-4,phi[i]),eta); sum+=w; return w; });
  let r=S.rnd()*sum, pick=0; for(let k=0;k<wts.length;k++){ r-=wts[k]; if(r<=0){pick=k;break;} }
  const ci=S.cand[pick]; S.cand.splice(pick,1); if(occ[ci])continue;
  occ[ci]=1; phi[ci]=0; const x=ci%COLS, y=(ci/COLS)|0;
  // attach to an occupied 4-neighbour = parent
  const nb=[[1,0],[-1,0],[0,1],[0,-1]]; let par=-1;
  for(const[dx,dy]of nb){ const j=(y+dy)*COLS+(x+dx); if(j>=0&&j<COLS*ROWS&&occ[j]){par=j;break;} }
  S.par[ci]=par; S.leaf=ci; addCand(x,y);
  if(par>=0){ const px=(par%COLS)*cw+cw/2, py=((par/COLS)|0)*ch+ch/2; // stamp channel segment
    S.buf.push(); if(st!=='schematic'){ S.buf.drawingContext.shadowBlur=7;
      S.buf.drawingContext.shadowColor = S.lut[200]; }
    S.buf.stroke(st==='schematic'?'rgb(210,235,255)':S.lut[Math.min(255,phi.length?180:180)]);
    S.buf.strokeWeight(1.3); S.buf.line(px,py, x*cw+cw/2, y*ch+ch/2);
    S.buf.drawingContext.shadowBlur=0; S.buf.pop(); }
}

// --- STRIKE: on beat (or K.t timer in silence) trace leaf->root, draw midpoint bolt ---
const wantStrike = (K.pulse>0.85 && (P.strike!==0)) || (Math.sin(K.t*0.7)>0.995);
if(wantStrike && S.flash<=0){ S.flash=6;
  const path=[]; let k=S.leaf, guard=0; while(k>=0 && guard++<400){ path.push([(k%COLS)*cw+cw/2, ((k/COLS)|0)*ch+ch/2]); k=S.par[k]; }
  S.bolt = path; }
if(S.flash>0){ S.flash--;
  const b=S.bolt||[]; if(b.length>1){
    blendMode(ADD); const a = (S.flash/6);            // fade over ~6 frames (partial, NOT full-frame)
    drawingContext.shadowBlur=18*P.energy; drawingContext.shadowColor=S.lut[220];
    stroke(st==='schematic'?200:52, 30, 100, 60*a);   // ONE polyline w/ midpoint jitter = 1 shape
    strokeWeight(1.5+3*P.energy*a); noFill(); beginShape();
    for(let i=0;i<b.length;i++){ const j=u*0.01*a*Math.sin(K.t*40+i*3.1);
      curveVertex(b[i][0]+j, b[i][1]+j*0.6); } endShape();
    drawingContext.shadowBlur=0; blendMode(BLEND); }
}

// --- MOTION FLOOR: creeping-leader glow at active candidates (continuous, silence-safe) ---
blendMode(ADD); noStroke();
for(let k=0;k<S.cand.length && k<120;k++){ const i=S.cand[k], x=i%COLS, y=(i/COLS)|0;
  const gl=Math.pow(phi[i],1.5)*(0.6+0.4*Math.sin(K.t*3+k)); 
  fill(52,20,100, gl*40*(0.5+P.energy)); circle(x*cw+cw/2, y*ch+ch/2, cw*1.4*gl); }
blendMode(BLEND); drawingContext.shadowBlur=0;
```

> Both loops end with `blendMode(BLEND)` and `shadowBlur=0` restored (contract requirement). The
> `S.buf.remove()` on rebuild prevents GPU-texture leaks across epochs.

---

## 3. Parameter surface

Order params so the **first two numerics move the render obviously at max** (the gate pokes both to
max). Use **`density` first, `speed`/`energy` second** — never `hue` first (360 wraps to red≈0).

**Universal seven (same semantics everywhere):**

| knob | venation | lightning | safe min/max |
|---|---|---|---|
| `density` | attractors 80→400 + node cap 400→1600 | grow-budget richness + candidate depth | .1 / 1 |
| `speed` | grow iters/frame (rate) | sweeps+grows/frame | .2 / 3 |
| `energy` | vein glow + sap-pulse amp | bolt bloom + leader glow | 0 / 1 |
| `scale` | blob radius (0.42u·scale) | (fixed grid; scales stamp/cell) | .4 / 2.2 |
| `hue` | palette phase / vein hue | plasma accent | 0 / 360 |
| `x`/`y` | root anchor / blob center | seed cell column | 0 / 1 → **clamp draw to .08–.92** |

**Family extras:**

- **Venation** — `taper` (Murray γ; .0=filament, 1=fat root-and-trunk; safe 0/1), `loops`
  (0=open tree, 1=closed/anastomosis mesh; a boolean-ish 0/1), `di` implied by `spread`
  (influence radius 0.08u–0.20u — bigger = long reaching veins, smaller = bushy).
- **Lightning** — `eta` (η straightness, **0.5/8**; low=fat branchy tree, high=whip bolt — never
  <0.5 or the weighted pick degenerates), `fork` (branch prob on strikes, 0/.6), `strike`
  (0=creep-only no bolts, 1=every beat), `bloom` (glow radius, folded into `energy` above).

**Range safety at both extremes:** node cap ≤1600 holds even at `density=1`+`speed=3` (grow stops at
cap, drift continues — no perf cliff). `bloom`/strike amplitude capped so `energy=1` strikes stay
**partial** (never full-frame → never trips 0.35). `eta≥0.5` floor keeps `Σφ^η>0`. Clamp the *draw*
anchor to 0.08–0.92 so `x/y` extremes can't push the whole figure off-canvas (blank-frame fail).

---

## 4. Palette / tone strategy

Colour comes from a **256-entry LUT rebuilt once per (seed,style,hue)** (§2 header), indexed by a
scalar: venation → `flow` (or depth), lightning → `φ` (or channel age). This costs nothing per
frame and gives smooth, seed-reproducible gradients. Three coloring disciplines:

- **iq cosine palette** — `iqRGB(t,a,b,c,d)`; swap the `(a,b,c,d)` vectors per style. Feed
  `hue/360` into `d` to rotate the whole ramp with the `hue` knob. Great for hyphae/neon/plasma.
- **HSB-native** — for organic looks (`leaf`, `nerve`): hue by flow, saturation high near tips,
  brightness ramp along thickness. `colorMode` on the **buffer only** (never the main canvas).
- **Duotone / thermal** — `cyanotype`/`schematic` = two inks (cyan ground + near-white lines,
  no bloom). `thermal` = `thermal(heat)` HSB ramp blue→red along channel age/φ (the diff_growth
  thermal idiom).

**≥3 divergent style looks per family, ≥1 non-representational:**

**Venation styles** —
1. **`hyphae`** *(default)* — Nervous System Hyphae: near-black ground, luminous white-gold
   filaments, thickness by flow, additive shadowBlur glow. Representational-organic, iconic.
2. **`leaf`** — botanical: warm parchment ground, green→amber veins thickening to a fat petiole,
   faint translucent lamina wash. Representational.
3. **`cyanotype`** *(non-representational)* — schematic: cyan ground, hairline white vein contour +
   node ticks at branch points, uniform weight, no organic shading. A *diagram* of a vein network.
4. **`nerve`** — biological synaptic: soft magenta↔cyan iq ramp, node swells at branch points,
   dark key — reads as dendrite/neuron, eerie.
5. **`ink-root`** — sumi: dry-brush tapering ink roots on toned paper (grain), near-monochrome.

**Lightning styles** —
1. **`bolt`** *(default)* — electric blue-white plasma on B≈7 near-black, additive core + bloom,
   frequent strikes. Representational.
2. **`lichtenberg`** — captured-in-acrylic figure: warm amber/copper fractal creeping on dark, slow
   growth, **rare** strikes (the frozen high-voltage-block look). Near-monochrome, austere.
3. **`schematic`** *(non-representational)* — deep-blue ground, thin uniform cyan channels, white
   node dots at every branch, **no bloom** — a wiring diagram of a discharge.
4. **`thermal`** *(non-representational)* — false-color heat ramp along channel age: hot white-red
   core near the seed → cool blue tips. Abstract data-viz read.
5. **`nerve`** — soft biological electric, magenta-cyan, synaptic swells — bridges to venation's mood.

---

## 5. Temporal strategy (30s → 5min)

This engine **freezes beat-locked-only motion at the 8s gate** (cps 0.5 → 16 beats re-phases).
Both members are **growth** systems, so they *do* evolve — but growth completes (venation exhausts
attractors; DBM stalls) and then the buffer is dead. Three layers keep it alive:

- **Real-time `K.t` motion floor (never re-phases — carries the 8s gate):**
  - Venation: the **sap-pulse** `0.5+0.5·sin(K.t·2.4 − i·0.05)` travelling along tips (§2), + tip
    shimmer. Optionally re-`image()` the buffer with a slow drift transform
    `translate(sin(K.t·0.11)·u·0.04,…); rotate(K.t·0.03)` (the diff_growth trick — that asset
    passes the motion gate at **0.0141**, *just* above 0.004, purely on this drift + wobble).
  - Lightning: the **creeping-leader glow** at candidates (§2) shimmers on `K.t` continuously;
    spontaneous micro-strikes fire on a `sin(K.t·0.7)` timer so **silence still evolves**.
  - **Aim motion 0.02–0.15** (comfortably above 0.004, well below 0.35). Make the drift *decisive* —
    don't scrape the floor like diff_growth did.
- **`K.section`/`K.intensity` arcs (30s–5min):** grow rate and attractor/grow budget scale with
  `intn` (higher sections → denser mesh / more frequent strikes). **Epoch regrow** =
  `floor(K.t/period)` (venation 40s, lightning 45s) rebuilds a fresh seeded figure each arc —
  **soft-fade, never hard-clear** (draw translucent ground over the buffer to dissolve, else a hard
  wipe inside an 8s window reads as a >0.35 jump). Audio on top: `A.bass` boosts grow iters and
  strike odds; `A.treble` sparkles tips — **never multiply the baseline by `A.*`** (validation runs
  silent).
- **Optional `P.act` programs (2–3 multi-minute dramaturgies):**
  - Venation: `grow` (steady → hold+drift, regrow each arc) · `breathe` (grow rate swells with
    intensity, veins pulse) · `prune` (grow then dissolve oldest tips → perpetual living churn, no
    regrow needed).
  - Lightning: `storm` (dense, frequent beat strikes) · `creep` (slow Lichtenberg, strikes off —
    the frozen look) · `cascade` (one big forking strike per section, progressively).

---

## 6. Exemplars + failure modes

**Exemplar artists** (no `_cards/` yet — cited by name):
- **Nervous System** — Jessica Rosenkrantz & Jesse Louis-Rosenberg. *Hyphae*, *Xylem*, *Laplacian
  Growth* — the canonical space-colonization/venation aesthetic; the `hyphae` style is a direct
  homage. Also their DBM/Laplacian-growth work is the reference for `lightning`'s organic tree.
- **Adam Runions / Przemyslaw Prusinkiewicz** (Univ. Calgary) — *Modeling and visualization of leaf
  venation patterns* (2005) and the space-colonization tree algorithm §1a implements.
- **Jared Tarbell** — *Substrate* / *Nodegarden*: the live-coding-native branch-growth lineage
  (crack propagation is a cousin rule); the tightest reference for "growth as generative canvas."
- **Andy Lomas** — *Aggregation* / *Cellular Forms*: DLA/dielectric-adjacent morphogenesis tone.
- **Niemeyer, Pietronero & Wiesmann (1984)** — the DBM model; **Theodore Gray / physical
  Lichtenberg-in-acrylic** — the `lichtenberg` visual reference.
- **Karl Sims** (*Panspermia*) & **Robert Hodgin** (flight404) — organic branching/particle mood.

**Failure modes (map to the exact gates):**
- **Blank render** — seed/anchor pushed off-canvas by `x/y` extremes; or `d_k` so large all
  attractors die turn 1; or `η` so high DBM stalls with one candidate. *Fix:* clamp draw anchor
  0.08–0.92, ensure `iters/G ≥ 1` and `η ≥ 0.5`, keep ≥1 live attractor/candidate.
- **Static (motion ≤ 0.004)** — growth finished + no `K.t` floor → dead buffer (the #1 trap; note
  diff_growth's razor-thin 0.0141). *Fix:* mandatory sap-pulse / creeping-leader overlay **and**
  buffer drift; make it decisive.
- **Luminance out of [0.02,0.92]** — pure-black lightning ground + tiny bolt → mean < 0.02
  (blackout fail); full-white strike → > 0.92. *Fix:* ground B ∈ [6..14] + vignette (never `0`);
  strikes **partial**, not full-frame.
- **Strobing (> 0.35)** — per-frame full-canvas strike flash, hard epoch-clear inside an 8s window,
  or redrawing the whole tree bright each frame. *Fix:* single-polyline localized bolt with capped
  bloom, **soft-fade regrow**, incremental buffer stamping (never repaint the world).
- **Perf** — naive O(nodes·attractors) nearest search (explodes as nodes grow); DBM
  relaxation-to-convergence per frame. *Fix:* spatial-hash the search (cell = `dᵢ`), node cap ≤1600,
  DBM = 2–4 sweeps/frame on ≤128×72, bolt as **one** shape.
```
