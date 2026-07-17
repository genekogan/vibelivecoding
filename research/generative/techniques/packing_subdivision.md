# Technique — Recursive packing / subdivision

Family: space-filling by **recursive tangency & partition** — the Apollonian
gasket (Descartes circle theorem), recursive polygon subdivision / tangram
shatter, and treemaps. All share one shape: a cheap *build* step recurses a
region into ever-smaller children until a stop rule, then a cheap *draw* step
animates the cached result.

**What already exists — do NOT rebuild it.**
- `genart.circle_packing` = greedy **relaxation** packing (random seeds, radius =
  distance to nearest neighbour). It is *not* a gasket — no mutual tangency, no
  Descartes recursion.
- `genart.subdivision` = **Mondrian** binary rect split → De Stijl mosaic, static
  cells, raking-light sweep.

**What this file authors (the open COVERAGE targets):**
1. **`apollonian`** — mutually-tangent circle gasket via the Descartes circle
   theorem (curvatures grow, radii shrink, fractal fills the disk). Distinct core
   algorithm from relaxation packing.
2. **`tangram_shatter`** — recursive **triangle** dissection that **displaces and
   reassembles** its shards. Distinct from the Mondrian rect split (triangles, not
   axis-aligned rects; the shatter/assemble dramaturgy is the whole point).

Treemap (squarified weighted rect packing) is covered here as a *variant* of the
subdivision recurrence (§1.3), not a separate asset — it lands too close to
`subdivision` to ship on its own; offer it as a `split:'treemap'` mode if wanted.

All budgets below are from `research/generative/PROBE.md`. This family spends the
**flat-shape** budget, essentially never the per-pixel-buffer budget.

---

## 1. Algorithm + math

### 1.1 Apollonian gasket — Descartes circle theorem

Work in **curvature** (signed bend) `b = ±1/r`. Sign convention: a circle that
*encloses* the others (the outer boundary) has **negative** curvature; interior
circles are **positive**.

Four mutually tangent circles satisfy the Descartes circle theorem:

```
(b1 + b2 + b3 + b4)²  =  2 (b1² + b2² + b3² + b4²)
```

Given three mutually tangent circles, solve the quadratic for the two circles
tangent to all three (one nestles into the gap, one is the enclosing circle):

```
b4  =  b1 + b2 + b3  ±  2·√(b1·b2 + b2·b3 + b3·b1)
```

To place the new circle you need its **centre**, not just its radius. Use the
**complex Descartes theorem** (Lagarias–Mallows–Wilks). Encode each centre as a
complex number `z = x + i·y` and let `w = b·z`:

```
w4  =  w1 + w2 + w3  ±  2·√(w1·w2 + w2·w3 + w3·w1)          (complex √)
z4  =  w4 / b4
```

The `±` in the centre pairs with the `±` in `b4` (`+`with`+`, `−`with`−`). Two of
the four sign combinations are the genuine Apollonian children; **validate each
candidate by an actual tangency test** and discard the spurious ones — this also
handles the "one child already exists" case for free.

**Recursion (BFS, count-capped).** Seed with an outer circle + two inner circles
that kiss at its centre. For each triple of mutually tangent circles, compute the
two Descartes candidates; for each valid, unseen candidate, add it and enqueue the
three new triples it forms with the parents. Curvature roughly doubles per
generation, so radius halves — a depth of 5–7 yields a few hundred circles before
you hit the pixel floor. **Stop rules:** `r < rMin` (pixel floor), `count ≥ Nmax`,
duplicate (rounded centre+radius already seen). This is the classic
Soddy/Shiffman construction.

### 1.2 Tangram shatter — recursive triangle dissection

Partition a polygon into children, recurse, stop on depth or min-area. For the
**triangle** flavour (the distinctive one — rects are already `subdivision`), use
**longest-edge bisection**:

```
find the longest edge (i→j); pick a split point m at fraction f∈[0.4,0.6] of it;
the two children are  △(i, m, k)  and  △(m, j, k)   where k is the third vertex.
```

