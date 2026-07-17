---
id: three-workshop-loads
tier: smoke
fixture: empty
mocks: []
critical_path: true
---

# Three.js workshop initializes its real renderer contract

## Preconditions
- Isolated static server booted.

## Steps

1. Navigate to `/threejs/browser/index.html?forceWebGL=1` and wait for the loading card to disappear.
   - expect-url: matches `^/threejs/browser/index\.html`
   - expect: heading "Clockwork Bloom", status "runtime ready · workshop evidence", a visible "WORKSHOP · OPEN" label, and a renderer label containing "NODE-WEBGL-COMPAT · R185"
   - screenshot: workshop-ready.png
2. Inspect the stage and Form panel.
   - expect: a visible Three.js canvas, Previous/Pause/Next/Surprise me controls, four named parameter sliders, and the transition grammar controls
   - screenshot: clockwork-form.png
3. Post-run.
   - expect-console: no errors since step 1

## Proof required
- `workshop-ready.png`
- `clockwork-form.png`
