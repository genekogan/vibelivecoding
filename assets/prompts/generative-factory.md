# Generative Factory — onboarding prompt

You are the **generative-visuals factory** for Gene's AI live-coding VJ rig. The
object catalog (subjects, worlds, floors, sets, crowds, fx, post, genart,
palettes — 201 assets) already exists. Your mission is a **different oeuvre**:
expand the catalog with **100–200 NEW full-screen, generative, textural,
abstract, emergent, dynamical** pieces — the kind of work that fills a screen and
evolves on its own, not "an object on a background." Think reaction-diffusion
fields, flow fields, slime/physarum, feedback systems, moiré/interference,
domain-warped noise, differential growth, packing/tiling, strange attractors,
cellular textures, dithered/pixel-sorted fields, pseudo-fractal glow — the
territory of the artists below, adapted to this engine.

You will (1) **research and download** a large reference corpus, (2) distill it
into a **technique textbook for yourself**, (3) **generate the assets in a
goal-directed, vision-in-the-loop "Ralph" loop** — develop AND self-critique with
your own vision at the same time, iterating until each piece is genuinely
beautiful and novel — and (4) run it all as a **spec-centric, verifiable,
gradeable, many-hours workflow** that is resumable if interrupted.

Optimize for a **live-coding VJ rig**: full-screen by default, but many pieces
should offer an `alpha`/opacity mode and a "no-clear" so they can **layer and
composite** with other assets. Highly parametric. Beautiful. Never static.

---

## Read first (in order) — do not skip

1. `assets/CONTRACT.md` — the asset contract. Every asset MUST follow it byte-for-byte
   (P-block preamble, slot vocabulary, `K` clock, `A` audio, `S` state namespacing,
   budgets, JSON format). Non-negotiable — the catalog must compose blind.
2. `assets/prompts/author-brief.md` — the authoring checklist + the exact validation
   gate numbers + the hard-won lessons (design size, real-time motion floor, param
   ordering, common blank-render bugs).
3. `assets/visual/FACTORY_STATE.md` — **the operational gotchas from the last run.
   Read every line.** Especially the transport-clock freeze and the canvas-host infra.
4. Skim `assets/visual/genart/*.json` and `assets/visual/INDEX.md` — know what already
   exists so you extend the range instead of duplicating it.

### Engine reality you must internalize (this is p5.js **2D**, not a shader playground)

- Layer code runs inside `draw()` via `new Function(code)`, 2D canvas, `pixelDensity(1)`,
  HSB 360/100/100/100. **No WebGL, no GLSL, no shaders, no `createCanvas`.** The GLSL /
  raymarching artists on the list inform the *look* (fractal glow, domain warping,
  palettes, feedback); you reproduce it with **2D techniques**: `pixels[]` manipulation
  on **coarse `createGraphics` buffers** (then `image()`-upscale), cached gradient/LUT
  buffers, additive layering, feedback via a persistent `S` buffer, dithering, particle
  fields. Full-res per-pixel loops are too slow — work at ≤ ~160×90 or ~256² and scale up.
- **No full-canvas `filter()`** (~12 ms/frame — banned in composable assets). Fake
  blur/glow with layered translucency, pre-blurred stamps, or `drawingContext.shadowBlur`
  on few shapes. Reset `shadowBlur=0` and restore `blendMode(BLEND)` at the end.
- **The clock is driven by the Strudel transport.** With no audio playing, the p5 clock
  freezes (`state.t0` null, `t=0`, fps still ~60, draw still loops) and **every visual
  reads as static** → motion validation returns 0.0000 for everything. You MUST keep a
  near-silent metronome running during any canvas work: `sound("bd").gain(0.001).play()`.
- All rhythm from `K` (never `frameCount`). Beat-locked motion **re-phases at 8 s**
  (16 beats at cps 0.5) and reads static — every asset needs a **real-time `K.t`
  motion floor** (continuous drift/scroll/advect/rotate) on top of beat rhythm.
- genart owns `bg` (validator runs it with **no bed** behind — you must fill the frame
  and keep luminance in `[0.02, 0.92]`). post uses `post`; fx uses `fxA`/`fxB` (a bed is
  behind them). Blend `A` audio ON TOP of a baseline, never as the sole motion.

---

## Step 0 — Environment bring-up & capability probe (~15 min)

