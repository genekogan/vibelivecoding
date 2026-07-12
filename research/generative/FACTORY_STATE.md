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

## Progress log (newest first)
- 2026-07-12 01:10 — Step 0 complete: server/host/clk verified, PROBE.md written
  (machine holds 60fps even on 3-layer heavy stack), research/ scaffolding + COVERAGE.md +
  vision harness built & smoke-tested on existing genart. Launching Phase 1 research +
  Phase 2 compendium + Phase 3 authoring wave 1.

## Acceptance gates (do not stop until ALL met)
- [ ] P1 research: ≥500 corpus imgs / ≥60 artists, cards + MANIFEST committed (text).
- [ ] P2 compendium: COMPENDIUM.md + ~15–25 technique files + ~15–25 recipe files, corpus-grounded.
- [ ] P3 assets: 100–200 accepted (validate.py PASS + self-graded ≥ bar), indexed, coverage saturated, ≥3 multi-layer VJ scenes captured.
- [ ] P4: contact sheet, ranked self-grade, final report, second-pass brief.
