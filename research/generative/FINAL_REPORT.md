# Generative Factory — Final Report (Phase 3/4)

**Target: +100–200 new full-screen generative/emergent p5.js-2D visuals. Status: +100 low-end target REACHED.**

- **Catalog genart: 34 → 134 (+100 net new accepted)**, all validated on the live canvas (schema, clean deploy, /errors-clean, fps≥25, motion 0.004–0.35, luminance 0.02–0.92, param responsiveness) and self-graded on 6 axes (beauty/novelty/texture/temporal/palette/vj).
- **Mean self-score 22.9 / 30** across 102 graded accepts; distribution skews high (39 assets ≥24, only 2 at the 16-floor).
- Produced across **11 authoring waves** (Workflow fan-outs, ≤10 agents each, one wave at a time to respect the quota ceiling) + **7 hand-authored kernels** for families subagents repeatedly failed.

## Coverage — every major generative-art family is now represented
- **Reaction–diffusion / excitable media:** gray_scott, bz_spirals, stable_fluids
- **Strange attractors:** lorenz, clifford, strange_dejong, gumowski_mira, hopalong (aizawa requeued)
- **Cellular automata:** conway_life, elementary_ca, langton_ant, cyclic_ca, hex_automaton, wireworld, sandpile, forest_fire, ising, biham_middleton, kuramoto, snowflake (Reiter)
- **Agent / particle sims:** boids, physarum, nbody (spiral galaxy), double_pendulum, coulomb_lattice
- **Growth systems:** venation, dla, percolation, phyllotaxis, fractal_tree, collatz_river
- **Fractals:** mandelbrot, julia_morph, newton_fractal, ifs_flame, lightning, lyapunov, magnetic_pendulum, buddhabrot, koch_flake, gosper_curve, lichtenberg, domain_coloring, plasma_globe
- **Flow / fluid:** curl_smoke, flow_ribbons, diffusion_dye, smoke, karman_vortex, kelvin_helmholtz, iron_filings, wave_packet
- **Tiling / symmetry:** quasicrystal, penrose, hyperbolic, kaleidoscope, voronoi_cells, truchet, wang_tiles, celtic_knot, wallpaper_group, kolam, rauzy, moebius_grid, delaunay_flux
- **Optical / interference:** moire_weave, guilloche, chladni, string_art, maurer_rose, munching_squares, droste, spirograph, lissajous_grid
- **Signal / print / glitch:** datascape, halftone_cmyk, pixel_sort, matrix_rain, slit_scan, stipple, ulam_spiral, additive_synth
- **Fields / painterly / alife:** plasma_warp, caustics, noise_contour, ripple_tank, oil_slick, godrays, prism, watercolor, marbling, lenia, metaballs, ferrofluid

## Top-ranked pieces (self-score 27–28 / 30)
gray_scott · magnetic_pendulum · gumowski_mira · celtic_knot · droste · domain_coloring · moebius_grid · godrays

## Hand-authored kernels (subagents failed these ≥2×; rescued in the main loop)
pixel_sort (Asendorf databend), lenia (continuous-CA alife), watercolor (layered pigment), chladni (cymatics), nbody (spiral galaxy — fixed orbital velocity + short trails), fractal_tree (fixed the classic single-frequency-wind trap: its period landed on the 8 s validation window → apparent motion 0 → fixed with **incommensurate** wind frequencies), guilloche (pale→engraved).

## Multi-layer VJ scenes — compositing verified (≥3 captured)
Every asset ships an `alpha` param (tint-based translucency). Verified 3 stacked scenes render and blend correctly:
1. **Cosmic** — nbody galaxy + starfield_warp(60) + gumowski_mira(45)
2. **Geometric** — moebius_grid + celtic_knot(45) + matrix_rain(40)
3. **Organic** — gray_scott + string_art(55) + snowflake(45)
(Snapshots in `scratchpad/gf/_vj/`.) Additive / dark-ground pieces layer best; opaque-paper pieces (watercolor, fractal_tree) work as bases.

## Second-pass brief (toward +200, or a polish pass)
- **Requeue backlog:** `aizawa` (density buffer never filled → near-empty/static; needs many more iterates + brighter splats + faster incommensurate 3D rotation).
- **Lowest-tier accepts (polish candidates):** lowpoly_mesh (generic), biham_middleton (reads as noise at default density — lower density for visible free-flow stripes), collatz_river (came grey; wants violet→gold), stipple/ulam_spiral (a touch dark/subtle).
- **Uncovered families for waves 12+ toward 200:** thomas/rossler/chua attractors, mandelbrot deep-zoom, Faraday waves, domain-warp variants, girih/aurora/interference variants already exist so avoid; WFC tiling, neural-CA, reaction-worm regimes, spectrogram waterfall, Turing-horn, sand ripples, crystal-facet growth.
- **Process notes:** subagent hit-rate ~85–90% when judged on-canvas in color; the recurring failure modes were (1) dead-black-space / too-dark, (2) motion re-phasing at the 8 s window (single-frequency animation — always drive motion with real-time K.t at incommensurate rates), (3) effects too faint/sparse. All are now baked into author-brief guidance.
