export const meta = {
  name: 'gf-author',
  description: 'Author generative visual assets into inbox/ — one subagent per family, seeded with the validated template',
  phases: [{ title: 'Author', detail: 'blind parallel authoring to assets/visual/inbox/*.json' }],
}

// args = [{id, name, family, recipe, kernel}, ...] (may arrive as a JSON string in this env)
let BATCH = args
if (typeof BATCH === 'string') { try { BATCH = JSON.parse(BATCH) } catch (e) { BATCH = [] } }
if (!Array.isArray(BATCH)) BATCH = (BATCH && BATCH.batch) || []

const RULES = `
You are authoring ONE p5.js 2D generative visual asset for a live-coding VJ engine. Output exactly ONE file: assets/visual/inbox/<id>.json. NEVER call the server/curl/HTTP — you write text only; a separate orchestrator validates on the live canvas.

READ FIRST (do it):
- assets/prompts/author-brief.md  (P-block, universal seven, style+seed mandate, EXACT validation gates)
- assets/CONTRACT.md  §"Visual contract"
- research/generative/PROBE.md  (perf budgets)
- assets/visual/genart/genart.plasma_warp.json  ← a VALIDATED, in-catalog EXAMPLE of exactly the shape/quality to match (study its code: coarse createGraphics buffer, seed hash fr(), iq cosine palette, 5 real styles, K.t drift motion floor, A audio on top, alpha param, params-order). If a research/generative/techniques/<x>.md exists for your family, read it too.

HARD REQUIREMENTS (any miss = rejected):
1. P-block preamble VERBATIM (D/P/S/K/A, the single token __SLOT__, window.state.clk). D defaults MUST equal your params defaults.
2. kind:"genart", slots:["bg"] (unless the work-order says post→["post"] or fx→["fxA","fxB"]). genart owns bg and is validated with NO bed behind → you MUST fill the whole frame, keep frame-mean luminance in [0.02,0.92] at DEFAULT params (not near-black, not near-white).
3. Real-time motion floor: derive ALL rhythm from K. Continuous K.t drift/advection/rotation that NEVER re-phases (beat-only motion re-phases at 8s → validator reads it static). Snapshots 8s apart must differ (mean-diff > 0.004) but NOT strobe (< 0.35 — no full-frame flashes/inversions).
4. style param: ≥3 genuinely divergent looks (different RENDERING PHILOSOPHY, not a hue shift), ≥1 non-representational/abstracted (wireframe/contour/blueprint/ink/thermal/halftone/x-ray). The work-order's style is the DEFAULT anchor — commit hard, make it NON-cartoon.
5. seed param {default:0,min:0,max:9999} with an inline hash (NOT p5 random()). Rebuild seed-dependent caches when P.seed changes.
6. alpha param {default:100,min:0,max:100} — default 100 (opaque). Lower alpha = translucent for VJ compositing (draw the field via tint(0,0,100,P.alpha) with no bg clear).
7. Params ORDER: the FIRST TWO numeric params must produce an OBVIOUS visual change at their max (put energy/scale/density/warp first; NEVER hue first — 360 wraps to red). Give every numeric a stretched-but-safe min/max (safe at BOTH extremes; the validator pokes to max).
8. Perf within PROBE: coarse pixels[] buffers ≤256² (prefer 128-200 wide) then image()-upscale; ≤2000 points; ≤150 heavy ADD shapes; half-canvas feedback; NO full-canvas filter(). Cache buffers in S keyed on width+'x'+height. HSB is already set — never call colorMode/createCanvas.
9. A audio (bass/mid/treble/rms/fft) blended ON TOP of the clk baseline, never the sole motion (audio is all-zero during validation).
10. Dramaturgy: use K.section (0..7) + K.intensity for a 30s-5min arc so the piece EVOLVES (not just loops) — palette drift, complexity build, behavior change across sections.
11. tags: ≥10 generous synonyms/moods/colors/categories. desc: one vivid sentence.

WORKFLOW: write the raw JS to a scratch file, syntax-check it:
  node -e 'const c=require("fs").readFileSync("<tmp>","utf8"); new Function(c.replace(/__SLOT__/g,"bg")); console.log("OK")'
then build the JSON (escape newlines) and verify it parses:
  python3 -c 'import json;json.load(open("assets/visual/inbox/<id>.json"))'
Self-review against the gates. Make it BEAUTIFUL and NOVEL — this is abstract/generative/textural art (fields, sims, fractals, CA), not "an object on a background".
`

phase('Author')
const results = await parallel(BATCH.map((w) => () =>
  agent(
`${RULES}

YOUR WORK ORDER:
- id: ${w.id}
- name: ${w.name}
- family: ${w.family}
- recipe / what to build: ${w.recipe}
- kernel/implementation hint: ${w.kernel || "choose the right p5-2D kernel (coarse pixels[] buffer, agent+trail buffer, parametric vector w/ trail, or coarse grid CA) for this family"}
- default style anchor: ${w.style || "(pick a strong non-cartoon anchor)"}

Author assets/visual/inbox/${w.id}.json now. Return one line: "${w.id}: <one-phrase description of what you built> · styles: <list>".`,
    { label: `author:${w.id}`, phase: 'Author' }
  ).then(r => String(r).slice(0, 300)).catch(e => `FAILED ${w.id}: ${String(e).slice(0,120)}`)
))

for (const r of results) log(r)
return { authored: results }
