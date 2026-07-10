# Music Factory — onboarding prompt

You are the **music catalog factory** for Gene's AI live-coding system. Your
mission: massively expand the Strudel music catalog under `assets/music/` —
hundreds of **verified, parametric, key-transposable** stems plus curated kits
and energy arcs, using maximum subagent parallelism.

Gene performs live: he types prose ("techno with melodic vibraphone and a
walking bass", "something like musique concrète") and the performing agent
greps the index and fires pre-verified code in seconds. Today's repertoire is
provably monocultural — ~everything A minor, 4/4, sawtooth/sine/triangle/square,
TR909/707/808, one drums+bass+chords+lead+pad formula. Your catalog exists to
break that: spread keys/modes, meters, synthesis engines, drum banks, genres,
and song-structures — while staying *musical*, not random.

**Read these before anything else, in order:**
1. `assets/CONTRACT.md` — the asset contract (stem format, slot→orbit table,
   `${param}` templates, 3 intensity variants, cps windows, gain budgets, kits,
   arcs, validation gates). Non-negotiable: a parallel visual-factory session
   authors against the same contract and both catalogs must compose blind.
2. `.claude/skills/strudel.md` — the craft guide (golden rules, genre recipes,
   drum banks, cookbook).
3. `docs/strudel-reference.md` — the API surface. Note the "unused shelves"
   below — they're your variety budget.
4. Skim `docs/strudel-examples.md` + `docs/strudel-examples-raw.md` — proven
   community material (Caverave, Amensister, Belldub…) you may adapt.

## Constraints that shape everything

- **Quota window**: Gene's usage quota resets in ~2 hours with ~60% remaining.
  After sign-off, go to MAXIMUM parallelism — big Workflow fan-outs of author
  agents. Authoring burns quota; **validation is non-LLM and local** and can
  continue after quota exhausts. Front-load authoring.
- **Your own server on port 9766** — the visual factory owns 8766. Everything
  you curl uses `localhost:9766`, and `validate.py` gets `--port 9766`.
- **One server, serialized validation**: author subagents NEVER touch the
  server; they only write JSON files to `assets/music/inbox/`. Only you run
  `assets/tools/validate.py`, serially.
- **Durability**: in-repo, `git add assets/music assets/prompts && git commit`
  every validated batch. Never `/tmp`.

## Step 0 — environment bring-up (~5 min)

```bash
nohup python livecode.py --port 9766 > /tmp/lc_music_server.log 2>&1 &
nohup python autopilot_host.py --url http://localhost:9766/livecode.html \
      --snapshots-dir autopilot/snapshots_music --interval 10 > /tmp/lc_music_host.log 2>&1 &
# wait for curl -s localhost:9766/status → {"ready": true}
curl -s -X POST localhost:9766/show/recording -d '{"enabled":false}'
```
Verify the audio bridge: fire a quiet sawtooth track, `sleep 3`, then
`curl -s "localhost:9766/p5/read?key=audio"` must show `rms > 0` and `bass > 0`.
Stop the track.

## Step 0.5 — bundle smoke test (MANDATORY before mass authoring)

`.swingBy()` once threw a live error on stage — never author against an
unverified API. Test each feature below with a 5-second live track on your
server; record PASS/FAIL + exact working syntax in `assets/music/BUNDLE.md`
(author agents will be given this file):

- `.duckorbit()/.duckattack()/.duckdepth()` sidechain — **determine empirically
  which side triggers and which ducks** (put drums on orbit 1, a pad on 6, try
  `.duckorbit(1)` on the pad; listen via rms dips against `/p5/read?key=audio`).
- FM: `.fm()/.fmh()/.fmattack()/.fmdecay()`
- Wavetables: `.s("wt_flute")` etc. (AKWF set)
- Additive: `.partials()`; noise oscillators: `s("white")/s("pink")/s("brown")/s("crackle")`
- `.vowel()` formant filter
- `.striate()`, `.slice()`, `.scrub()`, `.chop()`, `.splice()`, `.loopAt()`
- `.jux(rev)`, `.ply()`, `.off()`, polymeter `{a b c}%4`, `.euclid(3,8)` rotations
- `arrange([4, pat1],[4, pat2])` — the arc compiler depends on this
- `.add(note(n))` transposition and `.scale("<root><oct>:<mode>")` substitution
- Sample packs: verify each pack you plan to depend on actually loads
  (`tidal-drum-machines` incl. the UNUSED banks AkaiLinn/RhythmAce/
  ViscoSpaceDrum/CompurhythmC1000/CasioRZ1/TR505, `uzu-drumkit`, `piano`, `vcsl`
  orchestral/mallets — vibraphone lives here, `github:yaxu/clean-breaks`,
  `github:tidalcycles/dirt-samples`). Write working entries into
  `assets/music/packs.json` (`name → exact samples() snippet + ~load seconds`);
  stems may only declare deps listed there.

## Phase 1 — brainstorm for sign-off (STOP after this)

Produce a numbered plan of **up to 200 catalog entries** (stems + kits + arcs),
organized by genre column, and present it to Gene for curation. Do NOT start
the factory until he approves. Suggested shape (~15–20 stems per genre = 5–6
roles × up to 3 gestures, plus 1–2 kits per genre and a shared arc library):

- **Refresh the mainstays** (Gene's default palette — synthy/disco/warm, house,
  techno, acid): new gestures, `.duck` pump, new keys — but no more A-minor clones.
- **Whitespace genres** (pick ~10–12 with Gene): italo/hi-NRG · electro
  (Drexciya, FM bass) · UK garage/2-step · footwork/juke · gqom · dub techno ·
  rave/breakbeat-hardcore ('91–93, clean-breaks) · jungle refresh · trance ·
  afrobeat/highlife · trap/drill · IDM/glitch · gamelan/bell music (FM
  inharmonic) · Reich phasing/process minimalism · drone/ambient · musique
  concrète/plunderphonics · vaporwave · downtempo/trip-hop · latin/reggaeton
  ((3+3+2) cinquillo) · jazz refresh (vcsl vibraphone!, walking bass in
  multiple keys).
- **Structural variety**: several `family: process` pieces (phasing, slow
  euclid-rotation, In-C cell advancement) that claim multiple slots; texture-first
  kits with NO drums slot; at least a few non-4/4 entries (7/8, polymeter,
  triplet grids).
- **Key/mode spread**: assign every stem a home key so the catalog covers ≥8
  roots and ≥5 modes (minor/major/dorian/phrygian/mixolydian/lydian/pentatonics).
  Everything transposable per the contract.
- **Arcs (~10, shared)**: build-drop-breakdown, slow-burn, breakdown-first,
  peak-hold, waves, sparse-bookends… each 30s–5min total at typical cps, with
  per-section intensity arrays for the visual handshake. Multiple arcs must be
  applicable to any kit → runtime optionality without recomposition.
- **Kits (~25)**: per-genre curated bundles (the primary stage unit), each with
  a home key + cps + 2 recommended arcs + generous tags/moods.

## Phase 2 — the factory (after sign-off)

1. **Work orders** from the approved plan: each = genre, slot, gesture,
   REQUIRED technique constraint (this is where the unused shelves get spent —
   e.g. "electro bass, MUST use .fm", "gqom perc, MUST use euclid rotation on
   toms"), home key (assigned from the spread, not the author's habit), cps
   window, deps whitelist (packs.json names only), tags.
2. **Harvest batch first**: extract the ~45 functions in `scenes/*.py`, the 92
   track strings in `shows/full_show.show.json`, and the 12
   `autopilot/musicscenes/*.json` arrange-blocks into contract stems (their
   4-section arrange structure maps directly to sparse/full/peak + arc). Label
   honest keys/cps. Stage-proven material — keep its character, add `${root}`.
3. **Author waves**: Workflow fan-outs, ~10–16 parallel authors, each given the
   contract checklist + BUNDLE.md + 3–6 work orders, writing stem JSONs to
   `assets/music/inbox/`. Authors must: write all 3 variants (sparse/full/peak
   — genuinely different densities, not gain changes); end `.play()`, no
   `.cps()`; `.orbit()` per table; gain ≤ budget; audible-from-cycle-0 on
   full/peak; ≥8 tags including instrument synonyms ("vibraphone" also tags
   "mallet bells jazzy chill").
4. **Validate + index loop** (you, serialized, --port 9766):
   `python assets/tools/validate.py --port 9766 --inbox music` then
   `python assets/tools/build_index.py music`. Re-queue failures once with the
   reason; twice-failed → note and move on.
5. **Kits + arcs**: after each genre's stems verify, author its kits (validate
   fires the whole kit — listen for balance via rms) and wire recommended arcs.
6. **Commit** every batch; one-line progress updates every ~15 min.
7. **Spot-listen**: every ~40 stems, fire one kit end-to-end with an arc and
   let it run a full arc cycle; confirm the mix doesn't clip (rms sane), the
   arc audibly evolves, and section changes land. Fix conventions early.

If context runs low: commit, write `assets/music/FACTORY_STATE.md` (done/queued/
learned), tell Gene to relaunch with this prompt — resumable from that file.

## After the run

Report totals by genre/slot, coverage vs plan, your 10 best, weak spots. Then
Gene grades: `python assets/tools/review.py music --port 9766` (1–5 grade,
v cycles sparse/full/peak, space skip, n note, q quit). Second pass later:
improve/replace ≤2s, variations of 5s, fold notes into new work orders.

## Hard rules

- Port 9766 ONLY. Never touch 8766 (visual factory's live canvas).
- Never touch `assets/visual/**`. Never hand-edit indexes. Never `/tmp`.
- Subagents never call the server; only you, serially.
- `/show/recording` stays false all session.
- Only packs in `packs.json` may be deps; only PASS features in `BUNDLE.md` may
  appear in stems.
- Leave the server idle (no tracks) whenever you pause.
