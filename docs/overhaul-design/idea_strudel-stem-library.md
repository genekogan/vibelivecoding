# Strudel Stem Library — Design Proposal

## 1. The grid is a coverage report, not the data model

An instrument-role × genre grid is the right *checklist* and the wrong *storage shape*. Store a **flat pool of tagged stem files**; generate the grid as a derived view (`tools/coverage.py` → roles × genres matrix with empty cells highlighted) to direct practice sessions. Three reasons the grid can't be the schema: (a) process music (Reich phasing) and texture-first pieces don't decompose into drums/bass/chords/lead rows; (b) many stems legitimately span genre columns (a 909 four-on-floor serves disco, house, italo, techno); (c) the third asset kind — arrangement arcs — has no row at all.

**Three asset kinds**, all JSON files in-repo (the `autopilot/musicscenes/*.json` precedent, extended):

```
library/
  stems/<slot>/<id>.stem.json     # one playable track template
  arcs/<id>.arc.json              # energy-arc combinators (build/drop/breakdown)
  kits/<id>.kit.json              # curated stem bundles + arc + key + cps (the performance unit)
  packs.json                      # sample-pack registry: name → load snippet, URL, approx load ms
  index.json                      # GENERATED manifest — never hand-edited (kills catalog drift)
tools/
  stemlint.py                     # header + code-contract linter
  stemverify.py                   # live-server audibility/error verification (recording OFF)
  stemc.py                        # compiler: kit/stems+params → curls | .show.json steps
```

Roles (rows of the coverage view) map 1:1 to the **eight physical slots**, formalizing the currently-implicit convention: `drums→orbit 1, perc→2, bass→3, chords→4, lead→5, pad→6, texture→7, vox→8`. Slot name = track name = orbit owner. Because the server keys tracks by name and room/delay are global per orbit, *one stem per slot* makes bus collisions impossible by construction — this is the load-bearing rule that lets parallel subagents each own a slot.

## 2. The stem header contract (exact convention)

Every stem is one JSON file. Code bodies use `string.Template` `${param}` placeholders — **no f-strings ever** (JS brace-doubling is already failing at 50 assets). Every code body ends in `.play()`, contains exactly one `.play()`, never contains `.cps()` (server is the single tempo authority), and sets its own `.orbit(N)` + room/delay explicitly (owner-sets-bus rule).

```jsonc
{
  "id": "bass.italo.octave-pump.01",     // slot.genre.gesture.serial — globally unique
  "kind": "stem",
  "engine": "strudel-track",              // vs "strudel-send" for pack loads/helpers
  "slot": "bass", "orbit": 3,             // MUST match the slot→orbit table; linted
  "family": "groove",                     // groove | texture | process
  "claims": [],                           // extra slots this stem makes redundant (process stems)
  "genre": ["italo","hi-nrg","disco"],
  "mood": ["euphoric","night-drive"],
  "energy": 4,                            // 1–5, matches journal/visual intensity vocabulary
  "meter": "4/4",                         // "4/4" | "7/8" | "poly:3v4" | "free"
  "cycles_per_phrase": 4,                 // arrange()/section alignment; 4, 8, or 1(=free)
  "key": { "root":"a", "mode":"minor", "family":"minor" },  // family: minor|major|none
  "transpose": { "method":"add-note" },   // add-note | scale-sub | none(drums/noise)
  "cps": { "written":0.55, "min":0.48, "max":0.62, "density_flex":false },
  "gain": { "default":0.72, "max":0.90 }, // role budget enforced by lint (see §3)
  "deps": { "samples":[] },               // pack names resolved via packs.json
  "audible_cycle0": true,                 // never-silent mandate, verified not asserted
  "deterministic": true,                  // false for choose()/degradeBy stems
  "params": { "root":{"type":"int","default":0}, "gain":{"type":"float","default":0.72} },
  "code": {                               // 3 intensity variants, ALL ${}-templated
    "sparse": "note(\"a1 ~ ~ ~ a1 ~ ~ ~\")…​.orbit(3).play()",
    "full":   "note(\"a1 a2 a1 a2 …\")…​.orbit(3).play()",
    "peak":   "note(\"a1 a2 c2 c3 …\")…​.orbit(3).play()"
  },
  "verified": { "bundle":"strudel-web@1.0.3", "at":"…", "rms_cycle0":0.21 }
}
```

