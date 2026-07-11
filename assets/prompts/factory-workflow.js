export const meta = {
  name: 'visual-asset-factory-v2',
  description: 'Author all 201 visual assets (edgy/experimental mandate) to assets/visual/inbox/',
  phases: [
    { title: 'Author', detail: 'parallel authors, 2-3 work orders each, one JSON asset per order' },
  ],
}

// All 201 orders. Subjects/genart get per=2 (craft-heavy), others per=3, palettes one batch.
const SECTIONS = [
  {kind:'subject', start:0,   end:50,  per:2},
  {kind:'crowd',   start:50,  end:62,  per:2},
  {kind:'world',   start:62,  end:87,  per:3},
  {kind:'floor',   start:87,  end:102, per:3},
  {kind:'set',     start:102, end:122, per:3},
  {kind:'fx',      start:122, end:142, per:3},
  {kind:'post',    start:142, end:157, per:3},
  {kind:'genart',  start:157, end:191, per:2},
  {kind:'palette', start:191, end:201, per:10},
]

const batches = []
for (const s of SECTIONS)
  for (let i = s.start; i < s.end; i += s.per)
    batches.push({kind: s.kind, from: i, to: Math.min(i + s.per, s.end)})

log(`v2: authoring 201 orders (edgy mandate) in ${batches.length} batches`)

const RESULT_SCHEMA = {
  type: 'object',
  properties: {
    assets: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          id: {type: 'string'},
          look: {type: 'string', description: 'one-line description of the default look + how edgy'},
          styles: {type: 'array', items: {type: 'string'}},
        },
        required: ['id', 'look'],
      },
    },
    problems: {type: 'string'},
  },
  required: ['assets'],
}

const authorPrompt = (b) => `You are one of many parallel VISUAL ASSET AUTHORS for Gene's livecode catalog factory. Working directory: /Users/gene/Dev/livecode.

## READ FIRST (both, completely)
1. assets/prompts/author-brief.md — the full spec: JSON schema, P-block, mandatory style/seed params, EXACT validation gates, perf budget, the DESIGN-SIZE rules, and the AESTHETIC MANDATE. Read every section.
2. assets/CONTRACT.md — the underlying contract.

## YOUR WORK ORDERS — indices ${b.from}..${b.to - 1} of assets/prompts/work-orders-v1.json:
  python3 -c "import json; print(json.dumps(json.load(open('assets/prompts/work-orders-v1.json'))[${b.from}:${b.to}], indent=1))"

Author one complete asset JSON at assets/visual/inbox/<id>.json per order. OVERWRITE any existing file at that path (first-wave versions were too cartoonish — you are replacing them with better ones).

## THE TWO THINGS THAT MATTER MOST THIS WAVE

### 1. AESTHETIC: escape the cartoon default (Gene's explicit redirect)
First wave was ALL "cute cartoon" — thick outlines, flat fills, big eyes, blob bodies. Gene wants DIVERGENCE: edgy, experimental, sophisticated, each template feeling like a different artist made it.
- Commit HARD to your order's assigned "style" as the default, and make it genuinely non-cartoon (ink-wash = real brushed sumi with bleed/dry-brush; brutalist = hard concrete + raking shadow + monochrome; riso = true 2-ink misregistration + halftone; noir = chiaroscuro form-from-light, etc.).
- Your "style" options param (>=3) must vary the RENDERING PHILOSOPHY, not just hue: include at least one non-representational/abstracted option (wireframe, X-ray, single continuous contour line, pure silhouette, glitch-fractured, low-poly, halftone/CMYK, cubist, blueprint, chiaroscuro-no-outline, stipple/hatch engraving, iridescent, thermal false-color).
- Texture over flat fill (hatching/stipple/scanlines/grain/gradient-map/translucency/shadowBlur). Expressive line weight or no outline at all. Allow eerie/austere/menacing/sacred/clinical/decayed moods and desaturated/dark-key palettes — not only saturated party brights.

### 2. IT MUST NOT READ AS STATIC (the #1 first-wave failure)
The validator diffs 320px grayscale snapshots 8s apart; mean-diff must be > 0.004 (and < 0.35). A small subject with subtle motion FAILS even with a great rig. So:
- Subjects: at P.scale=1 the hero is 0.40-0.55 x min(width,height) tall — a stage hero, not a desk toy.
- Baseline motion (with A=0, no audio) must DISPLACE the silhouette: whole-body bob/sway/step >= 5% of body height + limb swings each beat. Not just blinks/outline-wiggle. Derive ALL rhythm from K (K.pulse/K.swell/K.beat*P.speed/K.section) — never frameCount.
- Add slow evolution over 30s-5min (K.section/K.intensity behavior changes, K.t drift) and a P.act param with 2-3 multi-minute dramaturgies where it fits.
- Audio-reactivity (A.bass/treble/rms) layered ON TOP of that baseline, never as the sole motion.

## PARAMS (validator pokes the FIRST TWO numeric params to their max together — render must visibly change > 0.003)
Order params so the first two numerics obviously transform the render (e.g. scale then energy/density). Give scale max >= 1.8. Never put hue first (max 360 wraps to red). Ship "seed" (0-9999) with hash-based deterministic randomness (rebuild cached seed-dependent structures when seed changes). Stretch every numeric to a generous-but-safe range; add proportion morphs (chub/limb/neck/etc.) for micro-variety.

## PER-ASSET QC BEFORE MOVING ON
1. Syntax: write code body to a scratch file, then: node -e "const c=require('fs').readFileSync('<scratch>','utf8'); new Function(c.replace(/__SLOT__/g,'subA')); console.log('OK')"
2. Parse: python3 -c "import json; a=json.load(open('assets/visual/inbox/<id>.json')); assert '__SLOT__' in a['code'] and 'window.state.clk' in a['code']"
3. Self-review vs the gates table + design-size rules + aesthetic mandate.

## HARD RULES
NEVER call the server (no curl/HTTP — a validation pipeline owns the one canvas). Never git commit. Only write asset files under assets/visual/inbox/ (scratch goes to $TMPDIR, never /tmp, never elsewhere in the repo). Never touch assets/music/**, index.jsonl, INDEX.md, or ids that aren't your orders.
Orders with a "harvest" field: Read that source, preserve its stage-proven CHARACTER but re-skin per the aesthetic mandate and convert frameCount->K, state->S, add P-block/params.
Palette orders: data-only (id/name/desc/tags/values HSB triples), no code.

Spend real craft. Return the structured summary when all orders are done.`

phase('Author')
const results = await parallel(batches.map(b => () =>
  agent(authorPrompt(b), {
    label: `author:${b.kind}[${b.from}-${b.to - 1}]`,
    phase: 'Author',
    schema: RESULT_SCHEMA,
    effort: 'high',
  })
))

const ok = results.filter(Boolean)
const written = ok.flatMap(r => r.assets || [])
const problems = ok.map(r => r.problems).filter(p => p && p.length)
log(`v2 authors done: ${written.length} assets, ${results.length - ok.length} agent failures`)
return {
  totalWritten: written.length,
  agentFailures: results.length - ok.length,
  assets: written.map(a => a.id),
  problems,
}
