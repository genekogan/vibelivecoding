# Coverage checklist — generative factory (families × looks)

The existing 34 genart pieces already cover the "obvious" families. NEW work must
either hit **uncovered territory** or bring a **hard-different treatment** to a
covered family (reject near-dupes). Legend: ✅ done-this-run · 🔜 queued · ⬜ open ·
🟡 covered-by-existing (only revisit with a genuinely different core algorithm/look).

## Already in catalog (the 34 — do NOT duplicate the core algorithm)
reaction_diffusion(GrayScott) · flowfield(curl-noise particle streaks) ·
attractor(Clifford) · diff_growth(contour subdivision) · feedback_paint ·
interference(ripple rings→moiré) · cellular(Conway/HighLife 2D life) ·
circle_packing · truchet(quarter-arc) · voronoi · voronoi_3d(gem facets) ·
metaballs(marching squares) · phyllotaxis · marbling(suminagashi) · dla ·
chladni(standing waves) · opart(Vasarely warp grid) · dither(Bayer 1-bit) ·
mandala · girih · lsystem · great_wave · aurora · blackhole · constellations ·
orrery · iso_city · subdivision(Mondrian) · wormhole · cloth_flag · ascii_rain ·
giant_word · word_storm · doodle_world.

## NEW-territory families (authoring targets) — the oeuvre expansion

### A · Field / continuum sims (coarse pixels[] buffer + upscale)
- ⬜ domainwarp_plasma — iq domain-warped fBm, cosine-palette plasma
- ⬜ physarum — slime-mold agent trail field (Sage Jenson)
- ⬜ stable_fluids — Navier-Stokes dye advection (Stam)
- ⬜ lenia — continuous CA / SmoothLife orbium
- ⬜ bz_reaction — Belousov-Zhabotinsky spiral waves (≠ GrayScott look)
- ⬜ excitable_media — FitzHugh-Nagumo spiral defects / cardiac
- ⬜ ripple_tank — wave-equation propagation (≠ chladni standing)
- ⬜ caustics — water/pool light caustics shimmer
- ⬜ quasicrystal — sum of N plane-wave gratings
- ⬜ curl_smoke — curl-noise dye/smoke plume (≠ flowfield streaks)
- ⬜ diffusion_dye — anisotropic diffusion / bleeding pigment

### B · Agent / particle / parametric-curve systems
- ⬜ boids — murmuration flock field (Reynolds/Hodgin)
- ⬜ venation — space-colonization leaf veins (Nervous System)
- ⬜ epicycles — Fourier epicycle chain tracing a contour
- ⬜ harmonograph — damped pendulum Lissajous curves
- ⬜ guilloche — rose-engine / banknote spirograph lattice
- ⬜ dejong — Peter de Jong / Svensson attractor (≠ Clifford)
- ⬜ lorenz — Lorenz/Rössler attractor projected + density
- ⬜ nbody — gravitational n-body orbit traces
- ⬜ double_pendulum — chaotic pendulum trail fan
- ⬜ particle_fountain — emergent particle life / clustering

### C · Tiling / geometry / symmetry
- ⬜ penrose — Penrose/aperiodic rhombus tiling (≠ truchet)
- ⬜ hyperbolic — Poincaré-disk hyperbolic tiling
- ⬜ kaleidoscope — live mirror-symmetry feedback (≠ mandala construct)
- ⬜ apollonian — Apollonian gasket recursive circles (≠ circle_packing)
- ⬜ spacefill — Hilbert/Gosper/Peano curve draw+morph
- ⬜ maze — recursive-backtracker maze carve + solve (≠ truchet)
- ⬜ celtic_knot — interlaced knotwork weave
- ⬜ lowpoly_mesh — Delaunay smooth gradient mesh (≠ voronoi_3d facets)
- ⬜ isolines — topographic contour map morphing (≠ metaballs)
- ⬜ tangram_shatter — recursive polygon shatter/reassemble

### D · Fractal / escape-time / recursive
- ⬜ mandelbrot — Mandelbrot/Julia escape-time slow zoom
- ⬜ newton_fractal — Newton root-basin fractal
- ⬜ ifs_flame — IFS fractal flame (Draves electric sheep) / Barnsley
- ⬜ koch — recursive Koch/de-Rham snowflake growth
- ⬜ lightning — dielectric-breakdown branching discharge (≠ dla)
- ⬜ mandelbox2d — 2D folding/kaleido-IFS escape field

### E · Discrete CA / rule systems
- ⬜ elementary_ca — Rule 30/90/110 1D→spacetime scroll (≠ 2D life)
- ⬜ langton_ant — Langton's ant / turmite highways
- ⬜ sandpile — abelian sandpile fractal
- ⬜ falling_sand — falling-sand toppling powder
- ⬜ cyclic_ca — cyclic CA rock-paper-scissors spirals
- ⬜ wireworld — Wireworld circuit CA pulses

### F · Signal / data / print / glitch (Ikeda · Asendorf · Sassoon · Gysin)
- ⬜ datascape — Ikeda barcodes / sine-grids / spectral bars / ticking data
- ⬜ pixel_sort — pixel-sorting threshold field (Asendorf)
- ⬜ halftone_cmyk — CMYK halftone rosette / moiré print (≠ dither Bayer)
- ⬜ ascii_field — ASCII/dot-matrix luminance render of a flow (Gysin, ≠ ascii_rain)
- ⬜ testcard — CRT test-pattern / SMPTE bars / signal tearing
- ⬜ datamosh — RGB-shift datamosh glitch field
- ⬜ seven_segment — LED seven-segment / dot counter grids (Gysin)
- ⬜ scanlines — rolling-shutter / scanline interference

### G · Optical / interference / light
- ⬜ oilslick — thin-film iridescence field
- ⬜ line_moire — overlapping rotating line families (≠ ripple interference)
- ⬜ prism — dispersion / spectral refraction bands
- ⬜ godrays — volumetric radial light / crepuscular rays
- ⬜ plasma_globe — electric arcs / tesla filaments
- ⬜ lens_warp — refraction/chromatic lens over a field

### H · Organic / painterly
- ⬜ watercolor — wet-on-wet pigment bloom (≠ marbling)
- ⬜ drip_paint — gravity drip / pour paint (Pollock/Klint)
- ⬜ rorschach — symmetric inkblot bloom
- ⬜ smoke — vapor/incense curl advection
- ⬜ fiber_comb — combed hair/fur fiber field
- ⬜ flow_ribbons — braided silk ribbons (differentiate hard from flowfield)

## Gamut axes to keep balanced (spot-check the spread every ~40 assets)
calm↔violent · sparse↔dense · monochrome↔chromatic · geometric↔organic ·
crisp↔textural · warm↔cold · light-key↔dark-key · flat↔deep.

## Accepted-this-run tally (recompute from disk on resume)
_See selfgrade.jsonl + `ls assets/visual/genart|post|fx`. Baseline before run:
genart=34, post=15, fx=20. New = current − baseline._