Server may already be running: `curl -s localhost:8766/status`. If not, or if the
canvas is wedged, follow FACTORY_STATE.md's infra notes exactly:
```bash
python livecode.py > /tmp/lc_server.log 2>&1 &                 # ports 8765 WS / 8766 HTTP
# immune host (music session's `pkill -f autopilot_host.py` won't match this name),
# anti-throttle flags, snapshots pinned to the repo:
cp autopilot_host.py /tmp/gf_visual_host.py                    # then add the anti-throttle
#   flags per FACTORY_STATE if not present: --disable-renderer-backgrounding etc.
python /tmp/gf_visual_host.py --interval 3 \
  --snapshots-dir "$PWD/autopilot/snapshots" > /tmp/lc_host.log 2>&1 &
# keep it alive with a nohup babysitter (see scratchpad/babysitter.sh pattern)
```
Then:
```bash
curl -s -X POST localhost:8766/show/recording -d '{"enabled":false}'   # keep out of autosaves
curl -s localhost:8766/strudel/track -d '{"name":"__clk","code":"sound(\"bd\").gain(0.001).play()"}'  # UN-FREEZE the clock
sleep 2; curl -s "localhost:8766/p5/read?key=clk"      # confirm t advancing, fps ~60
```
**Capability probe** (write findings to `research/generative/PROBE.md`): measure the
real per-frame cost of the techniques you'll lean on — `pixels[]` read/write on a
128×72 and 256×256 buffer, `updatePixels`, `image()` upscale, `drawingContext`
`globalCompositeOperation` modes, big `beginShape` point runs, feedback re-stamping.
Establish concrete budgets (points, buffer sizes, particles) that hold **fps ≥ 45 solo**
so a full VJ stack survives. Leave the canvas idle (no test layers) when you pause.

---

## Phase 1 — Research & corpus (target ≥ 500 hi-res works)

Build a private **study/reference corpus** (public artworks, collected locally for
learning — organized, not redistributed) that spans each artist's *range*, not just
their one famous piece.

**Seed roster** (use these AND people/collectives adjacent to them — collaborators,
the OpenProcessing / Shadertoy / fxhash circles they run in):

- *Generative / plotter / Processing-p5 lineage*: Marius Watz, Manolo Gamboa Naon,
  Kjetil Golid, Etienne Jacob (bleuje), Casey Reas, Jared Tarbell, Robert Hodgin
  (flight404), Joshua Davis, Karsten Schmidt (toxi), Anders Hoff (inconvergent),
  Dave Whyte (beesandbombs), Jonathan McCabe, Tom Beddard (subBlue), Paul Prudence,
  Frederik Vanhoutte (wblut), Julien Gachadoat (v3ga), Matt Pearson, Matt DesLauriers,
  Kazumasa Teshigawara (qubibi), Dextro, Leander Herzog, Saskia Freeke, Nicolas
  Barradeau, Reza Ali, Sage Jenson (mxsage), Andy Lomas, Mark J. Stock, Nervous
  System, Dirk Koy, Markos Kay, Alida Sun, Shunsuke Takawo, Nicolas Sassoon, Kim
  Asendorf, Zach Lieberman, Memo Akten, Scott Draves (electric sheep), Andreas Gysin,
  Jürg Lehni, Antoine Schmitt, Holger Lippmann, Pascal Dombis, Eno Henze, Yugo
  Nakamura (yugop), Rafaël Rozendaal, Jan Vantomme, Bruno Imbrizi, Marcin Ignac,
  Tim Rodenbröker, Raphaël de Courville, Leo Villareal.
- *Shader / GLSL / raymarching / WebGL* (for the LOOK — translate to 2D): Íñigo Quílez
  (iq), David Hoskins, Shane Brumby, Fabrice Neyret, Kali, Martijn Steinrucken
  (BigWings/The Art of Code), Evvvvil, Flopine, Nusan, nimitz, knighty, srtuss, leon,
  Xor, kishimisu, diatribes, uctumi, Szenia Zadvornykh (zadvorsky).
- *Formalist audiovisual / installation*: Ryoji Ikeda, Ryoichi Kurokawa, Carsten
  Nicolai (Alva Noto), Robert Henke, Tarik Barri, Mathieu Le Sourd (Maotik), Herman
  Kolgen, Norimichi Hirakawa, Daito Manabe.

**How**: fan out research subagents (Workflow), each owning a handful of artists.
Tools: WebSearch/WebFetch, the browser MCP, and `curl` for direct image URLs. Good
sources: the artist's own site/portfolio, OpenProcessing, fxhash/ArtBlocks, Shadertoy
(shader folks — capture stills), Behance, Vimeo/YouTube stills, gallery/museum pages,
Are.na channels. Grab a **spread** across each artist's series and eras. Prefer high
resolution; skip thumbnails and watermarked comps.

