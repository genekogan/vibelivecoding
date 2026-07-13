# Generative Factory — resumable state

_Fresh run started 2026-07-12 ~01:10 ET. Relaunch this file's prompt
(`assets/prompts/generative-factory.md`) to resume; recompute "remaining" from disk._

## Mission
Expand the visual catalog with 100–200 NEW full-screen **generative/textural/
abstract/emergent/dynamical** pieces (mostly `kind: genart`, some `post`/`fx`) —
fields, agent sims, fractals, CA, tilings, signal/print, optical, painterly.
NOT "an object on a background." Novel vs the 34 existing genart + each other.

## Baseline (before this run)
Catalog: worlds 25, floors 15, sets 20, subjects 51, crowds 12, fx 20, post 15,
genart 34, palettes 10. **New-this-run target: +100–200 genart/post/fx.**
`new = (current count in genart/post/fx) − (34/15/20)`.

## Environment (all local, must stay alive)
| Process | What | Restart |
|---|---|---|
| `livecode.py` (:8766) | server + canvas | `python livecode.py > /tmp/lc_server.log 2>&1 &` |
| `/tmp/vf_visual_host.py --interval 3` | Playwright host → autopilot/snapshots/latest.png | babysitter |
| `__clk` strudel track | near-silent metronome UN-FREEZING the p5 clock | `curl :8766/strudel/track -d '{"name":"__clk","code":"sound(\"bd\").gain(0.001).play()"}'` |
- MUST keep `__clk` playing or every visual reads static (clk.t frozen). `/show/recording` = false.
- Music session runs a SEPARATE server on :9766 — never touch it; never `pkill -f autopilot_host.py` (kills nothing of mine; my host is `vf_visual_host.py`).

## Tooling (this run)
- `scratchpad/gf/gf_snap.py --outdir DIR ASSET...` — deploy each to canvas, capture
  t & t+8s frames + motion/lum/fps → DIR/metrics.jsonl + `<id>__a.png`/`__b.png`(+full).
- `scratchpad/gf/gf_sheet.py --dir DIR --out sheet.png [--cols N] [--ab]` — labeled contact sheet for batch vision critique.
- `assets/tools/validate.py assets/visual/inbox/<id>.json` — mechanical gate; on pass, stamps verified + moves inbox→genart/.
- `assets/tools/build_index.py visual` — rebuild index (never hand-edit).
- Vision harness and validate BOTH drive the one canvas — run them SERIALLY, never together.

## Loop (Phase 3)
1. Pick most-valuable uncovered family from COVERAGE.md.
2. Fan out blind authoring (Workflow subagents → `assets/visual/inbox/*.json`, never touch server).
3. `gf_snap` the batch → contact sheet → **vision-critique** (beauty/novelty/texture/temporal-life/palette/VJ-value 1–5) → selfgrade.jsonl.
4. Kill duds, targeted re-author for near-misses, `validate.py` the keepers.
5. Commit every ~15–20 accepted; `build_index.py visual`; update COVERAGE.md ticks + this file.

## HARD-WON INFRA LEARNINGS (read before authoring/validating)
- **QUOTA/SESSION LIMIT is the binding constraint.** Big parallel Workflow fan-outs
  (16 + 40 agents) burned ~2.5M subagent tokens in ~13min and hit the session limit
  ("resets 2:30am ET"). PACE the night: the MAIN LOOP (hand-authoring on the canvas)
  keeps working when the subagent pool is throttled → hand-authoring is the PRIMARY,
  quota-resilient engine. Retry small subagent waves opportunistically, never depend on them.
