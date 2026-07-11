# Music Factory — resumable state (paused 2026-07-11)

Relaunch by re-reading `assets/prompts/music-factory.md`. This file is the
resume point. Server work uses **port 9766** only.

## Snapshot at pause

| Metric | Count |
|--------|-------|
| **Verified stems** | **280** (drums 60, chords 46, bass 43, lead 42, pad 32, perc 27, texture 17, vox 13) |
| **Arcs** | 12 (all structurally valid) |
| **Kits** | 0 (not started) |
| **Quarantined** (recoverable) | 113 — all under-loudness, not broken code |
| Inbox | 0 (drained) |

Everything is committed. Latest commits are `music factory: batch …` (valloop
auto-commits) interleaved with the visual factory's commits on `main`.

## Background processes (left running — all FREE, no Claude tokens)

- `livecode.py --port 9766` — server (PID may change; `pkill -f "livecode.py --port 9766"` to stop)
- `autopilot_host.py … --snapshots-dir autopilot/snapshots_music` — headed browser on 9766
- `scratchpad/valloop.py` — **local, non-LLM** validate→index→commit loop; idles on empty inbox, self-heals server+host (only ever touches the 9766 host, never 8766/9866). Drop JSON into `assets/music/inbox/` and it validates automatically.
- The token-burning **Monitor was stopped** at pause.

To fully stop everything: `pkill -f "livecode.py --port 9766"; pkill -f "autopilot_host.py.*snapshots_music"; pkill -f scratchpad/valloop.py`.

## DONE (procedure steps from music-factory.md)

- **Step 0** env bring-up ✅ · **Step 0.5** bundle smoke test ✅ → `BUNDLE.md` (feature matrix, banned list, pump idiom, loudness recipe) + `packs.json` (11 verified packs incl. vocals: dirt vocal shelf + shabda TTS).
- **Phase 1** plan + sign-off ✅ → `PLAN.md`. Gene expanded scope: all genres (no benching), vocals, more kits, sibling variants + param ranges.
- **Phase 2** authoring ✅ — all 30 genre columns + full_show harvester + 12 arcs, via a resumable Workflow (survived a mid-run quota exhaustion; resumed from cache).
- **Validate+index loop** ✅ running (280 verified, auto-committed).
- **Tools built**: `assets/tools/arc_compile.py` (kit+arc → per-slot `arrange()` forms + visual handshake — verified live). `assets/music/browse.html` (keyboard sound-space explorer on :9766, auto-ingests new assets, arc pickers on kit cards).
- **Engine bug fixed**: audio-bridge froze on first `.room()` (OfflineAudioContext tap) — see `[[audio-bridge-offline-context]]` memory. Survived the visual factory's v3 rewrite of livecode.html.

## QUEUED (resume here, in order)

1. **Gain-rescue wave** (highest value — recovers ~70-90 of 113 quarantined).
   - Shards precomputed: `scratchpad/rescue_shards.json` (14 shards of ~8). Fail-tracker (`scratchpad/valloop_state.json`) already reset to `{}` so rescued stems get fresh attempts.
   - **Empirically-confirmed recipe** (in BUNDLE.md loudness section): (1) `.shape(.3–.6)` — biggest lever, took a silent sub from rms 0.0000→0.0572; (2) gain→slot ceiling; (3) raise pump floor `saw.range(.6,.9)` not `(.4,.8)`; (4) denser full/peak (peak_rms is time-averaged); (5) crackle/noise kits lead with white/pink not crackle.
   - Each rescue agent: read quarantined `assets/music/inbox_failed/<id>.json` + its `last_fail.detail`, apply recipe preserving musical character, write corrected version to `assets/music/inbox/<id>.json`, then delete the `inbox_failed/` copy. valloop revalidates automatically.
2. **Kits wave** (~30, task #7) — after rescue drains, so kits draw from the fullest verified set. `livecode-kit-v1`: `{name,desc,cps,key,stems{slot:verified_stem_id},arc,tags}`, ≥2 slots audible in section 0, 2 recommended arcs each, incl. cross-genre wildcards + no-drums texture kits. Validate fires the whole kit (rms balance).
3. **Spot-listen QA** — fire a few kits end-to-end through arcs (`arc_compile.py <kit> <arc> --fire --port 9766`), confirm mix doesn't clip and the arc audibly evolves.
4. **Final report + Gene's grading** — `python assets/tools/review.py music --port 9766`.

## LEARNED (don't rediscover)

- Sidechain (`.duck*`), `.swing/.swingBy`, `.scrub`, tremolo family are ALL absent from the bundle → BANNED. Pump = `.gain(saw.range(floor,top).fast(4))`; swing = elongation/`.late`. (BUNDLE.md.)
- clean-breaks has NO `clean:N` names — named breaks (amen/think/apache…). mridangam loads single-arg only. (packs.json.)
- Under-loudness (not broken code) is the ONLY significant failure mode — 100% of fails are the audibility gate. Analyser reads subs fine (control g1 sine @.85 = rms .097); low reads mean quiet CODE. `.shape()` is the fix.
- valloop must target ONLY its own host (`snapshots_music`) / server (`--port 9766`) — a blanket `pkill -f autopilot_host.py` would kill the concurrent visual factory. (Fixed.)
