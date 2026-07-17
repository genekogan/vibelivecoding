# Onboarding prompt — resume the generative-visuals factory

Paste the block below to a fresh agent to take over.

---

You are resuming the **generative-visuals factory** for Gene's AI live-coding VJ rig — a
long, autonomous, goal-directed job to expand the visual catalog with 100–200 NEW
full-screen **generative / textural / abstract / emergent / dynamical** p5.js-2D pieces
(fields, sims, fractals, CA, tilings, attractors, optical, painterly — NOT "an object on a
background"). A previous agent got it to **24 accepted (catalog now 58 genart)** and paused
on a usage-limit. Pick up exactly where it left off and keep going until the Phase gates are met.

**Read first, in this order (do not skip):**
1. `assets/prompts/generative-factory.md` — the master spec (operating doctrine, phases, gates, hard rules).
2. `research/generative/FACTORY_STATE.md` — **the resume runbook.** The ">>> RESUME HERE <<<" block
   at the top has the accepted list, the exact next step, hard-won patterns, and quota pacing. Read every line.
3. `research/generative/COVERAGE.md` — per-family status (✅ done / 🟡 in-inbox / 🔜 failed-re-author / ⬜ open / 🟥 hand-author).
4. `research/generative/PROBE.md` — perf budgets. `assets/CONTRACT.md` §Visual + `assets/prompts/author-brief.md` — the asset contract, P-block, validation gates.

**Verify infra is alive before anything (it may need reviving — see FACTORY_STATE):**
```bash
curl -s "localhost:8766/p5/read?key=clk"        # need t advancing, fps ~60, playing:true
curl -s localhost:8766/status                    # need __clk in tracks; if not: POST /strudel/track {"name":"__clk","code":"sound(\"bd\").gain(0.001).play()"}
ps aux | grep vf_visual_host | grep -v grep       # Playwright snapshot host writing autopilot/snapshots/latest.png
curl -s -X POST localhost:8766/show/recording -d '{"enabled":false}'
```
Server dead? `python livecode.py > /tmp/lc_server.log 2>&1 &` then the host per FACTORY_STATE.
No `__clk` metronome running ⇒ the p5 clock freezes and EVERY visual reads static (motion 0.0000).

**IMMEDIATE NEXT STEP — 8 assets are authored in `assets/visual/inbox/` awaiting review**
(apollonian, drip_paint, guilloche, lorenz, lowpoly_mesh, newton_fractal, spacefill, superformula):
```bash
python3 scratchpad/gf/gf_snap.py --outdir scratchpad/gf/_wave3 --glob 'assets/visual/inbox/*.json'
python3 scratchpad/gf/gf_sheet.py --dir scratchpad/gf/_wave3 --out scratchpad/gf/_wave3/sheet.png --cols 3
# then READ the sheet image (it's COLOR), vision-critique each, and:
python3 assets/tools/validate.py assets/visual/inbox/<good ones>.json   # PASS moves them to genart/
# append a line per asset to assets/visual/selfgrade.jsonl; delete + re-author the duds.
```

**Then run the Ralph loop until 100–200 accepted:** pick uncovered families from COVERAGE.md →
launch an author wave → review its output on-canvas → validate keepers → commit every ~10–15 → repeat.
```bash
# author wave (subagents write assets/visual/inbox/*.json; they NEVER touch the server):
# Workflow tool, scriptPath = scratchpad/gf/author_workflow.js,
#   args = JSON array of {id,name,family,recipe,kernel,style} (see scratchpad/gf/wave2.json / wave3.json for the shape).
python3 assets/tools/build_index.py visual     # rebuild index (never hand-edit index.jsonl/INDEX.md)
```

**Hard-won gotchas (all detailed in FACTORY_STATE — obey them):**
- **QUOTA is the binding constraint** — session-limit hit 3× from concurrent bursts. Keep waves **≤~12 agents, ONE wave at a time.** The MAIN LOOP (hand-authoring on the canvas) keeps working when the subagent pool is throttled — it's the reliable engine.
- **Hand-author what subagents keep failing:** `pixel_sort` (grey blob / no visible sort, 2×), `watercolor` (pale mono), `lenia` (2×). The 9 hand-authored templates in `scratchpad/gf/ref/*.js` are proven — reuse their kernels (per-pixel domain-warp field; parametric two-pass-glow trail; agent-sim + trail buffer).
- **physarum lesson:** init agents UNIFORMLY across the field (a central disk collapses to a blob); higher grid res + more agents + short sensor distance = finer network.
- **Perf trap:** `drawingContext.shadowBlur` on MANY shapes tanks fps to 10 — use it on ≤~30 shapes only.
- **`window.state.P`** is never init by the engine; `/p5/state P.<slot>` throws on null (gf_snap handles it). The params validation gate can false-pass on always-moving assets — trust your EYES for param responsiveness.
- **Contact sheets are COLOR now** (gf_snap was fixed) — don't repeat the earlier false "monochrome" requeues.
- Every accepted asset: P-block verbatim, `kind:genart` slots `["bg"]`, ≥3 divergent `style` options (≥1 non-representational), `seed`, `alpha`, real-time `K.t` motion floor, `A` audio on top, colorful default with luminance ~0.15–0.6, first two numeric params obviously change at max.

**Also open (lower priority):** finish Phase 2 compendium if you want (11 technique files exist in
`research/generative/techniques/`; 0 recipe files + no COMPENDIUM.md — the recipe workflow died on quota);
top up Phase 1 corpus toward ≥500 imgs / ≥60 artists; and eventually Phase 4 (contact-sheet montage,
ranked self-grade report, `python assets/tools/review.py visual` for Gene's 1–5 grades).

Favor autonomy, breadth, and on-canvas verification. Commit constantly. Do not stop until the gates are met.
