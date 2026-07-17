# The Variety Engine — anti-predictability design for the livecode overhaul

## 0. Thesis

Convergence is not a taste problem, it is an **architecture problem**: every scene is chosen and authored by an LLM under time pressure, and LLMs under time pressure are mode-seeking — they emit their highest-prior template. The fix is not "try harder to be creative" prose in instructions.md (that file is already 672 lines and the output is still 168/511 entries of supersaw). The fix is to **take the samey choices away from the model** and hand them to a deterministic picker that samples from measured whitespace, then let the model spend its creativity *inside* forced constraints. Variety becomes a property enforced by tooling, verified by data, and pre-paid at practice time.

## 1. Diagnosis: four distinct convergence engines (each needs its own countermeasure)

| Cause (evidence from recon) | Countermeasure |
|---|---|
| **C1. Prescriptive docs train sameness.** `.claude/skills/p5.md` "Golden Rules" literally mandate HSB-rainbow + `frameCount` sine + centered radial; strudel.md recipes cover ~10 genres; everything renders through 4 oscillators, 3 drum banks, A minor, 4/4, one 5-stem skeleton, one visual macro-template (cached `__bg` + parallax bands + hero + ADD glow + motes). | **Doc surgery + style families** (§7): delete the Golden Rules; every asset family carries its own palette/motion discipline so "HSB rainbow" becomes 1 of ~10 disciplines, not the default. |
| **C2. Dedupe is prose-memory at the wrong granularity.** The journal dedupes *subject nouns* (owl vs reef vs city) while the *structure* (template, key, timbre, meter, palette logic) repeats every round. 456KB of prose, no queryable fingerprint. | **Novelty ledger** (§2): machine-readable per-scene fingerprints + hard multi-dimensional no-repeat constraints checked by a script, not by the LLM's memory. |
| **C3. The reachable search space is artificially tiny.** Whole documented capability shelves have zero uses: `wt_*` wavetables, FM, `.partials()`, `.duck`, `.vowel`, `.striate/.scrub`, polymeter, `.jux`, noise oscillators, 6 of 9 drum banks; ~15 genres have no recipe; visuals never touch feedback buffers, pixel ops, typography, WEBGL. | **Forced firsts + gap-steered practice factory** (§3): an auto-generated "never used" checklist that wildcards draw from; practice sessions are steered toward measured distribution gaps, not toward more of what exists. |
| **C4. Nothing moves when the agent is idle.** 60s wake floor + 2–5 min authoring means static minutes. Assets are momentary loops, not processes. | **Process assets with internal acts** (§5): every library asset must pass a "never-static" validation (two snapshots 90s apart must differ); music assets get long-cycle signal drift and `arrange()` arcs baked in. |

## 2. The novelty ledger + hard no-repeat constraints

Replace journal-prose dedupe with `autopilot/ledger.jsonl` — one fingerprint per fired scene, appended by the loop (same contract slot as journaling today, but structured):

