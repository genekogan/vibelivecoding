# Visual asset author brief — factory v1

You are one of many parallel authors filling `assets/visual/inbox/` with
p5.js visual assets for Gene's AI live-coding performance system. Read
`assets/CONTRACT.md` first if you haven't. This brief adds the factory-run
specifics and the exact validation gates your asset must pass.

## Absolute rules

- Write ONE JSON file per asset: `assets/visual/inbox/<id>.json`.
- **NEVER call the server.** No curl, no HTTP. You produce text files only.
  A single orchestrator validates against the live canvas serially.
- Never touch `assets/music/**`, `index.jsonl`, `INDEX.md`, or other authors'
  files. Never use `/tmp`.
- Filename = `<id>.json` exactly (e.g. `subject.penguin.json`).

## Asset JSON schema (all fields required unless noted)

```json
{ "format": "livecode-visual-v1",
  "id": "subject.penguin",            // must match ^<kind>\.[a-z0-9_.]+$
  "kind": "subject",                  // world|floor|set|subject|crowd|fx|post|genart|palette
  "name": "Penguin",
  "desc": "One vivid sentence a performing agent can match prose against.",
  "tags": ["penguin","bird","animal","waterfowl","cute","waddle","arctic","dance","character"],
  "slots": ["subA","subB","subC"],    // world/genart:["bg"] floor:["floor"] set:["setA","setB"]
                                      // subject:["subA","subB","subC"] crowd:["crowd"]
                                      // fx:["fxA","fxB"] post:["post"]
  "budget": "light",                  // light|medium|heavy (honest)
  "params": { ... },                  // see below
  "acts": null,                       // or ["build","drift"] if you implement P.act
  "deps": [], "verified": null,
  "code": "..." }
```

Palette assets: `{"format","id" (palette.<slug>),"kind":"palette","name","desc","tags","values":{...}}` —
`values` maps swatch names to `[h,s,b]` triples (HSB 360/100/100). No code/slots/params.

## The P-block preamble — copy this shape byte-for-byte at the top of `code`

```js
const D = { hue: 205, energy: .6, speed: 1, density: .5, scale: 1, x: .5, y: .8, style: 'flat', seed: 0 /*, extras…*/ };
const P = Object.assign({}, D, (window.state.P && window.state.P.__SLOT__) || {});
const S = window.state.__SLOT__ || (window.state.__SLOT__ = {});
const K = window.state.clk || { t:0, cps:.5, beat:0, bar:0, cyc:0, phase:0, pulse:0, swell:0, section:0, intensity:.6, fps:60 };
const A = window.state.audio || { bass:0, lowmid:0, mid:0, treble:0, rms:0, fft:[] };
```

- `__SLOT__` is the ONLY template token — never hardcode a slot name.
- `D` defaults must equal the `params` defaults in the JSON.
- Read `P.*` EVERY frame (never cache P values into S — live pokes must take
  effect immediately).
- ALL private state under `S` only. Self-init from undefined. Cached buffers in
  `S`, keyed on size: `if (!S.bg || S.key !== width+'x'+height) { ...; S.key = width+'x'+height; }`
- Tolerate `t0` resets (K.t/K.beat can jump backwards at any time): never store
  "last beat" assumptions that break on reset — guard with
  `if (S.lastBeat == null || K.beat < S.lastBeat) S.lastBeat = K.beat;`

## The universal seven + factory-mandatory extras

Every code asset honors: `hue` (0–360 primary hue), `energy` (0–1 motion/glow
amplitude), `speed` (beats-relative rate multiplier), `density` (0–1 element
count), `scale` (vs design size), `x`/`y` (anchor as canvas fraction).

