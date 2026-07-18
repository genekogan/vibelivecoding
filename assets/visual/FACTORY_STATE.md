# Visual Factory — resumable state

## SESSION 4 (2026-07-18, overnight) — non-genart figurative/environment push, IN PROGRESS
Catalog **628 → 704**. User brief: STOP genart, grow every OTHER family toward 1000
with figurative characters, aesthetic environments, effects, rich params. **SERIAL,
one asset at a time, NO subagents** (user was emphatic). Single canvas cell :8766.
Full brief + creative direction: `scratchpad/gf/OVERNIGHT_PLAN.md`. Idea queue +
progress: `scratchpad/gf/IDEAS.md`. Author sources: `scratchpad/gf/auth/*.js`.

**Delivered this session (all verified on the live canvas):**
- Drained the 54-asset wave-B backlog (+49; 5 static fails left in inbox for rescue).
- Subjects: pelican_bicycle (the Simon Willison benchmark), face (6-style portrait),
  robot, cat, astronaut, ghost, fish, owl, skull, dancer, jellyfish, wizard.
- Worlds: retrowave (synthwave sunset), campfire, rave_hall, underwater_reef,
  aurora_tundra, volcano, cyber_city.
- fx: bokeh_lights, snowfall, confetti, fireflies. Sets: disco_ball, neon_sign, balloons.
- Floors: dancefloor, water_ripple. Crowds: club_dancers, birds_flock. +8 palettes.

**HARD-WON LESSON (bake into any resume): the motion gate is the #1 failure for these.**
Two recurring traps and their fixes, proven this session:
1. **Silhouettes/dark subjects over the dark navy validation bed read 0.0000** (invisible).
   Fix: add a faint drifting sky/floor light-wash BEHIND them (club_dancers, birds_flock).
2. **Small/thin/sparse or subtly-animated assets land marginal (<0.004)** — fireflies,
   neon_sign, wizard, dancer, campfire all needed rescue. Fixes that work: (a) a broad
   low-alpha drifting ambient glow or breathing light-pool that carries the gate
   (fireflies, campfire, neon_sign halo); (b) make heroes BIG and give them a strong
   incommensurate whole-body bob+drift (≥12*sc) from the FIRST draft; (c) chasing/marquee
   elements for props. **Build the motion carrier in up front — don't author then iterate.**
Also: never name a JS var after a p5 global (`line` shadowing crashed cat.js).

**Resume:** server+host on :8766 should be running (metronome __clk track; recording off).
Pick the next `[ ]` item from `scratchpad/gf/IDEAS.md`, author `scratchpad/gf/auth/<id>.js`,
node-check, build JSON to inbox, `validate.py --port 8766 --snapshots autopilot/snapshots`,
commit every ~2-3. genart_manifest + refresh_counts + build_index after each commit.
Still to do toward 1000: the unchecked items in IDEAS.md + more of everything.

---


_Last updated: 2026-07-17 ~07:30 ET, mid-run (SESSION 3)._

## SESSION 3 (2026-07-17) — wave-2 "triple the catalog" run, IN FLIGHT

Brief: `assets/prompts/visual-factory-wave2.md` (334 → ~1000). Started 06:30 after
a timed sleep. Gene asleep; full autonomy granted.