**Fingerprint dimensions** (each is a small enum, extracted at author time and stored in the asset's metadata so fingerprinting a retrieval hit is free): `genre_family`, `key_root`, `key_mode`, `meter`, `cps_band` (5 bins), `drum_bank`, `synthesis_engines[]` (saw/wt/fm/additive/noise/sample-mangling), `music_template_id`, `visual_family` (figurative-character / world-scene / generative-system / typography / feedback / pixel / iso-voxel...), `palette_discipline` (neon-HSB / monochrome-ink / duotone-riso / pastel / earth / IR-thermal...), `motion_rig`, `symmetry_class`, `subject_category` (the existing journal tags), `process_type` (loop / phasing / drift / ecosystem / acts).

**Hard constraints, enforced by `tools/pick_scene.py` (not by the LLM):**
- No `subject_category` repeat within last 12 scenes (current rule, now enforced mechanically).
- No (`music_template_id`, `visual_family`) *pair* repeat within last 8 — this is the rule that kills "same template, different noun."
- Any single dimension value appearing in >40% of the last 20 scenes is **embargoed** for the next 5 (this is what finally rate-limits supersaw and A minor without banning them).
- Successive scenes must differ in ≥4 of the 14 dimensions (so "evolve" rounds are exempt — the constraint applies only on transitions).
- Per-show quotas honor Gene's stated mix (50–60% dance mainstays, 30–40% interspersed, 10–15% experimental): **variety is maximized within quota buckets**, never by overriding them.

The picker refuses to emit a brief if the ledger is stale (>1 scene behind /status), which forces the fingerprint-append discipline the journal never had.

## 3. Wildcards, virgin quota, forced firsts

`pick_scene.py` doesn't return an asset — it returns a **constraint card** (a "scene brief") the performing agent must satisfy. Choice is where convergence lives; the card removes the samey choices and leaves the creative ones:

- **Seeded dice over underused values**: root/mode drawn inverse-proportionally to ledger frequency (tonight you get Eb Phrygian whether the prior likes it or not); drum bank drawn the same way (CasioRZ1 and ViscoSpaceDrum finally get stage time); one `palette_discipline` and one `symmetry_class` forced.
- **Virgin quota**: every asset in `library/index.jsonl` carries `plays` and `last_played`; each show must fire ≥30% never-played assets, and each constraint card names 1–2 specific virgin assets as mandatory ingredients ("must include `library/visual/typography/word_rain_v2`").
- **Forced firsts**: `tools/gaps.py` greps the ledger + library for zero-use capabilities from a checklist (currently: `.duck`, `.vowel`, `fm/fmh`, `.partials`, `wt_*`, polymeter `{a b}%N`, `.striate`, `.scrub`, `.jux`, noise oscillators, 3/4 & 7/8 meters, feedback buffer, halftone, kinetic typography). Every show must exercise ≥2 items; an item graduates off the list after 5 uses. The list regenerates itself, so the frontier keeps moving.
- **One wildcard slot per show**: a scene brief that is *pure* dice — random genre × random visual family × random process type — flagged `wildcard:true` so both Gene and the taste system know it was a deliberate gamble. Wildcards are always drawn from **practice-validated** assets, so "random" never means "unverified on stage."

Direct user requests ("penguin DJ under a disco ball") **always preempt the card** — the engine fills whatever the user didn't specify (key, palette, drum bank) from the dice instead of from priors, so even requested scenes come out varied.

## 4. Mutation & crossover operators (practice-time, validated; performance-time, param-only)

Because the overhaul makes assets = template + param dict, most operators are param-space edits, cheap to mass-generate and validate offline:

**Music** (operate on stem params, never on raw strings):
- `transpose(root, mode)` — the single highest-leverage op; breaks the A-minor monoculture across the whole library in one batch job (scale()/chord() strings are the only key carriers).
- `retrograde` — wrap pattern in `rev()`; `mirror` — `.jux(rev)` (currently 0 uses, instant width).
- `metric_modulation` — re-render the same pattern spec at a new subdivision or euclid pair ((3,8)→(5,8) reggaeton cinquillo, (7,16) footwork feel); templates store rhythm as (pulses, steps, rotation) so this is arithmetic, not regex.
- `texture_swap` — same notes, different engine: sawtooth → `wt_*` wavetable → `fm` → `.partials()` additive → `.vowel()` formant. One melody spec × 5 engines = 5 timbrally distinct stems.
- `genre_transplant` — render stem params through a *different* genre's template (hiphop drum spec through the dnb template at 0.85 cps; disco bass line through the trance arp template). Crossover = pick two ledger entries, swap one stem role.
- `energy_ladder` — `.degradeBy/.mask/.chunk` variants pre-baked as intro/build/drop/breakdown versions of every stem, so energy is a retrieval parameter.
- `pump` — inject `.duck` sidechain keyed to the drums orbit (documented, never used, instantly "produced-sounding").

**Visuals** (params + rig recombination):
- `palette_swap/invert/rotate` — palette is data, not baked (the disco_dancers per-dancer config proves the pattern).
- `symmetry_break` — mirror count 1..8 as a param, including deliberate off-center asymmetry (the current library is pathologically centered).
- `rig_transplant` — choreography functions (the 16-beat `getMove` phrases) are separate assets from bodies: bind the dancer rig to the cat, the owl, the skeleton. One rig × 18 creatures = 18 new performers.
- `scale_explosion` — hero at 5× with camera drift vs. crowd of 30 at 0.2×; `world_swap` — any subject × any of the 8+ cached-buffer worlds.
- `post_transplant` — append one post layer (feedback-buffer trails, halftone, clip-mask projection, MULTIPLY nightfall) to any existing scene: cheapest "whole new look" operator in the system.

All mutants run through the practice validation harness (headless server + autopilot_host.py snapshots + `/errors` + audibility check + whiteout lint) before entering the index. **Performance-time mutation is restricted to param pokes via `/p5/state`** (~10ms, zero recompile) — code-level operators never run live.

## 5. Cross-modal bridges — the 5 cheapest striking wins, ranked

1. **AnalyserNode → `window.state.audio`** (~30 lines in livecode.html — grep confirms zero analyser code today). Tap the shared `getAudioContext()` destination, publish `{rms, bass, mid, treble, fft[32]}` every rAF. Every existing and future layer can read it with no API change. First visible payoff: floor tiles flash *on the actual kick*, not on a frame counter — the audience perceives this as a different product.
2. **Automatic beat-phase push**: make the `/strudel/cps` handler also write `cps` + `t0` into p5 state server-side (one line in livecode_server.py; today only autopilot assets do this by convention, scenes/ hardcode 28.8 frames/beat and silently desync). This makes the entire visual library tempo-portable — a precondition for every music×visual crossover above.
3. **Per-stem analysers** via Strudel's `.analyze(id)` / `getAnalyserById` (verify in the 1.0.3 bundle; fallback = per-orbit gain taps): the penguin's beak moves on the *vox* stem, lasers ride the *lead*, floor rides the *bass*. Cross-modal binding at the stem level reads as choreography, not visualization.
4. **Visual → music one-shots over the WS relay**: a page-level conductor snippet (injected once via `/p5/send`) watches `window.state.events` (fireworks burst, flock collision, dancer solo start) and sends pre-authored evaluate-mode Strudel one-shots (crash, riser, vocal stab) through the existing `type:'execute'` relay. Reverse causality — visuals playing the band — is the single most "how did it do that" moment available for ~40 lines.
5. **Shared section arc by construction**: the visual intensity array `[0.2,0.4,0.7,0.9,0.3,0.6,1.0,0.4]` already exists (instructions.md:183); encode the *same arc* in music templates' `arrange()` blocks so drops and visual peaks coincide without any runtime coordination. Pairing then only requires matching `cps` + section count (4/8) — both are index fields.

## 6. Process assets: the never-static guarantee

Every library asset declares `process_type`, and the library must maintain ≥25% non-loop processes:
- **Phasing** (Reich): the trick exists in docs (`.mul(speed("1,1.003"))`) but was never made a piece — ship 5 phasing works (marimba, bell/fm, vocal chop, wavetable, hats-only).
- **Long-cycle drift**: prime-length polymeter loops (Eno) + `sine.slow(64)`–`.slow(256)` signals on lpf/gain/pan baked into stems — the mix audibly breathes over 10 minutes with zero agent action.
- **Ecosystems**: boids with birth/death, differential growth, reaction-diffusion on coarse offscreen grids — visuals that are *different every minute by construction*.
- **Internal acts**: every scene asset ships an `acts[]` array (durations + param overrides: lighting, weather, cast size, camera) driven off the existing `state.t0` clock — a scene left alone performs its own 12-minute dramaturgy.
- **Validation**: practice harness snapshots at t and t+90s; if perceptual diff < threshold, the asset is rejected as static. This converts "never static for 10 min" from a hope into a lint rule.

## 7. Taste memory with satiation (so feedback doesn't become the next convergence engine)

- `autopilot/taste.jsonl` — structured events appended by the performing agent whenever Gene types feedback: `{ts, verdict: love|like|meh|ban, scope: {dimension:value} | asset_id, quote}`. Loop-contract rule, same standing as journaling. Bans are absolute and become **lint rules in the validator** (that's how whiteout/orb bans stop consuming instructions.md prose).
- A practice-time job distills events into `taste-model.json`: per-dimension weights consumed by `pick_scene.py`.
- **Satiation is the key design decision**: a `love` boost decays with each recent play of that value (weight = base_love × 0.8^plays_in_last_15). "More of this" means *tonight*, not *forever* — without decay, taste memory just rebuilds the supersaw monoculture with extra steps. Explicit in-the-moment requests bypass weights entirely.
- Instructions.md shrinks: durable taste → taste-model + lint rules; safety rules → asset validators; what remains live is <1 page.

## 8. Doc surgery

Rewrite `.claude/skills/p5.md`: delete Golden Rules 1–2; replace the recipe section with one recipe per *absent* territory (feedback trails, halftone, typography, iso-voxel, RD, ink-monochrome), each carrying its own palette discipline. Fix the stale scene catalog in livecode-compose.md by generating it from `library/index.jsonl` (index-from-assets, never hand-maintained — the drift already happened once).

## 9. What runs when

- **Practice**: subagent factory walks ideas.md × dimension grid + gap briefs from `tools/gaps.py`; applies mutation/crossover batches; validates everything (fps, audibility-from-frame-1, whiteout lint, never-static diff); writes assets + index + fingerprint metadata. Durable, in-repo (`library/`), never /tmp.
- **Performance round**: `pick_scene.py` (<100ms) → constraint card → agent retrieves named assets + fills creative gaps → fires via curl name-overwrite swaps (respecting the 2-track/no-silence rules, which pre-verified assets make cheap) → appends fingerprint + any taste events. The 673-line re-read, the 456KB journal scan, and the from-scratch authoring all disappear from the hot path.

EXAMPLES
### EX
**Constraint card emitted by `tools/pick_scene.py`** (what the performing agent receives instead of choosing everything itself):
```json
{
  "brief_id": "2026-07-10T21:04_card7", "bucket": "interspersed", "wildcard": false,
  "forced": {
    "genre_family": "footwork",            // inverse-frequency draw: 0 plays in ledger
    "key": {"root": "Eb", "mode": "phrygian"}, // A-family embargoed (14 of last 20 scenes)
    "drum_bank": "CasioRZ1",                 // virgin bank
    "meter": "(7,16) euclid grid",
    "palette_discipline": "duotone-riso",     // neon-HSB embargoed 3 more scenes
    "visual_family": "kinetic-typography",    // pair (music_template:5stem, visual:hero-parallax) blocked
    "process_type": "acts"
  },
  "mandatory_assets": ["library/visual/typography/word_rain_v2",  // virgin quota
                        "library/music/stems/bass_wt_scanner_v1"],
  "forced_firsts": [".duck sidechain on drums orbit", "noise-osc perc layer"],
  "free_choices": ["subject text/words", "lead melody contour", "act timings", "fx layer"],
  "taste_notes": {"boost": ["melody-forward", "warm pads (satiation 0.4 — used 6 of last 15)"], "ban": ["breathing orbs", "hh*16 baseline"]}
}
```
The agent's creativity goes into the `free_choices`; the samey axes are already decided.

### EX
**Library catalog entry** — parametric music stem with fingerprint metadata + mutation ops (note `code_template` uses string.Template `$vars`, not f-string brace-doubling):
```json
{
  "id": "music/stems/bass_acid_v3", "kind": "track", "slot": "bass", "orbit": 3,
  "template": "note(\"$pattern\").scale(\"$root$oct:$mode\").s(\"$engine\")\n  .lpf(sine.range($lpf_lo,$lpf_hi).slow($sweep_cycles)).resonance($res)\n  .attack(.005).release(.12).gain($gain).duck($duck_orbit).duckdepth($duck_depth)\n  .orbit(3).play()",
  "params": {"root": "a", "mode": "phrygian", "oct": 2, "engine": "sawtooth",
              "pattern": "0 ~ 0 [3 5] 0 ~ [7 5] 3", "lpf_lo": 200, "lpf_hi": 2400,
              "sweep_cycles": 8, "res": 18, "gain": 0.8, "duck_orbit": 2, "duck_depth": 0.6},
  "fingerprint": {"genre_family": "acid-house", "synthesis_engines": ["saw"],
                   "cps_range": [0.5, 0.62], "meter": "4/4", "process_type": "drift"},
  "deps": [], "gain_budget": 0.85, "plays": 0, "last_played": null,
  "mutations": {"transpose": ["root", "mode"], "texture_swap": {"engine": ["sawtooth", "wt_dbass", "square"]},
                 "retrograde": "wrap rev()", "energy_ladder": [".degradeBy(.4)", "full", "+octave doubling"]},
  "validated": {"audible_frame1": true, "harness_run": "2026-07-08T14:22"}
}
```
A practice batch of `transpose × texture_swap × energy_ladder` on this one entry yields 3×3×3 = 27 pre-validated stems.

### EX
**Audio-reactive bridge** — page-level snippet injected once (livecode.html patch or `/p5/send`), the highest-leverage 30 lines in the whole design:
```js
(function(){
  const ac = getAudioContext();               // shared by Strudel + p5 (livecode.html:640)
  const an = ac.createAnalyser(); an.fftSize = 256; an.smoothingTimeConstant = 0.75;
  // superdough routes to ac.destination; tap it (verify Pattern.analyze(id) in the
  // 1.0.3 bundle first — if present, prefer per-orbit getAnalyserById taps)
  const dest = ac.destination; const orig = dest; // safe tap: analyser in parallel
  try { ac.__tapNode = an; /* connect superdough master gain -> an if exposed */ } catch(e){}
  const buf = new Uint8Array(an.frequencyBinCount);
  function tick(){
    an.getByteFrequencyData(buf);
    const band = (a,b) => { let s=0; for(let i=a;i<b;i++) s+=buf[i]; return s/((b-a)*255); };
    window.state.audio = { bass: band(1,6), mid: band(6,40), treble: band(40,110),
                            rms: band(1,110), fft: Array.from(buf.slice(0,32)) };
    requestAnimationFrame(tick);
  } tick();
})();
// any layer, zero API change:  const a = window.state.audio || {bass:0};
//   tileBrightness = 30 + a.bass * 65;   // floor lights on the actual kick
// plus one server line: /strudel/cps handler also POSTs {key:'cps'} and nulls t0
// via the existing /p5/state path — kills the hardcoded 28.8 frames/beat forever
```

### EX
**Process asset pair** — Reich phasing piece (music) + acts-driven never-static scene (visual):
```
# library/music/pieces/phase_bells_v1  (fingerprint: process_type=phasing, engine=fm)
note("0 2 4 7 9 7 4 2").scale("$root4:$mode").s("sine").fm(3.01).fmh(1.5)
  .mul(speed("1, 1.003"))            // two voices drift one cycle apart over ~5min
  .room(.4).gain(.6).pan(sine.slow(31)).orbit(5).play()
```
```js
// library/visual/scenes/tide_town_v1 — 12-minute internal dramaturgy, agent-idle safe
const S = window.state; S.tt = S.tt || { start: millis() };
const ACTS = [ // duration s, param overrides — validated: snapshot(t) vs snapshot(t+90s) differ
  { dur: 180, sky: [255, 40, 70], tide: 0.2, boats: 2, rain: 0   },  // golden hour
  { dur: 180, sky: [265, 55, 45], tide: 0.5, boats: 5, rain: 0   },  // dusk, harbor fills
  { dur: 240, sky: [250, 60, 22], tide: 0.9, boats: 5, rain: 120 },  // night storm
  { dur: 120, sky: [210, 30, 85], tide: 0.4, boats: 1, rain: 0   },  // dawn clears
];
let t = (millis() - S.tt.start) / 1000, acc = 0, act = ACTS[0], prev = ACTS[ACTS.length-1], f = 0;
for (const a of ACTS){ if (t < acc + a.dur){ act = a; f = (t - acc)/a.dur; break; } prev = a; acc += a.dur; }
const L = (k) => lerp(prev[k], act[k], min(1, f*4));   // 25%-of-act crossfades
// ...cached-buffer town + water using L('tide'), L('rain'), lerped sky hue;
// audio hook: const au = window.state.audio||{bass:0}; waveAmp += au.bass*8;
```

RISKS
- Novelty is not quality: dice-forced combos (footwork × CasioRZ1 × Eb Phrygian × riso typography) can be coherently varied but aesthetically flat. Mitigation is practice-time curation (every wildcard-eligible asset was heard/seen and validated before it can be drawn), but if the factory pumps volume without a human-or-agent curation gate, the engine trades 'samey' for 'random-bad' — Gene will turn it off after one show.
- The whole mutation/crossover layer depends on the parametric refactor landing first. If assets stay baked strings (today: 48 of 50 scene functions take zero musical params, creatures hardcode position/palette in minified JS), operators degrade to regex surgery on code strings and the validation burden explodes. Sequencing risk: build templates+param-dicts before building the variety engine on top.
- Taste memory can become the next convergence engine. The satiation decay constant (0.8^plays) is a guess; too weak and 'love disco' re-creates the monoculture, too strong and the system refuses Gene's actual favorites and feels obstinate ('why won't it play warm synths, I said I love them'). Needs an explicit override channel (in-the-moment requests bypass all weights) and a visible knob, plus a few shows of tuning.
- Embargo/no-repeat constraints can collide with live steering and with stage-safety rules: the picker may forbid exactly what Gene just asked for, or a forced-first (.duck, unverified sample name) could fail audibly if it slipped past validation. Rules: user text always preempts the card, safety validators outrank novelty constraints, and forced-firsts are only drawn from harness-validated assets — if any of these precedence rules are skipped in implementation, the engine actively fights the performer.
- Ledger discipline is a loop-contract behavior, and the existing journal shows contract drift (456KB prose, two divergent loop specs, stale scene catalog). If the agent skips fingerprint appends under load, no-repeat constraints silently evaluate against stale data. The picker refusing on stale ledger mitigates but adds a new mid-show failure mode that needs a graceful fallback (warn + proceed with last-known ledger).
- Cross-modal bridges carry runtime risk: the AnalyserNode tap depends on how superdough exposes its output chain in the 1.0.3 CDN bundle (unverified — Pattern.analyze may or may not be present), per-frame FFT reads cost fps budget on a canvas already measured at 15–20fps in heavy scenes, and the visual→music WS relay bypasses recording/state entirely (one-shots won't replay in shows and vanish on reconnect). Each bridge needs a feature-detect + no-op fallback or a single bad night discredits the whole layer.