- **`window.state.P` is NEVER initialized by the engine** (only `window.state = {}`).
  `/p5/state {key:"P.<slot>"}` runs `window.state.P.<slot> = value` which THROWS on null P
  → the poke silently no-ops. FIX: run `/p5/send window.state.P = window.state.P || {}` once
  (survives /p5/clear). gf_snap.ensure_clk now does this. Style/param branches themselves work
  (verified: thermal renders red once P is init'd).
- **The params VALIDATION gate can FALSE-PASS** on any always-moving asset: it pokes the
  first 2 numerics and checks the frame changed >0.003 — but a drifting field changes >0.003
  from natural motion alone even if the poke no-ops. So VISUALLY confirm params respond;
  don't trust the gate. (My hand-authored assets read P every frame → genuinely responsive.)
- Snapshot host + server + __clk metronome all alive; clock advancing 60fps.

## >>> RESUME HERE (checkpoint 2026-07-12 ~23:30, opus-4-8 session) <<<
**82 new genart accepted (catalog 116, baseline 34).** Target +100-200 → 82/100, ~2 waves out; keep going.
Since the ~22:45 checkpoint: wave-5 reviewed (+8: gray_scott, truchet[refresh], voronoi_cells, cyclic_ca,
maze, lyapunov, rorschach-fix, sandpile-fix; dropped dup phyllotaxis; requeued dla), hand-authored chladni
(cymatics) + nbody spiral-galaxy (fixed after 2 subagent fails: TRUE circular-orbit v + short trails).
Wave-6 done (+4). Wave-7 done (+9: magnetic_pendulum STANDOUT, matrix_rain, forest_fire, iron_filings,
starfield_warp, julia_morph + feedback_tunnel/koch_flake/plasma_globe fixes ALL succeeded; dropped dup marbling).
Wave-8 done (+9: gumowski_mira STANDOUT, buddhabrot, conway_life, hopalong, ising, percolation, slit_scan,
wang_tiles, biham; requeued coulomb_lattice). Wave-9 done (+8: karman_vortex, kelvin_helmholtz, kuramoto, lissajous_grid, maurer_rose, snowflake,
string_art, coulomb-fix; hand-authored fractal_tree after subagent failed motion gate). Wave-10 IN FLIGHT
(9 new + ferrofluid fix): delaunay_flux, lichtenberg, munching_squares, celtic_knot, droste, wallpaper_group,
stipple, spirograph, kolam. Hand-authored kernels: +fractal_tree.js (incommensurate-wind motion-floor trick).
wave4-10.json. Requeue backlog: ferrofluid (in wave-10).
NOTE: check every wave asset's id vs existing catalog before validating — phyllotaxis & truchet already
existed (validate silently OVERWRITES same-id). Hand-authored kernels now in scratchpad/gf/ref/:
plasma/epicycles/caustics/noise_contour/godrays/prism/physarum/harmonograph + pixel_sort/lenia/watercolor/
chladni/nbody (13). wave batches: wave4/5/6.json.

---- (older checkpoint 22:45) ----
**42 new genart accepted (catalog 76, baseline 34).** Since the 24-checkpoint, added:
- wave-3 review: apollonian, drip_paint, lorenz, lowpoly_mesh, newton_fractal, spacefill, superformula (7).
- guilloche: hand-fixed pale->'engraved' high-contrast (was requeue), accepted.
- wave-4 (11 emergent families authored, 9 accepted): diffusion_dye, flow_ribbons, hyperbolic(STANDOUT),
  bz_spirals, curl_smoke, langton_ant, venation, wireworld + pixel_sort. Requeued: nbody, sandpile, rorschach.
- hand-authored (subagent-fail families): pixel_sort (Asendorf databend/chromatic/vhs), lenia (continuous-CA alife).
(Hand-authored kernels now: + pixel_sort.js, lenia.js in scratchpad/gf/ref/.)

**IN FLIGHT: wave-5 authoring (Workflow, 11 agents) — args=scratchpad/gf/wave5.json:**
gray_scott, dla, truchet, voronoi_cells, lyapunov, phyllotaxis, maze, cyclic_ca (8 NEW)
+ nbody, sandpile, rorschach (3 targeted FIXES with specific critique baked into the recipe).
→ When it lands: gf_snap glob inbox -> gf_sheet -> READ -> validate keepers -> requeue duds -> commit.
  (Batch gf_snap of ~11 assets takes >2min — run it BACKGROUND or in two halves; validate loop also >2min for 8.)

**Still-uncovered toward 100-200 (next waves):** watercolor(HAND-AUTHOR — subagents pale/mono), koch,
double_pendulum, plasma_globe, smoke, testcard, seven_segment, scanlines, celtic_knot, clifford/gumowski
attractors, gray-scott variants, hexlife, wave_interference, chladni, reaction spirals variants,
metaballs2, kaleido variants, halftone variants, feedback-tunnel, slitscan, ascii_rain, mandelbulb-2d-slice.

**PHASE STATUS (honest):** P1 research = partial (39 cards, 184-url manifest, 169 imgs downloaded —
below the ≥500/≥60-artist gate; corpus was throttled, not a blocker for authoring). P2 compendium =
partial (11 technique files in research/generative/techniques/; NO recipe files and NO COMPENDIUM.md
index — the recipe/compendium workflow died on the session limit; optional to finish). P3 generation =
IN PROGRESS, 24/100-200 accepted. P4 (contact sheet / ranked report / human review) = not started.

**Then keep the loop going:** launch next author wave (~12 uncovered families) via
`Workflow scriptPath=scratchpad/gf/author_workflow.js args=<[{id,name,family,recipe,kernel,style}]>`.
Still-uncovered families toward 100-200: venation, maze, rorschach, sandpile, lenia, watercolor,
pixel_sort(hand-author — subagents fail it 2x), bz/excitable-spirals(FHN, careful), curl_smoke,
langton_ant, wireworld, celtic_knot, hyperbolic, koch, nbody, double_pendulum, plasma_globe,
smoke, diffusion_dye, testcard, seven_segment, scanlines, watercolor, flow_ribbons, cyclic_ca(r=2).

**HARD-WON PATTERNS (reuse):**
- Contact sheet NOW shows COLOR (gf_snap fixed). Earlier grayscale sheets caused false 'monochrome' calls.
- Subagent hit-rate ~70-80% once judged in color. They occasionally miss: harmonograph (drew dashes),
  physarum (blob/single-vein collapse), pixel_sort (no visible sort). Hand-author those — I nailed all 3.
- physarum: init agents UNIFORMLY across field (central disk collapses to a blob); higher grid res
  (300w) + more agents (3000-9000) + short sensor dist = finer network. Mine is accepted but veins a
  bit thick — a later pass could go finer.
- Trail/curve pieces: two-pass glow (wide ADD dim + thin bright core), continuous coeff/precession
  drift on K.t so they never re-phase (motion floor). See epicycles.js / harmonograph.js.
- Perf trap: shadowBlur on MANY shapes tanks fps to 10 (warp_grid). Use it on ≤~30 shapes only.
- QUOTA: session-limit hit 3x from concurrent bursts. Keep waves ≤~12 agents; ONE wave at a time.
**Requeue/hand-author queue:** pixel_sort (2x subagent fail), watercolor (pale/mono), lenia (2x fail).
**Wave cadence that works:** author_workflow.js fans out ~10-13 agents (args = family batch,
passed as JSON — parses string). Each reads author-brief + genart.plasma_warp.json template.
~60-70% accept on-canvas; requeue the rest with specific critique (delete inbox file → re-issue
family w/ FIX recipe in next wave). Batch-review via gf_snap glob → gf_sheet contact sheet → 1 look.
**Prepped batches:** scratchpad/gf/wave2.json (running), wave3.json (12 families ready).
**Wave-1 lessons baked into author_workflow.js RULES:** default MUST be colorful (not grey),
luminance ~0.15-0.6 (several came too dark), trail pieces need continuous coeff-drift (harmonograph
went static), sim fields must not saturate (physarum flooded), effect must be edge-to-edge.
**Hand-authored templates (proven kernels):** plasma_warp (per-pixel domain-warp field),
epicycles (parametric vector + fade-trail glow), caustics + noise_contour (per-pixel field),
cyclic_ca SHELVED (needs radius-2 neighborhood for real spirals — scratchpad/gf/ref/cyclic_ca.js).
**Next actions:** when wave 2 lands → gf_snap glob + sheet → accept/requeue/validate → launch wave 3
(wave3.json) → repeat toward 100-200. Keep ONE wave always authoring so the loop self-continues.

## Progress log (newest first)
- 2026-07-12 22:45 — 42 accepted (catalog 76). Reviewed wave-3 (+7), hand-fixed guilloche, ran wave-4
  (+9 incl. hyperbolic standout), hand-authored pixel_sort + lenia. Wave-5 (8 new + 3 fixes) authoring.
  Commits 770cfe0..259d01f. Pace picking up under opus-4-8. pixel_sort took ~5 iters (Asendorf look is
  hard from synthetic source — key was decoupling hue from the sort key + row-based rainbow). lenia stable
  (homeostatic reseed prevents die-out; 108-wide grid holds 60fps at ~9.5ms/frame in node).
- 2026-07-12 09:55 — 9 accepted. Wave-2 (10 new + 3 fixes) authoring. Rhythm established.
- 2026-07-12 09:35 — Salvaged from throttled workflows: 39 artist cards, 11 technique files,
  MANIFEST.jsonl (184 image URLs / 20 artists), corpus download running. First asset
  genart.plasma_warp authored + validated + in catalog. Pivoting to main-loop hand-authoring loop.
- 2026-07-12 01:10 — Step 0 complete: server/host/clk verified, PROBE.md written
  (machine holds 60fps even on 3-layer heavy stack), research/ scaffolding + COVERAGE.md +
  vision harness built & smoke-tested on existing genart. Launching Phase 1 research +
  Phase 2 compendium + Phase 3 authoring wave 1.

## Acceptance gates (do not stop until ALL met)
- [ ] P1 research: ≥500 corpus imgs / ≥60 artists, cards + MANIFEST committed (text).
- [ ] P2 compendium: COMPENDIUM.md + ~15–25 technique files + ~15–25 recipe files, corpus-grounded.
- [ ] P3 assets: 100–200 accepted (validate.py PASS + self-graded ≥ bar), indexed, coverage saturated, ≥3 multi-layer VJ scenes captured.
- [ ] P4: contact sheet, ranked self-grade, final report, second-pass brief.