Longest-edge bisection keeps triangles well-shaped (no slivers) as depth grows.
Seed the canvas as two triangles (the diagonal of the frame) and recurse each.
Occasionally stop early (10–13% chance per node) so shard sizes vary — uniform
depth reads mechanical.

Each **leaf** shard stores its vertices and **home centroid** `c`. Animation
displaces each shard from `c` and rotates it about `c`, then lerps back — a
controllable *shatter ↔ reassemble* axis (§5). Displacement of a point `p`:

```
dir = normalize(c − anchor);            anchor = (P.x·W, P.y·H)
p'  = R(θ)·(p − c) + c + dir·push       push, θ driven by the shatter amount
```

### 1.3 Treemap (variant of the subdivision recurrence)

Given weights `wᵢ ≥ 0`, tile a rect so each child's **area ∝ wᵢ** with aspect
ratios near 1 (squarified treemap, Bruls–Huizing–van Wijk): sort weights
descending; greedily add rects to the current row along the shorter side while the
worst aspect ratio improves, then lay the row and recurse on the remaining
rectangle. It's the same recurse-a-region skeleton as §1.2 with an
area-proportional split rule. Ship it only as a `split` mode of the tangram/
subdivision engine — standalone it duplicates `subdivision`.

---

## 2. p5-2D implementation (this engine)

### Cache doctrine (the #1 rule for this family)

The recursion is a **build**, not a per-frame cost. Build once into `S`, **keyed
on `width+'x'+height+'|'+seed+'|'+depthBucket`**, exactly like `circle_packing`
and `subdivision` do. Rebuilding geometry every frame is a perf sink; rebuilding
**on the beat** *strobes* (whole field jumps → trips the 0.35 motion ceiling).
Motion comes from animating the *drawing* of cached geometry, never from
re-running the recursion each frame.

**Budget spent (named against PROBE):**
- Apollonian: per-frame ≤ ~**380 flat `circle()`** — cheap. The PROBE 150-cap is
  specifically ≥¼-canvas **ADD/alpha** shapes; all but the outermost 1–3 gasket
  circles are far smaller, and most are drawn opaque `BLEND`. Neon glow pass:
  ≤ **24** `shadowBlur` circles (PROBE: fine ≤ ~30). **No** per-pixel buffer,
  **no** full-canvas `filter()`.
- Tangram: per-frame ≤ ~**160 flat filled polygons** (`beginShape`/`vertex`) —
  opaque `BLEND` fills, not heavy ADD, so comfortably under caps.

### 2.1 Apollonian — cached build (helpers hoist; call from the size-keyed guard)