**Key transposability is the single highest-leverage field** (the repertoire is currently ~all A minor). Two sanctioned mechanisms only: melodic stems written as `n("0 2 4 …").scale("${root}${octave}:${mode}")` (`scale-sub`), or `note(...)` stems that get `.add(note(${root}))` appended by the compiler (`add-note`). `chord("Am9")`-style stems that can't transpose are marked `method:"none"` and pinned to their written key — the kit builder treats them as key anchors. Both mechanisms get smoke-tested against the 1.0.3 bundle *before* mass authoring (see risks).

**cps compatibility** is a declared window, not a hope: `written` is the groove's home tempo, `[min,max]` the range where the feel survives. `density_flex:true` means the compiler may `.fast(2)`/`.slow(2)`-wrap the pattern to re-home it an octave of tempo away (hiphop stem at dnb cps = half-time feel — a feature when declared, a mess when accidental).

## 3. Blind combination: what breaks, and the field that prevents it

| Failure today | Preventing metadata | Compiler action |
|---|---|---|
| Key clash (disco Cm vs everything Am) | `key` + `transpose.method` | pick target key; transpose all pitched stems; `mode.family` must agree (minor≈dorian≈phrygian; major≈lydian≈mixo); anchors (`method:none`) win target-key election |
| Wrong perceived speed | `cps.{written,min,max,density_flex}` | intersect windows → target cps; empty intersection → density-flex offenders or reject |
| Reverb/delay bus fights | `slot`+`orbit` (one stem per slot, fixed table) | impossible by construction; lint rejects orbit mismatch |
| Sample silently missing | `deps.samples` + `packs.json` | union deps → emit `samples()` preamble via `/strudel/send` **outside the timeline**, before first dependent track; practice pre-warms CacheStorage |
| Clipping when stacking loud stems | `gain.max` per role budget (drums .90, bass .90, chords .50, lead .45, pad .35, texture .30, vox .50) | lint at author time; compiler scales `${gain}` down when a kit exceeds the sum budget |
| One malformed stem silences the whole `stack()` re-eval | `verified` block | only verified stems enter `index.json`; live fires skip the 2 s /status recheck because verification moved to practice time |
| Silent intros violating never-silent mandate | `audible_cycle0` (measured RMS, not asserted) | kits must have ≥3 slots `audible_cycle0:true` in section 0; lint on kit files |
| Phrase misalignment vs visuals' 8-section clock | `cycles_per_phrase` | arcs only combine stems whose phrase length divides the section length; compiler pushes cps→`/p5/state` and nulls `t0` on fire |

The performance-time flow: `stemc.py fire kit:italo.night --key f --cps 0.56` (or raw curls from grepping `index.json`) resolves deps → samples preamble → `/strudel/cps` → tracks posted in slot order, drums first. Total wall time ≈ pack-load (0 if pre-warmed) + N×~30 ms. Decision latency collapses to a grep over `index.json` (id, slot, genre, mood, energy, key, cps window, deps, one-liner) instead of reading 13 KB source files.

## 4. Genre expansion — first ten territories

Ordered for boredom-relief (breakbeat → concrète), each with its distinctive Strudel handle:

