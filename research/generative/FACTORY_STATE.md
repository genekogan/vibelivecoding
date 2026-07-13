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

## LIVE PROGRESS SNAPSHOT (recompute from `ls assets/visual/genart` on resume)
**Accepted new genart (9 as of 09:55):** plasma_warp, epicycles, caustics, quasicrystal,
datascape, strange_dejong, ripple_tank, noise_contour, moire_weave. (baseline was 34 → catalog 43.)
**Requeue queue (re-author with COLOR + fuller frame):** watercolor (pale/mono). physarum,
harmonograph, pixel_sort are being re-authored in wave 2.
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