```js
// complex helpers ([re,im]); function declarations hoist above the draw body.
function cadd(a,b){return [a[0]+b[0],a[1]+b[1]];}
function csub(a,b){return [a[0]-b[0],a[1]-b[1]];}
function cmul(a,b){return [a[0]*b[0]-a[1]*b[1], a[0]*b[1]+a[1]*b[0]];}
function cscl(a,s){return [a[0]*s,a[1]*s];}
function csqrt(a){const m=Math.hypot(a[0],a[1]); const re=Math.sqrt((m+a[0])/2);
  let im=Math.sqrt(Math.max(0,(m-a[0])/2)); if(a[1]<0)im=-im; return [re,im];}
// tangent(external OR internal) within tol — filters spurious Descartes combos
function tang(A,B,tol){const d=Math.hypot(A.z[0]-B.z[0],A.z[1]-B.z[1]);
  const ra=1/Math.abs(A.b), rb=1/Math.abs(B.b);
  return Math.abs(d-(ra+rb))<tol || Math.abs(d-Math.abs(ra-rb))<tol;}

function buildGasket(cx,cy,R,rMin,Nmax,fr,depth){
  const f = 0.5 + (fr(1)-0.5)*0.24;                 // seed the split → varied gaskets
  const r1=R*f, r2=R*(1-f), tol=R*0.02;
  const c0={b:-1/R, z:[cx,cy], gen:0};
  const c1={b: 1/r1, z:[cx-(R-r1),cy], gen:1};
  const c2={b: 1/r2, z:[cx+(R-r2),cy], gen:1};
  const all=[c0,c1,c2], q=[[c0,c1,c2]], seen=new Set();
  const kOf=c=>Math.round(c.z[0])+'_'+Math.round(c.z[1])+'_'+Math.round(1/Math.abs(c.b));
  let guard=0;
  while(q.length && all.length<Nmax && guard++<Nmax*5){
    const [a,b,c]=q.shift();
    const s=a.b+b.b+c.b, rt=2*Math.sqrt(Math.abs(a.b*b.b+b.b*c.b+c.b*a.b));
    const wa=cscl(a.z,a.b), wb=cscl(b.z,b.b), wc=cscl(c.z,c.b);
    const wsum=cadd(cadd(wa,wb),wc);
    const wrt=cscl(csqrt(cadd(cadd(cmul(wa,wb),cmul(wb,wc)),cmul(wc,wa))),2);
    const gg=Math.max(a.gen,b.gen,c.gen)+1;
    for(const [b4,w4] of [[s+rt,cadd(wsum,wrt)],[s-rt,csub(wsum,wrt)]]){
      if(!isFinite(b4)||b4===0) continue;
      const r=1/Math.abs(b4); if(r<rMin||r>R) continue;
      const nc={b:b4, z:cscl(w4,1/b4), gen:gg};
      const d=Math.hypot(nc.z[0]-cx,nc.z[1]-cy); if(d+r>R+tol) continue;   // inside outer
      if(!(tang(nc,a,tol)&&tang(nc,b,tol)&&tang(nc,c,tol))) continue;      // real child
      const k=kOf(nc); if(seen.has(k)) continue; seen.add(k);
      all.push(nc); q.push([a,b,nc]); q.push([a,c,nc]); q.push([b,c,nc]);
      if(gg>=depth+2 || all.length>=Nmax) break;
    }
  }
  return all;                        // [{b, z:[x,y], gen}]
}
```

### 2.2 Apollonian — live draw (P-block; reads P every frame; K.t motion floor)