1. **Rave / breakbeat hardcore ('91–93)** — `github:yaxu/clean-breaks` + `.slice(8,"…")` break-chopping, `.ply` stutters, detuned supersaw hoovers, piano-stab chords. First real use of the breaks pack outside `improvise.py`.
2. **Footwork/juke (160)** — cps ~0.67, triplet claps against duple 808 subs via `{…}%8` polymeter (currently 0 uses anywhere), `.ply(3)` vocal-chop repeats. Half-time sub vs double-time surface is the whole genre.
3. **Electro (Drexciya)** — TR808 (already cached) syncopated 16th kicks, first use of the FM stack (`.fm(2).fmh(1.5)` bass), `.vowel()` robot formants.
4. **Italo / Hi-NRG** — octave-pump bass with the never-used `.duckorbit(1).duckdepth()` sidechain (one line, instantly authentic), fast `n()` arpeggio runs, unused CasioRZ1/LinnDrum banks.
5. **UK garage / 2-step** — shuffle via nested mini-notation `[hh [~ hh]]` (`.swingBy` is confirmed absent from the bundle), skipping kicks, pitched vox chops from dirt-samples via `.chop`+`.speed`.
6. **Gqom** — subtractive rhythm: broken 3-against-4 kicks, no four-floor, huge toms, dark bev vox stabs; euclid rotations `(5,8)` finally used as a groove not a footnote.
7. **Dub techno (Basic Channel)** — recipe exists, zero stems: one minor-9 stab where `.delayfeedback(.7)` on a dedicated orbit *is* the instrument, `s("crackle")`/pink noise beds (noise oscillators: 0 current uses).
8. **Gamelan / bell music** — inharmonic FM (`.fmh(1.618)`) or additive `.partials()` bells, colotomic structure (gong every 16 as a `cycles_per_phrase:16` texture stem), pelog approximated with explicit note lists. Non-4/4-adjacent without needing odd meter.
9. **Reich phasing / process minimalism** — the documented-but-never-a-piece trick: two identical mallet patterns, one `.slow(1.008)`, drifting through full phase over ~2 min. Ships as a `family:process` stem claiming chords+lead+pad.
10. **Musique concrète / plunderphonics** — `.scrub` (tape music in one call), `.striate`, `.speed(-1)`, `.coarse/.crush` over shabda-fetched freesound material **pre-cached during practice** (network live = banned). Texture-family, `key:none`, `meter:free`.

(Next tier: IDM/glitch via `.degradeBy`+ZZFX, trance, drone via `.partials()`, wavetable `wt_*` safari — 1000 AKWF waveforms untouched.)

## 5. Structural variety: families, meters, aleatoric

`family` is the anti-sameness field. **groove** stems fill the classic slots. **texture** stems remap the same 8 physical slots to a different role vocabulary (bed→pad-slot, gesture→lead-slot, punctuation→perc-slot, air→texture-slot, pulse→bass-slot) — kits declare their family so retrieval can be told "give me a texture-first set" and the drums slot legitimately stays empty (never-silent is satisfied by RMS, not by kick drums). **process** stems are self-contained evolving pieces (phasing, In-C-style cell advancement via `.iter`, slow euclid rotation through `<>` alternation) that `claims` multiple slots so the kit builder doesn't stack redundant harmony on top.

Non-4/4 lives in the `meter` field: 7-pulse cycles are just 7-element mini-notation bars; polymeter via `{a b c}%N`; stems only blind-combine when meters match or one side is `free`. Aleatoric stems (`choose`, `wchoose`, `degradeBy`, perlin-modulated filters) are first-class but flagged `deterministic:false` — legal in live kits, excluded from shows that must replay identically.

## 6. Arcs — the second asset kind

Energy arcs are **not stems**. An arc is a section script over slots:

```jsonc
{ "kind":"arc", "id":"arc.build-drop-breakdown.4x8", "sections":[
  {"len":8,"label":"intro",    "slots":{"drums":"sparse","bass":"full","chords":"sparse","lead":"off","pad":"full"}},
  {"len":8,"label":"build",    "slots":{"drums":"full","bass":"full","chords":"full","lead":"sparse","pad":"full"}},
  {"len":8,"label":"drop",     "slots":{"*":"peak"}},
  {"len":8,"label":"breakdown","slots":{"drums":"off","bass":"sparse","chords":"full","lead":"off","pad":"peak"}} ] }
```

This is why every stem ships **three intensity variants** (sparse/full/peak): the arc indexes into them. Two compile targets, both already supported by the engine:

- **arrange-compile** (autopilot mode): each slot's variants get wrapped into one `arrange([8,sparse],[8,full],[8,peak],[8,…]).play()` string — a self-evolving track needing zero further intervention. This is exactly the shape the 12 `autopilot/musicscenes/*.json` files already use, so the pattern is stage-proven.
- **step-compile** (showrunner mode): emit `livecode-show-v1` steps with `/show/mark` labels and per-step dwell (`8bars`) for arrow-key stepping via the existing server, no format changes.

Arcs also carry the visual handshake: section count (4/8) and per-section intensity array matching the autopilot section-clock contract (`window.state.cps`/`t0`), so any music arc syncs any visual skeleton at the same cps.

## 7. Bootstrapping: harvest before authoring

~150 stems exist before anyone writes a new one: 45 `scenes/*.py` functions (mechanical extraction — jazz.py's 5×drums/5×bass families become 2 templates × param dicts), 92 track strings inside `shows/full_show.show.json`, and the 12 `autopilot/musicscenes` files whose `arrange([8,…]×4)` structure *is* the 4-variant intensity form, retrofitted directly into `code:{sparse,full,peak}`. Then practice sessions run parallel subagents down the coverage matrix's empty cells: each subagent owns one genre column, authors stems against the header contract, and hands them to `stemverify.py` — post to a live server with `/show/recording {enabled:false}`, wait 2 s, assert track present in `/status`, `/errors` empty, cycle-0 RMS above threshold (add the ~30-line analyser bridge; superdough exposes one), write the `verified` block. Unverified stems never reach `index.json`. Target: 10 new genres × 5 slots × 2 stems × 3 variants ≈ 300 verified code bodies within a few practice sessions, on top of the harvested 150.

EXAMPLES
### EX
**Italo bass stem** (`library/stems/bass/bass.italo.octave-pump.01.stem.json`) — first real use of the .duck sidechain, add-note transposition, 3 intensity variants:
```json
{
  "id": "bass.italo.octave-pump.01", "kind": "stem", "engine": "strudel-track",
  "slot": "bass", "orbit": 3, "family": "groove",
  "genre": ["italo", "hi-nrg", "disco"], "mood": ["euphoric", "night-drive"], "energy": 4,
  "meter": "4/4", "cycles_per_phrase": 4,
  "key": {"root": "a", "mode": "minor", "family": "minor"},
  "transpose": {"method": "add-note"},
  "cps": {"written": 0.55, "min": 0.48, "max": 0.62, "density_flex": false},
  "gain": {"default": 0.72, "max": 0.90}, "deps": {"samples": []},
  "audible_cycle0": true, "deterministic": true,
  "params": {"root": {"type": "int", "default": 0}, "gain": {"type": "float", "default": 0.72}, "duck": {"type": "float", "default": 0.4}},
  "code": {
    "sparse": "note(\"a1 ~ ~ ~ a1 ~ a2 ~\").add(note(${root})).s(\"sawtooth\").shape(.3).lpf(700).attack(.004).decay(.09).sustain(.25).release(.08).gain(${gain}).room(.12).orbit(3).play()",
    "full": "note(\"a1 a2 a1 a2 a1 a2 a1 a2\").add(note(${root})).s(\"sawtooth\").shape(.3).lpf(sine.range(700,1600).slow(8)).attack(.004).decay(.09).sustain(.25).release(.08).duckorbit(1).duckattack(.02).duckdepth(${duck}).gain(${gain}).room(.12).orbit(3).play()",
    "peak": "note(\"<[a1 a2 a1 a2] [a1 a2 a1 a2] [c2 c3 c2 c3] [g1 g2 g1 g2]>\").add(note(${root})).s(\"sawtooth\").shape(.35).lpf(sine.range(900,2400).slow(4)).duckorbit(1).duckdepth(${duck}).gain(${gain}).room(.12).orbit(3).play()"
  },
  "verified": {"bundle": "strudel-web@1.0.3", "at": "2026-07-08T21:14:00Z", "rms_cycle0": 0.21}
}
```
Fire in F minor: compiler substitutes ${root}=-4, posts to /strudel/track as name "bass" — ~30 ms live.

### EX
**Reich phasing process stem** (`library/stems/chords/process.reich.mallet-phase.01.stem.json`) — family:process, claims three slots so the kit builder leaves harmony empty; the documented-but-never-used phasing trick as an actual piece:
```json
{
  "id": "process.reich.mallet-phase.01", "kind": "stem", "engine": "strudel-track",
  "slot": "chords", "orbit": 4, "family": "process", "claims": ["lead", "pad"],
  "genre": ["minimalism", "process"], "mood": ["hypnotic", "luminous"], "energy": 2,
  "meter": "free", "cycles_per_phrase": 1,
  "key": {"root": "e", "mode": "major:pentatonic", "family": "major"},
  "transpose": {"method": "scale-sub"},
  "cps": {"written": 0.45, "min": 0.38, "max": 0.55, "density_flex": false},
  "gain": {"default": 0.4, "max": 0.5}, "deps": {"samples": ["piano"]},
  "audible_cycle0": true, "deterministic": true,
  "params": {"root": {"type": "str", "default": "e4"}, "drift": {"type": "float", "default": 1.008}},
  "code": {
    "sparse": "n(\"0 2 4 7 9 7\").scale(\"${root}:major:pentatonic\").s(\"piano\").gain(.35).pan(.5).room(.4).orbit(4).play()",
    "full": "stack(n(\"0 2 4 7 9 7 4 2 0 4 7 9\").scale(\"${root}:major:pentatonic\").s(\"piano\").gain(.4).pan(.32), n(\"0 2 4 7 9 7 4 2 0 4 7 9\").scale(\"${root}:major:pentatonic\").s(\"piano\").gain(.4).pan(.68).slow(${drift})).room(.45).orbit(4).play()",
    "peak": "stack(n(\"0 2 4 7 9 7 4 2 0 4 7 9\").scale(\"${root}:major:pentatonic\").s(\"piano\").gain(.42).pan(.25), n(\"0 2 4 7 9 7 4 2 0 4 7 9\").scale(\"${root}:major:pentatonic\").s(\"piano\").gain(.42).pan(.75).slow(${drift}), n(\"0 4 9\").scale(\"${root}:major:pentatonic\").s(\"triangle\").attack(.5).release(2).gain(.15).slow(4)).room(.5).orbit(4).play()"
  },
  "verified": {"bundle": "strudel-web@1.0.3", "at": "2026-07-08T21:40:00Z", "rms_cycle0": 0.14}
}
```
The .slow(1.008) copy drifts through full phase over ~2 minutes — structure emerges with zero further commands, ideal for the 60 s autopilot wake cadence.

### EX
**Kit + arc, arrange-compiled** — the curated performance unit and what the compiler emits for one slot. Kit file `library/kits/italo.night-drive.kit.json`:
```json
{
  "kind": "kit", "id": "italo.night-drive",
  "cps": 0.55, "key": {"root": "f", "mode": "minor"},
  "stems": {
    "drums": "drums.italo.four-floor-linn.01",
    "perc": "perc.italo.rz1-shaker.01",
    "bass": "bass.italo.octave-pump.01",
    "chords": "chords.italo.saw-stabs.02",
    "lead": "lead.italo.arp-runs.01",
    "pad": "pad.warm.supersaw-slow.03"
  },
  "arc": "arc.build-drop-breakdown.4x8",
  "section0_audible": ["drums", "bass", "pad"],
  "visual_pair_hints": {"sections": 4, "intensity": [0.4, 0.7, 1.0, 0.3]}
}
```
`stemc.py fire kit:italo.night-drive` resolves each stem's 3 variants through the arc and posts ONE self-evolving string per slot, e.g. the bass track becomes:
```js
arrange(
  [8, note("a1 ~ ~ ~ a1 ~ a2 ~").add(note(-4)).s("sawtooth")/* sparse */.orbit(3)],
  [8, note("a1 a2 a1 a2 a1 a2 a1 a2").add(note(-4))/* full, ducked */.orbit(3)],
  [8, note("<[a1 a2 a1 a2] …>").add(note(-4))/* peak */.orbit(3)],
  [8, note("a1 ~ ~ ~ a1 ~ a2 ~").add(note(-4))/* sparse again = breakdown */.orbit(3)]
).play()
```
Same kit, `--target show` instead emits livecode-show-v1 steps with /show/mark labels and dwell "8bars" per section for arrow-key stepping. Total live fire: samples preamble (cached) + 1 cps curl + 6 track curls ≈ under half a second.

### EX
**Musique concrète texture stem** (`library/stems/texture/texture.concrete.tape-scrub.01.stem.json`) — texture family, no key, free meter, shabda dependency pre-cached at practice time:
```json
{
  "id": "texture.concrete.tape-scrub.01", "kind": "stem", "engine": "strudel-track",
  "slot": "texture", "orbit": 7, "family": "texture",
  "genre": ["concrete", "plunderphonics", "experimental"], "mood": ["uncanny", "archival"], "energy": 2,
  "meter": "free", "cycles_per_phrase": 1,
  "key": {"root": null, "mode": null, "family": "none"},
  "transpose": {"method": "none"},
  "cps": {"written": 0.45, "min": 0.30, "max": 0.70, "density_flex": true},
  "gain": {"default": 0.30, "max": 0.30},
  "deps": {"samples": ["shabda:field-recording-train"]},
  "audible_cycle0": true, "deterministic": false,
  "params": {"gain": {"type": "float", "default": 0.3}},
  "code": {
    "sparse": "s(\"train\").scrub(sine.range(0.1, 0.4).slow(16)).coarse(3).lpf(2400).gain(${gain}).room(.5).orbit(7).play()",
    "full": "stack(s(\"train\").scrub(perlin.range(0, 0.8).slow(8)).coarse(4), s(\"train\").striate(16).speed(\"<-1 0.5 -0.5>\").degradeBy(.4).crush(6)).lpf(3200).gain(${gain}).room(.55).orbit(7).play()",
    "peak": "stack(s(\"train\").scrub(perlin.range(0, 1).slow(4)).coarse(6), s(\"train\").striate(32).speed(\"<-2 1.5 -0.5 0.25>\").ply(\"<1 2 3>\").crush(4)).hpf(300).gain(${gain}).room(.6).orbit(7).play()"
  },
  "verified": {"bundle": "strudel-web@1.0.3", "at": "2026-07-09T10:02:00Z", "rms_cycle0": 0.09}
}
```
packs.json entry `shabda:field-recording-train` records the exact samples() snippet and requires a practice-session CacheStorage warm; stemverify refuses to mark it verified if the fetch happens at fire time. deterministic:false (perlin + degradeBy) flags it as excluded from replay-identical shows.

RISKS
- Documented-but-unused Strudel features may not exist in the @strudel/web 1.0.3 CDN bundle — .swingBy already threw a real error on stage, and this design leans on .duckorbit, .scrub, .striate, .vowel, .fm/.fmh, .partials, noise oscillators, and .add(note(n))-based transposition. A bundle smoke-test matrix (one 5-second verification per feature against the live server) must run BEFORE mass-authoring stems on any of them, or whole genre columns get built on APIs that silently no-op.
- Metadata prevents clashes, not blandness: blind combination of compatible stems yields harmonically/rhythmically legal but aesthetically dead mixes. Kits (practice-curated bundles) must stay the primary performance unit, with blind combination as the fallback — if the workflow drifts to pure grep-and-stack, the 'too predictable' problem returns wearing a schema.
- Verification staleness: 'verified' blocks are pinned to strudel-web@1.0.3 and CDN-hosted sample packs; a CDN change, pack 404 (strudel-samples already died), or bundle upgrade invalidates hundreds of stems silently. Needs a periodic re-verify sweep, and the kiosk-mode fresh-Chrome-profile issue must be fixed (persistent user-data-dir) or every performance starts with a cold sample cache regardless of practice warming.
- Whole-stack re-eval cost grows with the library's ambition: 6-8 slots each carrying a 4-section arrange() string makes every single track update re-transpile a very large stack(); if that pushes browser eval toward the 5 s timeout, gapless slot-swaps degrade. Budget code-body size per stem and measure re-eval latency at 8 full arrange tracks early.
- Gain budgets without a master compressor are advisory physics: peak sections stacking 6 verified stems at their individual maxima can still clip in ways per-stem RMS verification never sees. A practice-time full-kit render check (or adopting .compressor on a master orbit if the bundle supports it) is needed, not just per-stem lint.
- Harvest quality risk: the ~150 extracted stems inherit today's A-minor/909/saw monoculture, and retrofitting them with honest key/cps/energy metadata is judgment work, not mechanical work — mislabeled harvested stems poison blind combination worse than no metadata because the compiler trusts them.
- Authoring throughput is still LLM-bound: 300+ new verified code bodies is many hours of practice-session subagent time, and automated verification only checks audibility/errors/RMS — groove quality still requires listening. Budget for a human-in-the-loop cull pass or accept a library where a third of entries are technically-valid filler.
- Aleatoric stems (deterministic:false) break the reproducibility doctrine if they leak into saved shows — the .show.json will replay different audio than what was performed. The step-compiler must either reject them or freeze a rendered choice at compile time, and this edge needs a test in test_steps.py before it bites during an archival replay.