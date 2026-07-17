export const meta = {
  name: 'visual-asset-factory-remaining',
  description: 'Author the remaining ~146 non-subject visual assets (edgy mandate) to inbox',
  phases: [ { title: 'Author', detail: 'parallel authors over work-orders-remaining.json' } ],
}

// args = array of {from, to, kind} batches over assets/prompts/work-orders-remaining.json
const batches = typeof args === 'string' ? JSON.parse(args) : args
log(`remaining fleet: ${batches.length} batches, indices ${batches[0].from}..${batches[batches.length-1].to-1}`)

const RESULT_SCHEMA = {
  type: 'object',
  properties: {
    assets: { type: 'array', items: { type: 'object', properties: {
      id: {type:'string'}, look: {type:'string'}, styles: {type:'array', items:{type:'string'}}
    }, required: ['id','look'] } },
    problems: { type: 'string' },
  },
  required: ['assets'],
}

const authorPrompt = (b) => `You are one of many parallel VISUAL ASSET AUTHORS for Gene's livecode catalog factory. Working directory: /Users/gene/Dev/livecode.

## READ FIRST (both, completely)
1. assets/prompts/author-brief.md — full spec: JSON schema, P-block, mandatory style/seed params, EXACT validation gates, perf budget, DESIGN-SIZE rules, and the AESTHETIC MANDATE. Read every section.
2. assets/CONTRACT.md — the underlying contract.

## YOUR WORK ORDERS — indices ${b.from}..${b.to - 1} of assets/prompts/work-orders-remaining.json:
  python3 -c "import json; print(json.dumps(json.load(open('assets/prompts/work-orders-remaining.json'))[${b.from}:${b.to}], indent=1))"

Author one complete asset JSON at assets/visual/inbox/<id>.json per order (the <id> is in each order).

## THE TWO THINGS THAT MATTER MOST

### 1. AESTHETIC: escape the cartoon default (Gene's explicit redirect)
The subject wave that already passed came out too "cute cartoon" (thick outlines, flat fills, blob bodies). Gene wants DIVERGENCE: edgy, experimental, sophisticated — each template feeling like a different artist made it. For YOUR kinds (worlds/floors/sets/fx/post/genart/crowds/palettes):
- Commit HARD to your order's assigned "style" as the default, genuinely non-cartoon (ink-wash = real brushed sumi with bleed/dry-brush; brutalist = hard concrete + raking shadow + monochrome; riso = true 2-ink misregistration + halftone; thermal = false-color heat ramp; noir = chiaroscuro; etc.).
- Your "style" options param (>=3) must vary the RENDERING PHILOSOPHY, not just hue: include at least one non-representational/abstracted option (wireframe, X-ray, blueprint/schematic, glitch-fractured, low-poly, halftone/CMYK, ASCII/dot-matrix, cubist, chiaroscuro-no-outline, stipple/hatch engraving, iridescent, thermal false-color).
- Texture over flat fill (hatching/stipple/scanlines/grain/gradient-map/translucency/shadowBlur). Allow eerie/austere/menacing/sacred/clinical/decayed moods and desaturated/dark-key palettes — not only saturated party brights.

### 2. IT MUST NOT READ AS STATIC (the #1 failure mode)
The validator diffs 320px grayscale snapshots 8s apart; mean-diff must be > 0.004 (and < 0.35). IMPORTANT LESSON from failures: motion that is purely beat-locked can REALIGN at 8s (at cps~0.5, 8s = exactly 16 beats) and read as static. So ALWAYS include a REAL-TIME motion floor that never re-phases: use K.t (seconds) for continuous drift/scroll/roll/wander IN ADDITION to K.beat/K.pulse/K.swell rhythm. Worlds: drifting clouds/sky/fog/stars/water. Floors: scrolling or shimmering. FX/particles: continuous emission + travel. Post: keep flashes PARTIAL-frame (never full-frame invert -> trips the 0.35 strobe ceiling). Derive ALL rhythm from K, never frameCount. Blend audio (A.bass/treble/rms) ON TOP of the baseline, never as the sole motion. Add slow 30s-5min evolution via K.section/K.intensity + K.t, and a P.act param with 2-3 dramaturgies where it fits.

## PARAMS (validator pokes the FIRST TWO numeric params to their max together — render must change > 0.003)
Order params so the first two numerics obviously transform the render. For worlds/genart use density or scale first (not hue — max 360 wraps). Give ranges that visibly differ at max. Ship "seed" (0-9999) hash-deterministic (rebuild cached seed-dependent structures on seed change). Stretch every numeric to a generous-but-safe range.

## KIND-SPECIFIC
- world/genart: full-bleed, own the bg. Cache the static base in a createGraphics buffer keyed on size(+seed); animate on top. NO full-canvas filter() (~12ms). The validator runs you with NO bed behind — you must fill the frame and keep luminance in [0.02,0.92].
- floor: ground plane; validator puts a bed behind you.
- set/fx/post: validator puts an opaque bed (background(240,30,12)) behind you; assume it. Restore blendMode(BLEND) and shadowBlur=0 at end.
- crowd: N-instance renderer with n/energy/pal params; honest n max (particle budget: <=150 heavy, <=500 points).
- palette: DATA ONLY — {format:'livecode-visual-v1', id:'palette.<slug>', kind:'palette', name, desc, tags(>=8), values:{swatchName:[h,s,b],...}}. No code/slots/params. Make the swatch set genuinely useful and match the named discipline.

## PER-ASSET QC BEFORE MOVING ON
1. node -e "const c=require('fs').readFileSync('<scratch>','utf8'); new Function(c.replace(/__SLOT__/g,'SLOT')); console.log('OK')"  (use the asset's real first slot for SLOT)
2. python3 -c "import json; a=json.load(open('assets/visual/inbox/<id>.json')); assert a['kind']=='palette' or ('__SLOT__' in a['code'] and 'window.state.clk' in a['code'])"
3. Self-review vs the gates table + design-size + aesthetic mandate + the real-time-motion-floor lesson above.

## HARD RULES
NEVER call the server (no curl/HTTP — a validation pipeline owns the one canvas). Never git commit. Only write asset files under assets/visual/inbox/ (scratch to $TMPDIR only, never /tmp, never elsewhere in the repo). Never touch assets/music/**, index.jsonl, INDEX.md, or ids that aren't your orders.
Orders with a "harvest" field: Read that source, preserve its stage-proven CHARACTER but re-skin per the aesthetic mandate; convert frameCount->K, state->S, add P-block/params.

Spend real craft. Return the structured summary when all orders are done.`

phase('Author')
const results = await parallel(batches.map(b => () =>
  agent(authorPrompt(b), { label: `auth:${b.kind}[${b.from}-${b.to-1}]`, phase: 'Author', schema: RESULT_SCHEMA, effort: 'high' })
))
const ok = results.filter(Boolean)
const written = ok.flatMap(r => r.assets || [])
log(`remaining authors done: ${written.length} assets, ${results.length-ok.length} agent failures`)
return { totalWritten: written.length, agentFailures: results.length-ok.length,
         assets: written.map(a=>a.id), problems: ok.map(r=>r.problems).filter(p=>p&&p.length) }