```js
const D = { density:.5, energy:.6, speed:1, scale:1, hue:200, x:.5, y:.5,
            style:'ink', glow:.5, seed:0, act:'reveal' };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0,cps:.5,beat:0,bar:0,cyc:0,phase:0,pulse:0,swell:0,section:0,intensity:.6,fps:60 };
const A = window.state.audio || { bass:0,lowmid:0,mid:0,treble:0,rms:0,fft:[] };
const clp=(v,a,b)=>Math.max(a,Math.min(b,v)), TAU=Math.PI*2, md=(a,n)=>((a%n)+n)%n;
const fr=i=>{const s=Math.sin(i*127.1+P.seed*311.7)*43758.5453;return s-Math.floor(s);};
if(S.lastBeat==null||K.beat<S.lastBeat)S.lastBeat=K.beat; S.lastBeat=K.beat;   // t0-reset guard
const W=width,H=height,u=Math.min(W,H);

// ---- cached gasket: rebuild ONLY on size / seed / depth-bucket / scale-bucket ----
const depth=Math.round(3+clp(P.density,0,1)*4);            // 3..7
const R=u*0.5*clp(P.scale,0.6,1.4);
const key=W+'x'+H+'|'+P.seed+'|'+depth+'|'+Math.round(clp(P.scale,.6,1.4)*10);
if(S.key!==key){
  S.key=key;
  S.g=buildGasket(P.x*W,P.y*H,R, u*0.006, 380, fr, depth);
  let lo=1e9,hi=-1e9; for(const c of S.g){const L=Math.log(Math.abs(c.b)); if(L<lo)lo=L; if(L>hi)hi=L;}
  for(const c of S.g){ c.tp=(Math.log(Math.abs(c.b))-lo)/(hi-lo+1e-6);   // 0=biggest .. 1=tiniest
                       c.ph=fr(c.z[0]*0.7+c.z[1]*1.31+3); }
}
const G=S.g, style=P.style, hue=md(P.hue,360), en=clp(P.energy,0,1)*(.5+.7*K.intensity);

// ---- bg per style: NEVER pure black (luminance floor 0.02) ----
noStroke();
if(style==='neon'||style==='thermal') background(md(hue+200,360),40,11);
else if(style==='blueprint')          background(210,60,14);
else                                  background(38,10,90);   // ink / stained on warm paper

// ---- progressive reveal: how deep we show; drifts on K.t so it NEVER re-phases ----
const rev = (P.act==='pulse') ? 1
          : clp((0.4+0.6*(0.5+0.5*Math.sin(K.t*0.05*P.speed)))*(0.6+0.5*K.intensity),0,1);

for(let i=0;i<G.length;i++){
  const c=G[i], x=c.z[0], y=c.z[1], tp=c.tp;
  const vis=clp((rev-tp)*6,0,1); if(vis<=0.02) continue;                 // fade deeper gens in/out
  const bloom=1 + 0.08*Math.sin(K.t*0.6*P.speed + c.ph*TAU)             // K.t breathe → edges move every frame
              + (K.pulse*0.12 + A.bass*0.15)*en*(tp<0.4?1:0.3);         // beat/bass bloom on big circles
  const r=(1/Math.abs(c.b))*bloom; if(r<u*0.004) continue;
  // cosine palette in HSB channels (iq idea, HSB-native — see §4)
  const hh=md(hue + 70*Math.cos(TAU*tp*0.6) + K.t*1.5, 360);
  const ss=clp(50+38*Math.cos(TAU*(tp*0.6+0.15)),0,100);
  const bb=clp(58+34*Math.cos(TAU*(tp*0.6+0.30)),0,100);
  if(style==='ink'){        noFill(); stroke(hue,12,18,80*vis); strokeWeight(clp(r*0.06,0.6,2.4)); circle(x,y,r*2); }
  else if(style==='stained'){ noStroke(); fill(hh,ss,bb,100*vis); circle(x,y,r*2);
                              noFill(); stroke(hue,22,8,90*vis); strokeWeight(clp(r*0.07,0.8,3)); circle(x,y,r*2); }
  else if(style==='thermal'){ noStroke(); fill(hh,ss,bb,100*vis); circle(x,y,r*2); }   // form from COLOR only, no outline
  else if(style==='blueprint'){ noFill(); stroke(196,60,80,70*vis); strokeWeight(clp(r*0.04,0.6,1.6)); circle(x,y,r*2); }
  else { noStroke(); fill(hh,ss,bb*0.5,60*vis); circle(x,y,r*2); }        // neon base, glow pass below
}

// ---- neon glow: only the largest few, shadowBlur capped ≤24 (PROBE ≤~30) ----
if(style==='neon'){
  blendMode(ADD); let n=0;
  for(let i=0;i<G.length && n<24;i++){ const c=G[i]; if(c.tp>0.4) continue;
    const vis=clp((rev-c.tp)*6,0,1); if(vis<=0.05) continue;
    const r=1/Math.abs(c.b), hh=md(hue+70*Math.cos(TAU*c.tp*0.6)+K.t*1.5,360);
    drawingContext.shadowBlur=clp(r*0.5,4,26); drawingContext.shadowColor=color(hh,80,100).toString();
    noFill(); stroke(hh,70,100,(45+en*45)*vis); strokeWeight(2); circle(c.z[0],c.z[1],r*2); n++; }
  drawingContext.shadowBlur=0; blendMode(BLEND);
}
blendMode(BLEND); drawingContext.shadowBlur=0;
```

### 2.3 Tangram shatter — build + shatter draw (condensed)

