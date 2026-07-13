# Music Factory — resumable state (updated 2026-07-13, session-4 arc-audibility fix)

## SESSION 4 (2026-07-13 — KIT×ARC SECTION AUDIBILITY FIX)

Gene reported new kits sounded "broken or too quiet" through `slow_burn`,
`sparse_bookends`, `waves`. ROOT CAUSE (a real process hole): validate.py fires
each stem solo and each kit at all-`full`, but NEVER plays a kit THROUGH an arc
section-by-section. Those arcs' intro/breakdown/outro sections named only 1-2
slots at `sparse`; any kit lacking those slots played SILENT there (a kit with
one quiet slot = too quiet ~0.007) for 20-30s. A section verifier found **18
broken kit×arc combos** (e.g. amapiano_lounge has no pad/texture → dead through
slow_burn's pad+texture intro).

**FIX (committed):** added `"*":"sparse"` floor to the affected sections of 8
arcs (build_drop, drop_out, ghost_intro, long_arch, slow_burn, sparse_bookends,
tide, waves). Every kit slot now plays ≥sparse there; named full/peak accents
keep the dynamics. `browse.html` (line ~328) and `arc_compile.py` resolve `"*"`
identically, so BOTH surfaces are fixed by the one data change.

**NEW PERMANENT GATE:** `assets/tools/verify_arcs.py` — fires every kit through
every arc it lists, section by section, measures live audibility, exits non-zero
on any silent/too-quiet/errored section. **RUN BEFORE ANY HANDOFF** (stop the
valloop first; it needs the server exclusively). Definitive run after the fix:
**88 kit×arc combos, 0 problems** (engine control 0.45, all sections audible).

**This is now part of the process:** a kit is not "done" until it passes both
validate.py (stem+kit gates) AND verify_arcs.py (section audibility through arcs).

---

# (session-3) Music Factory — resumable state (2026-07-13 ~03:05 EDT, expansion)

## SESSION 3 (2026-07-13 ~03:00 EDT — post-3hr-pause EXPANSION)

On resume, the catalog was already **COMPLETE**: 389 stems / 35 kits / 12 arcs,
0 quarantined, valloop audit passing 389/389. Machine load was high (~9 — the
visual factory's "+100 TARGET REACHED" closeout), so **live QA/validation is
load-blocked** (valloop gate = loadavg < 4.5). Did a focused, LOAD-INDEPENDENT
expansion per Gene's standing directives (vox was thinnest slot; "more kits";
"variety is king"; "spend quota"):

- **+18 vox stems → inbox** (6 subagents) filling vox genre gaps: ukg/garage/
  footwork, jungle/dnb/trance, disco/gqom/afrobeat, drone/ambient/world-sindhen,
  drill/gaze/gamelan-kecak, idm-glitch/concrete/triphop. All pass the static
  lint (orbit 8, 3 variants ending `.play()`, gain ≤ .50, deps ⊆ packs.json, no
  banned APIs, ≥8 tags). Sources: dirt-samples vocal shelf + shabda accents +
  vowel-filtered synth choir.
- **+9 kits → inbox** for gap genres: `kit.reich_minimal` (C maj), `kit.latin_salsa`
  (Bb), `kit.reggaeton_dembow` (Gm), `kit.shoegaze_wall` (C#), `kit.concrete_collage`,
  `kit.world_raga` (E), `kit.gamelan_kotekan` (Db pent, w/ drums — distinct from
  drumless `gamelan_fm`), `kit.drone_deep` (E maj — distinct from C-lydian
  `drone_dawn`), `kit.exp_polymeter`. Each references only verified stems whose
  cps windows all intersect the kit cps (the `validate_kit` hard gate).

**RESULT (session-3 COMPLETE, ~04:20 EDT)**: valloop validated the batch under
low load → **26/27 passed first try** (all 9 kits + 17/18 vox). One vox stem
(`vox.trance.anthem_hook.01`) genuinely under-loud (full rms 0.0074) — the
`.vowel()` formant + heavy `.room(.6)` were energy sinks; **rescued** (denser
8-notes/cycle, `.shape(.55)`, dropped the vowel filter, tamed reverb, pump floor
`saw.range(.8,1)×gain`) → re-validated **full rms 0.0585**. All 18 vox verified.
- **Live QA** (arc_compile --fire): world_raga / reggaeton_dembow / reich_minimal
  / shoegaze_wall / concrete_collage all fired clean — audible, no clipping, ZERO
  runtime errors, arcs evolve (world_raga swept rms 0.04→0.42). Swapped
  `concrete_collage` default arc to `tide` (its `long_arch` intro opened near-silent).

**FINAL CATALOG: 407 stems · 44 kits · 12 arcs (463 indexed).**

**valloop is STOPPED** (was mid-audit; I took an exclusive server window for the
trance re-validate + QA, and left it stopped so Gene's `review.py` grades on an
idle server without audit collision). Server is hushed/idle.
- To resume autonomous audit/drain: `nohup python assets/tools/valloop_music.py > /tmp/lc_music_valloop.log 2>&1 &`
- To grade: `python assets/tools/review.py music --port 9766`
- Working-tree note: the valloop's hourly audit leaves stems' `verified.rms`
  metadata perpetually re-written; that churn is reverted at each of my commits
  so the tree stays clean. Restarting the valloop will re-introduce it (harmless).

---

## (earlier) updated 2026-07-11 ~16:10, rescue wave in flight

## RESUME SESSION 2 STATUS (2026-07-11 afternoon)

- **Rescue wave 1** (14 agents): 4 agents finished (32 stems), 10 died on quota
  limit mid-run. ~70 stems total got rescued before/during the outage.
- **CRITICAL LESSON — load-induced false fails**: a `restic` backup (plus the
  concurrent visual factory) pushed loadavg to ~7; browser main-thread
  starvation makes Strudel drop/delay events, so `audio.rms` reads sporadic
  bursts or exactly 0.0000 even for a gain-.88 sine sub. ~66 legitimately
  rescued stems were falsely re-quarantined this way. The g1-sine control
  (rms .074) and varying reads proved bridge + analyser are HEALTHY — it's the
  *scheduling*, not the tap. **valloop now has a load gate (loadavg < 4.0) and
  a stricter bridge check (≥5/14 healthcheck samples > .03).** Never validate
  under heavy load; never trust an rms-0.0000 fail without checking loadavg.
- Fixed state: 66 falsely-failed rescued stems re-queued to inbox (last_fail
  stripped, fail-tracker reset); **rescue wave 2** (6 agents) launched for the
  45 stems whose agents died before touching them.
- valloop source now lives in session 49fb0cba's scratchpad; fail-tracker
  `valloop_state.json` reset to {}.
- Verified stems: **283** (was 280; +3 passed even under load).



Relaunch by re-reading `assets/prompts/music-factory.md`. This file is the
resume point. Server work uses **port 9766** only.

## Snapshot 4 (2026-07-11 evening — COLLECTION COMPLETE, catalog audit finishing)

**389 verified stems · 35 kits · 12 arcs · 436 indexed assets.** All committed.
Stems by slot: drums 71, bass 66, lead 59, chords 54, perc 44, pad 41, texture 30, vox 24.

- **Root cause of the mass silence FOUND & FIXED**: `owned_transport.js` skips
  `initStrudel()`, which is also what registers superdough's DSP AudioWorklets —
  so `.shape/.coarse/.crush` output SILENCE (a regression that silenced ~139
  verified + all 107 rescued stems, since BUNDLE.md's loudness rescue leans on
  shape). Fix: `livecode.html` start handler now calls `window.initAudio()` after
  `ac.resume()`. See [[dsp-worklets-initaudio]] memory. **Users must hard-reload
  livecode.html once to pick it up.**
- **Validation is now self-policing** (validate.py): engine health pre-check
  (aborts if bridge/worklets/load bad — never corrupts the catalog), Defer verdict
  (load-silence ≠ real-silence via a 909 control), and `--audit music` that
  re-validates the verified catalog and DEMOTES anything now silent. valloop
  auto-audits hourly when idle.
- Rescue: 107/107 quarantined recovered; 4 inherently-quiet VCSL mallet/perc
  stems boosted (framedrum→darbuka body layer, glock/marimba shape+clip).
- QA: 6 kits fired through arcs — clean dynamics, no clipping, audible, evolving.
  build_drop verified end-to-end (needs a kit to fire; had none before).
- The full catalog audit was interrupted ~1/3 in (0 demotions); the valloop's
  hourly auto-audit finishes it autonomously.

REMAINING (optional polish): key/mode tag hygiene (dupes like `major pentatonic`
vs `major:pentatonic`); vox is the thinnest slot (24). Otherwise done.

## Snapshot at pause 3 (2026-07-11 ~18:45 — SUPERSEDED — was: validation blocked by load)

**State:** 283 verified stems · **107 rescued stems staged & clean in inbox** ·
0 kits · 12 arcs. All committed (`c368719`).

**The blocker is environmental, definitively diagnosed:** concurrent AI-agent
sessions on this machine (opencode, codex, claude) hold 1-min loadavg swinging
**5–13**. Above ~load 5 the browser audio thread stalls for seconds and a
genuinely LOUD stem reads `rms 0.0000` non-deterministically. Proven: raw
`sawtooth` peaks 0.05 at load 5 but 0.00 at load 12; the 909 control peaks 0.58
at load 9 (bridge/analyser HEALTHY); the same stem config read 0.12 then 0.00
one minute apart as load spiked. **The 107 staged stems are musically fine —
they play when load is low. Do NOT re-rescue them; they are not broken.**
supersaw is a real quiet-synth caveat (~0.008, a few trance/rave stems) — those
few may need a louder treatment, but only confirm that at low load.

**What's armed:** the load-gated valloop (`assets/tools/valloop_music.py`) is
running; it preloads external packs + validates + commits automatically the
moment loadavg drops below 4.5. validate.py's `peak_rms` is now adaptive
(listens through stalls without lowering the gate). So the 107 drain with ZERO
tokens whenever the machine frees up — no agent action needed.

**To finish:** either wait for the machine to quiet (other agents to stop), or
run the factory when the box is otherwise idle. Then: verify inbox drained →
kits wave → QA → report. Kit AUTHORING and kit VALIDATION both need the same
low-load window (kits fire stems through the same bridge).

## Snapshot at pause 2 (2026-07-11 ~16:30 — superseded)

| Metric | Count |
|--------|-------|
| **Verified stems** | **283** |
| **Arcs** | 12 (all structurally valid) |
| **Kits** | 0 (not started — NEXT STEP after inbox drains) |
| **Inbox (staged, contract-linted)** | **111 rescued stems** — all 113 quarantined were rescued (2 passed validation already); static lint clean (orbit/play()/gain ceilings/deps/tags/banned APIs; note `s("dantranh_tremolo")` is a legal vcsl sample name, not the banned tremolo API) |
| Quarantined | 0 |

**The 111 validate + commit AUTOMATICALLY** — the load-gated valloop is running
and will process them (~30-40 min) once 1-min loadavg < 4.0 (a restic backup was
hogging the machine at pause time). No agent needed. On resume, first check:
`ls assets/music/inbox | wc -l` (0 = drained) and `grep -c '"kind":"stem"' assets/music/index.jsonl`.
Fails get 2 automatic attempts (fresh tracker); genuine twice-fails land back in
`inbox_failed/` — re-rescue those once with deeper levers, then leave any
stragglers documented here.

## Snapshot at pause 1 (superseded)

280 verified (drums 60, chords 46, bass 43, lead 42, pad 32, perc 27,
texture 17, vox 13) · 12 arcs · 0 kits · 113 quarantined · inbox 0.

Everything is committed. Latest commits are `music factory: batch …` (valloop
auto-commits) interleaved with the visual factory's commits on `main`.

## Background processes (left running — all FREE, no Claude tokens)

- `livecode.py --port 9766` — server (PID may change; `pkill -f "livecode.py --port 9766"` to stop)
- `autopilot_host.py … --snapshots-dir autopilot/snapshots_music` — headed browser on 9766
- valloop — **local, non-LLM** validate→index→commit loop; idles on empty inbox, self-heals server+host (only ever touches the 9766 host, never 8766/9866). Drop JSON into `assets/music/inbox/` and it validates automatically. **The hardened version (load gate + strict bridge check) is committed at `assets/tools/valloop_music.py`**; the running instance + its `valloop_state.json` fail-tracker live in session 49fb0cba's scratchpad (`/private/tmp/claude-501/-Users-gene-Dev-livecode/49fb0cba-*/scratchpad/`). If it died (reboot), relaunch: `nohup python assets/tools/valloop_music.py > /tmp/lc_music_valloop.log 2>&1 &` (state file will sit next to the tool — fine).
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

0. **Check the automatic validation drained** (see Snapshot at pause 2 above):
   `ls assets/music/inbox | wc -l` → 0 and quarantine empty means all rescued
   stems landed; expect ~370-395 verified total. If files remain in inbox the
   valloop is likely load-gated (check `tail /tmp/lc_music_valloop.log` and
   `uptime`) or dead (relaunch per Background processes above). If new
   `inbox_failed/` entries exist: re-rescue ONCE with deeper levers (recipe
   below), then document stragglers here and move on.
   - **Rescue recipe** (BUNDLE.md loudness section): (1) `.shape(.3–.6)` — biggest lever; (2) gain→slot ceiling; (3) raise pump floor `saw.range(.6,.9)` not `(.4,.8)`; (4) denser full/peak (peak_rms is time-averaged); (5) crackle/noise kits lead with white/pink not crackle.
1. **Kits wave** (~30-35) — kits draw from the now-full verified set. `livecode-kit-v1`: `{name,desc,cps,key,stems{slot:verified_stem_id},arc,tags}`, only verified stem ids (grep `assets/music/index.jsonl`), kit cps inside EVERY stem's cps window, ≥2 slots audible in section 0 of the recommended arc, 2 recommended arcs each (12 arc ids under `assets/music/arcs/`), cover every genre column + 2-3 cross-genre wildcards + a couple no-drums texture/ambient kits. Validate via inbox (validate.py fires whole kit at kit cps with `full` variants + param defaults; combined rms > .02; stems must be harmonically compatible AT THEIR DEFAULT keys — kit key is a label, not auto-transposition). Helper: `scratchpad/kit_context.py` in session 49fb0cba dumps a per-genre verified-stem table (id|slot|key|cps|energy|claims|deps) — regenerate it fresh.
2. **Spot-listen QA** — fire a few kits end-to-end through arcs (`python assets/tools/arc_compile.py <kit> <arc> --fire --port 9766`), confirm mix doesn't clip and the arc audibly evolves. Hush after.
3. **Final report + Gene's grading** — totals by genre/slot, coverage vs PLAN.md, 10 best, weak spots; then `python assets/tools/review.py music --port 9766`.

## LEARNED (don't rediscover)

- Sidechain (`.duck*`), `.swing/.swingBy`, `.scrub`, tremolo family are ALL absent from the bundle → BANNED. Pump = `.gain(saw.range(floor,top).fast(4))`; swing = elongation/`.late`. (BUNDLE.md.)
- clean-breaks has NO `clean:N` names — named breaks (amen/think/apache…). mridangam loads single-arg only. (packs.json.)
- Under-loudness (not broken code) is the ONLY significant failure mode — 100% of fails are the audibility gate. Analyser reads subs fine (control g1 sine @.85 = rms .097); low reads mean quiet CODE. `.shape()` is the fix.
- valloop must target ONLY its own host (`snapshots_music`) / server (`--port 9766`) — a blanket `pkill -f autopilot_host.py` would kill the concurrent visual factory. (Fixed.)
- **Machine load ≥ ~5 produces FALSE audibility fails** (rms 0.0000 even for a gain-.88 sine): browser main-thread starvation makes Strudel drop/delay note scheduling. The analyser itself stays healthy (g1 sine control ~.074-.097, values vary). Never validate under load; never lower the gate; check `uptime` before trusting a 0.0000 read. valloop_music.py enforces this (loadavg < 4.0 + ≥5/14 loud healthcheck samples).
- valloop loads its fail-tracker into memory at startup — resetting the JSON file while it runs does nothing (it writes stale counts back). Restart the loop to reset.
- Workflow tool: pass big args by embedding them in the script literal — the `args` param arrived JSON-stringified once and the script saw `undefined`.
