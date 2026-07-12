# Technique — Aperiodic & non-Euclidean tilings

**Family:** Penrose P3 rhombus tiling by **deflation**, and **{p,q} hyperbolic
tiling on the Poincaré disk** (Escher's *Circle Limit*). Girih (Islamic
strapwork) and Truchet (quarter-arc) already ship — see `genart.girih.json` and
`genart.truchet.json`; this file deliberately does **not** re-cover those. It
covers the two things they don't: an *aperiodic* plane tiling with no
translational symmetry (fivefold quasicrystal), and a *non-Euclidean* tiling
whose cells shrink to the boundary of a disk.

> **Architecture in one sentence (both sub-families):** the tiling is
> **expensive static geometry** — a deflation recursion or a reflection-group BFS
> that produces hundreds–thousands of cells. **Bake it once** into a cached
> `createGraphics` buffer keyed on structural params, then per frame just
> `image()`-upscale it and animate a **cheap overlay** (a sweeping glow-front, an
> elliptic spin, a beat bloom). This is exactly the pattern `genart.girih` and
> `genart.truchet` use and both cleared the motion gate (0.0126 / 0.0228).
> **Never regenerate the tiling in `draw()`.**

All counts, the deflation growth, the hyperbolic `rv` formula, the geodesic
interior-arc guard, and the "skip edge B→C" rhombus-merge rule below were
**numerically verified** (node), not asserted.

---

## 1. Algorithm + math

### 1a. Penrose P3 (rhombus) by deflation — Robinson half-triangles

Work with **Robinson triangles** (half-rhombi), not rhombi — deflation is clean
on triangles. Two types, both isosceles, φ = (1+√5)/2:

- **type 0 ("fat", half of the 72°/108° thick rhombus)** — apex 36°, base 72°.
- **type 1 ("thin", half of the 36°/144° thin rhombus)** — apex 108°, base 36°.

Represent a triangle as `[type, A, B, C]` with points as `{x,y}`. The
**subdivision (deflation) rules** — the canonical Preshing scheme, each step
replaces every triangle with smaller ones scaled by 1/φ:

```js
const PHI = (1 + Math.sqrt(5)) / 2;
function deflate(tris){
  const out = [];
  for (const [c, A, B, C] of tris){
    if (c === 0){                                   // fat  → 1 fat + 1 thin
      const P = { x:A.x+(B.x-A.x)/PHI, y:A.y+(B.y-A.y)/PHI };
      out.push([0, C, P, B], [1, P, C, A]);
    } else {                                        // thin → 2 thin + 1 fat
      const Q = { x:B.x+(A.x-B.x)/PHI, y:B.y+(A.y-B.y)/PHI };
      const R = { x:B.x+(C.x-B.x)/PHI, y:B.y+(C.y-B.y)/PHI };
      out.push([1, R, C, A], [1, Q, R, B], [0, R, Q, A]);
    }
  }
  return out;
}
```

**Seed = a wheel of 10 fat triangles** around the origin (this is what gives the
fivefold symmetric "sun" at the centre); mirror every other one so edges match:

```js
function wheel(){
  const t = [];
  for (let i = 0; i < 10; i++){
    let B = { x:Math.cos((2*i-1)*Math.PI/10), y:Math.sin((2*i-1)*Math.PI/10) };
    let C = { x:Math.cos((2*i+1)*Math.PI/10), y:Math.sin((2*i+1)*Math.PI/10) };
    if (i % 2 === 0){ const s = B; B = C; C = s; }   // mirror — omit and you get a seam defect
    t.push([0, { x:0, y:0 }, B, C]);
  }
  return t;
}
```

**Growth (verified):** all vertices stay inside the unit circle at every depth.

| depth | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| triangles | 10 | 20 | 50 | 130 | 340 | 890 | 2330 | 6100 |

Growth ≈ φ² ≈ 2.6×/level. **Useful band: depth 3 (130, chunky) → depth 6 (2330,
fine).** Cap at 6.

**Rendering into seamless rhombi (verified rule):** fill each triangle by type
(fat = one tone, thin = another) — that alone reads unmistakably as Penrose. For
crisp *rhombus* outlines with no internal diagonal seam, stroke the two equal
**legs A→B and C→A** and **skip the base edge B→C**. Verified: for the tuple
order above, edge **B→C is the base (the shared internal diagonal of a rhombus
pair) for 100% of triangles** at every depth, so skipping it merges the two
half-rhombi visually.