```js
// --- helpers (hoist) ---
function pArea(p){let a=0;for(let i=0;i<p.length;i++){const j=(i+1)%p.length;a+=p[i][0]*p[j][1]-p[j][0]*p[i][1];}return Math.abs(a)/2;}
function pCent(p){let x=0,y=0;for(const v of p){x+=v[0];y+=v[1];}return [x/p.length,y/p.length];}
function splitTri(p,id,fr){ let bi=0,bl=-1;
  for(let i=0;i<3;i++){const j=(i+1)%3;const d=Math.hypot(p[j][0]-p[i][0],p[j][1]-p[i][1]);if(d>bl){bl=d;bi=i;}}
  const i=bi,j=(bi+1)%3,k=(bi+2)%3, f=0.4+fr(id*7.7)*0.2;
  const m=[p[i][0]+(p[j][0]-p[i][0])*f, p[i][1]+(p[j][1]-p[i][1])*f];
  return [[p[i],m,p[k]],[m,p[j],p[k]]]; }
function buildShards(W,H,depth,minA,fr){
  const out=[]; const rec=(p,dp,id)=>{
    if(dp<=0 || pArea(p)<minA || fr(id*5.9)<0.11){ out.push(p); return; }
    splitTri(p,id,fr).forEach((q,k)=>rec(q,dp-1,id*3+k+1)); };
  rec([[0,0],[W,0],[W,H]],depth,1); rec([[0,0],[W,H],[0,H]],depth,2);
  return out.slice(0,160); }                       // cap ≤160 shards

// --- P-block identical shape to §2.2 (defaults: shatter first numeric) ---
const D = { shatter:.35, energy:.6, speed:1, density:.5, hue:20, scale:1, x:.5, y:.5,
            style:'paper', gap:.25, seed:0, act:'shatter' };
/* ...P / S / K / A / clp / md / fr / lastBeat guard / W,H,u exactly as §2.2... */

const depth=Math.round(4+clp(P.density,0,1)*4);   // 4..8
const key=W+'x'+H+'|'+P.seed+'|'+depth;
if(S.key!==key){ S.key=key;
  S.sh=buildShards(W,H,depth,(u*u)*0.0012,fr).map((v,i)=>({v, c:pCent(v), rnd:fr(i*3.3+7)})); }
const SH=S.sh, hue=md(P.hue,360), en=clp(P.energy,0,1)*(.5+.7*K.intensity);
const ax=P.x*W, ay=P.y*H, maxD=u*0.30, gap=clp(P.gap,0,1)*0.06;   // grout ≤6% of shard

background(38,12,88);                              // paper bed (fill frame)
// shatter amount: continuous K.t floor + section arc + partial beat kick (keep <0.35 strobe)
let base = P.act==='assemble' ? clp(1-K.section/7,0,1)
         : P.act==='breathe'  ? 0.5+0.5*Math.sin(K.t*0.08*P.speed)
         :                      0.25+0.55*(0.5+0.5*Math.sin(K.t*0.05*P.speed));
const sh = clp((clp(P.shatter,0,1)*0.7 + base*0.5)*(0.5+0.6*K.intensity)
               + (K.pulse*0.22 + A.bass*0.28)*en, 0, 1.2);

for(let i=0;i<SH.length;i++){ const s=SH[i], c=s.c;
  const nx=c[0]-ax, ny=c[1]-ay, dl=Math.hypot(nx,ny)+1, push=sh*maxD*(0.4+s.rnd*0.9);
  const ox=nx/dl*push + Math.cos(s.rnd*TAU+K.t*0.3)*push*0.25;
  const oy=ny/dl*push + Math.sin(s.rnd*TAU+K.t*0.3)*push*0.25;
  const rot=(s.rnd-0.5)*sh*1.2 + K.t*0.05*(s.rnd-0.5);
  const hh=md(hue + (s.rnd-0.5)*46 + K.t*1.2, 360), br=clp(58+s.rnd*30,20,90);
  push(); translate(c[0]+ox,c[1]+oy); rotate(rot); translate(-c[0],-c[1]);
  if(P.style==='wire'){ noFill(); stroke(hue,20,20,70); strokeWeight(1.2); }
  else if(P.style==='facet'){ const lit=clp(70 - push/maxD*40 + 20*Math.cos(rot),15,95);   // form from light, no outline
                              noStroke(); fill(hh,clp(40+s.rnd*30,0,100),lit); }
  else { noStroke(); fill(hh,52,br); }                                                       // paper / stained flat
  beginShape(); for(const v of s.v){ const dx=v[0]-c[0],dy=v[1]-c[1],inl=1-gap/Math.max(0.001,Math.hypot(dx,dy)/(u*0.06));
                                     vertex(c[0]+dx*clp(inl,0.85,1), c[1]+dy*clp(inl,0.85,1)); } endShape(CLOSE);
  if(P.style==='stained'){ noFill(); stroke(hue,25,8,90); strokeWeight(clp(u*0.004,1,3));
    beginShape(); for(const v of s.v) vertex(v[0],v[1]); endShape(CLOSE); }
  pop(); }
blendMode(BLEND); drawingContext.shadowBlur=0;
```

