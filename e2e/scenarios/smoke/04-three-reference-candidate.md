---
id: three-reference-candidate
tier: smoke
fixture: empty
mocks: []
critical_path: true
---

# Reference candidate stays distinct from accepted catalog art

## Preconditions
- Isolated static server booted.

## Steps

1. Navigate to `/threejs/browser/index.html?forceWebGL=1&scene=scene.005.product-totem-kinematics` and wait for the loading card to disappear.
   - expect-url: matches `^/threejs/browser/index\.html`
   - expect: heading "Product Totem Kinematics", a visible "REFERENCE · CANDIDATE" label, status containing "commissioned reference candidate", and renderer label containing "NODE-WEBGL-COMPAT · R185"
   - screenshot: product-reference-ready.png
2. Inspect the Form panel and timeline.
   - expect: sliders named "partRatio", "jointBias", and "highlightWidth"; `partRatio` is labeled as a geometry update; and the timeline spans 64 cycles
3. Pause the scene, activate "seeded random" once, and wait for the staged transaction to return to active.
   - expect: the candidate remains visible, `partRatio` resolves inside its safe range, the active slot generation advances, and no structural-update or destination-eligibility error is shown
   - screenshot: product-staged-ratio.png
4. Move the transport timeline to cycle 62 and wait for the seek proof frame.
   - expect: the cycle readout is approximately 62, tick debt is zero, and no fast-forward-limit error is shown
   - screenshot: product-residue.png
5. Open the Proof panel.
   - expect: "Commissioned reference candidate" is OPEN, the host transaction pattern is ACCEPTED, rendered-master DSP remains OPEN, and the manifest does not contain accepted scene-acceptance evidence
   - screenshot: product-open-evidence.png
6. Navigate directly to `/threejs/browser/index.html?forceWebGL=1&scene=scene.005.product-totem-kinematics&capture=1&paused=1&cycle=20&motion=still&audio=low&audioWarmFrames=120&panel=audio` and wait for the loading card to disappear.
   - expect: the Audio panel is active, low pressure is selected, the cycle remains exactly 20, the still motion profile is selected, the mapping ledger contains a nonzero bounded `scene.energy` write, and no warm-up card overlays the scene
   - screenshot: product-fixed-proof.png
7. Post-run.
   - expect-console: no errors since step 1

## Proof required
- `product-reference-ready.png`
- `product-staged-ratio.png`
- `product-residue.png`
- `product-open-evidence.png`
- `product-fixed-proof.png`
