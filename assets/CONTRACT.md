# The Asset Contract — livecode catalog v1

Shared framework for the **visual factory** and **music factory** sessions and for
every subagent they spawn. Anything that enters the catalog MUST follow this
contract. An asset that ignores it will misbehave when composed with others on
stage — the whole point of the catalog is that any assets can be combined blind.

## Principles

1. **Performance = retrieval + parameters, never code generation.** Assets are
   pre-written, pre-verified, parametric code. On stage the agent greps the
   index, fills params, and fires curls.
2. **Verified or invisible.** Assets without a `verified` stamp never enter
   `index.jsonl`. Validation is mechanical (`assets/tools/validate.py`), not
   asserted.
3. **Durable and in-repo.** Everything lives under `assets/`. Never `/tmp`
   (a previous 90-scene library evaporated there on reboot).
4. **Indexes are generated, never hand-edited** (`assets/tools/build_index.py`).
   Hand-maintained catalogs in this repo have already rotted once.
5. **Never static.** Every asset must visibly/audibly evolve on its own.
   Target: internal dramaturgy over 30s–5min with zero agent intervention.
6. **Tags are the retrieval surface.** Gene types prose on stage ("ducks and
   dogs on a disco floor") and the agent greps. Tag generously: synonyms,
   categories, moods, colors, genres. A brilliant asset with poor tags is lost.

## Runtime facts (engine v2 — patched 2026-07-10)

The browser (`livecode.html`, VERSION 2) provides two global read-only objects,
updated every frame, that ALL assets sync to:

### `window.state.clk` — the clock authority

```js
{ t,          // seconds since state.t0
  cps,        // current cycles/sec (server pushes on every /strudel/cps)
  beat,       // continuous beat counter (4 beats per cycle)
  bar,        // beat/4
  cyc,        // fraction through current cycle 0..1
  phase,      // fraction through current beat 0..1 (0 at each beat onset)
  pulse,      // pow(1-phase, 3) — spikes to 1 on the beat, decays. Use for kicks/flashes.
  swell,      // sin half-wave over the beat — smooth breathe
  section,    // 0..7, advances every state.secBeats beats (default 32 = 8 bars)
  intensity,  // state.arc[section] — default [.2,.4,.7,.9,.3,.6,1,.4]
  fps }       // measured frame rate
```

- **NEVER use `frameCount`-based beat math** (`frameCount/28.8` is banned — it
  breaks below 60fps and on tempo change). Derive ALL rhythm from `clk`.
- `state.secBeats` and `state.arc` are overridable per scene (music arcs set them
  so visual intensity tracks the musical arc).
- Scene transitions null `state.t0` (via `/p5/state {"key":"t0","value":null}`)
  to restart the section arc. Assets must tolerate `t0` resetting at any time.

### `window.state.audio` — the audio-reactive bridge

```js
{ bass,     // 0..1  ~21–172 Hz   (kick, sub)
  lowmid,   // 0..1  ~172–516 Hz
  mid,      // 0..1  ~516 Hz–2.6 kHz
  treble,   // 0..1  ~2.6–11 kHz  (hats, air)
  rms,      // 0..~0.5 true RMS of the output signal
  fft }     // 32 log-packed bins, each 0..1
```

- Visual assets SHOULD be audio-reactive where it reads as musical (glow on
  bass, sparkle on treble, size on rms) but must look intentional in silence —
  always blend audio on top of a clk-driven baseline, never multiply by it.
- Music validation uses `rms` as the audibility gate.

### Other engine facts

- Canvas: p5 1.11.11 global mode, 2D, `pixelDensity(1)`,
  `colorMode(HSB, 360, 100, 100, 100)`, full-window, resizable at any time.
- Layer code runs inside `draw()` every frame via `new Function(code)` — no
  imports, no async, no top-level `return`. Auto-wrapped in `push()/pop()`.
- Layer z-order = insertion order; replacing a layer by name keeps its position.
- Syntax errors keep the OLD layer running; runtime errors are caught per-layer
  (throttled 1/s) and appear in `GET /errors`.
- `GET /p5/read?key=<dotted.path>` returns any `window.state` value as JSON
  (used by validation/review tools: `key=clk`, `key=audio`).
- Every accepted `/strudel/*` and `/p5/*` POST auto-records into the show
  timeline. **Factories must POST `/show/recording {"enabled":false}` at
  session start.**
- The HTTP server is single-threaded — serialize validation traffic per server;
  parallelize *authoring* (pure text), not server calls.
- Strudel: every `/strudel/track` update re-evaluates ALL tracks as one
  `stack()`. One malformed track silences everything → validation is per-stem
  AND per-kit.
- Known broken in the @strudel/web 1.0.3 bundle: `gm_*` soundfonts, `setcps()`,
  `.swingBy()`, `github:tidalcycles/strudel-samples` (404). Never use.

---

## Visual contract

### Slot vocabulary (fixed)

Scenes bind assets to named layer slots, installed in this canonical z-order:

```
bg → floor → setA → setB → subA → subB → subC → crowd → fxA → fxB → post
```

| kind    | legal slots        | what it is |
|---------|--------------------|------------|
| world   | bg                 | full-bleed background (cached buffer) |
| floor   | floor              | ground/stage plane |
| set     | setA, setB         | mid-ground scenery & props (DJ booth, mirror ball, trees) |
| subject | subA, subB, subC   | figurative hero — character/creature/vehicle, posable |
| crowd   | crowd              | N-instance renderer (dancers, flock, traffic) |
| fx      | fxA, fxB           | atmospheric overlays (confetti, lasers, rain, fireflies) |
| post    | post               | full-screen last pass (beat flash, feedback zoom, vignette, grain) |
| genart  | bg                 | self-sufficient generative piece (claims bg; scene skips world/floor) |
| palette | —                  | data only: named HSB swatch set |

### The P-block preamble (mandatory, byte-for-byte pattern)

Every visual asset's `code` starts with:

```js
const D = { hue: 205, energy: .6, speed: 1, density: .5, scale: 1, x: .5, y: .8 /*, extras…*/ };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };
```

- `__SLOT__` is the ONLY template token; binding = `code.replace(/__SLOT__/g, slot)`.
  Deployed code is fully literal (reproducibility doctrine: shows never
  reference the library).
- **The universal seven** — `hue, energy, speed, density, scale, x, y` — must be
  honored by every asset with the same semantics everywhere (`hue` 0–360 primary
  hue; `energy` 0–1 motion/glow amplitude; `speed` beats-relative rate multiplier;
  `density` 0–1 element count; `scale` vs design size; `x/y` anchor as canvas
  fraction). Kind-specific extras (`pose`, `props`, `n`, `pal`, `spots`…) are
  declared in `params` with default/min/max/doc.
- Live retune = `POST /p5/state {"key":"P.subA","value":{"hue":140}}` — ~10ms,
  no recompile. Params must be readable EVERY frame (no caching P values into S
  at first run — poke must take effect immediately).
- **Private state only under `S`** (i.e. `window.state.<slot>`). Never write any
  other `window.state` key. Self-init from undefined (transitions null your slot
  state). Cached `createGraphics` buffers live in `S`, keyed on size:
  `if (!S.bg || S.bgKey !== width+'x'+height) { …rebuild…; S.bgKey = width+'x'+height; }`

### Performance budget (validated, not advisory)

- fps ≥ 25 solo in the validation cell (stage floor is 20 with a full scene).
- Static content MUST be pre-rendered into a cached `createGraphics` buffer
  (never per-scanline gradients in the draw loop).
- Particle budgets: ≤ ~150 heavy (drawn shapes w/ alpha), ≤ ~500 points.
- `blendMode(ADD)` alpha ≤ 35 on shapes larger than ¼ canvas; light beams must
  terminate on-screen; always assume an opaque `bg` exists below you.
- Resolution-agnostic: scale by `min(width,height)`; never bake pixel constants.

### Never-static + acts

- Validation snapshots at t and t+8s must differ (and not strobe). Beyond that,
  design assets whose *character* evolves over 30s–5min: use `K.section` /
  `K.intensity` for arcs, `K.t` for slow drift, and optionally an `acts`
  program: read `P.act` (a string) and switch behavior — so one asset offers
  multiple multi-minute dramaturgies selectable at fire time without recompose.

---

## Music contract

### Slot → orbit table (fixed; one stem per slot; effects are per-orbit globals)

```
drums=1  perc=2  bass=3  chords=4  lead=5  pad=6  texture=7  vox=8
```

Track name = slot name = orbit owner. Every stem sets `.orbit(N)` matching its
slot and owns that orbit's `room/delay` settings.

### Stem rules

- `code` bodies are **`string.Template` `${param}` templates** (never Python
  f-strings — JS braces make f-strings untenable).
- Every variant ends with exactly one `.play()`. **Never `.cps()`** — the server
  is the single tempo authority (`/strudel/cps`).
- **Three intensity variants required**: `sparse`, `full`, `peak`. Arcs index
  into them; energy becomes a retrieval parameter instead of a rewrite.
- **Audible-from-cycle-0** for `full` and `peak` (validated via `audio.rms`
  within 2.5s). No slow-attack silent intros on those variants.
- **Key & transposition** (kills the everything-in-A-minor monoculture):
  - `transpose: "scale-sub"` — melodic content as `n("0 2 4…").scale("${root}${oct}:${mode}")`
  - `transpose: "add-note"` — `note(...)` content + compiler appends `.add(note(${root}))`
  - `transpose: "none"` — unpitched (drums/noise/concrète) or unmovable chord symbols
- **cps window** declared honestly: `{written, min, max}` — the range where the
  groove's feel survives. Cross-genre combination intersects windows.
- **Gain budgets** (defaults; `max` enforced): drums .90, perc .50, bass .90,
  chords .50, lead .45, pad .35, texture .30, vox .50.
- `deps`: sample-pack names resolved via `assets/music/packs.json` (each entry:
  name → exact `samples(...)` snippet). Load deps via `/strudel/send` BEFORE
  dependent tracks; wait 2–3s. Only packs proven to load may be listed.
- `deterministic: false` for stems using `choose/wchoose/degradeBy/perlin` —
  legal live, excluded from replay-identical shows.
- `claims`: extra slots this stem makes redundant (process pieces claiming
  chords+lead+pad so kits don't stack harmony on top).

### Kits and arcs (the performance units)

- **Kit** = curated bundle: `{name, desc, cps, key, stems: {slot: stem_id}, arc, tags}`.
  Kits are the primary unit fired on stage; blind slot-sampling is the fallback.
  Every kit must have ≥2 slots audible in section 0.
- **Arc** = section script over slots:
  `{sections: [{cycles, label, slots: {"drums":"full","lead":"off",…,"*":"peak"}}]}`.
  Compiled via `arrange([cycles, variant]…)` into ONE self-evolving string per
  slot — the music breathes for minutes with zero further commands.
  **Total duration 30s–5min** at the kit's cps. Ship multiple arcs per kit
  (e.g. `build_drop`, `slow_burn`, `breakdown_first`) for runtime optionality.
- Arcs carry the visual handshake: on fire, push `secBeats` (= section cycles×4)
  and the per-section `arc` intensity array to `/p5/state`, and null `t0` — the
  visual section clock then tracks the musical arc by construction.

---

## File formats

### Visual asset — `assets/visual/<dir>/<id>.json`

Kind → directory map (dirs are pluralized where natural): world→`worlds`,
floor→`floors`, set→`sets`, subject→`subjects`, crowd→`crowds`, fx→`fx`,
post→`post`, genart→`genart`, palette→`palettes`.

```json
{ "format": "livecode-visual-v1",
  "id": "subject.penguin_dj",
  "kind": "subject",
  "name": "Penguin DJ",
  "desc": "Chubby penguin at the decks, beat-synced head-bob, flipper-scratch.",
  "tags": ["penguin","bird","animal","dj","music","club","cute","character"],
  "slots": ["subA","subB","subC"],
  "budget": "light",
  "params": { "hue": {"default":205,"min":0,"max":360,"doc":"body hue"},
              "pose": {"default":"dj","options":["dj","dance","idle","wave"],"doc":"pose preset"} },
  "acts": null,
  "deps": [],
  "verified": null,
  "code": "const D = { hue:205, … };\n…draw body…" }
```

(Palette assets: `"kind":"palette"`, a `"values"` object, no code/slots.)

### Music stem — `assets/music/stems/<slot>/<id>.json`

```json
{ "format": "livecode-stem-v1",
  "id": "bass.italo.octave_pump.01",
  "kind": "stem",
  "slot": "bass", "orbit": 3,
  "name": "Italo octave pump",
  "desc": "Eighth-note octave bass with filter sweep and sidechain pump.",
  "tags": ["italo","disco","bass","pump","euphoric","night"],
  "genre": ["italo","hi-nrg","disco"], "mood": ["euphoric"], "energy": 4,
  "meter": "4/4", "cycles_per_phrase": 4,
  "key": {"root":"a","mode":"minor"}, "transpose": "add-note",
  "cps": {"written":0.55,"min":0.48,"max":0.62},
  "claims": [], "deterministic": true, "deps": [],
  "params": {"root":{"default":0,"doc":"semitone offset"}, "gain":{"default":0.72,"max":0.9}},
  "code": {"sparse":"…${root}…​.orbit(3).play()",
           "full":"….orbit(3).play()",
           "peak":"….orbit(3).play()"},
  "verified": null }
```

Kits: `assets/music/kits/<id>.kit.json` (`livecode-kit-v1`).
Arcs: `assets/music/arcs/<id>.arc.json` (`livecode-arc-v1`).

### Index & review

- `assets/visual/index.jsonl`, `assets/music/index.jsonl` — GENERATED by
  `assets/tools/build_index.py`; one line per verified asset:
  `{id, kind, slot?, tags, blurb, energy?, cps?, key?, budget?, params, grade, path}`.
  Also emits a grep-friendly `INDEX.md` next to each.
- `assets/review.jsonl` — append-only grades from `assets/tools/review.py`:
  `{ts, id, grade (1–5), note}`. Latest grade per id wins; folded into the index.
- **Taste grading (browser, preferred):** the visual grader (`grade.html`) and the
  music browser (`assets/music/browse.html`) record a simpler `{ts, id, grade}`,
  grade ∈ {bad, ok, good}, via `POST /music/grade` → `assets/music/grades.jsonl`
  (latest-per-id wins). `good` = reinforce Gene's taste; `bad` = delete via
  `assets/tools/prune_graded.py` (soft-moves to `graveyard/`, kept as an RL signal).

## Validation gates (what `assets/tools/validate.py` enforces)

| Gate | Visual | Music |
|------|--------|-------|
| compiles / deploys clean | ✓ | ✓ (all 3 variants) |
| `/errors` delta empty | ✓ | ✓ |
| fps ≥ 25 (`/p5/read?key=clk`) | ✓ | — |
| motion: snapshots differ, don't strobe | ✓ | — |
| luminance not white/blackout | ✓ | — |
| audible: peak `audio.rms` > 0.01 within 2.5s (polled at 0.2s — sparse patterns read 0 between notes) | — | ✓ (full & peak; sparse > 0.003) |
| params respond (poke → output changes) | ✓ | — |
| schema fields valid | ✓ | ✓ |

Passing stamps `verified: {at, …metrics}` into the asset file. Unverified
assets sit in `inbox/` and never reach the index.

**Music kits additionally** must pass `assets/tools/verify_arcs.py`: fired
through each recommended arc, EVERY section must be audible. `validate.py` only
fires a kit at all-`full` and never through an arc, so a kit can pass it and
still go silent in an arc's sparse intro/breakdown/outro. This is a required
pre-handoff gate; arcs carry a `"*":"sparse"` floor on thin sections so any kit
stays audible. See `assets/music/README.md`.

## Authoring checklist for subagents (the short version)

**Visual:** P-block preamble verbatim · read `K` for all rhythm · blend `A` on
top of a baseline · state only under `S` · cached buffers for static content ·
resolution-agnostic · HSB · respect budget caps · never-static · tag generously.

**Music:** `${param}` templates · 3 variants · `.orbit()` per the table · ends
`.play()` · no `.cps()` · honest cps window · declared key + transpose method ·
gain ≤ budget · deps from packs.json only · audible-from-cycle-0 · tag generously.

**Both:** one JSON file per asset in `inbox/` → validate → it moves to its kind
directory → rebuild index. Never edit `index.jsonl` by hand. Never use `/tmp`.
Never touch the other domain's subtree.