---

## 3. Parameter surface

Order the first two numeric params so **both at max** produce an obvious change
(the validator pokes them together, needs > 0.003 diff). **Never put `hue`
first** (360 wraps to red ≈ 0).

### Apollonian (`density`, `energy` lead)

| param | maps to | default | min → max | notes |
|---|---|---|---|---|
| `density` | recursion depth / Nmax | .5 | 0 → 1 | 0 ⇒ depth 3 (few big circles, bg still fills); 1 ⇒ depth 7, ~380-cap. **Rebuilds** (bucketed). |
| `energy` | bloom/glow amplitude + bass response | .6 | 0 → 1 | 0 ⇒ calm rings; 1 ⇒ strong breathe + neon bloom |
| `speed` | reveal + breathe rate (beats-relative) | 1 | 0 → 3 | 0 = frozen drift is fine (K.t term tiny but nonzero) |
| `scale` | outer radius vs `min(w,h)` | 1 | 0.6 → 1.4 | 0.6 ⇒ vignette margin; 1.4 ⇒ gasket overflows frame. **Rebuilds.** |
| `hue` | palette anchor | 200 | 0 → 360 | — |
| `x`,`y` | outer centre + glow anchor + thermal light dir | .5/.5 | 0 → 1 | |
| `glow` | shadowBlur amount (neon) | .5 | 0 → 1 | caps at ≤24 shapes regardless |
| `style` | render discipline | `ink` | ink · stained · thermal · neon · blueprint | §4 |
| `seed` | gasket layout (hash) | 0 | 0 → 9999 | rebuild on change |
| `act` | dramaturgy | reveal | reveal · pulse · drift | §5 |

### Tangram shatter (`shatter`, `energy` lead)

| param | maps to | default | min → max | notes |
|---|---|---|---|---|
| `shatter` | base displacement amount | .35 | 0 → 1 | 0 ⇒ assembled mosaic; 1 ⇒ exploded (clamped to `maxD=0.30u`, never clears frame) |
| `energy` | beat-kick + hue-swim amplitude | .6 | 0 → 1 | |
| `speed` | shatter/breathe cycle rate | 1 | 0 → 3 | |
| `density` | subdivision depth / shard count | .5 | 0 → 1 | 0 ⇒ depth 4 (chunky); 1 ⇒ depth 8, ≤160-cap. **Rebuilds.** |
| `hue` | palette anchor | 20 | 0 → 360 | |
| `scale` | reserved / overall zoom | 1 | 0.5 → 1.5 | |
| `x`,`y` | shatter explosion centre + facet light dir | .5/.5 | 0 → 1 | |
| `gap` | grout width between shards | .25 | 0 → 1 | capped 6% of shard so cells never vanish |
| `style` | render discipline | `paper` | paper · stained · facet · wire · riso | §4 |
| `seed` | dissection layout | 0 | 0 → 9999 | rebuild on change |
| `act` | dramaturgy | shatter | shatter · assemble · breathe | §5 |

**Extreme-safety:** at `density=0` there are always ≥3 circles / ≥8 shards over an
opaque bed (no blank frame); at `density=1` the count caps hold fps. `shatter=1`
displacement is clamped so ≥40% of shards stay on-frame. `gap=1` grout is capped.

---

## 4. Palette / tone strategy