**Factory-mandatory on every code asset (Gene's macro/micro versatility ask):**

1. **`style`** — an options param with **≥3 named looks** that genuinely change
   the aesthetic: different palette discipline, stroke/fill treatment, texture,
   shading — NOT just a hue shift. Your work order assigns a primary style
   discipline; that's the default. Add 2–4 more from a different family
   (e.g. a neon asset also offers "riso", "ink", "pastel").
   Example: `"style": {"default":"riso","options":["riso","ink","neon","paper"],"doc":"aesthetic"}`
2. **`seed`** — `{"default":0,"min":0,"max":9999}` int. All randomness must be
   seed-deterministic so a look is reproducible. Use an inline hash, NOT p5
   `random()`/`randomSeed()` (global pollution across layers):
   ```js
   const fr = i => { const s = Math.sin(i*127.1 + P.seed*311.7) * 43758.5453; return s - Math.floor(s); };
   ```
   Rebuild seed-dependent cached structures when the seed changes:
   `if (S.seedUsed !== P.seed) { S.seedUsed = P.seed; ...rebuild...; }`
3. **Stretched safe ranges** — give every numeric generous min/max that stays
   safe at BOTH extremes (the validator pokes params to max). Where the form
   allows it, add 1–3 proportion morphs (`chub`, `limb`, `neck`, `wobble`… 0–1)
   so one template covers many bodies/moods.

Kind-specific extras: subjects need `pose` (≥3 options incl. an idle + a
dance/action, beat-synced motion per pose); crowds need `n` (int, honest max)
+ `pal`; sets/fx as fits (e.g. neon sign takes `text`).

## Never-static + audio (both are validated)

- The asset must visibly evolve with ZERO param changes: snapshots 8s apart
  must differ. Use `K` for all rhythm — `K.pulse` (beat kick), `K.swell`
  (breathe), `K.beat*P.speed` for cycles, `K.section`/`K.intensity` for
  30s–5min arcs, `K.t` for slow drift. `frameCount`-based beat math is BANNED
  and mechanically rejected (`frameCount/28.8` etc.).
- Design a dramaturgy: something should be different a minute in (section-
  indexed behavior changes, slow builds, color drift, population growth).
  Where it fits, implement `P.act` — 2–3 named multi-minute programs.
- Audio-reactivity ON TOP of the clk baseline: e.g.
  `const kick = K.pulse*.6 + A.bass*.8;` glow on bass, sparkle on treble,
  sway on lowmid, size on rms. **During validation audio may be all zeros —
  the baseline alone must carry the motion gate.** Never multiply core motion
  by `A.*`.

## Validation gates — exact numbers (fail any → you get ONE requeue)

| Gate | Threshold |
|---|---|
| schema | id regex, legal slots, params have defaults, code contains `__SLOT__` and `window.state.clk`, no `frameCount/<digit>`, no `createCanvas`, no `setcps` |
| deploy | compiles via `new Function`; zero entries in `/errors` tagged with your slot for 2s |
| fps | ≥ 25 solo (bed background + your layer only) |
| motion | mean grayscale diff of 320px snapshots at t and t+8s must be **> 0.004** (not static) and **< 0.35** (not strobing). Full-frame flashes/inversions WILL trip 0.35 — keep flash amplitude partial (post assets especially). |
| luminance | frame mean in **[0.02, 0.92]** — never near-black or near-white frames |
| params | the FIRST TWO numeric params in your `params` object are poked to their **max** together; the render must change by > 0.003. **Order your params so the first two numerics produce an obvious visual change at max** (energy, scale, density are good; `hue` first is risky — hue max 360 wraps to red ≈ hue 0). |
| runtime | validator renders you over a plain `background(240,30,12)` bed (subjects/sets/fx/etc.) or alone (world/genart) |

## Performance budget (stage floor is 20fps with ELEVEN layers composed)

- Pre-render static content into cached `createGraphics` buffers keyed on size.
  Never per-scanline gradients or thousand-shape loops directly in draw.
- ≤ ~150 heavy shapes (alpha/blended), ≤ ~500 points. Respect `density`.
- **NO full-canvas `filter(...)` — measured ~12ms/frame.** Fake blur/glow with
  layered translucent shapes, pre-blurred sprite stamps (blur a small buffer
  ONCE at build), or `drawingContext.shadowBlur` on FEW shapes (reset to 0 after).
- `blendMode(ADD)` alpha ≤ 35 on shapes larger than ¼ canvas; ALWAYS restore
  `blendMode(BLEND)` at the end of your code.
- Resolution-agnostic: `const u = Math.min(width,height);` scale everything by
  `u*P.scale`, anchor at `P.x*width, P.y*height`. No baked pixel constants.
  Canvas can resize any frame (rebuild size-keyed caches).
- Colors: HSB (`colorMode` is already HSB 360/100/100/100 — do NOT call colorMode).

## Confirmed engine capabilities (probed live — see assets/visual/BUNDLE.md)

`createGraphics` ✓ · `drawingContext` clip/shadow ✓ · blendMode ADD/MULTIPLY/SCREEN ✓ ·
`text()`/`textFont` with system fonts ✓ · `loadImage('/repo/path')` ✓ (but no
curated images exist — draw everything with code) · full-canvas `filter()` ✗ (too slow).

## Craft bar (what "good" means here)

The reference is `compositions/scripts/disco_dancers.py`: parametric pose rigs
(limb angles as data), beat-indexed choreography with snap/lerp easing, layered
shading, silhouettes that read at 50px and at 500px. Subjects have personality:
eyes, weight shifts, anticipation before beats (use `K.phase` to prepare, land
on `K.pulse`). Avoid: centered-radial-rainbow default look, uniform HSB cycling,
motionless clipart with a sine bob. Curves (`beginShape`/`bezierVertex`) over
primitive-only bodies where the form calls for it.

## AESTHETIC MANDATE — escape the cartoon default (Gene's directive)

First-wave assets ALL came out reading "cute cartoon": thick outlines, flat
fills, big friendly eyes, rounded blob bodies, one bounce. Competent but a
monoculture. **Your job now is aesthetic DIVERGENCE.** Each template should feel
like it came from a different artist. Push edgy / experimental / sophisticated:

- **Your assigned `style` default is the ANCHOR — commit hard, make it
  NON-cartoon.** "ink-wash" → real brushed sumi (dry-brush edges, bleed, tonal
  washes), not grey cartoon fill. "brutalist" → hard concrete, harsh raking
  shadow, monochrome, weight. "riso" → true 2-ink misregistration + halftone.
- **At least ONE style option per asset must be non-representational or
  radically abstracted** — from: wireframe / X-ray / anatomical, single
  continuous contour line, pure silhouette (no interior), glitch-fractured /
  datamoshed, low-poly faceted, halftone/CMYK print, ASCII/dot-matrix,
  cubist-fragmented, blueprint/schematic, chiaroscuro (form from light only, no
  outline), stippled/hatched engraving, iridescent/oil-slick, thermal false-color.
- **Rendering philosophy varies, not just palette.** Options differ in HOW form
  is built: outline-vs-mass, hard-vs-soft edge, flat-vs-modeled light,
  geometric-vs-organic, clean-vs-degraded. A hue swap is NOT a style.
- **Texture beats flat fill** — hatching, stippling, scanlines, grain, gradient
  mapping, layered translucency, `shadowBlur` on few shapes. Big flat HSB fills
  are the cartoon tell; break them up.
- **Line quality is a choice** — vary strokeWeight expressively; tapered / wobbly
  / broken / doubled lines, or no outline at all (mass and shadow only).
- **Mood range** — not everything is a happy party. Allow eerie, austere,
  melancholy, menacing, sacred, clinical, decayed, sublime. Let `hue`/palette
  extremes reach desaturated, near-monochrome, and dark-key — not only brights.
- Edgy ≠ noisy mush: composition and contrast still rule, stay performant. But
  default to the sophisticated/experimental read over the cute one.

## Workflow for each asset you author

1. Design: subject + assigned style discipline + variant axes + dramaturgy.
2. Write the code as a plain JS snippet first (mentally or in scratch), then
   embed in JSON (escape newlines as `\n`).
3. **Syntax-check before writing the final file** (node is available):
   `node -e 'const c=require("fs").readFileSync("<tmpfile>","utf8"); new Function(c.replace(/__SLOT__/g,"subA")); console.log("OK")'`
   — write the raw JS to a scratch file for this check, then produce the JSON.
4. Validate JSON parses: `python3 -c 'import json;json.load(open("assets/visual/inbox/<id>.json"))'`
5. Self-review against the gates table above — especially: params order,
   motion baseline without audio, style options actually differ, seed rebuild.

Tags: ≥8, generous synonyms ("duck" → duck bird animal waterfowl quack pond
yellow cute), categories, moods, colors, era/genre words. `desc` is one vivid
sentence — Gene's prose gets grepped against desc+tags.

## Design size & motion amplitude (added after first validation failures)

Live-canvas evidence: a well-rigged character occupying ~3% of the frame reads
as STATIC on the 320px motion gate (mean-diff 0.003 < 0.004) no matter how it
flails. Rules:

- **Subjects**: at `P.scale=1` the hero stands **0.40–0.55 × min(width,height)
  tall**. It's a stage hero, not scenery.
- **Baseline motion must displace the silhouette**: whole-body bob/sway/steps
  of ≥5% of body height + limb swings — not just outline wiggles or eye blinks.
- **Sets/fx**: the animated portion should sweep ≥10% of the frame area over
  8s (beams move, particles cross, cones pump).
- **Param poke sanity**: with the first two numeric params at max, the render
  must OBVIOUSLY differ (e.g. scale max ≥ 1.8 → nearly double size; energy max
  → exaggerated dance). If max just looks like default, the gate fails you.

## Motion re-phasing & luminance — the two silent killers (distilled from 130+ assets)

1. **Re-phasing (the #1 cause of a "STATIC" fail on a piece that clearly moves).**
   The motion gate compares snapshots **8 s apart**. Two ways to accidentally read
   as frozen: (a) motion driven **only** by `K.beat/K.pulse/K.cyc` — at cps≈0.5, 8 s
   ≈ 16 beats, so it's byte-identical 8 s later; (b) a **single-frequency `K.t`**
   animation whose period lands near 8 s (`sin(K.t*0.8)` has period ~7.85 s → returns
   to nearly the same pose). **Fix:** always carry a real-time `K.t` motion floor built
   from **incommensurate frequencies** so the pose never repeats, e.g.
   `0.9*Math.sin(K.t*0.61) + 0.5*Math.sin(K.t*1.43+1.7) + 0.32*Math.sin(K.t*2.29)`.
   For rotating/attractor pieces, rotate on **two incommensurate rates**. Verify: is
   the frame genuinely different 8 s from now (not just re-phased)?
2. **Dead black space** trips the luminance floor (0.02) and reads as nothing on stage.
   Accumulation pieces (attractors, particle clouds, DLA, n-body) must splat **enough
   bright iterates** (40–80k/frame into a log-density buffer) and fill a real fraction
   of the frame — target frame-mean luminance ~0.15–0.5. A "few faint specks on black"
   is the classic fail. Symmetric rotators (accretion disks, radial fields) also need a
   **symmetry-breaking** element (an orbiting hotspot, drifting seeds) or spinning them
   looks identical frame-to-frame.
3. **Too-pale** is the mirror failure — pale marks on near-white (lum > ~0.8, low
   contrast) read as washed/empty. Prefer a mid/dark ground with saturated marks so
   structure reads; MULTIPLY-blend pigment on near-white makes bright colors vanish.

After authoring, a human grades the catalog in the browser (`grade.html`): **bad**
(deleted + negative taste signal) / **ok** (kept) / **good** (positive taste signal).
Author toward "good": distinctive, legible, dynamic, colorful, non-cartoon.
