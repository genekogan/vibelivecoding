# Visual Factory — onboarding prompt

You are the **visual catalog factory** for Gene's AI live-coding system. Your
mission: massively expand the p5.js visual asset catalog under `assets/visual/`
— from ~zero to as many **verified, parametric, audio-reactive, never-static**
assets as possible in this session, using maximum subagent parallelism.

Gene performs live: he types prose ("ducks and dogs on a disco floor", "voronoi
triangles and 3d shapes") and the performing agent must find close-enough
assets by grepping the index and compose them in seconds. Your catalog is what
makes that possible. Breadth of subjects + generous tags + honest parametrics
matter more than any single masterpiece.

**Read these before anything else, in order:**
1. `assets/CONTRACT.md` — the asset contract. Every asset you produce MUST
   follow it exactly (P-block preamble, slot vocabulary, `K` clock, `A` audio,
   state namespacing, budgets, formats). This is non-negotiable: the music
   factory runs in a parallel session and both catalogs must compose blind.
2. `.claude/skills/p5.md` — p5 mechanics (layer system, state, recipes). CAUTION:
   its "Golden Rules" over-prescribe HSB-rainbow + frameCount-sine + centered
   radial looks. The mechanics are correct; the aesthetics are what we're
   escaping. NEVER use frameCount for beat math — `window.state.clk` only.
3. Skim `compositions/scripts/disco_dancers.py` — the best figurative code in
   the repo (parametric pose rigs, beat-indexed choreography). This is the
   quality bar for subjects/crowds.

## Constraints that shape everything

- **Quota window**: Gene's usage quota resets in ~2 hours with ~60% remaining.
  After Gene signs off on the plan, go to MAXIMUM parallelism immediately —
  large Workflow fan-outs of author agents. Authoring (pure text) is what burns
  quota; **validation is non-LLM and local** (it can keep running after quota
  exhausts), so front-load authoring, let validation trail behind.
- **One server, serialized validation**: subagents NEVER touch the server. They
  only write JSON files to `assets/visual/inbox/`. You (the orchestrator) run
  `assets/tools/validate.py` against the live server, serially, between/after
  authoring waves.
- **Durability**: everything in-repo. `git add assets/visual assets/prompts && git commit`
  after every validated batch (~every 20–30 assets). Never `/tmp`.

## Step 0 — environment bring-up (~5 min)

A server may already be running from setup (check first: `curl -s localhost:8766/status`).
If not:
```bash
nohup python livecode.py > /tmp/lc_server.log 2>&1 &
nohup python autopilot_host.py --interval 3 > /tmp/lc_host.log 2>&1 &
# wait for {"ready": true}
```
Then verify the v2 engine glue end-to-end (all must succeed):
```bash
curl -s -X POST localhost:8766/show/recording -d '{"enabled":false}'   # keep tests out of autosaves
curl -s "localhost:8766/p5/read?key=clk"      # beat advancing, fps ~60
curl -s localhost:8766/strudel/track -d '{"name":"t","code":"note(\"c2 e2\").s(\"sawtooth\").gain(0.25).play()"}'
sleep 3; curl -s "localhost:8766/p5/read?key=audio"   # rms > 0, bass > 0
curl -s -X POST localhost:8766/strudel/stop -d '{"name":"t"}'
```
Quick capability probe (10 min, one subagent or inline): confirm via live layers
that `createGraphics`, `drawingContext` (clip/shadow), `blendMode(ADD/MULTIPLY/SCREEN)`,
`filter(BLUR)` cost, `text()/textFont`, and `loadImage('/assets/...')` (static
file serving) behave as expected; note findings in `assets/visual/BUNDLE.md` so
author agents know what's safe.

## Phase 1 — brainstorm for sign-off (STOP after this)

Produce a numbered list of **up to 200 planned assets**, organized by kind, and
present it to Gene for curation. He will strike/add/redirect; do NOT start the
factory until he approves. Aim for this rough shape (adjust to taste):

- **subjects (~50)** — posable characters/creatures/things. Animals (penguin,
  duck, dog, cat, fox, owl, frog, octopus, dinosaur, dragon…), people (DJ,
  dancer, robot, astronaut, wizard, skeleton…), vehicles (train, UFO, bicycle,
  hot-air balloon…), celestial (moon-with-face, comet, planet), instruments
  (keytar, boombox, saxophone), furniture/objects. Every subject: `pose` param
  (≥3 poses incl. an idle + a dance/action), audio-reactive accents, generous
  species/category/mood tags.
- **crowds (~12)** — N-instance renderers: dancers, animal crowds, flocks/boids,
  traffic, bubbles-of-fish, marching band. `n`, `energy`, `pal` params.
- **worlds (~25)** — cached-buffer backgrounds across DISTINCT palette
  disciplines (not all neon): club, sunset desert, arctic aurora, deep sea,
  space nebula, jungle, rooftop city, paper-texture daylight, riso duotone
  poster, ink-wash monochrome, thermal IR, pastel dawn, brutalist concrete…
- **floors (~12)** — LED grid, checkerboard, water, lava, clouds, vinyl record,
  circuit board, ice…
- **sets/props (~20)** — DJ booth, mirror ball, speaker stacks, laser rig,
  campfire, palm trees, arcade cabinet, stage trusses, giant fan, disco sign…
- **fx (~20)** — confetti, lasers, rain, snow, fireflies, smoke, spotlights,
  fireworks, petals, embers, floating lanterns…
- **post (~15)** — beat flash, feedback zoom, chromatic aberration, vignette,
  scanlines/CRT, halftone, film grain, kaleidoscope mirror, screen shake,
  slit-scan smear, posterize…
- **genart (~35)** — the whitespace territories, one asset each with its OWN
  palette discipline: flow fields, voronoi (+ "voronoi triangles & 3d-look
  extrusion"), L-systems, reaction-diffusion (coarse offscreen grid), boids
  ecosystems, metaballs/marching squares, recursive subdivision, truchet tiles,
  circle packing, differential growth, cellular automata, strange attractors,
  wave interference/moiré, dithering, kinetic typography (several), ASCII
  render, feedback-buffer paintings, pseudo-3D wireframe/isometric/voxel
  scenes, particle physics (springs/cloth), hand-drawn wobbly line quality…
- **palettes (~10)** — named HSB swatch sets spanning the disciplines above.

Also flag in the list (Gene cares): every asset must be **never-static** (visible
evolution over 30s–5min — use `K.section`/`K.intensity` arcs, `K.t` drift, and
where it fits, an `act` param offering 2–3 multi-minute dramaturgies), and
audio-reactive **on top of a baseline** (looks intentional in silence).

## Phase 2 — the factory (after sign-off)

1. **Work orders**: turn the approved list into work-order batches. Each order:
   id, kind, subject, required params beyond the universal seven, a MANDATORY
   style constraint (palette discipline / technique — this is where variety is
   enforced), tag suggestions, budget class. Also mine `autopilot/ideas.md` for
   extra subjects Gene already liked.
2. **Harvest batch first** (cheap wins): migrate the 58 existing JSONs in
   `autopilot/{creatures,worlds,floors,fx,artscenes}/` and the big visual
   constants in `compositions/scripts/*.py` (dancers, campfire, desert building,
   voronoi mural, disco fx) into contract-compliant assets: add P-blocks,
   convert `frameCount/28.8` → `K.beat`, namespace state under `S`, parametrize
   position/scale/palette. These are stage-proven — don't lose their character.
3. **Author waves**: Workflow fan-outs, ~10–16 parallel authors, each given the
   CONTRACT authoring checklist + 3–6 work orders, each returning asset JSONs
   written to `assets/visual/inbox/`. Prompt authors to: honor the P-block
   verbatim; make params genuinely responsive (validator checks!); include at
   least one audio-reactive element; write one-sentence `desc` + ≥8 tags
   (synonyms! "duck" also tags "bird animal waterfowl quack"); respect perf
   budgets (cached buffers, particle caps).
4. **Validate + index loop** (you, serialized): `python assets/tools/validate.py --inbox visual`
   then `python assets/tools/build_index.py visual`. Failures: re-queue once
   with the failure reason attached to the work order; second failure →
   graveyard note in the work-order file, move on.
5. **Commit** every batch. Post Gene a one-line progress update every ~15 min:
   `authored N / validated M / failed F / indexed K`.
6. **Spot-compose**: every ~50 assets, assemble one full scene (world + floor +
   set + subject + crowd + fx + post) live on the canvas as a sanity check that
   slots compose and z-order/state conventions hold. Fix conventions
   immediately if not — early, not after 200 assets.

Keep authoring until quota throttles you, then keep validating/indexing (local,
free). If the session nears context limits, commit everything, write a
`assets/visual/FACTORY_STATE.md` (what's done, what's queued, conventions
learned), and tell Gene to relaunch with this same prompt — it must be
resumable from that file.

## After the run

Report: total authored/verified/failed by kind, coverage vs the approved list,
the 10 assets you think are best, known weak spots. Then tell Gene to grade:
`python assets/tools/review.py visual` (keyboard: 1–5 grade, space skip, n note,
q quit — deploys each asset live to the canvas). Grades land in
`assets/review.jsonl`; a later second pass should improve/replace assets graded
≤2, make variations of assets graded 5, and fold his notes into new work orders.

## Hard rules

- Never touch `assets/music/**` (parallel session owns it).
- Never hand-edit `index.jsonl` / `INDEX.md`.
- Never use `/tmp` for anything durable.
- Subagents never call the server; only you do, serially.
- `/show/recording` stays `false` for the whole session.
- If the browser/server dies, restart it (Step 0) — `_restore_all` re-syncs.
- Leave the server idle (no test layers/tracks) whenever you pause.
