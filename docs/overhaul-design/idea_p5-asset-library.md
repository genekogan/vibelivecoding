# The p5 Parametric Asset Library — "assets/" v1

## Design stance

One opinionated bet drives everything: **at perform time, the agent never writes rendering code — it binds assets to slots and pokes parameters.** Code generation moves 100% to practice sessions. The two primitives that make this possible already exist and are proven: atomic name-overwrite on `/p5/layer` (~10ms, gapless) and `/p5/state` as a zero-recompile parameter channel (~10ms). Everything below is conventions that make hundreds of assets safely composable through those two routes.

The nascent library at `autopilot/{creatures,worlds,floors,fx,artscenes}` (58 JSON files) is the seed but it is format-inconsistent (keys `name`/`world`/`art` vary per category), non-parametric (position/scale/palette baked into minified code), and uses two competing beat clocks. v1 supersedes it with a migration script; don't extend it in place.

## 1. Taxonomy — seven layer kinds + three data kinds

**Layer kinds** (each deploys to a canvas slot; z is fixed by slot, not by kind):

| kind | what | z-slot(s) | examples |
|---|---|---|---|
| `world` | full-bleed cached background (createGraphics buffer, drawn once) | `bg` | night_club, desert_dusk, arctic_aurora, space_nebula |
| `floor` | ground/stage plane, perspective grid or terrain | `floor` | led_grid, checkerboard, lava, ocean_surface |
| `set` | mid-ground scenery & props at stage scale | `setA`,`setB` | dj_booth, mirror_ball, city_skyline_band, campfire, palm_trees |
| `subject` | figurative hero: character/creature/vehicle, posable | `subA`,`subB`,`subC` | penguin_dj, owl, night_train, dancer_soloist |
| `crowd` | data-driven N-instance renderer (the disco_dancers pattern) | `crowd` | dancers, penguin_colony, boid_flock, traffic |
| `fx` | atmospheric overlay particles/lights | `fxA`,`fxB` | confetti, laser_fans, rain, fireflies, spotlights |
| `post` | full-screen last-pass effect | `post` | beat_flash, feedback_zoom, vignette, scanlines, shake |
| `genart` | self-sufficient full-canvas generative piece (occupies bg+floor+sub simultaneously; exclusive with world/floor) | `bg` | flowfield, voronoi_mural, reaction_diffusion, truchet |

**Data kinds** (no layer of their own; consumed at bind or practice time):

- `palette` — named HSB swatch sets (`{bg,ground,skin,accent1,accent2,glow}`), passed as P values, never baked into code.
- `choreo` — beat-indexed pose sequences (16/32-beat phrases, snap/ease timing — extracted from disco_dancers `getMove`), referenced by name in subject/crowd P (`choreo:'strut16'`).
- `kit` — shared JS renderer families (the biped rig) installed as a guarded `__kit_<name>` layer (see §4). Use sparingly: only when ≥5 assets share a rig.

This taxonomy is a formalization of what already exists — worlds/floors/fx/artscenes map 1:1, `set` and `post` are the two missing categories the recon flagged (props like the DJ booth and mirror ball are currently trapped inside monolithic scene code; strobe/wash/shake layers already behave as post but have no home).

## 2. The parametric contract — the P-block

Every asset's code opens with an identical four-line preamble plus a machine-parseable comment header. This is the whole API a performing agent needs:

```
/* P ──────────────────────────────────────────────
 * hue     210   0..360     primary hue
 * energy  0.6   0..1       motion amplitude, glow intensity
 * speed   1.0   0.25..3    animation rate (beats-relative)
 * density 0.5   0..1       element count (20..160 sparks)
 * scale   1.0   0.4..2.5   size vs design size
 * x  y    0.58 0.82  0..1  anchor, canvas fraction
 * pose    dj    dj|dance|idle|wave   pose preset
 * props   [headphones]  ⊆ {headphones,sunglasses,cap}
 * P ────────────────────────────────────────────── */
const D={hue:210,energy:.6,speed:1,density:.5,scale:1,x:.58,y:.82,pose:'dj',props:['headphones']};
const P=Object.assign({},D,(window.state.P&&window.state.P.__SLOT__)||{});
const S=window.state.__SLOT__||(window.state.__SLOT__={});
const K=window.state.clk||{beat:0,bar:0,pulse:0,section:0,intensity:.6};
```

Rules:

