---
id: three-browser-stress-recovery
tier: regression
fixture: empty
mocks: []
critical_path: true
---

# Three.js catalog remains live through prolonged browsing and camera interaction

## Preconditions
- The generated scene registry has been rebuilt with `npm run catalog`.
- Run against the isolated compatibility lane on port 4112.

## Steps

1. Navigate to `/threejs/browser/index.html?forceWebGL=1&scene=scene.093.clay-archaeopteryx-marionette` and wait for "Clay Archaeopteryx Marionette".
   - expect-url: matches `^/threejs/browser/index\.html`
   - expect: the page reports app ready/pass, a numeric frame id, zero recent errors, and a visible "Free camera" control
   - screenshot: direct-stress-initial.png
2. Open the scene catalog, alternate full-height upward and downward scrolling 30 times, and leave the grid at its final row.
   - expect: the catalog remains responsive with no more than 37 facet buttons, all scene cards remain reachable, catalog render suspension is true, and frame id does not advance while the modal is open
   - screenshot: direct-catalog-bottom.png
3. Close the catalog, alternate inspector scrolling with 20 next-scene requests over at least 30 seconds, then wait for the final transaction to settle.
   - expect: frame id advances, transition state returns to active, queued navigation is false, Play/Pause is responsive, and recent errors remain empty
   - screenshot: direct-navigation-stress.png
4. Open the catalog, choose "Plush Moon Mechanic", close the catalog, and let it render for at least six seconds.
   - expect: frame id continues increasing, app pass remains true, frame state is not error or stalled, the recovery control stays hidden, and recent errors remain empty
   - screenshot: plush-purity-regression.png
5. Drag horizontally and vertically across the Three.js canvas, then wheel over the canvas; do not interact with the inspector.
   - expect: camera ownership leaves authored state, pointer session and camera-change receipts increase, pan stays disabled, and the camera remains within its declared orbit and zoom bounds
   - screenshot: direct-free-camera.png
6. Stop pointer input and wait for idle reacquisition.
   - expect: camera ownership returns to authored and the current pose exactly matches the latest authored position, quaternion, and field of view
7. Navigate to `/catalog.html`, wait for the embedded Three.js page, and repeat 20 alternating inspector scrolls, five scene navigations, one canvas drag, and one idle camera return.
   - expect-url: matches `^/catalog\.html`
   - expect: the embedded page frame id continues increasing, its transition returns to active, camera ownership completes an interactive-to-authored lifecycle, and its error ledger remains empty
   - screenshot: unified-three-stress.png
8. Open the embedded scene catalog and alternate full-height scrolling 30 times.
   - expect: embedded catalog render suspension is true, its frame id stays fixed while open, no more than 37 facet buttons exist, and the outer catalog shell remains responsive
   - screenshot: unified-catalog-stress.png
9. Post-run.
   - expect-console: no errors since step 1

## Proof required
- `direct-stress-initial.png`
- `direct-catalog-bottom.png`
- `direct-navigation-stress.png`
- `plush-purity-regression.png`
- `direct-free-camera.png`
- `unified-three-stress.png`
- `unified-catalog-stress.png`
