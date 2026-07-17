export const meta = {
  name: 'visual-asset-rescue',
  description: 'Re-author the 21 assets that failed validation twice, fixing their exact failure',
  phases: [ { title: 'Rescue', detail: 'targeted re-author of graveyard assets' } ],
}

const batches = typeof args === 'string' ? JSON.parse(args) : args
log(`rescue: ${batches.length} batches over assets/prompts/rescue-orders.json`)

const RESULT_SCHEMA = {
  type: 'object',
  properties: {
    assets: { type:'array', items:{ type:'object', properties:{
      id:{type:'string'}, fix:{type:'string', description:'the exact fix applied for the recorded failure'}
    }, required:['id','fix'] } },
    problems: { type:'string' },
  },
  required: ['assets'],
}

const prompt = (b) => `You are a VISUAL ASSET RESCUE author for Gene's livecode catalog. Working dir: /Users/gene/Dev/livecode.

These assets were authored, deployed to the live validation canvas, and FAILED the mechanical gate TWICE. Your job: re-author each so it PASSES, fixing its exact recorded failure. Overwrite the file in assets/visual/inbox/<id>.json.

## READ FIRST
- assets/prompts/author-brief.md (full spec + gates + DESIGN-SIZE rules + AESTHETIC MANDATE + the real-time-motion-floor lesson)
- The current (failing) code is in assets/visual/graveyard/<id>.json — READ IT to see what's there, then fix or rewrite.

## YOUR ORDERS — indices ${b[0]}..${b[1]-1} of assets/prompts/rescue-orders.json (each has a "FAILURE" field with the exact gate + measurement):
  python3 -c "import json; print(json.dumps(json.load(open('assets/prompts/rescue-orders.json'))[${b[0]}:${b[1]}], indent=1))"

## REMEDY PLAYBOOK — apply the one(s) matching each order's FAILURE string:

FAILURE "motion: static: diff 0.00XX <= 0.004"  (too subtle — snapshots 8s apart nearly identical):
  - THE #1 CAUSE is beat-locked motion re-phasing: at cps~0.5, 8s = exactly 16 beats, so anything driven only by K.beat/K.pulse/K.cyc looks IDENTICAL 8s later. FIX: add a REAL-TIME motion floor driven by K.t (seconds), which never re-aligns — a continuously scrolling / drifting / rotating / traveling element with meaningful amplitude (e.g. S.acc += (element speed) each frame using K.t deltas, or position = (K.t*rate) % range). Put substantial pixels in motion (a drifting cloud band, orbiting sparks, a scrolling element across >10% of frame, a rotating structure).
  - If diff is exactly 0.0000: the layer is THROWING (nothing draws). Common bug: a local variable shadowing a p5 global (line/fill/text/point/rect...) or an undeclared variable (ReferenceError). Extract the code, run it through node new Function with a p5 stub that defines the globals, find the throw, fix it. Verify it actually draws.

FAILURE "params: poke ['a','b'] changed output by only 0.00XX":
  - The validator poked the FIRST TWO numeric params to their max together and the render barely changed. FIX: reorder params so the first two numerics are ones that OBVIOUSLY transform the image at max (scale with max>=1.8, density, count, amplitude). Ensure each is actually read every frame and has a large visible effect at max. Do NOT put hue or a subtle param first.

FAILURE "luminance: 0.0XX outside [0.02, 0.92]":
  - Frame mean brightness out of range (0.019 = too dark). FIX: raise the baseline — fill the frame with a dim but non-black base (e.g. a low-value gradient ~8-15% brightness) BEFORE the dark content, or brighten the marks. Keep it clearly above 0.02 and below 0.92 across all styles.

FAILURE "fps: XX.X < 25":
  - Too slow. FIX: cut per-frame cost — cache static content in a size-keyed createGraphics buffer built ONCE (not per frame), shrink any offscreen grids/buffers, reduce particle/point counts, avoid per-pixel loops and any full-canvas filter(). Target 40+ fps with margin.

## UNIVERSAL (still required)
Keep the aesthetic mandate (non-cartoon anchor style, >=3 style options incl. one abstracted, texture over flat) and all schema rules (P-block verbatim with __SLOT__, K for rhythm, A blended on top, state under S, seed determinism, no frameCount/createCanvas/setcps/full-canvas-filter, blendMode(BLEND)+shadowBlur=0 restored). Worlds/genart own the full frame with NO bed behind them (fill it, keep luminance in range). Sets/fx/post get an opaque bed behind them.

## QC BEFORE DONE (do this rigorously — these already failed once)
1. Write the code body to a scratch file ($TMPDIR only) and run it through a p5-stub node harness across styles/poses/acts AND a t0-reset (K.beat jumping backwards): node must report ZERO throws. If FAILURE was 0.0000, your harness MUST reproduce the original throw first, then confirm your fix removes it.
2. For motion fixes: mentally (or numerically) confirm the K.t element displaces meaningfully between t and t+8s at cps=0.5 — it must NOT re-phase.
3. python3 -c "import json; a=json.load(open('assets/visual/inbox/<id>.json')); assert '__SLOT__' in a['code'] and 'window.state.clk' in a['code']"

HARD RULES: never call the server (no curl/HTTP), never git commit, only write the inbox file(s) for your orders, scratch to $TMPDIR only. Leave graveyard copies in place (orchestrator removes them when yours pass).

Return each id + the exact fix you applied.`

phase('Rescue')
const results = await parallel(batches.map(b => () =>
  agent(prompt(b), { label:`rescue[${b[0]}-${b[1]-1}]`, phase:'Rescue', schema:RESULT_SCHEMA, effort:'high' })
))
const ok = results.filter(Boolean)
const fixed = ok.flatMap(r=>r.assets||[])
log(`rescue authors done: ${fixed.length} re-authored, ${results.length-ok.length} agent failures`)
return { reAuthored: fixed.length, agentFailures: results.length-ok.length,
         fixes: fixed, problems: ok.map(r=>r.problems).filter(p=>p&&p.length) }