### 1b. Hyperbolic {p,q} on the Poincaré disk

The unit disk is the whole hyperbolic plane. **Geodesics** are circular arcs
that meet the boundary circle at right angles (a diameter is the degenerate
case). A regular tiling **{p,q}** has p-gons, q around each vertex, and exists in
the hyperbolic plane iff **1/p + 1/q < 1/2** (e.g. {7,3}, {6,4}, {5,4}, {8,3},
{4,5}, {3,7}). At the boundary 1/p+1/q = 1/2 it degenerates to the Euclidean
{4,4}/{3,6}/{6,3}.

**Central polygon vertex radius** (Euclidean, inside the disk) — verified real
for all valid pairs:

```js
const rv = Math.sqrt( Math.cos(Math.PI*(1/p + 1/q)) / Math.cos(Math.PI*(1/p - 1/q)) );
// {7,3}=0.301  {6,4}=0.518  {5,4}=0.398  {8,3}=0.406  {4,5}=0.398  {3,7}=0.301
```

`cos(π(1/p+1/q)) ≥ 0` exactly when the pair is hyperbolic, so a NaN `rv` **is**
your "not a valid tiling" guard — clamp `q` up until `1/p+1/q < 0.5`.

**Building the tiling = a reflection-group BFS.** Reflecting a polygon across one
of its geodesic edges = **circle inversion** in that edge's orthogonal circle.
Given an edge (v1,v2), the orthogonal circle passes through v1, v2 **and the
inverse point** v1* = v1/|v1|² (three points → circumcircle). Invert all p
vertices in that circle to get the neighbour on the far side of the edge. BFS out
from the central polygon, dedup by rounded centroid, cap the count:

```js
function circumcenter(A,B,C){
  const d = 2*(A.x*(B.y-C.y)+B.x*(C.y-A.y)+C.x*(A.y-B.y));
  if (Math.abs(d) < 1e-12) return null;
  const a2=A.x*A.x+A.y*A.y, b2=B.x*B.x+B.y*B.y, c2=C.x*C.x+C.y*C.y;
  return { x:(a2*(B.y-C.y)+b2*(C.y-A.y)+c2*(A.y-B.y))/d,
           y:(a2*(C.x-B.x)+b2*(A.x-C.x)+c2*(B.x-A.x))/d };
}
function reflectEdge(poly, i){                       // returns the neighbour polygon
  const v1 = poly[i], v2 = poly[(i+1)%poly.length];
  if (Math.abs(v1.x*v2.y - v1.y*v2.x) < 1e-6){       // edge is a diameter → line reflection
    const dx=v2.x-v1.x, dy=v2.y-v1.y, L=Math.hypot(dx,dy), nx=-dy/L, ny=dx/L;
    return poly.map(z => { const t=(z.x-v1.x)*nx+(z.y-v1.y)*ny; return { x:z.x-2*t*nx, y:z.y-2*t*ny }; });
  }
  const d1=v1.x*v1.x+v1.y*v1.y, v1i={ x:v1.x/d1, y:v1.y/d1 };
  const c = circumcenter(v1, v2, v1i); if (!c) return null;
  const rr2 = (v1.x-c.x)**2 + (v1.y-c.y)**2;         // invert every vertex in circle (c, √rr2)
  return poly.map(z => { const dx=z.x-c.x, dy=z.y-c.y, k=rr2/(dx*dx+dy*dy);
                         return { x:c.x+dx*k, y:c.y+dy*k }; });
}
```

Verified: BFS to a 400-cell cap keeps every vertex inside the disk (maxR ≤ 0.999)
for all six pairs above.

**Drawing a geodesic edge** (the load-bearing primitive) — the circle through
z1, z2, z1* , then the **interior arc** (guard: if the short-way midpoint escapes
the disk, sweep the other way):