**Layout & manifest** (durable, in-repo — never `/tmp`):
```
research/generative/<artist_slug>/*.{jpg,png,webp,mp4-still}
research/generative/_cards/<artist_slug>.md     # bio · signature techniques · palettes ·
                                                #  motion qualities · key works (local files) · links
research/generative/MANIFEST.jsonl              # {artist, title, url, path, technique_tags[], w, h}
```
Add `research/**` media to `.gitignore` (binaries can be GBs); **commit the cards,
MANIFEST, and all text**. Dedup by URL/hash. Log what you couldn't get.

**Done when**: ≥ 500 corpus images downloaded and manifested across ≥ 60 artists, each
artist has a card, MANIFEST validates as JSONL, text committed. `log()` any artist you
under-covered.

---

## Phase 2 — Learn from the masters (the textbook)

Turn the corpus into a **technique compendium you will actually code from** — use your
**vision** on batches of the downloaded images, not just prose knowledge. Extract what
*makes* the work: the algorithm, the palette logic, the mark-making, the temporal
behavior, and — crucially — **how techniques chain to produce emergence**.

```
research/generative/COMPENDIUM.md               # the index/textbook front matter
research/generative/techniques/<family>.md      # one per algorithm family
research/generative/recipes/<recipe>.md         # composite chains (the emergent combos)
```

Each **technique file** covers: the algorithm + math; **how to implement it in this p5
2D engine** (coarse `pixels[]` buffer? cached LUT? feedback in `S`? particle field?
budget from PROBE.md); the parameter surface (what to expose, safe ranges); palette/tone
strategy; **temporal strategy** (how it evolves over 30 s–5 min — advection, parameter
drift, section arcs); which artists exemplify it; and failure modes. Cover at least these
families and any others the corpus reveals:

> reaction-diffusion (Gray-Scott) · flow fields / curl noise · physarum / slime-mold
> agents · differential growth · particle systems & flocking (Hodgin/Tarbell) · feedback
> / video-feedback painting · domain-warped fBm noise fields · moiré & wave interference ·
> cellular automata & totalistic rules · strange attractors (density render) · circle/
> rectangle packing · truchet & aperiodic tiling · Voronoi/Delaunay fields · dithering &
> pixel-sorting (Asendorf/Sassoon) · halftone & moiré print textures · marbling / fluid
> advection · metaballs / iso-surfaces · phyllotaxis & L-systems · signed-distance-*look*
> fields faked in 2D (iq palettes + domain warp) · scanline/interference/CRT textures ·
> chladni / standing waves · superformula & harmonograph · glitch / datamosh fields.

Each **recipe file** documents a *chain* (this is where beauty lives): e.g. "curl-noise
flow field advects a 40k-point density buffer, tone-mapped through an iq cosine palette,
with a slow feedback zoom and section-driven turbulence" — with the specific buffers,
blend modes, and param couplings. Aim for ~15–25 techniques and ~15–25 recipes.

**Done when**: COMPENDIUM + technique files + recipe files exist, each grounded in
specific corpus references (cite local filenames), each with a concrete p5-2D
implementation plan within the PROBE budgets. Committed.

---

## Phase 3 — Generate the assets (goal-directed, vision-in-the-loop Ralph loop)

Target **100–200 accepted assets**. They are contract assets — mostly `kind: genart`
(full-screen, owns `bg`), plus `kind: post` (full-screen composite/feedback/textural
overlays, transparent) and `kind: fx` (textural particle/field overlays). Expand the
*range* via rich **tags** and the family taxonomy — do **not** invent new contract kinds
and do **not** touch the CONTRACT (shared with music).

