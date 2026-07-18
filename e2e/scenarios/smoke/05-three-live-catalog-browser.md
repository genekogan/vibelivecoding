---
id: three-live-catalog-browser
tier: smoke
fixture: empty
mocks: []
critical_path: true
---

# Generated scene catalog stays browsable and deeply controllable

## Preconditions
- The generated scene registry has been rebuilt with `npm run catalog`.

## Steps

1. Navigate to `/threejs/browser/index.html?forceWebGL=1&scene=scene.043.plush-moon-mechanic` and wait for "Plush Moon Mechanic".
   - expect-url: matches `^/threejs/browser/index\.html`
   - expect: the header reports 200 indexed authored scenes, 200 visible generated scenes, and catalog watching; frame timing is a finite milliseconds-p95 value, draw and triangle counts are numeric, app pass is true, and the application error ledger is empty
   - screenshot: catalog-browser-initial.png
2. Select the "intimate" Camera mode and activate "seeded random".
   - expect: the document camera mode is intimate, parameter outputs remain finite and in the selected safe range, and the canvas remains nonblank
   - screenshot: intimate-seeded-variation.png
3. Select the "expressive" Range and activate "seeded random".
   - expect: the document parameter range is expressive, every parameter input exposes its manifest expressive bounds, every output remains finite and within those bounds, an exact parameter-variation seed is published, and the canvas remains nonblank
   - screenshot: expressive-seeded-variation.png
4. Select the "extreme" Range, activate "seeded random", and record the visible World seed plus every parameter output. Activate "Re-seed this world" and wait for the transaction, then navigate to an exact replay URL for the recorded seed, range and `p.*` parameter values.
   - expect: the re-seed transaction first publishes a different exact World seed; after replay, the scene identity, extreme range, world seed and every parameter output exactly match the recorded state, app pass remains true, and the canvas remains nonblank
   - screenshot: extreme-seed-exact-replay.png
5. Select the "counter repair" Act and activate "reset".
   - expect: the active scene serializes the requested act and every visible parameter returns to its manifest default
6. Select the "neutral form study" Lighting mode, inspect the stage, and restore "authored atmosphere".
   - expect: each selection is reported as the active lighting reading, the scene stays nonblank with exactly one renderer canvas, and the application error ledger stays empty
   - screenshot: neutral-form-lighting.png
7. Pause the scene, select playback speed 0.25×, record the current simulation tick, and activate "+1" once.
   - expect: playback stays paused except for one exact simulation step, the tick advances by exactly one, tick debt remains zero, playback rate remains 0.25, and the scene stays visible
   - screenshot: exact-slow-step.png
8. Open the scene catalog and search for "negative-space".
   - expect: "Negative-Space Chapel" remains visible and unrelated scene families are filtered
   - screenshot: generated-catalog-search.png
9. Activate the "Negative-Space Chapel" scene card and wait for the transaction.
   - expect: the scene identity becomes `scene.014.negative-space-chapel`, the dialog closes, the canvas remains nonblank, and renderer tick debt returns to zero
   - screenshot: catalog-transaction-chapel.png
10. Activate "Autoplay" and then stop it.
   - expect: the document autoplay state changes from on to off without creating another renderer or browser error
11. Open the Proof panel and expand "Sources, licenses and modification seams".
   - expect: the exact Negative-Space Chapel source path, module/content/aggregate hashes, license reading, provenance groups, parameter seams, acts, camera directors and evidence files are visible
   - screenshot: source-license-modification-navigation.png
12. Activate "Copy source path" and then "Copy source record".
   - expect: the first copy reports an exact source path and the second reports a source, license and modification record, or each exposes selectable fallback text when clipboard access is denied
13. Navigate to `/threejs/browser/index.html?forceWebGL=1&scene=scene.043.plush-moon-mechanic&recording=plush-moon-rendered-master-v1&recordingCycle=20&panel=audio` and wait for "Plush Moon Mechanic".
   - expect: the Audio panel reports "RECORDED MASTER", audio source is `recorded-rendered-master`, recording cycle is exactly 20, the mapping ledger is populated, the canvas remains nonblank, and the application error ledger stays empty
   - screenshot: recorded-master-review.png
14. Navigate to `/threejs/browser/index.html?forceWebGL=1&scene=scene.043.plush-moon-mechanic&audioSource=live-rendered-master&panel=audio` and wait for "Plush Moon Mechanic"; activate "live master" once.
   - expect: the Audio panel reports "MASTER WAITING", audio source is `live-rendered-master`, the provider remains honestly unavailable without an enabled same-origin engine analyser, no synthetic meter or mapping values are invented, the canvas remains nonblank, and the application error ledger stays empty
   - screenshot: live-master-honest-waiting.png
15. Activate "Surprise me" and wait for the random scene transaction to settle.
   - expect: the scene identity changes, transition state returns to active, frame id continues increasing, the canvas remains nonblank, and the error ledger stays empty
16. Open the Curate panel, choose "reject", and activate "Save review"; then choose "requeue" and save again.
   - expect: the first summary reports one rejected seed and the second reports one requeued seed with zero rejected seeds
17. Activate "Copy link" and then "Copy recipe".
   - expect: each operation reports exact copied state or exposes selectable fallback text within one second when clipboard access is denied
18. Activate "Pin current frame" once.
   - expect: the comparison count becomes 1 / 12, exactly one serialized comparison card appears, status reports one serialized state, app pass remains true, and the application error ledger stays empty
   - screenshot: serialized-comparison-pin.png
19. Post-run.
   - expect-console: no errors since step 1

## Proof required
- `catalog-browser-initial.png`
- `intimate-seeded-variation.png`
- `expressive-seeded-variation.png`
- `extreme-seed-exact-replay.png`
- `neutral-form-lighting.png`
- `exact-slow-step.png`
- `generated-catalog-search.png`
- `catalog-transaction-chapel.png`
- `source-license-modification-navigation.png`
- `recorded-master-review.png`
- `live-master-honest-waiting.png`
- `serialized-comparison-pin.png`
