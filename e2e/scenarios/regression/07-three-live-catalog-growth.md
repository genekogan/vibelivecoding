---
id: three-live-catalog-growth
tier: regression
fixture: empty
mocks: []
critical_path: true
---

# An open Three.js catalog appends a newly built scene without reload

## Preconditions
- The generated registry is at the authoritative 200-scene aggregate hash.
- `threejs/catalog/preflight/runtime-growth-probe/` does not exist.
- Run against the isolated compatibility lane on port 4112.

## Steps

1. Navigate to `/threejs/browser/index.html?forceWebGL=1&scene=scene.043.plush-moon-mechanic` and wait for "Plush Moon Mechanic".
   - expect: the page reports 200 indexed authored scenes, 200 visible generated scenes, catalog watching, app pass true, a numeric advancing frame id and an empty application error ledger
   - screenshot: growth-before-200.png
2. Keep the browser page open. Run `node e2e/helpers/three-runtime-growth-probe.mjs install`, then run `npm run catalog --prefix threejs/browser` exactly once.
   - expect: the build reports 201 records, 195 preflights and a changed aggregate source hash while the registration-ledger hash remains unchanged
3. Wait for one catalog discovery interval without reloading the page.
   - expect: status reports "catalog discovered 1 new scene", the same page reports 201 indexed and 201 visible scenes, frame id continues increasing, app pass remains true and the application error ledger stays empty
4. Open the scene catalog and search for "runtime growth probe".
   - expect: exactly one Runtime Growth Probe card is visible, catalog render suspension is true, and the card is labeled temporary rather than accepted artistic content
   - screenshot: growth-after-201.png
5. In a guaranteed teardown, close the page, run `node e2e/helpers/three-runtime-growth-probe.mjs remove`, and run `npm run catalog --prefix threejs/browser` exactly once.
   - expect: the temporary source directory no longer exists and the generated registry returns to 200 records, 194 preflights and aggregate hash `sha256:138c4616d478f4d02161b8b9add6fbb9507a0080e7d4fa2d5601635254308e59`
6. Navigate to `/threejs/browser/index.html?forceWebGL=1&scene=scene.043.plush-moon-mechanic` in a fresh page.
   - expect: the restored page reports 200 indexed and 200 visible scenes, app pass true and an empty application error ledger
   - expect-console: no errors since step 6
   - screenshot: growth-restored-200.png

## Proof required
- `growth-before-200.png`
- `growth-after-201.png`
- `growth-restored-200.png`