- **The universal seven** — `hue, energy, speed, density, scale, x, y` — MUST be honored by every asset of every kind, with the same semantics everywhere. An agent that knows these seven words can retune any of 500 assets without reading its code. Kind-specific extras (`pose`, `props`, `n`, `choreo`, `face`, `pal`) are declared in the P header.
- **Retune = one curl, no recompile:** `curl :8766/p5/state -d '{"key":"P.subA","value":{"hue":140,"energy":0.9}}'` — 10ms, auto-recorded into the timeline, survives layer-code replacement. This is how "make the penguin green and hype it up" is answered in under a second.
- **`__SLOT__` is the only template token.** Binding an asset to a slot is a single flat `code.replace('__SLOT__', slot)` — no f-strings, no brace-doubling (which the recon correctly calls untenable at scale). The deployed string is fully literal, so the reproducibility doctrine (shows are self-contained) is preserved automatically.
- The P header's fixed-column format is parsed by the index builder — **param schema is extracted from code, never hand-written**, killing the index-vs-body drift already visible in livecode-compose.md's phantom scene files.
- The validator (§6) proves each declared param actually does something: it deploys the asset, sweeps each param to its min/max, and snapshot-diffs. A param that changes nothing fails QA.

## 3. The clock — one shared beat authority

Kill both existing conventions (frameCount/28.8 is broken at any fps<60 or tempo change; per-asset millis math is duplicated). One reserved layer, `clock`, installed first in every scene, computes once per frame:

```
// layer "clock" — sole beat authority, ~0 cost
const c=window.state.cps||0.5; if(window.state.t0==null)window.state.t0=millis()/1000;
const el=millis()/1000-window.state.t0, b=el*c*4;
const sec=Math.floor(b/32)%8;
window.state.clk={beat:b, bar:b/4, cyc:(b/4)%1, pulse:Math.pow(Math.max(0,Math.sin((b%1)*Math.PI)),4),
  section:sec, intensity:[.2,.4,.7,.9,.3,.6,1,.4][sec]};
```

Assets only ever read `K` (with the safe fallback in the preamble). This makes the entire visual library tempo-portable, fps-robust, and section-aware in one stroke, and it speaks the autopilot's existing section-clock protocol (`state.cps`/`state.t0`, 8-section intensity array) so pre-built music and visual assets sync combinatorially. Pair it with the one-line server change the recon identified: `/strudel/cps` also POSTs `state.cps` (and nulls `t0` on scene transitions via the binder).

## 4. State namespacing — slot-keyed, evictable