```js
function geodesic(g, z1, z2, CX, CY, R){             // R = disk pixel radius, (CX,CY) centre
  const cross = z1.x*z2.y - z1.y*z2.x, d1 = z1.x*z1.x + z1.y*z1.y;
  if (Math.abs(cross) < 1e-4 || d1 < 1e-9){          // diameter → straight chord
    g.line(CX+z1.x*R, CY+z1.y*R, CX+z2.x*R, CY+z2.y*R); return;
  }
  const z1i = { x:z1.x/d1, y:z1.y/d1 }, c = circumcenter(z1, z2, z1i);
  const rr = Math.hypot(z1.x-c.x, z1.y-c.y);
  let a1 = Math.atan2(z1.y-c.y, z1.x-c.x), a2 = Math.atan2(z2.y-c.y, z2.x-c.x);
  let da = a2 - a1; while (da > Math.PI) da -= 2*Math.PI; while (da < -Math.PI) da += 2*Math.PI;
  const mx = c.x+Math.cos(a1+da/2)*rr, my = c.y+Math.sin(a1+da/2)*rr;
  if (mx*mx + my*my > 1) da -= Math.sign(da)*2*Math.PI;   // interior-arc guard
  g.beginShape();
  for (let s=0; s<=10; s++){ const a=a1+da*s/10; g.vertex(CX+(c.x+Math.cos(a)*rr)*R, CY+(c.y+Math.sin(a)*rr)*R); }
  g.endShape();
}
```

---

## 2. p5-2D implementation (this engine, within PROBE budgets)

**Budgets I am spending (named):**
- **One cached `createGraphics` buffer**, rebuilt *only* on a structural key
  (`size | seed | depth/{p,q} | style | scale | anchor`). This is the PROBE
  "pre-render static content into a size-keyed buffer" allowance — the deflation
  (≤2330 fills) / BFS (≤400 polys × p geodesics) runs **once**, a one-frame
  build hitch, never per frame. For the Penrose "drift" act I oversize the buffer
  to **1.45·max(w,h) square** so a slow rotation never exposes a corner.
- **Per frame:** one `image()` upscale of that buffer (PROBE `feedback_fullcanvas`
  / upscale = free) + a glow overlay of **≤150 ADD ellipses ≤¼-canvas, alpha ≤ 35**
  (PROBE `heavy_150_add` = 59.7fps, free) + a scan of **≤~300 stored centroids**
  (trivial CPU). Total: comfortably 60fps solo, safe in an 11-layer stack.
- **Optional heavy act only** — the hyperbolic Möbius "dive" redraws vector cells
  each frame; hard-cap **≤50 polygons × p edges × 6 segments ≈ 2000 line-vertices**
  (the PROBE `points_2000` ceiling). Document it as the expensive act, not default.

### 2a. Penrose core loop