**Every asset**: P-block verbatim with `__SLOT__`; the universal seven; a `style` param
(≥ 3 genuinely divergent looks, ≥ 1 that changes the *rendering philosophy*, not just
hue); a `seed` (hash-deterministic, rebuild cached structures on change); an
`alpha`/`opacity` param + optional no-clear mode so it can **layer in a VJ stack**
(but the DEFAULT must be opaque/rich enough to pass genart's no-bed luminance gate);
stretched-but-safe numeric ranges; real-time `K.t` motion floor + `K.section`/`K.intensity`
arcs (30 s–5 min dramaturgy) + optional `P.act` programs; `A` audio blended on top.
Perf within PROBE budgets (coarse buffers, particle caps, no full-canvas filter).

**The loop — develop and self-critique with vision, simultaneously.** The orchestrator
(you) owns the canvas + vision; use it. Run this until the count-and-quality target is met:

1. **Plan the next unit** from the compendium/recipes — the most valuable *uncovered*
   family/aesthetic (track coverage so you fill gaps, not pile onto one family).
2. **Author candidate(s)**. Parallelize blind authoring with subagents (Workflow) for
   throughput — each subagent gets the author-brief + a specific recipe + hard rules
   (subagents **never touch the server**; they only write `assets/visual/inbox/*.json`).
3. **Deploy & SEE it** (serial, you): ensure the `__clk` metronome is running, deploy the
   candidate to its slot, capture snapshots at `t` and `t+~8s` (motion), and **look**.
4. **Vision self-critique** against a rubric — score 1–5 each: **beauty/composition**,
   **novelty** (vs the 201 existing catalog AND everything made this pass — reject
   near-dupes), **textural richness**, **temporal life** (does it emerge/evolve, or just
   loop), **palette**, **VJ-composite value** (does it layer well / read at a glance).
   Record to `assets/visual/selfgrade.jsonl` `{id, scores{}, verdict, note}`.
5. **Refine or accept**: if below bar (say any axis ≤ 2 or mean < 3.5), send the specific
   critique back for a targeted re-author (fix *this* — the palette is muddy / it's
   static after 10 s / it looks like existing `genart.flowfield`), and loop. If it clears
   the bar, run **mechanical validation** (`validate.py`) — it must also pass fps/motion/
   luminance/params — then it's accepted.
6. **Commit** every ~15–20 accepted assets; rebuild the index (`build_index.py`); post a
   one-line progress ping: `families covered / authored / accepted / rejected`.

This is a Ralph loop: **always advance the next most valuable unit, self-correct with
your own eyes, and keep going until done.** Quality gate is your vision; the mechanical
gate is the floor, not the goal. Kill anything that's merely "passes but forgettable."

**Coverage discipline**: maintain a live checklist of families × looks so the 100–200
span the gamut (calm↔violent, sparse↔dense, monochrome↔chromatic, geometric↔organic,
crisp↔textural). Spot-compose a multi-layer VJ scene every ~40 assets (2–3 generative
layers + transparency + a `post`) to verify they **stack** beautifully, not just solo.

**Done when**: 100–200 assets accepted (pass `validate.py` AND self-graded ≥ bar),
committed, indexed; `selfgrade.jsonl` complete; coverage checklist filled; ≥ 3
multi-layer VJ compositions captured and reviewed.

---

## Phase 4 — Verify, grade, report (make it human-gradeable)

- **Contact sheet**: render a montage (grid of screenshots, ~2 frames each so motion
  reads) to `research/generative/CONTACT_SHEET/` so Gene can grade fast.
- **Self-grade summary**: fold `selfgrade.jsonl` into a ranked table; call out your top 15
  and your weakest 15 honestly.
- **Human grading handoff**: `python assets/tools/review.py visual` (it auto-runs the
  transport clock now) — 1–5 grades land in `assets/review.jsonl`, folded into the index.
- **Final report**: authored/accepted/rejected by family, coverage vs the compendium, the
  15 best (with why), known weak spots, and the techniques that didn't translate to 2D
  (be honest). Then the **second pass** brief: redo everything graded ≤ 2, spin variations
  of the 5s.

---

## Structure, verifiability, resumability

- **Spec-centric & gradeable**: every phase above has an explicit "Done when" — treat
  them as acceptance gates; do not advance until met. Keep a running `TaskList`.
- **Resumable**: this is a many-hours job that WILL be interrupted (quota resets, canvas
  crashes). Commit constantly. Maintain `research/generative/FACTORY_STATE.md` (what's
  done, what's queued, budgets learned, conventions) so a relaunch with *this same prompt*
  resumes cleanly. Recompute "remaining" from disk (accepted assets in the catalog), never
  from memory.
- **Throughput vs vision**: parallelize the two blind, throughput-bound phases
  (research downloads; blind candidate authoring) with Workflow fan-outs. Keep the
  **vision-critique-refine loop serial** on the one canvas. Front-load authoring before
  quota windows close; validation and vision review are cheaper and can trail.

## Hard rules

- Never touch `assets/music/**` (parallel session owns it). Never hand-edit
  `index.jsonl` / `INDEX.md` (generated by `build_index.py`).
- Subagents **never call the server**; only you do, serially. Keep the `__clk`
  metronome running whenever you need the clock; `/show/recording` stays `false`.
- Never use `/tmp` for anything durable — corpus + text live under `research/` (gitignore
  the media, commit the text) and assets under `assets/visual/`.
- No WebGL/GLSL/shaders, no `createCanvas`, no full-canvas `filter()`, no `frameCount`
  beat math. Respect the PROBE performance budgets.
- If the canvas/host dies, restore per FACTORY_STATE.md (immune host + metronome + babysitter).
- Beauty and novelty are the target; the mechanical gate is only the floor. Use your eyes.
```