- **Private state:** each asset instance owns exactly `window.state.<slot>` (via `__SLOT__` substitution — `S` in the preamble). No more ad-hoc `_dsp/_ep/_ff` globals. Slot names are identifier-safe (`subA`, not `50_sub`) because `/p5/state` eval-interpolates dotted keys.
- **Parameters:** `window.state.P.<slot>` — the only externally-poked namespace.
- **Shared read-only:** `state.clk`, `state.cps`, `state.t0`, `state.pal` (active palette object). Assets never write these; only the clock layer and the binder do.
- **Eviction:** on scene transition the binder sends `/p5/state {key:"<slot>", value:null}` for every rebound slot *before* posting new code; assets must self-init from undefined (the preamble's `||(window.state.__SLOT__={})` guarantees it). Cached createGraphics buffers live inside `S` keyed as `S.bg` guarded by `S.bgKey!==width+'x'+height+':v2'` — this fixes both the stale-cache bug (the journal's 'hwBg2' rename hack) and the unbounded buffer-leak the recon flagged. Deliberate cross-swap persistence (improvise.py's particle continuity) is still available: rebind the same slot *without* the eviction poke.
- **Kits:** shared renderers install as `window.LIB.<kit>` from a `__kit_<name>` layer whose body is `if(!window.LIB?.biped||window.LIB.biped.v!==3){...define...}` — per-frame cost is one guard check. Because kits are layers (not `/p5/send`, which is never recorded and never restored on reconnect), they ride the timeline and survive browser reconnects for free.

## 5. Composability — fixed slots, canonical order, scene = binding

**The slot vocabulary is fixed and small**, mirroring the music side's load-bearing drums/bass/chords collision semantics:

```
clock → [__kit_*] → bg → floor → setA → setB → subA → subB → subC → crowd → fxA → fxB → post
```

- Insertion order = z-order (livecode.html fact), and replacing an existing name keeps its position — so the binder installs missing slots in canonical order and thereafter every swap is order-safe by construction. No reorder route needed.
- **A scene is a binding manifest**, not code: `assets/scenes/<name>.scene.json` maps slots → asset ids (+ P overrides + palette). The binder (`assets/bind.py`) resolves assets, substitutes `__SLOT__`, and emits either live curls (perform mode, ~13 posts ≈ 150ms total on the single-threaded server) or `livecode-show-v1` steps (compose mode) — literal code, no library references, old shows keep playing forever.
- **Transitions are slot-diffs:** new scene rebinds only changed slots; slots absent from the new manifest get `/p5/remove` (the orphan sweep). `/p5/clear` stays banned per autopilot rules.
- **Parallel subagents partition by slot**: one owns bg+floor, one owns subjects, one owns fx+post — no collisions possible because writes are keyed by slot name, exactly like the music orbit contract.
- Kind→slot legality is enforced by the binder from asset metadata (`kind:"fx"` can only bind fxA/fxB; `genart` claims bg and forbids floor).

## 6. File format, index, retrieval

**One JSON per asset**, in-repo (durable — the /tmp scene_queue evaporation must never recur), format-versioned like the show format:

```
assets/
  worlds/ floors/ sets/ subjects/ crowds/ fx/ post/ genart/   # one .json each
  kits/ palettes/ choreo/                                      # data kinds
  scenes/*.scene.json                                          # bindings
  previews/<id>.png                                            # validator thumbnails
  inbox/                                                       # unverified new assets land here
  index.jsonl                                                  # GENERATED — never hand-edited
  build_index.py  bind.py  validate.py  migrate_autopilot.py
```

Asset doc: `{format:"livecode-asset-v1", id:"sub.penguin_dj", kind:"subject", name, desc (one sentence), tags[], params (extracted from P header), palette_slots[], cost:{fps_1080p, budget:light|med|heavy}, kit_dep, verified:{at, preview}, code}`.

**`index.jsonl` is the perform-time surface** — one grep, no 13KB source reads: each line carries `id kind budget tags blurb params path`. `grep -i penguin assets/index.jsonl` answers in milliseconds; `jq` filters by kind/budget/tag for programmatic selection. It is regenerated by `build_index.py` from the asset files (parse P headers, verify preview exists), so it cannot drift. Assets missing validation are excluded from the index — unverified work is invisible to the performing agent by construction.

**Validation harness** (practice-time, reuses autopilot_host.py): toggle `/show/recording {enabled:false}`, deploy asset solo over a neutral world at 3 params points, assert `/errors` stayed empty, fps ≥ 24, snapshot neither >90% white nor black (the whiteout lint, encoding the ADD-alpha ≤35 / on-screen-beam rules as measurements), sweep each declared param and snapshot-diff, write `previews/<id>.png` + measured cost into the asset doc. Passing assets graduate from `inbox/` to their kind directory.

## 7. Figurative requests — the penguin-DJ pipeline

Three-tier response, fastest path first:

1. **Direct hit** (target: <5s): grep index → bind a scene manifest → ~13 curls + P pokes. "Penguin DJ under a disco ball" = `bg:world.night_club + floor:floor.led_grid + setA:set.dj_booth + setB:set.mirror_ball + subA:sub.penguin{pose:'dj',props:['headphones']} + fxA:fx.laser_fans + post:post.beat_flash`. The request decomposes into slots precisely because the taxonomy was designed around how these requests actually decompose.
2. **Near miss**: closest subject + prop/pose params. Props are implemented per subject family at practice time against standardized anchor points (head/face/handL/handR) and toggled via `P.props`; poses come from the shared preset vocabulary (`idle|bob|dance|dj|wave|point|jump`) so choreography transfers across species even though skeletons differ. Do NOT build a universal skeleton — penguins aren't bipeds; standardize the *vocabulary* (pose names, 16-beat phrase structure, snap timing from disco_dancers) not the bones. Crowds get the full biped rig via `kit.biped` because humanoids genuinely share one.
3. **True miss**: the agent hand-draws one new subject — but MUST write it against the contract (P-block, `__SLOT__`, `K` clock) and drop it in `assets/inbox/`. The next practice session validates and indexes it. **Every one-off becomes a library asset**; the library grows during shows, not despite them.

## 8. Population plan (practice sessions)

- **Migrate**: `migrate_autopilot.py` wraps the 58 existing autopilot JSONs + the ~2,331 lines trapped in `compositions/scripts/*` (dancers, campfire, desert building, voronoi mural, disco fx) into v1 — parametrize position/scale/palette, convert `frameCount/28.8` to `K.beat`, extract the DJ-booth/mirror-ball/props into `set` assets. Day-one catalog: ~90 assets.
- **Generate**: parallel subagents walk `ideas.md` (~350 concepts × ~30 categories) and a subjects×poses×props grid; each output must pass `validate.py` to exist. Target 300+ assets across the first few sessions; unclaimed generative territory (reaction-diffusion, truchet, circle packing, kinetic typography, feedback buffers) fills `genart/` and `post/`.
- **Global setup**: ship a canonical `/p5/setup` string (in `assets/setup/default.js`) adding `pixelDensity(1)` — the single cheapest fps win on retina, directly protecting the ≥20fps floor that also keeps any residual frame-based motion honest.
- **Rewrite `.claude/skills/p5.md` Golden Rules** to point at the contract + index instead of prescribing the HSB-rainbow/frameCount-sine sameness — the doc currently trains the agent into the exact look the overhaul exists to escape.

EXAMPLES
### EX
ASSET — assets/subjects/penguin_dj.json (code field, abbreviated):

/* P ──────────────────────────────────────────────
 * hue     205   0..360     body hue (belly stays warm-white)
 * energy  0.6   0..1       head-bob amplitude + glow
 * speed   1.0   0.25..3    bob rate in beats
 * scale   1.0   0.4..2.5   vs design height ≈ 0.45*height
 * x  y    0.50 0.80  0..1  feet anchor
 * pose    dj    dj|dance|idle|wave
 * props   [headphones]  ⊆ {headphones,sunglasses,bowtie}
 * P ────────────────────────────────────────────── */
const D={hue:205,energy:.6,speed:1,scale:1,x:.5,y:.8,pose:'dj',props:['headphones']};
const P=Object.assign({},D,(window.state.P&&window.state.P.__SLOT__)||{});
const S=window.state.__SLOT__||(window.state.__SLOT__={});
const K=window.state.clk||{beat:0,pulse:0,section:0,intensity:.6};
const u=Math.min(width,height)/1000*P.scale, cx=width*P.x, by=height*P.y;
const bob=K.pulse*P.energy*14*u*P.speed;
push(); translate(cx, by-bob); noStroke();
fill(P.hue,55,30); ellipse(0,-90*u,120*u,150*u);          // body
fill(40,8,96);     ellipse(0,-75*u,80*u,110*u);           // belly
// head, beak, flippers (pose 'dj' = flippers on decks, scratch on bar%4==3)…
if(P.props.includes('headphones')){ stroke(0,0,15); strokeWeight(6*u); noFill(); arc(0,-150*u,64*u,50*u,PI,TWO_PI); /* cans */ }
pop();

Deploy: binder does code.replace('__SLOT__','subA') → POST /p5/layer {name:'subA', code}. Retune live: curl :8766/p5/state -d '{"key":"P.subA","value":{"hue":140,"energy":0.95,"pose":"dance"}}'  (~10ms, no recompile, auto-recorded).

### EX
INDEX — assets/index.jsonl (generated by build_index.py from P headers; the performing agent's entire discovery surface):

{"id":"sub.penguin_dj","kind":"subject","budget":"light","tags":"penguin animal dj character cute music","blurb":"Chubby penguin, beat-synced head-bob, flipper-scratch on bar 4","params":"hue energy speed scale x y pose{dj,dance,idle,wave} props{headphones,sunglasses,bowtie}","path":"assets/subjects/penguin_dj.json"}
{"id":"set.mirror_ball","kind":"set","budget":"light","tags":"disco ball mirror prop ceiling sparkle","blurb":"Hanging mirror ball, rotating facet glints + floor light spots","params":"hue energy speed scale x y spots{0..24}","path":"assets/sets/mirror_ball.json"}
{"id":"crowd.dancers","kind":"crowd","budget":"med","tags":"crowd people dancing disco biped","blurb":"N biped dancers, 16-beat choreo phrases, per-dancer palette","params":"n{1..9} energy density choreo{strut16,hustle32,idle} pal","path":"assets/crowds/dancers.json"}
{"id":"post.beat_flash","kind":"post","budget":"light","tags":"strobe flash pulse post overlay","blurb":"Full-screen additive flash on beat, ADD alpha capped 30","params":"hue energy speed every{1,2,4}","path":"assets/post/beat_flash.json"}

Retrieval under stage pressure: grep -i penguin assets/index.jsonl  → 1 line → path → bind. No 13KB source reads, no reasoning about internals.

### EX
SCENE — assets/scenes/penguin_rave.scene.json + perform-mode bind (answers 'penguin DJ under a disco ball' in ~13 posts ≈ 150ms after a one-grep lookup):

{
  "format": "livecode-scene-v1",
  "name": "penguin_rave",
  "palette": "pal.night_neon",
  "bind": {
    "bg":    "world.night_club",
    "floor": "floor.led_grid",
    "setA":  "set.dj_booth",
    "setB":  {"asset": "set.mirror_ball", "P": {"y": 0.12, "spots": 12}},
    "subA":  {"asset": "sub.penguin_dj", "P": {"x": 0.5, "scale": 1.4, "pose": "dj"}},
    "crowd": {"asset": "crowd.dancers", "P": {"n": 6, "energy": 0.8}},
    "fxA":   "fx.laser_fans",
    "post":  "post.beat_flash"
  }
}

python assets/bind.py penguin_rave            # live: evict rebound slots' state, install clock + kits if absent,
                                              # post slots in canonical order, /p5/remove orphans
python assets/bind.py penguin_rave --steps    # emit livecode-show-v1 steps: literal code, self-contained,
                                              # spliceable into shows — reproducibility doctrine intact

### EX
CLOCK + KIT — the two reserved layers every scene gets (installed by bind.py, recorded as ordinary /p5/layer steps so they restore on browser reconnect, unlike /p5/send):

// layer 'clock' — sole beat authority; replaces BOTH frameCount/28.8 and per-asset millis math
const c=window.state.cps||0.5; if(window.state.t0==null)window.state.t0=millis()/1000;
const el=millis()/1000-window.state.t0, b=el*c*4, sec=Math.floor(b/32)%8;
window.state.clk={beat:b, bar:b/4, cyc:(b/4)%1,
  pulse:Math.pow(Math.max(0,Math.sin((b%1)*Math.PI)),4),
  section:sec, intensity:[.2,.4,.7,.9,.3,.6,1,.4][sec]};

// layer '__kit_biped' — shared humanoid rig (generalized from disco_dancers.py's
// {dy,tilt,hipX,lArm,rArm,lLeg,rLeg,spin,crouch} pose interface); guard = one check/frame
if(!window.LIB) window.LIB={};
if(!window.LIB.biped || window.LIB.biped.v!==3){
  window.LIB.biped={v:3,
    draw:(x,y,sc,pose,pal)=>{ /* torso/limbs from pose angles, colors from pal */ },
    choreo:{strut16:(beat)=>({hipX:0,lArm:-.6,/*…16-beat phrase, snap timing*/}),
            hustle32:(beat)=>({/*…*/}), idle:(beat)=>({/*…*/})}};
}
// crowd.dancers then reduces to: data array of {xFrac,sc,pal} + LIB.biped.draw per instance.

RISKS
- Convention without enforcement rots: the P-block, slot vocabulary, and state namespacing are honor-system inside free-form JS. If validate.py doesn't mechanically verify them (param sweep snapshot-diffs, grep for stray window.state writes outside the slot, whiteout/fps lints), subagent-generated assets will drift within one practice session and the index becomes a catalog of lies — the exact stale-catalog failure already visible in livecode-compose.md.
- Fixed slot vocabulary may be too rigid for maximalist scenes (3 subjects + 2 sets + 2 fx caps density; genart-vs-world exclusivity blocks hybrids). Mitigation is versioned slot expansion, but every expansion touches bind.py, the validator, and every scene manifest — budget for one slot-schema revision after the first real performances.
- The clock layer is a single point of failure and a hidden dependency: every asset silently degrades to static defaults if clock is missing or state.cps was never pushed (server-side /strudel/cps→/p5/state hook is a one-line change in someone else's lens — if it doesn't land, tempo desync survives the overhaul). Also old window.state.t0/cps values leaking across scenes can make section arcs start mid-phrase unless the binder reliably nulls t0.
- Parametric retuning covers maybe 80% of stage requests; the other 20% ('make the penguin ride the mirror ball') need code surgery on deployed assets, which reintroduces live generation. If the library's pose/prop/anchor vocabulary is too coarse, performers will bypass the contract and hand-patch, and one-offs will stop flowing back through inbox/ validation.
- Scale economics of self-contained assets: at 500 assets with per-asset embedded rigs, near-duplicate code balloons (the jazz.py copy-paste problem at 10x). Leaning harder on kits fixes duplication but creates version-coupling (kit v3 breaks assets authored against v2) — the kit version guard helps but cross-version validation across hundreds of dependents is real ongoing maintenance.
- Validation throughput: snapshot-based QA (deploy, sweep params, diff, fps check) at ~30-60s per asset × 300 assets × revalidation after kit changes is hours of practice-session time on a single-threaded server with one browser — parallelizing needs multiple server+browser instances on alternate ports, which nothing in the current stack provides out of the box.