```js
const D = { hue: 42, energy: .6, speed: 1, density: .5, scale: 1, x: .5, y: .5,
            style: 'stained', act: 'inflate', glow: .5, seed: 0 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };
const u = Math.min(width, height), st = P.style, intn = (K.intensity!=null?K.intensity:.6);
const fr = i => { const s = Math.sin(i*127.1 + P.seed*311.7)*43758.5453; return s - Math.floor(s); };
if (S.lastBeat == null || K.beat < S.lastBeat) S.lastBeat = K.beat; S.lastBeat = K.beat;

// depth from density (structural — first-poke param produces an obvious change)
const depth = 3 + Math.round(Math.min(1, Math.max(0, P.density)) * 3);   // 3..6
const key = [width, height, depth, st, P.seed, P.scale.toFixed(2), P.x.toFixed(2), P.y.toFixed(2)].join('|');
if (S.key !== key){
  S.key = key;
  // 1) deflate
  let t = (function(){ const w=[]; for(let i=0;i<10;i++){ let B={x:Math.cos((2*i-1)*Math.PI/10),y:Math.sin((2*i-1)*Math.PI/10)},
        C={x:Math.cos((2*i+1)*Math.PI/10),y:Math.sin((2*i+1)*Math.PI/10)}; if(i%2===0){const s=B;B=C;C=s;} w.push([0,{x:0,y:0},B,C]); } return w; })();
  for (let d=0; d<depth; d++) t = deflate(t);        // deflate() + PHI defined once above the P-block-safe way (inline them)
  // 2) map unit disk → screen so the tiling overfills the frame; oversize for 'drift' rotation
  const over = (P.act==='drift') ? 1.45 : 1.06;
  const BW = Math.ceil(over*Math.max(width,height)), sc = BW*0.5*P.scale*1.02;
  const CX = BW*0.5, CY = BW*0.5;
  if (S.buf) S.buf.remove();
  S.buf = createGraphics(BW, BW);                    // NOTE: leave buffer in native RGB for iq-cosine fills
  const g = S.buf; g.push();
  paintPaper(g, st, P.hue);                          // opaque bg into the buffer (never leave it transparent)
  const cents = [];
  for (let k=0; k<t.length; k++){
    const [c,A0,B0,C0] = t[k];
    const ax=CX+A0.x*sc, ay=CY+A0.y*sc, bx=CX+B0.x*sc, by=CY+B0.y*sc, cx=CX+C0.x*sc, cy=CY+C0.y*sc;
    const rr = ((A0.x+B0.x+C0.x)/3);                 // radial order for the reveal/wavefront
    fillTile(g, st, c, ax,ay,bx,by,cx,cy, P.hue, fr(k));
    if (st!=='ink') { g.stroke(0,0,0,st==='blueprint'?40:70); g.strokeWeight(1); g.noFill();
      g.line(ax,ay,bx,by); g.line(cx,cy,ax,ay); }    // legs A→B, C→A ; skip base B→C (seamless rhombi)
    cents.push({ x:(ax+bx+cx)/3, y:(ay+by+cy)/3, c, r:Math.hypot((A0.x+B0.x+C0.x)/3,(A0.y+B0.y+C0.y)/3) });
  }
  g.pop();
  S.cents = cents; S.BW = BW; S.maxR = 1.0;
}

// ---- live: image the baked buffer centred, then cheap animated overlay ----
push();
translate(width*0.5, height*0.5);
if (P.act==='drift') rotate(K.t * 0.03 * P.speed);   // elliptic-ish slow spin — continuous, never re-phases
image(S.buf, -S.BW*0.5, -S.BW*0.5);
pop();

// inflation wavefront: an expanding ring re-lights tiles as it passes (real-time K.t floor)
const front = (P.act==='inflate') ? Math.min(1, ((K.t*P.speed*0.09) % 1.6)/1.0) : ((K.t*P.speed*0.06)%1);
const bw = 0.10 + P.glow*0.16, beatBloom = K.pulse*0.5 + A.bass*0.9, peak = 40 + P.energy*50;
blendMode(ADD);
let drawn = 0;
for (let i=0; i<S.cents.length && drawn<150; i++){
  const t2 = S.cents[i]; let dd = Math.abs(t2.r - front); if (dd > bw*1.4) continue;
  const amt = Math.max(0, 1 - dd/bw);
  const off = { x: t2.x - S.BW*0.5, y: t2.y - S.BW*0.5 };    // buffer→canvas centre offset
  const hx = (P.hue + t2.c*24 + t2.r*40) % 360;
  fill(hx, 40, 100, amt * (0.10 + peak*0.006) * 100 * 0.35 * (0.6+intn));
  circle(width*0.5 + off.x, height*0.5 + off.y, u*0.05*(0.7+amt));
  drawn++;
}
// partial-frame beat bloom on the central sun (never a full-frame flash → stays < 0.35 strobe gate)
if (beatBloom > 0.05){ fill((P.hue+20)%360, 30, 100, beatBloom*12); circle(width*0.5, height*0.5, u*0.5*(1+beatBloom*0.2)); }
blendMode(BLEND); drawingContext.shadowBlur = 0;
```

*(Inline `deflate`/`PHI` and the `paintPaper`/`fillTile` style helpers into the
asset — layer code is one `new Function` body, so define them as `const … =
(…)=>{…}` above the draw work or inline the loops.)*

### 2b. Hyperbolic core loop (delta from 2a)

Same skeleton; the **build** runs the reflection BFS instead of deflation and
bakes geodesic edges + filled cells; the **default motion** is a pure disk
rotation (a hyperbolic *elliptic* isometry — rotating the baked bitmap about the
disk centre is geometrically exact and seamless, disk→disk):