`colorMode` is already HSB 360/100/100/100 — **never call `colorMode`**. Drive
colour in HSB.

**HSB-native cosine ramp (the workhorse — iq's cosine-palette idea transplanted
into HSB channels).** Feed it a scalar `t` (for Apollonian, `t = c.tp`, the
normalised log-curvature = depth; for tangram, `t = shard.rnd`):

```js
const hh = md(hue + 70*Math.cos(TAU*(t*0.6      )), 360);   // hue swings ±70°
const ss = clp(50 + 38*Math.cos(TAU*(t*0.6+0.15)), 0,100);  // three phase-shifted
const bb = clp(58 + 34*Math.cos(TAU*(t*0.6+0.30)), 0,100);  // cosines → non-monotone ramp
```

Add `+ K.t*1.5` to the hue for a slow, section-spanning colour drift. Want a
*true* iq RGB cosine palette (thermal/oil-slick banding)? Convert per-fill:

```js
const rgb2hsb=(r,g,b)=>{const mx=Math.max(r,g,b),mn=Math.min(r,g,b),d=mx-mn;let h=0;
  if(d){h=mx===r?((g-b)/d)%6:mx===g?(b-r)/d+2:(r-g)/d+4;h*=60;if(h<0)h+=360;}
  return [h, mx?d/mx*100:0, mx*100];};
// iq: col(t)=a+b*cos(2π(c*t+d)), a/b/c/d are rgb triples in [0,1]
```

**Per-style discipline (each gives a divergent read; ≥1 is non-representational):**

Apollonian —
- **`ink`** (anchor, non-cartoon): near-monochrome sumi/etching — dark stroke-only
  circles on warm paper, weight ∝ radius, no fills. Austere, print-like.
- **`stained`**: leaded stained glass — saturated flat fills, dark "lead" outline
  per circle, jewel tones from the cosine ramp.
- **`thermal`** *(non-representational)*: false-colour — map log-curvature to the
  cosine ramp, **fills only, no outline**; form emerges from colour banding alone.
- **`neon`**: dark bed, ADD glow rings on the biggest circles (bass-bloom), cool→hot
  hue by depth.
- **`blueprint`**: schematic — thin cyan strokes on dark cyan, drafting look.

Tangram —
- **`paper`** (anchor): matte cut-paper collage, flat warm fills, subtle grout.
- **`stained`**: leaded glass shards — saturated fills + dark cames.
- **`facet`** *(non-representational)*: low-poly — each triangle shaded by
  displacement + rotation (light from `x/y`), **no outline**; form from light only.
- **`wire`** *(non-representational)*: X-ray wireframe — stroke-only triangles, no
  fill, blueprint/schematic.
- **`riso`**: 2-ink misregistered shards (offset MULTIPLY duplicate + halftone).

Mood range: let `hue` extremes reach desaturated / near-monochrome / dark-key —
`ink`, `blueprint`, `facet` and `wire` are deliberately not "party" looks.

---

## 5. Temporal strategy (30 s – 5 min, never re-phases)

Cached geometry ⇒ **the drawing must animate, or it reads static**. Beat-locked-
only motion re-phases at 8 s (cps 0.5 → 16 beats) and trips the motion gate; every
term below carries a **real-time `K.t` floor** so silence + a frozen beat still move.

- **Continuous floor (always on):**
  - Apollonian: the `reveal` scalar drifts on `sin(K.t·0.05)` (deeper gens fade in/
    out) **and** each circle breathes radius on `sin(K.t·0.6 + phase)` — edges
    displace every frame. Hue drifts `+K.t·1.5`.
  - Tangram: the `sh` shatter amount drifts on `sin(K.t·0.05)`; per-shard tangential
    wobble `cos(rnd·TAU + K.t·0.3)` + slow spin `K.t·0.05` — every shard moves.
- **Beat layer (on top, additive):** `K.pulse` blooms/brightens on the kick;
  `A.bass` adds glow (Apollonian) or a **partial** shatter kick (tangram). Keep the
  kick partial — a full-field jump trips the 0.35 strobe ceiling.
