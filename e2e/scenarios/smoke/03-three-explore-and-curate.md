---
id: three-explore-and-curate
tier: smoke
fixture: empty
mocks: []
critical_path: true
---

# Parameter, audio, seek, catalog and curation controls stay inspectable

## Preconditions
- Workshop initialized.

## Steps

1. Navigate to `/threejs/browser/index.html?forceWebGL=1` and wait for "Clockwork Bloom".
   - expect-url: matches `^/threejs/browser/index\.html`
2. Activate "seeded random" in the Form panel.
   - expect: parameter outputs remain finite and within the selected safe range
3. Open the Audio panel and activate "low pressure".
   - expect: the "SYNTHETIC REVIEW BUS" and "NOT LIVE DSP" labels remain visible, low-region meters respond, and a mapping ledger is populated
   - screenshot: synthetic-audio.png
4. Move the transport timeline to cycle 4 and wait for the seek proof-frame status.
   - expect: the cycle readout is approximately 4, tick debt is zero after reconstruction, and the scene remains visible
   - screenshot: seek-cycle-four.png
5. Open the Curate panel, check "Keep in my constellation", choose grade 5, type "Strong silhouette; inspect material noise." into the notes field, and activate "Save review".
   - expect: status contains "review saved" and the curation summary reports one reviewed seed
6. Open the scene catalog, search for "kawaii", and inspect the results.
   - expect: "Orbit Familiar" is visible and the other three scene cards are filtered out
   - screenshot: catalog-kawaii-search.png
7. Close the catalog and post-run.
   - expect-console: no errors since step 1

## Proof required
- `synthetic-audio.png`
- `seek-cycle-four.png`
- `catalog-kawaii-search.png`