```js
// --- build (inside the S.key rebuild) ---
const p = Math.max(3, Math.min(8, Math.round(P.sides))), q = validQ(p, Math.round(P.valence));
const rv = Math.sqrt(Math.cos(Math.PI*(1/p+1/q)) / Math.cos(Math.PI*(1/p-1/q)));
let poly0 = []; for (let i=0;i<p;i++){ const a=(i+0.5)*2*Math.PI/p; poly0.push({x:rv*Math.cos(a),y:rv*Math.sin(a)}); }
const cap = 60 + Math.round(P.density*300);           // 60..360 cells
const polys=[poly0], seen=new Set([ckey(centroid(poly0))]); let frontier=[poly0];
while (polys.length<cap && frontier.length){ const nx=[]; for (const Pp of frontier){ for (let i=0;i<Pp.length;i++){
  const Rp = reflectEdge(Pp,i); if(!Rp) continue; const cc=centroid(Rp); if(Math.hypot(cc.x,cc.y)>0.999) continue;
  const kk=ckey(cc); if(seen.has(kk)) continue; seen.add(kk); polys.push(Rp); nx.push(Rp); if(polys.length>=cap)break; }
  if(polys.length>=cap)break; } frontier=nx; }
// bake: disk radius R = 0.5*min(w,h)*scale ; fill cells (iq cosine by ring), draw geodesic edges via geodesic()
const R = 0.5*Math.min(width,height)*P.scale*0.98, CX=width*0.5, CY=height*0.5;
S.buf = createGraphics(width,height); const g=S.buf; paintPaper(g, st, P.hue);
for (const Pp of polys){ fillCell(g, st, Pp, CX,CY,R, P.hue); for (let i=0;i<Pp.length;i++) geodesic(g, Pp[i], Pp[(i+1)%Pp.length], CX,CY,R); }
if (st==='blueprint'||st==='ink'){ g.noFill(); g.stroke(0,0,0,60); g.circle(CX,CY,2*R); }   // the boundary circle
S.cents = polys.map(Pp=>{ const c=centroid(Pp); return {x:c.x,y:c.y,hr:Math.hypot(c.x,c.y)}; });

// --- live overlay ---
push(); translate(width*0.5,height*0.5); rotate(K.t*0.05*P.speed);         // elliptic spin = motion floor
image(S.buf, -width*0.5, -height*0.5); pop();
// expanding geodesic glow-ring center→boundary (hyperbolic radius sweep), + central beat bloom (partial-frame)
```

Helper `validQ(p,q)` bumps q until `1/p+1/q < 0.5`; `ckey` rounds a centroid to
3 dp; `centroid` averages vertices. The **'dive' act** (Escher infinite-zoom):
precompute the vector cells **once** in `S`, then per frame apply one disk
automorphism `T(z) = (z−a)/(1 − ā·z)` with `a` sliding along a geodesic
(`a = {x: 0.34*Math.sin(K.t*0.15), y:0}`), transform stored vertices, redraw with
`geodesic()`. **Cap ≤50 cells** for this act (≈2000 line-vertices).

---

## 3. Parameter surface

Order matters: the **first two numeric params are poked to max** by the
validator — put the two that visibly transform the frame first.

| param | default | min | max | maps to | notes |
|---|---|---|---|---|---|
| `density` | .5 | 0 | 1 | universal | **1st poke.** Penrose: deflation depth 3→6. Hyperbolic: cell cap 60→360. Rebuilds the buffer. |
| `scale` | 1 | .55 | 2.2 | universal | **2nd poke.** Rhombus/cell size (Penrose overfill factor; hyperbolic disk radius). Rebuilds. |
| `energy` | .6 | 0 | 1 | universal | glow-front & bloom brightness. Safe at 0 (baked tiling still fills frame) and 1 (ADD alpha capped). |
| `speed` | 1 | 0 | 3 | universal | wavefront / spin rate. 0 keeps the K.t drift term alive elsewhere — never let 0 freeze all motion. |
| `hue` | 42 (Penrose gold) / 205 (hyperbolic) | 0 | 360 | universal | primary hue. **Never first** (360 wraps to red≈0). |
| `x`,`y` | .5 | 0 | 1 | universal | tiling centre as canvas fraction (Penrose sun / disk centre). |
| `glow` | .5 | .05 | 1 | extra | width of the sweeping glow-front along the tiling. |
| `sides` (hyperbolic) | 7 | 3 | 8 | extra | p in {p,q}. |
| `valence` (hyperbolic) | 3 | 3 | 8 | extra | q; auto-bumped until `1/p+1/q<1/2`. |
| `style` | see §4 | — | — | mandatory | ≥3 divergent looks. |
| `act` | inflate/spin | — | — | dramaturgy | §5. |
| `seed` | 0 | 0 | 9999 | mandatory | Penrose wheel/mirror phase & per-tile jitter; hyperbolic rotation offset & palette. Rebuild cache on change. |

