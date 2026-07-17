export const meta = {
  name: 'visual-micro-rescue',
  description: 'Surgical fix for the last 4 motion-gate stragglers',
  phases: [ { title: 'MicroRescue', detail: '4 single-asset agents, laser-specific fixes' } ],
}

const TARGETS = [
  { id:'subject.bicycle', slot:'subA', order:45,
    fix:`Currently motion diff 0.0032 (needs >0.004) — SO CLOSE. Amplify the real-time (K.t) motion: the whole rider+bicycle must visibly TRANSLATE and/or bob more, and the wheels/pedals must roll faster and larger. Add a continuous K.t-driven horizontal glide that wraps across a good fraction of the frame (bike rides across), OR a bigger continuous body bob (>=8% of body height) plus faster wheel-spoke rotation. Do NOT rely on beat-locked motion alone (it re-phases at 8s). Aim for a comfortable 0.01+ diff.` },
  { id:'fx.fireworks', slot:'fxA', order:123,
    fix:`Currently motion diff 0.0002 — essentially blank/near-static. The problem: bursts are too sparse, so two snapshots 8s apart can both land on empty sky. FIX: guarantee CONTINUOUS activity — stagger many shells (using K.t + seeded offsets) so at EVERY instant several are rising and/or mid-explosion, and keep persistent drifting smoke, sparks, and falling embers between bursts. There must never be an empty frame, and the content must clearly differ 8s apart. Also double-check it isn't throwing (0.0002 can mean a runtime error) — run the code through a p5-stub node harness and confirm it actually draws.` },
  { id:'genart.attractor', slot:'bg', order:157,
    fix:`Currently motion diff 0.0036 — SO CLOSE. This is a genart that OWNS the full frame (no bed behind it) so fill it and keep luminance in [0.02,0.92]. Amplify visible evolution: continuously rotate/precess the whole attractor point-cloud via K.t, AND slowly drift its parameters so the shape morphs over time; add gentle continuous hue/position drift. The trace at t and t+8s must look clearly different. Aim for 0.01+ diff. Keep the earlier params fix too (first two numeric params must obviously change the render at max).` },
  { id:'genart.blackhole', slot:'bg', order:186,
    fix:`Currently motion diff 0.0005 — near-static. ROOT CAUSE: a rotating accretion disk is ROTATIONALLY SYMMETRIC, so spinning it looks identical frame-to-frame → tiny frame-diff. FIX by BREAKING SYMMETRY with continuous K.t motion: (1) an orbiting bright hotspot (Doppler-beaming crescent) that travels around the disk over a few seconds; (2) discrete infalling blobs/streaks that spawn at the outer edge and spiral inward, appearing/disappearing continuously (seeded, K.t-driven); (3) subtle jet/photon-ring flicker. The frame must look MATERIALLY different 8s apart, not just rotated. This is a genart owning the full frame (no bed) — fill it, keep luminance in [0.02,0.92] (space is dark but the disk + starfield must keep mean >=0.02). Aim for 0.01+ diff.` },
]

const SCHEMA = { type:'object', properties:{ id:{type:'string'}, fix:{type:'string'} }, required:['id','fix'] }

const prompt = (t) => `You are a SURGICAL RESCUE author for Gene's livecode catalog. Working dir: /Users/gene/Dev/livecode.

Re-author exactly ONE asset so it PASSES the live motion gate (320px grayscale snapshots 8s apart must have mean-diff > 0.004 and < 0.35). Overwrite assets/visual/inbox/${t.id}.json.

READ FIRST: assets/prompts/author-brief.md (gates, P-block, DESIGN-SIZE, AESTHETIC MANDATE, real-time-motion-floor lesson). The current failing code is at assets/visual/graveyard/${t.id}.json — READ IT and improve it (keep its aesthetic; fix the motion).

Its order spec: python3 -c "import json; print(json.dumps(json.load(open('assets/prompts/work-orders-v1.json'))[${t.order}], indent=1))"

## THE EXACT FIX REQUIRED
${t.fix}

Slot is "${t.slot}". Keep everything else contract-compliant: P-block verbatim with __SLOT__, ALL rhythm from K (never frameCount), audio A blended ON TOP of the baseline, state under S, seed determinism, no createCanvas/setcps/full-canvas-filter, blendMode(BLEND)+shadowBlur=0 restored, resolution-agnostic, style options intact.

## MANDATORY QC (this asset already failed 3 times — be rigorous)
1. Run the code body through a p5-stub node harness (define p5 globals as no-ops, window.state.clk/audio) across styles and a t0 reset — ZERO throws. If the old diff was ~0.000X, PROVE the old code threw or drew nothing, then prove yours draws.
2. NUMERICALLY estimate the 8s frame-diff: simulate the code's drawn geometry at K.t and K.t+8 (at cps=0.62 AND cps=0.5) and confirm a large fraction of pixels move. The motion MUST come from K.t (real seconds), which never re-phases — not from K.beat alone.
3. python3 -c "import json; a=json.load(open('assets/visual/inbox/${t.id}.json')); assert '__SLOT__' in a['code'] and 'window.state.clk' in a['code']"

HARD RULES: never call the server, never git commit, only write assets/visual/inbox/${t.id}.json, scratch to $TMPDIR only.

Return the id and the exact fix applied.`

phase('MicroRescue')
const results = await parallel(TARGETS.map(t => () =>
  agent(prompt(t), { label:`micro:${t.id}`, phase:'MicroRescue', schema:SCHEMA, effort:'high' })
))
const ok = results.filter(Boolean)
log(`micro-rescue: ${ok.length}/${TARGETS.length} re-authored`)
return { reAuthored: ok.length, fixes: ok }