- **Section arcs (30 s–min scale):** `K.intensity` scales reveal depth + glow
  (Apollonian shows only shallow gens early, unfurls the full fractal in peak
  sections) and displacement (tangram sits assembled in low sections, explodes in
  high ones). `K.section` can rotate the palette anchor.
- **`P.act` programs (multi-minute dramaturgies, selectable at fire time):**
  - Apollonian: `reveal` (progressive depth unfurl) · `pulse` (fixed full depth,
    beat bloom) · `drift` (slow hue + radius breathing, no reveal gate).
  - Tangram: `shatter` (drift in/out of explosion) · `assemble` (shards converge to
    home across the show, `1−section/7`) · `breathe` (slow full in-out).

**Hard rule:** do **not** rebuild the recursion per frame or per beat. Depth/seed/
scale changes are *bucketed* and slow (section-indexed at most). Reveal/shatter are
continuous floats over a *fixed* max-depth build — smooth, never a jump-cut.

---

## 6. Exemplars + failure modes

**Exemplar artists** (`_cards/` empty at authoring — cite by name):
- **Apollonian / tangency:** René **Descartes** (the theorem) · Frederick **Soddy**
  ("The Kiss Precise", 1936 — Soddy circles) · Benoît **Mandelbrot** (fractal
  framing) · **Jos Leys** (Apollonian gasket & Kleinian-group renderings) · Daniel
  **Shiffman** (Coding Train Apollonian — the canonical p5 build) · **M.C. Escher**
  (*Circle Limit* — nested-circle, hyperbolic sensibility) for the `ink`/`blueprint`
  restraint.
- **Subdivision / shatter:** **Georg Nees** (*Schotter* — progressively displaced/
  rotated squares; the definitional shatter reference) · **Vera Molnár** (systematic
  geometric fracture & displacement — the strongest `tangram_shatter` anchor) ·
  **Frieder Nake** · **Sol LeWitt** (systematic partition) · **Piet Mondrian** /
  **Theo van Doesburg** (De Stijl — already `subdivision`'s anchor, so *diverge* from
  it) · **Ben Shneiderman** (invented the treemap) · contemporary generative:
  **Tyler Hobbs**, **Manolo Gamboa Naon**.

**Failure modes (each maps to a validation gate):**

| symptom | cause | fix |
|---|---|---|
| **Blank / near-black frame** (lum < 0.02) | forgot `background()` (genart owns bg, validated with no bed); or gasket all below `rMin`; or shatter `maxD` so large every shard left frame | always fill the bed each style; clamp `rMin` so ≥3 circles survive; clamp `maxD ≤ 0.30u` |
| **Static** (motion-diff < 0.004) | animating cached geometry that's drawn identically each frame; or beat-only motion (re-phases at 8 s) | keep the `K.t` reveal/breathe/shatter floor (§5); never rely on `K.beat` alone |
| **Strobing** (motion-diff > 0.35) | rebuilding depth/seed on the beat (whole field jumps); full-frame flash; reveal snapping between integer depths | bucket rebuilds & keep them slow; animate a *continuous* reveal/shatter float over a fixed build; partial (never full-frame) beat flash |
| **Luminance > 0.92** (white-out) | stained-glass full-sat highlights + white grout at high density | mid-key bed, cap fill brightness ≤ ~90, grout not pure white |
| **fps < 25 / jank** | rebuilding recursion every frame; > 30 `shadowBlur` shapes; uncapped circle/shard count | cache keyed on size+seed+depth (build once); `shadowBlur` ≤ 24; `Nmax` 380 circles / 160 shards |
| **params gate no-op** | first two numerics don't visibly move at max, or `hue` placed first (wraps to red) | lead with `density`+`energy` (Apollonian) / `shatter`+`energy` (tangram); verify max ⇒ obvious change |
| **Apollonian looks like random circles** | spurious Descartes sign combos not filtered ⇒ non-tangent junk | keep the `tang()` validator — accept a child only if tangent to all three parents |
