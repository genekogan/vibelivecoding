# Coverage checklist — generative factory (families × looks)

_Updated 2026-07-12 ~21:00 (checkpoint). Recompute truth from `ls assets/visual/genart`._

The existing 34 genart pieces already covered the "obvious" families. NEW work must
either hit **uncovered territory** or bring a **hard-different treatment** to a
covered family (reject near-dupes). Legend:
**✅ accepted this run** · **🟡 authored, in `inbox/` awaiting review** · **🔜 attempted but
failed (re-author)** · **⬜ open** · **🟥 hand-author (subagents failed it 2×)** · 🟡grey = covered-by-existing.

## Status tally (this run)
- **24 accepted** (catalog genart 34→58). **8 in inbox pending review.** **~4 failed/queued.**
- Accepted: plasma_warp, epicycles, caustics, quasicrystal, datascape, strange_dejong, ripple_tank,
  noise_contour, moire_weave, warp_grid, oil_slick, godrays, prism, boids, mandelbrot, penrose,
  ifs_flame, kaleidoscope, halftone_cmyk, lightning, stable_fluids, elementary_ca, harmonograph, physarum.
- In inbox (REVIEW FIRST on resume): apollonian, drip_paint, guilloche, lorenz, lowpoly_mesh,
  newton_fractal, spacefill, superformula.

## Already in catalog pre-run (the 34 — do NOT duplicate the core algorithm)
reaction_diffusion(GrayScott) · flowfield(curl-noise streaks) · attractor(Clifford) ·
diff_growth · feedback_paint · interference(ripple rings) · cellular(2D life) · circle_packing ·
truchet · voronoi · voronoi_3d · metaballs · phyllotaxis · marbling · dla · chladni · opart ·
dither(Bayer) · mandala · girih · lsystem · great_wave · aurora · blackhole · constellations ·
orrery · iso_city · subdivision · wormhole · cloth_flag · ascii_rain · giant_word · word_storm · doodle_world.

## NEW-territory families — status

### A · Field / continuum sims (coarse pixels[] buffer + upscale)
- ✅ domainwarp_plasma → genart.plasma_warp (hand-authored)
- ✅ physarum → genart.physarum (hand-authored; uniform-init fix; veins a bit thick — could refine)
- ✅ stable_fluids → genart.stable_fluids
- 🟥 lenia — failed 2× (subagent); hand-author (coarse float grid + ring-kernel convolution)
- ⬜ bz_reaction / excitable_media (FitzHugh-Nagumo spirals) — the "real spirals" gap (cyclic_ca shelved)
- ✅ ripple_tank → genart.ripple_tank
- ✅ caustics → genart.caustics (hand-authored)
- ✅ quasicrystal → genart.quasicrystal
- ⬜ curl_smoke · ⬜ diffusion_dye

### B · Agent / particle / parametric-curve systems
- ✅ boids → genart.boids · ✅ epicycles → genart.epicycles (hand-authored)
- ✅ harmonograph → genart.harmonograph (hand-authored rescue) · ✅ dejong → genart.strange_dejong
- 🟡 guilloche (inbox) · 🟡 lorenz (inbox) · 🟡 superformula (inbox)
- 🔜 venation (wave-3 failed — re-author)
- ⬜ nbody · ⬜ double_pendulum · ⬜ particle_fountain / particle-life

### C · Tiling / geometry / symmetry
- ✅ penrose → genart.penrose · ✅ kaleidoscope → genart.kaleidoscope
- ✅ isolines → genart.noise_contour · ✅ grid-distortion → genart.warp_grid (Watz)
- 🟡 apollonian (inbox) · 🟡 spacefill (inbox) · 🟡 lowpoly_mesh (inbox)
- 🔜 maze (wave-3 failed — re-author)
- ⬜ hyperbolic (Poincaré) · ⬜ celtic_knot · ⬜ tangram_shatter

### D · Fractal / escape-time / recursive
- ✅ mandelbrot → genart.mandelbrot · ✅ ifs_flame → genart.ifs_flame · ✅ lightning → genart.lightning
- 🟡 newton_fractal (inbox)
- ⬜ koch · ⬜ mandelbox2d

### E · Discrete CA / rule systems
- ✅ elementary_ca → genart.elementary_ca
- 🔜 sandpile (wave-3 failed — re-author)
- ⬜ langton_ant · ⬜ falling_sand · ⬜ wireworld · ⬜ cyclic_ca (shelved: needs radius-2 neighborhood)

### F · Signal / data / print / glitch (Ikeda · Asendorf · Sassoon · Gysin)
- ✅ datascape → genart.datascape · ✅ halftone_cmyk → genart.halftone_cmyk
- 🟥 pixel_sort — failed 2× (subagent gave grey blob / soft gradient, no visible sort); hand-author
- ⬜ ascii_field · ⬜ testcard · ⬜ datamosh · ⬜ seven_segment · ⬜ scanlines

### G · Optical / interference / light
- ✅ oilslick → genart.oil_slick · ✅ line_moire → genart.moire_weave
- ✅ prism → genart.prism · ✅ godrays → genart.godrays (hand-authored)
- ⬜ plasma_globe · ⬜ lens_warp

### H · Organic / painterly
- 🟡 drip_paint (inbox)
- 🔜 rorschach (wave-3 failed — re-author)
- 🟥 watercolor — requeued (pale/mono); re-author with colorful aquarelle washes + fuller coverage
- ⬜ smoke · ⬜ fiber_comb · ⬜ flow_ribbons

## Gamut axes — spot-check the spread every ~40 assets
calm↔violent · sparse↔dense · monochrome↔chromatic · geometric↔organic ·
crisp↔textural · warm↔cold · light-key↔dark-key · flat↔deep.
Current spread is good (warm: godrays/mandelbrot/penrose; cold: caustics/plasma; geometric:
warp_grid/moire_weave/penrose; organic: physarum/stable_fluids/oil_slick; data: datascape/halftone;
crisp: elementary_ca/epicycles). GAPS: more violent/energetic, more dense-textural, more painterly.