Extremes hold: `density`+`scale` at max → depth-6 Penrose / 360-cell hyperbolic
scaled 2.2× (obvious change, still ≥25fps because it's baked); at min → chunky
depth-3 / 60-cell (still fills the frame — the overfill factor guarantees no
blank border).

---

## 4. Palette / tone strategy (≥3 divergent looks, ≥1 non-representational)

The whole family is non-representational, so *every* look is abstract — the job
is to diverge on **rendering philosophy** (mass-fill vs line vs additive-glow),
not just hue. Bake fills in the buffer; keep the live overlay in HSB.

**iq cosine palette** — bake it in the buffer's **native RGB** (a fresh
`createGraphics` is RGB unless you call `.colorMode(HSB…)`; don't, for stained):

```js
function iq(t, ph){                                  // t in [0,1] → [r,g,b] 0..255
  const a=[.5,.5,.5], b=[.5,.5,.5], c=[1,1,1], d=[0,.33+ph,.67+ph];
  return [ 255*(a[0]+b[0]*Math.cos(6.2832*(c[0]*t+d[0]))),
           255*(a[1]+b[1]*Math.cos(6.2832*(c[1]*t+d[1]))),
           255*(a[2]+b[2]*Math.cos(6.2832*(c[2]*t+d[2]))) ]; }
// fillTile: const [r,g_,bl]=iq((c? .55:.08)+t2.r*.4, P.hue/360); g.fill(r,g_,bl);
```

Five styles (default + at least one that changes the philosophy):

1. **`stained`** *(default, chromatic mass)* — Escher stained-glass: cells filled
   by type/ring index through the iq cosine LUT, thin dark leading on the legs.
   The rich, opaque, VJ-friendly default that clears the no-bed luminance gate.
2. **`brass`** *(dark-key, line)* — gilt double-line strapwork (a wide dark
   under-stroke + a thin bright gold over-stroke on the legs) on deep lapis; the
   glow-front sweeps the ribbons. Near-mono, sacred. (Mirrors `girih` 'gold'.)
3. **`ink`** *(near-monochrome, non-representational)* — sumi single-ink: no
   fills, one dark hue (≈38° low-sat) on warm paper (bri ≈ 86, **not** pure
   white — keeps luminance < 0.92), dry-brush weight jitter `sw*(0.7+0.5*fr(k))`,
   occasional broken/tapered legs. Austere, hand-drawn.
4. **`blueprint`** *(clinical, schematic)* — cyan geodesic/edge lines + faint
   guide construction (the bounding disk, the central polygon's circumcircle) on
   navy; white vertex ticks. Reads as a maths plate.
5. **`neon`** *(kinetic, additive)* — `blendMode(ADD)` glow tubes: a wide low-α
   halo stroke + a bright core, `drawingContext.shadowBlur` on the ≤30 tiles
   nearest the wavefront (reset to 0 after). Dark bg; the front is the subject.

HSB discipline for the overlay: derive hue from `(P.hue + type*Δ + ring*Δ) %
360`, keep sat 30–60 on the bloom (over-saturated ADD clips to white and trips
the luminance gate). Duotone/thermal variants: drive the LUT with two anchor hues
(`P.hue` and `P.hue+150`) picked by tile type.

---

## 5. Temporal strategy (30s–5min; this engine FREEZES beat-only motion at 8s)

**Real-time `K.t` motion floor (never re-phases → clears the 8s gate):**
- Penrose: the **inflation wavefront** `front = (K.t*speed*0.09) % 1.6` — an
  expanding ring that re-lights tiles outward forever; plus optional whole-buffer
  **rotation** `rotate(K.t*0.03)` on the oversized buffer (drift act).
- Hyperbolic: **elliptic spin** `rotate(K.t*0.05*speed)` of the baked disk —
  continuous, exact, seamless. Plus an expanding geodesic glow-ring center→edge.
- Both: a low-amplitude per-tile shimmer `bri += 6*Math.sin(cent·k + K.t*0.3)`.

**Beat layer (on top, partial-frame only):** `K.pulse` blooms the central
sun/polygon and the wavefront tiles; **keep it a subset (≤150 ADD, low α)** so a
kick never flips the whole frame (that trips the 0.35 strobe gate).

**Section arc (`K.section` / `K.intensity`, ~30s–5min):** scale glow-front peak
and shimmer amplitude by `intn`; rotate the palette anchor slowly with
`K.section`; let low-intensity sections read as calm baked tiling with a faint
sweep, high-intensity sections light more tiles / widen the front / speed the
spin. Never gate the *baseline* on intensity — a 0-intensity section must still
drift.

**`P.act` programs:**
- Penrose — **`inflate`** (wavefront sweeps outward over ~18s then wraps, echoing
  the deflation growth) · **`pulse`** (fully-lit tiling, beat-massed blooms) ·
  **`drift`** (oversized buffer, slow rotation + gentle sweep).
- Hyperbolic — **`spin`** (default elliptic rotation + ring) · **`bloom`**
  (repeating center→boundary geodesic glow-ring, tiling held) · **`dive`** (the
  heavy Möbius infinite-zoom, ≤50 cells, vector redraw).

---

## 6. Exemplar artists + failure modes

**Exemplars.** *Penrose/aperiodic:* **Roger Penrose** (the tiling), **M.C.
Escher** (aperiodic/impossible-tiling kinship), **Craig S. Kaplan** (tiling
theory, Islamic↔aperiodic), **Peter J. Lu** (medieval girih-as-quasicrystal),
**Marius Watz** / **Kjetil Golid** / **Jared Tarbell** (generative geometric
subdivision sensibility). *Hyperbolic:* **M.C. Escher** (*Circle Limit I–IV* —
the definitive reference), **H.S.M. Coxeter** (the maths that inspired Escher),
**Jos Leys** & **Vladimir Bulatov** (hyperbolic/Möbius ornament), **Frank
Farris** (symmetry), **Roice Nelson** (MagicTile). For the VJ palette/glow
translation of both, the **iq** cosine-palette + additive-feedback lineage. In
this repo, `genart.girih.json` and `genart.truchet.json` are the concrete
bake+glow-front precedents to imitate.

**Failure modes (and the fix):**
- **Blank / luminance out of [0.02,0.92].** Forgot to paint an **opaque** bg into
  the buffer → transparent → genart no-bed fails. Always `paintPaper()` first.
  `ink` on pure-white paper exceeds 0.92 — cap paper bri ≈ 86. `neon`/`brass` on
  pure black with a sparse front drops below 0.02 — add a faint radial vignette or
  a dim baked tiling so the mean stays ≥ 0.02. Penrose not overfilling the frame
  (tiny tiling centred in a void) → set the disk→screen scale so the tiling radius
  ≥ canvas half-diagonal (overfill factor ≥ 1.06).
- **Static (motion 0).** Relying only on beat-locked phase (re-phases at 8s) or
  baking and never animating the overlay. Fix: the `K.t` wavefront / spin floor
  above — both are continuous. Don't multiply the floor by `A.*` (audio is 0 in
  validation).
- **Strobing > 0.35.** Beat-recolouring *all* tiles, or a full-frame flash/palette
  inversion on the kick. Keep beat blooms to a **subset near the centre/front**,
  ADD alpha ≤ ~35, and never invert the whole buffer.
- **Perf.** Regenerating the deflation/BFS in `draw()` (the cardinal sin — bake
  it). Penrose depth > 6 (>2330 tiles) or hyperbolic cap > ~400; the Möbius
  `dive` uncapped (blows the 2000-vertex budget — cap ≤50 cells). Rotating a
  **full-canvas** buffer that isn't oversized → corner gaps (use the 1.45×
  oversize for `drift`, or don't rotate — spin only works corner-free for the
  hyperbolic disk which sits *inside* the frame).
- **Hyperbolic-specific.** Geodesic drawing the **outer** arc → cells bleed
  outside the disk: use the interior-midpoint guard. Non-hyperbolic {p,q}
  (`1/p+1/q ≥ 1/2`) → `rv` is NaN → clamp/bump `q` (`validQ`). Inversion blow-up
  on a diameter edge → the `|cross|<1e-6` line-reflection branch. Missing centroid
  dedup → the BFS loops forever / duplicates cells (cap + `seen` set).
- **Penrose-specific.** Omitting the `i%2` wheel mirror → a visible seam/defect
  through the sun. Hairline cracks between fills at high depth (float drift) →
  give fills a 1px same-colour stroke, or draw fills before the dark leading.
  Stroking the **base** B→C → every rhombus shows its internal diagonal (looks
  like triangles, not Penrose) — stroke legs A→B and C→A only.
```
