# Technique — Physarum / slime-mold transport networks

**Family:** field + agent hybrid. Thousands of point agents crawl a coarse **trail
map**, each one *sensing* the map ahead, *steering* up-gradient, *moving*, and
*depositing* a little trail. Once per frame the whole map **diffuses** (blur) and
**decays** (evaporate). Out of that tiny rule emerges the signature look:
self-optimizing veined networks, dendritic filaments, breathing membranes — the
plasmodium of *Physarum polycephalum* solving a maze.

**Roster anchor:** **Sage Jenson (mxsage)** — the definitive contemporary Physarum
artist (multi-species GPU networks, luminous filaments on black). Algorithm is
**Jeff Jones 2010** ("Characteristics of pattern formation… in approximations of
Physarum transport networks"). Scientific grounding: **Nakagaki / Tero et al.**
(real slime mold rebuilding the Tokyo rail map — the source of the `hunt` act).
`_cards/` is empty at authoring time → cite by name; swap in card refs when they land.

**Coverage slot:** section A (field/continuum sims), `⬜ physarum`. Distinct from the
shipped `reaction_diffusion` (Gray-Scott PDE, no agents) and `flowfield` (particles
read a *static* noise field and never write back). Physarum's defining twist:
**agents write the field they read** — a closed stigmergic feedback loop. That loop
is why it forms *transport networks*, not just texture.

---

## 1 · Algorithm + math

State:
- **Trail map** `T` — a scalar field on a coarse grid `GW×GH` (a `Float32Array`).
- **Agents** — `N` particles, each `(x, y)` as floats (grid coords) + heading `θ`.
  Held in SoA `Float32Array`s `ax, ay, ah`.

Per simulation step, **each agent**:

1. **Sense** three points a sensor-distance `SO` ahead, offset by sensor-angle `SA`:
   ```
              F = T(x + SO·cosθ,      y + SO·sinθ)          forward
      L (θ−SA) ·                                            front-left
              ·  F                    R (θ+SA)              front-right
        agent →→→ θ                   R = T(x + SO·cos(θ+SA), y + SO·sin(θ+SA))
   ```
2. **Rotate** by rotation-angle `RA` (Jones' motor rule — steer toward more trail):
   ```
   if F ≥ L and F ≥ R:   keep θ                 (straight — trail is ahead)
   elif F < L and F < R: θ += ±RA  (random)     (dead ahead is empty — pick a side)
   elif L < R:           θ += RA                 (right sensor richer → turn right)
   elif R < L:           θ -= RA                 (left  sensor richer → turn left)
   ```
3. **Move** a step `SS` along the new heading, **toroidal wrap**:
   `x += SS·cosθ ; y += SS·sinθ ; (x,y) mod (GW,GH)`.
4. **Deposit** `dep` into `T` at the new cell.

Then **once per frame, on the whole map**:

5. **Diffuse** — 3×3 mean blur (models chemical diffusion). Separable: two 3-tap
   passes. `T ← (1−k)·T + k·blur(T)` with diffuse strength `k≈0.6`.
6. **Decay** — evaporate: `T ← T · (1−decay)`.

Jones' canonical "reference network" constants (full-res): `SA=22.5°`, `RA=45°`,
`SO=9px`, `SS=1px`, `dep=5`, `decay=0.1`, 3×3 mean diffuse. We reproduce the same
*regime* on a coarse grid by expressing `SO`/`SS` in **grid cells** (§3).

**Regime intuition** (the knobs you actually feel):
- `SO`/`SA` small + `RA` small → fine parallel filaments, dense mesh.
- `SA` large → exploratory, chunky lattices.
- `RA` large → twitchy, labyrinthine curls.
- `decay` low + `dep` high → thick persistent arteries (careful: can flood to a blob).
- `decay` high → ghostly wisps that never consolidate.

The sweet spot is a **network** (connected veins with holes), not a uniform blob and
not scattered dust. Keep `SO ≥ 3` cells and `decay ≥ 0.04` and you're in it.

---

## 2 · p5-2D implementation

**Everything is CPU `Float32Array` + one `createGraphics` upscale.** No WebGL, no
shaders. This is the same shipped pattern as `genart.reaction_diffusion` (coarse grid
→ map to `buf.pixels` → `image()` upscale), which verified **63 fps**.

**Budget ledger (name what you spend):**

| Item | Spend | PROBE cap | Headroom |
|---|---|---|---|
| Trail buffer `160×90` (default) | 14.4k px/frame | per-pixel ≤ 256² = 65k | ~4.5× |
| Trail buffer `192×108` (solo ceiling) | 20.7k px | 65k | ~3× |
| Diffuse = **2 separable 3-tap passes** | ~6 reads/cell | (lighter than 3-oct warp — free) | ✓ |
| Agents (points) | 700–2000 | points ≤ 2000 | at ceiling |
| Agent substeps/frame | ≤ 3 | — | keep ≤3 |
| Render | **one** `image()` upscale | no full-canvas `filter()` | ✓ |
| Bass glow | half/full-canvas ADD, α ≤ 14 | ADD α ≤ 35, partial only | ✓ |

Default **160×90**; push to **192** solo; drop to **128–144** when stacked deep or
running two species (§Extensions). Upscale-and-smooth turns the coarse grid into an
organic *ink-bleed*; you trade Sage-Jenson filament crispness for it — an honest,
on-house-style tradeoff (RD looks great at 92 wide upscaled).

The **closed loop** (agents write the field they read) is what makes this
never-static for free — but we still add a K.t drift + respawn floor (§5) so a
quasi-settled network can't trip the 8s motion gate.

```js
// ---------- P-block ----------
const D = { energy:.6, density:.55, speed:1, scale:1, hue:150, x:.5, y:.5,
            sensor:.5, turn:.5, deposit:.5, decay:.4,
            style:'lumen', act:'wander', seed:0 };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };

const clp=(v,a,b)=>Math.max(a,Math.min(b,v)), TAU=Math.PI*2;
const hsh=i=>{const s=Math.sin(i*127.1+(P.seed|0)*311.7)*43758.5453; return s-Math.floor(s);};
if(S.lastBeat==null||K.beat<S.lastBeat)S.lastBeat=K.beat; S.lastBeat=K.beat; // tolerate t0 reset

const W=width, H=height;

// ---------- coarse trail grid + agent pool (size+seed keyed) ----------
// BUDGET: per-pixel buffer 160x90 = 14.4k px  (<< 256² = 65k cap)
const LS=160;                                                   // long side (192 solo max)
const GW=Math.max(64,Math.min(192,Math.round(LS*W/Math.max(W,H))));
const GH=Math.max(64,Math.min(192,Math.round(LS*H/Math.max(W,H))));
const NG=GW*GH, MAXA=2000;                                      // BUDGET: points ≤ 2000
if(!S.trail || S.gw!==GW || S.gh!==GH || S.seedUsed!==(P.seed|0)){
  S.gw=GW; S.gh=GH; S.seedUsed=(P.seed|0);
  S.trail=new Float32Array(NG); S.tmp=new Float32Array(NG);
  S.ax=new Float32Array(MAXA); S.ay=new Float32Array(MAXA); S.ah=new Float32Array(MAXA);
  for(let i=0;i<MAXA;i++){                                      // seed agents in a soft disc
    const r=Math.sqrt(hsh(i*2+1))*0.40, a=hsh(i*2+2)*TAU;
    S.ax[i]=(0.5+Math.cos(a)*r)*GW; S.ay[i]=(0.5+Math.sin(a)*r)*GH; S.ah[i]=hsh(i*3+7)*TAU;
  }
  if(S.buf)S.buf.remove&&S.buf.remove(); S.buf=createGraphics(GW,GH);
}
const trail=S.trail, tmp=S.tmp, ax=S.ax, ay=S.ay, ah=S.ah, buf=S.buf;
const nAg=Math.round(700 + clp(P.density,0,1)*1300);           // 700..2000 live agents

// ---------- knobs + K.t / section motion floor (never re-phases) ----------
const drift=K.t*0.03 + K.section*0.5;
const SA = (0.18+clp(P.sensor,0,1)*0.85) + 0.06*Math.sin(drift);        // sensor angle (rad)
const SO = 2.5 + clp(P.sensor,0,1)*7;                                   // sensor offset (cells)
const RA = (0.22+clp(P.turn,0,1)*0.95) + 0.05*Math.cos(drift*0.8);      // rotate angle (rad)
const SS = Math.min(SO*0.9, 0.5 + P.speed*1.0);                         // step ≤ sensor dist
let   dep = (0.6 + clp(P.deposit,0,1)*2.0) * (0.8+0.4*K.intensity);     // deposit / hit
let   decay = clp(0.02 + clp(P.decay,0,1)*0.16, 0.02, 0.20);            // evaporate / frame
const sub = Math.max(1, Math.min(3, Math.round(1 + P.speed*1.4)));      // substeps ≤ 3

// ---------- act dramaturgy (multi-minute) ----------
let foodX=-1, foodY=-1, foodOn=false;
if(P.act==='bloom'){ dep *= 1 + 0.8*Math.max(0,Math.sin(drift*0.7)); decay *= 0.9; }
else if(P.act==='hunt'){ foodOn=true;                                  // Nakagaki homage
  const fa=K.t*0.11, fr=0.30+0.12*Math.sin(K.t*0.05);                  // migrating food node
  foodX=(0.5+(P.x-0.5)*0.5+Math.cos(fa)*fr)*GW;
  foodY=(0.5+(P.y-0.5)*0.5+Math.sin(fa)*fr)*GH;
}
// wander = pure defaults; the SA/RA drift above IS the motion floor for it.

if(foodOn){                                                            // agents build veins toward food
  const rr=2;
  for(let dy=-rr;dy<=rr;dy++)for(let dx=-rr;dx<=rr;dx++){
    const x=((foodX|0)+dx+GW)%GW, y=((foodY|0)+dy+GH)%GH; trail[y*GW+x]+=dep*1.6;
  }
}

// ---------- agent update: sense → rotate → move → deposit ----------
const smp=(x,y)=>{ let xi=x|0; if(xi<0)xi+=GW; else if(xi>=GW)xi-=GW;
                   let yi=y|0; if(yi<0)yi+=GH; else if(yi>=GH)yi-=GH;
                   return trail[yi*GW+xi]; };                          // nearest, toroidal
const CAP=12.0;                                                        // anti-runaway clamp
for(let s=0;s<sub;s++){
  for(let i=0;i<nAg;i++){
    const x=ax[i], y=ay[i], th=ah[i];
    const F=smp(x+Math.cos(th)*SO,      y+Math.sin(th)*SO);
    const L=smp(x+Math.cos(th-SA)*SO,   y+Math.sin(th-SA)*SO);
    const R=smp(x+Math.cos(th+SA)*SO,   y+Math.sin(th+SA)*SO);
    let nth=th;
    if(F>=L && F>=R){}                                                 // straight
    else if(F<L && F<R){ nth += (hsh(i+((K.t*17)|0))<0.5?-1:1)*RA; }   // random (empty ahead)
    else if(L<R){ nth += RA; } else if(R<L){ nth -= RA; }             // steer up-gradient
    let nx=x+Math.cos(nth)*SS, ny=y+Math.sin(nth)*SS;
    if(nx<0)nx+=GW; else if(nx>=GW)nx-=GW;
    if(ny<0)ny+=GH; else if(ny>=GH)ny-=GH;
    ax[i]=nx; ay[i]=ny; ah[i]=nth;
    const di=(ny|0)*GW+(nx|0), nv=trail[di]+dep; trail[di]=nv>CAP?CAP:nv;
  }
}

// ---------- continuous respawn (fresh growth → guarantees motion floor) ----------
const resp=1+Math.round(A.bass*6);
for(let q=0;q<resp;q++){
  const i=(((K.t*97)|0)*7 + q*131) % nAg;
  const r=Math.sqrt(hsh(i+((K.t*3)|0)))*0.45, a=hsh(i*5+((K.t*3)|0))*TAU;
  ax[i]=(0.5+Math.cos(a)*r)*GW; ay[i]=(0.5+Math.sin(a)*r)*GH; ah[i]=hsh(i)*TAU;
}

// ---------- diffuse (separable 3-tap box blur) + decay ----------
const keep=1-decay, diff=0.6;
for(let y=0;y<GH;y++){ const row=y*GW;                                 // horizontal → tmp
  for(let x=0;x<GW;x++){ const xm=x>0?x-1:GW-1, xp=x<GW-1?x+1:0;
    tmp[row+x]=(trail[row+xm]+trail[row+x]+trail[row+xp])*0.33333; } }
for(let y=0;y<GH;y++){ const ym=(y>0?y-1:GH-1)*GW, yp=(y<GH-1?y+1:0)*GW, row=y*GW; // vertical + decay
  for(let x=0;x<GW;x++){
    const blur=(tmp[ym+x]+tmp[row+x]+tmp[yp+x])*0.33333;
    trail[row+x]=(trail[row+x]*(1-diff)+blur*diff)*keep; } }

// ---------- render trail → color → upscale (STYLE: lumen; swap the body per §4) ----------
function hsb2rgb(h,s,v){h=((h%360)+360)%360;s/=100;v/=100;const c=v*s,xx=c*(1-Math.abs((h/60)%2-1)),m=v-c;let r,g,b;const k=Math.floor(h/60)%6;if(k===0){r=c;g=xx;b=0;}else if(k===1){r=xx;g=c;b=0;}else if(k===2){r=0;g=c;b=xx;}else if(k===3){r=0;g=xx;b=c;}else if(k===4){r=xx;g=0;b=c;}else{r=c;g=0;b=xx;}return[(r+m)*255,(g+m)*255,(b+m)*255];}
const bgH=((P.hue%360)+360)%360, gain=0.8+clp(P.energy,0,1)*2.2;
buf.loadPixels(); const px=buf.pixels;
for(let i=0;i<NG;i++){
  let f=clp(trail[i]*0.14*gain,0,1); f=Math.pow(f,0.75);
  const c=hsb2rgb((bgH+f*40)%360, 95-f*55, 6+f*94);                   // lumen: dark→neon→white core
  const idx=i*4; px[idx]=c[0]; px[idx+1]=c[1]; px[idx+2]=c[2]; px[idx+3]=255;
}
buf.updatePixels();

// ---------- upscale with P.scale zoom-crop + slow drift (global motion floor) ----------
const zoom=clp(P.scale,1,2.6), sw=GW/zoom, sh=GH/zoom;
const sx=clp((GW-sw)*(0.5+0.12*Math.sin(K.t*0.02)),0,Math.max(0,GW-sw));
const sy=clp((GH-sh)*(0.5+0.10*Math.cos(K.t*0.017)),0,Math.max(0,GH-sh));
noStroke(); drawingContext.imageSmoothingEnabled=true;
image(buf,0,0,W,H,sx,sy,sw,sh);

// ---------- partial-frame bass glow (α ≤ 14 → never trips the 0.35 strobe gate) ----------
if(A.bass>0.01 || K.pulse>0.01){
  blendMode(ADD); noStroke();
  fill(bgH,70,100, clp(K.pulse*4+A.bass*10,0,14)); rect(0,0,W,H);
  blendMode(BLEND);
}
drawingContext.shadowBlur=0;
```

Correctness notes: agents are **allocated at `MAXA=2000` once** and only `nAg` are
iterated — so `density` pokes live with no realloc. Sampling is **nearest-neighbor**
(3 reads/agent, not bilinear) — Jones-standard and cheap. Step is capped `SS ≤ 0.9·SO`
so agents can't teleport past what they sensed even at `speed` max. Toroidal wrap means
agents never leave the grid (no silent blank-out).

---

## 3 · Parameter surface

Order `params` so the **first two numerics are `energy`, `density`** — the validator
pokes those two to max together and both obviously change the frame (gain 3.0 = bright
saturated cores; 2000 agents = dense mesh). Never put `hue` first (360 wraps to red≈0).

| Param | Range | Default | Maps to | Safe at both extremes? |
|---|---|---|---|---|
| `energy` | 0 – 1 | .6 | render `gain` (contrast/glow) | 0 → gain .8 (network still visible over base val 6); 1 → gain 3 (bright, but dark bg keeps mean < .92) ✓ |
| `density` | 0 – 1 | .55 | live agents 700 → 2000 | 700 still forms a network; 2000 = points ceiling ✓ |
| `speed` | .2 – 3 | 1 | `SS` + substeps + drift | .2 = slow crawl (respawn/drift still animate); 3 = fast, `SS` capped ≤ `SO`·.9 ✓ |
| `scale` | 1 – 2.6 | 1 | display zoom-crop | just a crop of the field ✓ |
| `hue` | 0 – 360 | 150 | base hue (green≈mycelial) | wraps ✓ |
| `x`,`y` | 0 – 1 | .5 | `hunt` food bias + zoom pan | ✓ |
| `sensor` | 0 – 1 | .5 | `SA` 10°→59° + `SO` 2.5→9.5 cells | low = fine parallel filaments, high = broad lattice — both are networks ✓ |
| `turn` | 0 – 1 | .5 | `RA` 13°→67° | low = smooth veins, high = labyrinthine curls ✓ |
| `deposit` | 0 – 1 | .5 | `dep` 0.6→2.6 /hit (×intensity, `CAP=12`) | faint wisps → bold arteries; clamp stops runaway ✓ |
| `decay` | 0 – 1 | .4 | evaporate .02→.18 /frame | persistent thick mesh → ghostly fast-fade ✓ |
| `style` | enum | `lumen` | color mapping (§4) | — |
| `act` | enum | `wander` | dramaturgy (§5): wander·bloom·hunt | — |
| `seed` | 0 – 9999 | 0 | initial agent layout + turn RNG | rebuild on change (keyed) |

**One soft caution** (ranges are individually safe): `deposit`≈max **and** `decay`≈min
**together** floods toward a saturated blob. It won't blank or blow luminance (the
`CAP` + coverage hold it in gamut), but it loses the network read. If you want the
default look bullet-proof, clamp their product, or nudge `decay` up when `deposit` is
high.

---

## 4 · Palette / tone — ≥3 divergent looks, ≥1 non-representational

`buf.pixels` are raw RGBA bytes, so map trail `f` (0..1) → RGB directly (the sketch's
`hsb2rgb` helper bridges HSB discipline into byte-land — never call `colorMode`).
Drop any block below in place of the **lumen** mapping loop.

**`lumen` (default, the mxsage signature) — dark-key, chromatic, bioluminescent.**
Filaments glow from the base hue and burn to a white core; background is a dim non-zero
so the frame never blacks out.
```js
const c=hsb2rgb((bgH+f*40)%360, 95-f*55, 6+f*94);   // base val 6 ⇒ mean ≥ ~.05 (clears .02)
```

**`ink` — light-key, near-monochrome, sumi mycelium on paper (inverted).**
Dark veins on warm paper. Keep paper value **≤ 88** and add grain/vignette (finishing
pass, like RD's ink mode) so the mostly-bright frame stays under the .92 luminance cap.
```js
const paper=hsb2rgb((bgH+30)%360, 10, 88), ink=Math.pow(f,0.7), tone=1-ink*0.92;
const c=[paper[0]*tone, paper[1]*tone, paper[2]*tone];
// finishing pass (outside the pixel loop): MULTIPLY a few dozen 2px grain dots + a soft vignette rect
```

**`thermal` — false-color ironbow ramp (the non-representational / data-viz look).**
Black → violet → red → orange → white. Reads as a heat/scientific scan, not a picture.
```js
const stops=[[4,2,16],[60,12,110],[170,30,60],[240,120,20],[255,240,180]];
const ff=f*(stops.length-1); let si=ff|0; if(si>=stops.length-1)si=stops.length-2; const tt=ff-si;
const a=stops[si], b=stops[si+1];
const c=[a[0]+(b[0]-a[0])*tt, a[1]+(b[1]-a[1])*tt, a[2]+(b[2]-a[2])*tt];
```

**`duotone` — riso two-ink.** Lerp one ink color ↔ a paper tint by `f`. Flat, printy.
```js
const inkC=hsb2rgb(bgH,80,70), paperC=hsb2rgb((bgH+40)%360,14,92), t=Math.pow(f,0.8);
const c=[paperC[0]+(inkC[0]-paperC[0])*t, paperC[1]+(inkC[1]-paperC[1])*t, paperC[2]+(inkC[2]-paperC[2])*t];
```

**`spectral` — iq analytic cosine palette** (Inigo Quilez `a + b·cos(2π(c·t+d))`), a 5th
option; rotate `d[0]` with `P.hue/360` or a slow `K.t` term for palette drift.
```js
const PA=[.5,.5,.5],PB=[.5,.5,.5],PC=[1,1,1],PD=[0,.33,.67], t=clp(f,0,1);
const c=[255*clp(PA[0]+PB[0]*Math.cos(TAU*(PC[0]*t+PD[0])),0,1),
         255*clp(PA[1]+PB[1]*Math.cos(TAU*(PC[1]*t+PD[1])),0,1),
         255*clp(PA[2]+PB[2]*Math.cos(TAU*(PC[2]*t+PD[2])),0,1)];
```

That's five: **lumen** (dark neon), **ink** (light mono), **thermal** (hot false-color),
**duotone** (riso), **spectral** (cosine) — spanning dark↔light, mono↔chromatic,
organic↔schematic. `thermal`/`spectral` are the non-representational data looks.

---

## 5 · Temporal strategy (30 s – 5 min)

The engine **freezes beat-locked-only motion at 8 s** (cps .5 → 16 beats re-phases →
reads static on the gate). Physarum's answer is that its motion is **intrinsic and
real-time**, never purely beat-locked:

- **K.t motion floor (the guarantee):** three continuous, non-re-phasing sources —
  (a) `SA`/`RA` sensor-drift `±0.06·sin(K.t·0.03)` so the network morphology is always
  wandering; (b) **continuous agent respawn** (`resp`/frame) injecting fresh growth;
  (c) a slow **zoom-crop drift** `sin(K.t·0.02)` sliding the whole upscaled field. Even
  a fully quasi-settled network keeps shifting — clears the 0.004 motion floor with
  margin, well under 0.35 strobe (all changes are smooth, no full-frame flips).
- **K.section / K.intensity arcs:** `dep` scales with `K.intensity` (denser, brighter in
  loud sections); `drift` includes `K.section·0.5` so morphology **steps** every 8 bars —
  the whole regime shifts (fine mesh → open lattice → thick arteries) across a set.
- **P.act programs (multi-minute dramaturgy):**
  - `wander` — steady exploration; the network perpetually reorganizes. Default.
  - `bloom` — deposit surges on a slow sine (`×(1+0.8·sin)`) + slightly lower decay →
    the network **blooms** outward then consolidates, breathing over ~40 s cycles.
  - `hunt` — a slow-migrating **food node** (`K.t`, biased by `P.x/P.y`) dumps extra
    trail; agents' chemoattraction pulls them into **transport veins** toward it, which
    they build and abandon as it moves — the Nakagaki/Tero maze-solver behavior made
    visible. The most narratively "alive" act.
- **Audio on top, never sole:** `A.bass` adds respawn bursts + the partial glow; blend
  only — during validation audio is all zeros and the K.t floor alone must carry motion.

---

## 6 · Exemplar artists + failure modes

**Exemplars** (cite by name until `_cards/` lands):
- **Sage Jenson (mxsage)** — the reference. Luminous multi-species networks; deposit/
  decay tuned for dendritic filigree; duotone & dark-neon palettes. Aim `lumen` here.
- **Jeff Jones (2010)** — the algorithm's origin; the canonical `SA/RA/SO/SS` regime.
- **Nakagaki, Tero et al.** — biological *Physarum* rebuilding the Tokyo rail network;
  the scientific soul of the `hunt` act (slime mold as computer).
- **Sebastian Lague / Softology (Jason Rampe)** — well-known implementations & parameter
  atlases; good for sanity-checking regimes.

**Failure modes (map to the exact validation gates):**
- **Blank / black frame** — `decay` overwhelms `dep` (map evaporates); agents left the
  grid (must **wrap toroidally**); trail went NaN (unclamped). Fixes: `decay ≤ .20`, keep
  the `CAP`, dim base val floor (6), seed ≥ 700 agents.
- **Static (motion ≤ 0.004)** — you locked all params and the network settled. The
  built-in `K.t` SA/RA drift + respawn + crop drift prevent this; never gate the whole
  sim behind beat-only timing (`frameCount` beat math is banned anyway).
- **Luminance out of [0.02, 0.92]** — `lumen` too sparse → near-black (raise base val or
  agent count); `ink` too empty → near-white (paper val **≤ 88** + grain + vignette,
  ensure ink coverage). RD's shipped `ink` mode is the template.
- **Strobing (> 0.35)** — no full-frame flashes/inversions on the beat; keep the ADD glow
  α ≤ ~14 and don't jump the palette hue per-frame. Field sims evolve smoothly, so this
  only breaks if you *add* a flash.
- **Blob (loses the network read)** — `deposit` max + `decay` min + `SO` too small. Keep
  `SO ≥ 3` cells, `decay ≥ .04`; consider clamping `deposit·(1−decay)`.
- **Perf** — grid > 192 long side, agents > 2000, `sub` > 3, or bilinear sampling on all
  three sensors. Stay nearest-neighbor, separable blur, single `image()` upscale, **no
  full-canvas `filter()`**. If stacked deep in an 11-layer scene, drop `LS` to 128–144.

---

## Extensions (documented, on-budget)

- **Two species (mxsage's territorial look).** Two trail buffers `TA,TB`; species-A
  agents sense `smpA(...) − rep·smpB(...)` (attract own, repel other) and deposit to
  `TA`; species B symmetric. Render `TA→hueA`, `TB→hueB` additively → membranes carve
  along the boundary. Cost: 2 buffers + 2 blur passes — fine at `LS=144–160`; drop from
  192. This is the strongest "≥1 radically different" content axis for the family.
- **Spore / agent-points render.** Instead of (or over) the field, stamp agent heads as
  ADD points: `beginShape(POINTS)` over `ax/ay` scaled to canvas, `nAg ≤ 2000` — one
  points-budget spend. Gives a living-particle shimmer riding the veins; pair with a
  faint field underneath.
- **Sensor/rotation modulated by local trail density** (Jenson) — read `F` and scale
  `RA` or `SA` by it (`RA*(0.6+0.8·f)`) so dense regions curl tighter → richer,
  self-differentiating morphology at near-zero extra cost.