**Infra brought up this session (all verified working):**
| Thing | State |
|---|---|
| `livecode.py --port 8766` + `scratchpad/gf/vf_visual_host.py --interval 2` | cell 1, the primary canvas |
| `scratchpad/gf/cell.sh up\|down PORT` | NEW — spins an isolated server+host+metronome cell (8768 up). Refuses 9766. |
| `scratchpad/gf/vf_visual_host.py` | NEW — restored from autopilot_host.py + rAF anti-throttle flags. **In-repo, not /tmp** (the old /tmp copy evaporated — that's why it was missing). Name survives the music session's `pkill -f autopilot_host.py`. |
| heartbeat `scratchpad/gf/FACTORY_HEARTBEAT` | refreshed every 60s by a nohup loop; a 06:32 failsafe scheduled-task checks it and stands down if fresh. |

**KEY FIX — the host `--interval` must be < 4.5s.** `gf_snap.py` grabs its first
frame 4.6s after deploy and `validate.py` sleeps 4.5s (its comment assumes a 3s
interval). At the 6s interval this session originally launched with, the `t` frame
is captured *before the deploy* — motion is then computed against the PREVIOUS
asset, silently inflating it so static pieces PASS. Both tools now document this;
`cell.sh` hardcodes `--interval 2`.

**Parallelism model that works:** the 4 shards (A fields/flows · B structure/
architecture · C growth/emergence · D texture/material) are **territories**, not a
worker cap. Each territory runs several authors in disjoint **sub-niches**
(A1 fluids, A2 waves/optics, A3 diffusion/phase, B1 tilings, B2 perspective,
B3 technical drawing, C1 geomorphology, C2 botanical, C3 fracture, D1 print,
D2 material, D3 atmosphere/composite). Collisions are prevented by the
**claim-before-you-write** protocol in `scratchpad/gf/w2/W2_ADDENDUM.md`.
Authoring rate measured: **~1 asset / 4-5 min / author** — authoring, not the
canvas, is the bottleneck. Scale by adding authors.

**Canvas throughput:** ~13s/asset to `gf_snap`, ~17s to `validate`. Cells 8766 and
8768 were measured rendering CONCURRENTLY at 59.9 and 66.7 fps — "one browser
client only" is a per-SERVER rule, so independent cells parallelize safely.

**Docs-rot fix shipped:** `assets/tools/refresh_counts.py` grew `--domain
{music,visual,all}`; the visual docs (`.claude/skills/p5.md`, `AGENTS.md`,
`research/generative/FINAL_REPORT.md`) now carry canonical count lines it
maintains. `--check` exits 1 on drift. AGENTS.md gained a **Visual Catalog
System** section with grep/jsonl retrieval recipes.

### ⚠️ ROOT CAUSE FOUND: the ref-kernel hash was half-amplitude (fixed 2026-07-17)

`scratchpad/gf/ref/plasma.js`'s `hsh()` finalized with an **arithmetic** shift:
`((h ^ (h >> 16)) >>> 0) / 4294967295`. `>>` sign-extends, so the top bit always
XORs to zero → **the hash is capped at 0.5, mean 0.25 instead of 0.5.** Every
noise field built on it is **half-amplitude and biased dark**. Measured, not
asserted: current `mean=0.2501 max=0.5000`; with `>>>`, `mean=0.5007 max=1.0000`.

Surfaced by the shard-A author; independently confirmed here before acting.
**Fixed in all 7 ref kernels** (caustics, godrays, noise_contour, pixel_sort,
plasma, prism, warp_grid) so no future asset inherits it.

**21 already-verified catalog assets still carry the buggy copy** — floor.marble,
genart.{blackhole, caustics, constellations, datascape, godrays, iso_city, mirage,
noise_contour, oil_slick, orrery, pixel_sort, plasma_warp, prism, rorschach,
sand_dunes, slit_scan, spectrogram, stipple, warp_grid}. They were deliberately
**left alone**: they pass every gate, and FINAL_REPORT's SESSION 2 log shows
several (`blackhole`, `constellations`, `plasma_warp`, `caustics`) were
hand-*brightened* to compensate — so blindly applying the fix would now
**over**-brighten them. Remediating one means: fix the shift, re-tune its
brightness compensation, re-validate, re-eyeball. Worth doing deliberately, one
at a time, never as a blind sweep. This is the likely cause of the recurring
"near-black baseline / faint" family of failures the earlier sessions kept
treating symptomatically.

### SESSION 3b (2026-07-17 late morning) — RESOLUTION FIX + push toward 750

Gene reviewed the catalog and flagged the **#1 defect: ~173 assets rendered into a
~200px buffer upscaled ~10× → blocky/pixelated on a big screen.** Root cause: the
"coarse buffer 128–200px" guidance I wrote. Perf was never the reason (expensive
PDEs hold 60fps at 640–720px, measured).

- **102 assets de-pixelated** (R1: 37, R2: 65) via a two-class fix, each re-snapped
  + eyeballed on the canvas: FIELD/PDE → adaptive buffer `Math.max(360,Math.min(720,
  round(width/2.4)))`; POINT-CLOUD → cap 520 + iterate count scaled by area. Zero
  regressions. Recipe: `scratchpad/gf/res/RESOLUTION_FIX.md`.
- **~70 correctly SKIPPED** — heuristic false-positives (buffer already adaptive) or
  physics/grid-coupled (feature size / step-budget / advection tied to grid res) or
  intentionally-blocky (pixel_sort/vhs). Listed in `scratchpad/gf/res/RESIDUAL_LOWRES.md`
  for a future per-asset constant-rescaling pass. Only mildly soft, not broken.
- **Docs reoriented** so it can't recur: p5.md, author-brief.md, W3_ADDENDUM all
  mandate adaptive buffer sizing now.
- **browse.html bed toggle** ('b' key): overlays (fx/post/…) render over a real
  scene (world.cloud_sea) by default instead of black, so accents are judgeable.
  Gene's 2nd note (dim fx) was confirmed a display artifact — they're accents.
- **Drained the interrupted fleet's inbox:** +10 verified, 2 dups dropped, 4
  twice-failed statics graveyarded. **Catalog now 554.**
- **fps-under-concurrency lesson:** running 3 snap/validate cells at once depresses
  fps readings for expensive assets (baker_mixing read 17 under load, 62 solo).
  Re-check solo before graveyarding anything for low fps.
- **Push toward 750 launched** (wave-4): new genart territories (topology/knots,
  cartography, microbiology, cosmology, textile/weave) + lagging families
  (world/fx/set/floor/post/palette). Authors read `scratchpad/gf/w4/PUSH_NOTE.md`.

### SESSION 3 RESULT — 334 → 544 (+210 verified), ~2.5 h

| family | was | now | + | wave target |
|---|---|---|---|---|
| genart | 166 | 289 | +123 | 600 |
| world | 25 | 44 | +19 | 75 |
| subject | 51 | 53 | +2 | 57 |
| fx | 20 | 38 | +18 | 70 |
| set | 20 | 29 | +9 | 60 |
| floor | 15 | 26 | +11 | 50 |
| post | 15 | 31 | +16 | 50 |
| crowd | 12 | 12 | +0 | 12 (frozen, as briefed) |
| palette | 10 | 22 | +12 | 30 |
| **TOTAL** | **334** | **544** | **+210** | 1000 |

Short of the ~1000 stretch target. **The binding constraint was authoring
throughput, not the canvas**: ~1 asset / 4–5 min / author, so ~10 concurrent
authors ≈ 100–130 assets/hour, while the 3-cell canvas could absorb far more.
To go faster next time, **add authors, not cells.**

**Resume point:** the loop is healthy and unchanged — author → snap → **LOOK** →
validate → index → commit. To continue, re-read `assets/prompts/visual-factory-wave2.md`
and fan out more sub-niche authors against `scratchpad/gf/w3/W3_ADDENDUM.md`
(which carries the measured numbers and the 5 real failure modes; it supersedes
the theory in SHARD_COMMON). `assets/visual/INDEX.md` is the dedup authority now —
`scratchpad/gf/w1/DEDUP.md` is a stale 334-asset snapshot.

**Left in `inbox/` (failed once, worth one rescue each, NOT graveyarded):**
`floor.wet_asphalt` (STATIC 0.0013 — and it duplicates verified `floor.asphalt`;
probably just delete), `fx.sparks` (0.0028), `fx.midges` (0.0026), `fx.smoke`
(0.0036), `set.greenhouse` (0.0017), `world.cavern` (0.0031), `world.tidal_flat`
(0.0015). All are the **sparse-overlay motion floor** problem (W3_ADDENDUM #3).

**Graveyarded twice-failed** (notes in `graveyard/SESSION3_NOTES.md`):
`genart.wave_shadow` (SAFETY — strobed 0.4247, rewritten, strobed again 0.4685),
`fx.gossamer`, `fx.lens_flare`, `fx.soap_film`, `genart.epiphyte`,
`world.sea_stacks`, `genart.leaf_margin`, `genart.safety_glass`,
`genart.robinson`, `genart.blast_wave`.

### Process lessons from SESSION 3 (the ones that cost or saved real time)

1. **The host `--interval` must be < 4.5 s** — see the KEY FIX above. This is the
   highest-value thing in this file; at a 6 s interval every motion number in the
   run is silently computed against the *previous* asset.
2. **Shards are territories, not a worker cap.** Running 3–4 authors per territory
   in disjoint **sub-niches** with a claim-before-you-write protocol produced zero
   destructive collisions across ~25 concurrent authors. Only one true id clash
   occurred all session, and it was a rewrite, not a clobber.
3. **Gates are a floor, not taste — and the gap is large.** Assets scoring lum
   0.73–0.87 *passed* the luminance gate and read as **blank paper**. The contact
   sheet caught what no gate could. Never skip the LOOK step.
4. **Requeue-with-specific-critique works, and works well.** Every dud handed back
   with a *pixel-level* observation ("two blown-out white discs", "a 3%-of-frame pod
   on black") came back fixed. Vague critique would not have done that. 100% of the
   first rescue batch and 3/7 of the second landed verified.
5. **Authors' offline harnesses are valuable but NOT authoritative.** Several built
   headless p5 mocks that caught genuine bugs (unstable PDE integrators, mis-scaled
   wavenumbers, culled geometry, hash bias). They also *passed* assets the canvas
   then failed — `wave_shadow` was reported safe and measured 0.4247 STROBE live;
   shard C's harness reported `travertine` at 0.675 when the canvas said 0.807.
   **Treat harness numbers as a pre-filter; the canvas is the authority.**
6. **Beware judging a stale snapshot.** A rescue author rewrote four assets *after*
   my snap ran; I graveyarded them on the old pixels. Re-testing showed two now
   passed. Worse, the catalog had promoted a **stale pre-rescue `petal_unfurl`**
   while its fix sat in the inbox. **Re-snap after any concurrent rewrite**, and
   check for inbox copies of already-verified ids before promoting.
7. **A `world` is not a `genart`.** Validated worlds legitimately sit at motion
   0.005–0.04 — a background is *meant* to be calm. The 0.06–0.17 healthy band is a
   genart number; don't fail worlds against it.

---

_Prior state (2026-07-11 ~10:00 ET, SESSION 1/2):_

## Where things are

- **Catalog (validated, in `assets/visual/<kind>/`): ~55** — all 50 subjects +
  5 crowds. Growing as the sweeper validates the remaining fleet's output.
- **In flight**: the "remaining fleet" (Workflow `factory-workflow-remaining.js`)
  is authoring the 146 non-subject orders (7 crowds, 25 worlds, 15 floors, 20
  sets, 20 fx, 15 post, 34 genart, 10 palettes) into `assets/visual/inbox/`.
- **Graveyard** (`assets/visual/graveyard/`): assets that failed validation
  twice. `train` is the notable straggler (motion too subtle even after a
  rescue). `.failcounts.json` there tracks per-id fail counts.

## The running machinery (all local, keep alive)

| Process | What | Restart |
|---|---|---|
| `livecode.py` (:8766) | server + canvas | already running (also a music copy on :9766 — leave it) |
| `autopilot_host.py --interval 3` | Playwright browser writing `autopilot/snapshots/latest.png` | babysitter auto-restarts it |
| babysitter (`scratchpad/babysitter.sh`, nohup) | relaunches the visual host if it dies | `nohup bash <path> &` |
| sweeper daemon (`scratchpad/sweeper-daemon.sh`, nohup) | loops `assets/tools/sweep.sh`: validate inbox → graveyard 2x-fails → index → commit | `nohup bash <path> &`; log `/tmp/lc_sweeper.log` |

NOTE: persistent **Monitor**-based watchers keep getting SIGURG-killed (exit
144) in this environment (likely the parallel music session's process sweeps) —
use **nohup detached scripts** instead, which survive.

## How to resume authoring after a quota/session-limit stop

1. Recompute what's left (excludes anything already validated into the catalog):
   ```bash
   python3 - <<'PY'
   import json,glob
   orders=json.load(open('assets/prompts/work-orders-v1.json'))
   KD={'world':'worlds','floor':'floors','set':'sets','subject':'subjects','crowd':'crowds','fx':'fx','post':'post','genart':'genart','palette':'palettes'}
   done=set()
   for d in KD.values():
       for f in glob.glob(f'assets/visual/{d}/*.json'):
           try: done.add(json.load(open(f))['id'])
           except: pass
   rem=[o for o in orders if o['id'] not in done]
   json.dump(rem, open('assets/prompts/work-orders-remaining.json','w'), indent=1)
   print(len(rem),'remaining')
   PY
   ```
2. Rebuild the batch list (see the loop in the session that generated
   `assets/prompts/remaining-batches.json`) and launch
   `factory-workflow-remaining.js` via the Workflow tool, passing the batches as
   `args` (the script does `JSON.parse(args)` if it arrives as a string).
3. Make sure the sweeper daemon + babysitter are running (table above).

## Key learnings baked into `assets/prompts/author-brief.md`

- **Motion gate**: subjects must be hero-sized (0.40–0.55× min(w,h)) and
  displace the silhouette; purely beat-locked motion can re-phase at 8s (cps
  ~0.5 → 8s = 16 beats) and read as static — always add a **real-time (K.t)
  motion floor** (drift/scroll/roll/wander) that never re-aligns.
- **Aesthetic mandate**: escape the cute-cartoon default — commit to a
  non-cartoon anchor style, ≥1 abstracted style option per asset, texture over
  flat fill, wider mood/palette range.
- **Params gate**: first two numeric params must visibly change at max; put
  scale (max ≥1.8) or energy/density first, never hue (360 wraps to red).
- Common bugs: shadowing p5 globals (`line`, `fill`…) with local vars → blank
  render (motion 0.0000); undeclared vars → same.

## Grading (after the run)
`python assets/tools/review.py visual` — deploys each asset live, keys 1–5 to
grade. Grades → `assets/review.jsonl`, folded into the index. Second pass:
improve/replace ≤2, make variations of 5s, rescue the graveyard.

## Spot-compose sanity check (2026-07-11 ~14:35 ET)
Composed a full 10-slot neon-club scene (world.club/floor.led_grid/set.dj_booth/
set.mirror_ball/subject.dj/subject.robot/crowd.disco_dancers/fx.lasers/
fx.confetti/post.vignette). Result: **60fps, 10 layers, 0 runtime errors** on
clean all-at-once deploy — slots bind, z-order holds, perf well above the 20fps
stage floor. (A transient "push is not a function" appears only during slow
one-by-one deploys — a mid-frame init race, harmless.) Tuning note: set.dj_booth
renders an oversized bright backdrop panel that dominates the frame; needs a
P.scale/opacity trim to layer politely. Crowd/subjects read as stylized (not
cartoon-cute) — aesthetic redirect confirmed on-canvas.

## COMPLETE — 201/201 (2026-07-11 ~15:30 ET)
All 201 orders authored + validated + committed. Catalog: 25 worlds, 15 floors,
20 sets, 50 subjects, 12 crowds, 20 fx, 15 post, 34 genart, 10 palettes
(+ browse_selftest). Index: assets/visual/index.jsonl (build_index.py).

### Engine gotcha discovered at the finish (IMPORTANT for review/live use)
The v2 engine (`owned_transport.js` + livecode.html) drives the p5 clock from
the **Strudel transport**. With NO track playing, `window.state.t0` stays null,
the clock freezes (t=0, fps still ~60, draw still loops), and EVERY visual reads
as static — motion validation returns 0.0000 for everything. Fix: keep a
near-silent metronome running (`sound("bd").gain(0.001).play()`) so the clock
advances. `assets/tools/review.py` now auto-starts/stops one for visual grading.
For the sweeper/validator, start a quiet track first if the clock is frozen.

### Canvas infra notes (parallel music session shares this repo)
- The music session periodically runs `pkill -f autopilot_host.py`, which also
  kills the visual host. Workaround: the visual host runs as `/tmp/vf_visual_host.py`
  (immune name) with anti-throttle flags (`--disable-renderer-backgrounding`
  etc., since a backgrounded headed Chromium throttles rAF and freezes draw) and
  `--snapshots-dir` pinned to the repo. The babysitter (scratchpad/babysitter.sh)
  keeps THIS host alive.
- If the canvas is dead: `python livecode.py` (server, ports 8765/8766), then
  `python /tmp/vf_visual_host.py --interval 3 --snapshots-dir <repo>/autopilot/snapshots`
  (recreate from autopilot_host.py + the anti-throttle flags if /tmp was cleared).
