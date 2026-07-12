export const meta = {
  name: 'gf-compendium',
  description: 'Technique textbook: one file per algorithm family + composite recipes, grounded in this p5-2D engine + PROBE budgets',
  phases: [
    { title: 'Techniques', detail: '24 algorithm-family files' },
    { title: 'Recipes', detail: '16 composite emergent-chain files' },
  ],
}

const SHARED = `
This is for a p5.js **2D** live-coding VJ engine (NO WebGL/GLSL/shaders, NO createCanvas). Read FIRST:
- assets/prompts/author-brief.md (the P-block, universal seven, style/seed mandate, validation gates)
- research/generative/PROBE.md (performance budgets: coarse pixels[] buffers ≤256², domain-warp on 128x72, ≤2000 points, ≤150 heavy ADD shapes, half-canvas feedback, no full-canvas filter)
- assets/CONTRACT.md §Visual contract (slots, P-block, never-static, K clock, A audio)
Skim 1-2 existing examples in assets/visual/genart/ for the house style.
If research/generative/_cards/*.md exist, cite specific artist cards; otherwise cite artists by name.

Write a rigorous, CONCRETE file a coder authors from. Every claim must be implementable in THIS engine within PROBE budgets. Use fenced js snippets for the core loop. Do NOT write vague prose — give the actual algorithm, the buffer sizes, the blend modes, the parameter ranges.
`

const TECH_SECTIONS = `Cover, in order:
1. **Algorithm + math** — the update rule / equations, concisely.
2. **p5-2D implementation** — exactly how to do it here: coarse createGraphics buffer size + upscale? cached LUT/gradient? feedback via persistent S buffer? particle field? Give a fenced js core-loop sketch using the P-block conventions (D/P/S/K/A, __SLOT__). Stay within PROBE budgets and name the budget you're spending.
3. **Parameter surface** — which knobs to expose (map onto the universal seven where natural: energy/speed/density/scale/hue) + family-specific extras, with SAFE min/max that hold at both extremes.
4. **Palette / tone strategy** — how to color it (iq cosine palette code, HSB discipline, duotone, thermal, near-monochrome) so ≥3 divergent 'style' looks are possible, ≥1 non-representational.
5. **Temporal strategy** — how it evolves over 30s-5min: real-time K.t motion floor (never re-phases) + K.section/K.intensity arcs + optional P.act programs. This engine FREEZES beat-locked-only motion at 8s — say what the continuous drift is.
6. **Exemplar artists** (from the roster/cards) + **failure modes** (blank render, static, luminance out of [0.02,0.92], strobing >0.35, perf).`

const TECHNIQUES = [
  ["domain_warp_fbm","Domain-warped fBm noise fields → plasma. iq domain warping (warp the lookup coords by another noise field), iq cosine palettes a+b*cos(2π(c*t+d)). Coarse buffer, per-pixel."],
  ["flow_fields","Flow/curl-noise fields advecting particles or dye. NOTE genart.flowfield already does sumi/thermal/neon particle streaks — document NEW treatments (dye buffers, ribbon bundles, streamline contours, ASCII-sampled flow) that are hard-different."],
  ["reaction_diffusion","Gray-Scott + variants (Belousov-Zhabotinsky spiral waves, FitzHugh-Nagumo excitable media). NOTE genart.reaction_diffusion covers Gray-Scott sumi/neon/topo/thermal — document the BZ spiral & excitable-media looks specifically."],
  ["physarum","Physarum/slime-mold: thousands of agents deposit+sense a trail map, diffuse+decay it. Sage Jenson (mxsage). Agents in a Float array in S, trail on a coarse buffer."],
  ["stable_fluids","Stam stable-fluids / semi-Lagrangian advection of a dye field on a coarse grid; velocity from curl noise or injected impulses. Blur=diffuse."],
  ["lenia_smoothlife","Continuous cellular automata: SmoothLife / Lenia orbium. Convolution kernels on a coarse float grid, smooth growth mapping. Gliders/organisms emerge."],
  ["discrete_ca","Discrete rule systems: elementary 1D CA (Rule 30/90/110) scrolled as spacetime, cyclic CA (RPS spirals), Langton's ant/turmites, abelian sandpile, falling-sand, Wireworld."],
  ["strange_attractors","Attractor density render: de Jong, Svensson, Lorenz/Rössler (project 3D→2D), Ikeda map. NOTE genart.attractor is Clifford — document the OTHER maps + density/exposure tone-mapping."],
  ["flocking_particles","Boids/murmuration, particle-life (asymmetric attraction species), n-body gravity. Emergent clustering. Reynolds/Hodgin/Tarbell. Spatial hashing for neighbor queries within budget."],
  ["growth_systems","Differential growth (repel+subdivide a contour), space-colonization venation (Nervous System), DLA variants, dielectric-breakdown lightning. NOTE diff_growth/dla exist — cover venation & lightning."],
  ["escape_time_fractals","Mandelbrot/Julia escape-time + Newton root-basins. Coarse buffer, iteration→color, smooth (continuous) iteration count, slow Julia-param orbit / zoom for motion."],
  ["ifs_flame","Iterated Function Systems: Barnsley fern, Sierpinski, fractal flame (Draves electric sheep) with log-density gamma + palette. Chaos-game point accumulation on a buffer."],
  ["quasicrystal","Quasicrystal = sum of N plane-wave gratings (cos(x·cosθ+y·sinθ+phase)) over N rotations; interference → aperiodic crystal. Rotate phases in time. Coarse buffer."],
  ["moire_optical","Moiré & optical interference: overlapping rotating line/dot families, thin-film iridescence, lens/refraction warp, op-art. NOTE interference(ripple) & opart(Vasarely) exist — cover line-moiré, oil-slick, prism."],
  ["aperiodic_tilings","Aperiodic & non-euclidean tilings: Penrose rhombus (deflation), Wang tiles, Poincaré-disk hyperbolic tiling. NOTE truchet/girih exist — cover Penrose & hyperbolic."],
  ["packing_subdivision","Recursive packing/subdivision: Apollonian gasket (Descartes circle theorem), recursive rect/tri subdivision, treemaps. NOTE circle_packing/subdivision exist — cover Apollonian & tangram-shatter."],
  ["voronoi_delaunay","Voronoi/Delaunay: Lloyd relaxation, low-poly smooth gradient mesh, Delaunay flip. NOTE voronoi/voronoi_3d exist — cover low-poly gradient mesh (smooth, not gem facets)."],
  ["curves_mazes","Space-filling curves (Hilbert/Gosper/Peano) drawn+morphing, maze generation (recursive backtracker/growing-tree) carve+solve with a glow-front."],
  ["wave_fields","Wave-equation ripple tank (propagation), Chladni standing waves, water caustics (min-distance to warped grid), harmonograph pendulum curves. NOTE chladni exists — cover ripple-tank, caustics, harmonograph."],
  ["feedback_systems","Video-feedback painting, kaleidoscope live mirror-N symmetry, buffer echo/trails, datamosh feedback. NOTE feedback_paint exists — cover kaleidoscope & buffer-echo."],
  ["dither_halftone","Ordered dithering (Bayer), CMYK halftone rosettes, pixel-sorting (Asendorf threshold intervals), ASCII/dot-matrix luminance render (Gysin). NOTE dither(Bayer)/ascii_rain exist — cover CMYK halftone, pixel-sort, ASCII-field."],
  ["datascape_signal","Ikeda/Alva-Noto data aesthetic: barcode strips, sine-strobe grids, spectral/waveform bars, ticking data columns, CRT test-cards/SMPTE bars, seven-segment/LED counters, RGB-shift datamosh glitch."],
  ["painterly_fluid","Painterly: watercolor wet-on-wet pigment bloom, gravity drip/pour (Pollock), symmetric Rorschach inkblot, suminagashi marbling. NOTE marbling exists — cover watercolor, drip, rorschach."],
  ["parametric_curves","Parametric curve engines: Fourier epicycle chains tracing a contour, guilloché/rose-engine (banknote) spirographs, Lissajous/harmonograph, superformula, Koch/de-Rham recursive curves."],
]

const RECIPES = [
  ["plasma_contour_drift","Domain-warp fBm plasma → posterize into topographic contour bands → slow iq-palette drift + section-driven warp strength. Buffers, blend, param couplings, 30s-5min arc."],
  ["physarum_glow_arc","Physarum trails on a coarse buffer → additive bloom upscale → K.section drives sensor-angle/deposit so the network morphs from filigree to blobs to highways over minutes."],
  ["curl_density_feedback","Curl-noise flow advects a 40k-point density buffer → iq cosine tonemap → slow feedback zoom+rotate + K.intensity turbulence. (Differentiate from genart.flowfield: this is a density FIELD, not streaks.)"],
  ["rd_isoline_thermal","Reaction-diffusion field → extract topographic isolines (marching squares) → thermal false-color + a bloom pass; feed/kill drift across sections spots→maze→mitosis."],
  ["quasicrystal_halftone","Quasicrystal grating sum → CMYK halftone screen render → chromatic per-channel offset; N-fold + phase rotate on K.t, rms pumps contrast."],
  ["boids_trail_hue","Flocking murmuration → per-agent motion-blur trails (fade buffer) → speed-mapped hue + predator disturbance on the beat; density grows across the arc."],
  ["attractor_exposure_ink","Strange-attractor (de Jong/Lorenz) density accumulation → exposure/gamma tone-map → blueprint, sumi-ink and thermal render modes; coefficients morph over minutes."],
  ["fluid_dye_oilslick","Stable-fluid dye field → curl impulse injected on bass hits → oil-slick thin-film palette mapping of velocity magnitude; slow global rotation."],
  ["voronoi_glass_drift","Lloyd-relaxed Voronoi → stained-glass leaded edges + per-cell gradient fill → sites drift on curl noise, cells breathe on swell; re-seed each section."],
  ["julia_orbit_stripe","Escape-time Julia with the c-parameter orbiting a slow circle → interior stripe/orbit-trap coloring → outer smooth-iteration palette; zoom breathes on intensity."],
  ["flame_gamma_sheep","IFS fractal flame chaos-game accumulation → log-density gamma → electric-sheep palette crossfade between two variation sets over sections."],
  ["maze_glowfront_neon","Recursive-backtracker maze carves live → a flood-fill glow-front sweeps the connected path in neon ribbon → re-carve each section with a new seed."],
  ["epicycles_glyph_trail","Fourier epicycle chain traces a glyph/heart/word contour → decaying trail buffer keeps the drawn line glowing → guilloché underlay; number of epicycles ramps with density."],
  ["pixelsort_warp_duo","Pixel-sort a domain-warp source along threshold intervals → duotone → sort direction rotates by section; Kim-Asendorf glitch cadence."],
  ["datascape_arc_sync","Ikeda datascape: barcode strips + sine-grid + spectral bars, all quantized and synced to K.section/K.intensity so the 'data' reads as reacting to the musical arc; monochrome + single accent."],
  ["kaleido_emitter_mirror","Kaleidoscope feedback: a particle emitter feeds a buffer that is mirror-N folded each frame → symmetry order steps by section → hue drift + bloom."],
]

phase('Techniques')
const tech = await parallel(TECHNIQUES.map(([slug, spec]) => () =>
  agent(
`Write research/generative/techniques/${slug}.md — the technique file for this algorithm family.

FAMILY: ${spec}

${SHARED}
${TECH_SECTIONS}

Write the file with the Write tool. Return one line: the path + line count + the ≥3 'style' looks you propose for assets in this family.`,
    { label: `tech:${slug}`, phase: 'Techniques' }
  ).then(r => r).catch(e => `FAILED ${slug}: ${e}`)
))

phase('Recipes')
const rec = await parallel(RECIPES.map(([slug, spec]) => () =>
  agent(
`Write research/generative/recipes/${slug}.md — a COMPOSITE RECIPE (a chain of techniques that produces emergent beauty), for the p5-2D VJ engine.

RECIPE: ${spec}

${SHARED}

Document the chain concretely: (a) the exact buffers (sizes) and passes in order, (b) blend modes, (c) the parameter couplings (which knob drives what), (d) the 30s-5min temporal dramaturgy using K.section/K.intensity/K.t (name the continuous motion floor so it never reads static at 8s), (e) which technique files it draws on, (f) the ≥3 divergent 'style' looks. Give a fenced js sketch of the key pass. Write with the Write tool. Return one line: path + line count.`,
    { label: `recipe:${slug}`, phase: 'Recipes' }
  ).then(r => r).catch(e => `FAILED ${slug}: ${e}`)
))

log(`compendium: ${tech.filter(x=>!String(x).startsWith('FAILED')).length}/${TECHNIQUES.length} techniques, ${rec.filter(x=>!String(x).startsWith('FAILED')).length}/${RECIPES.length} recipes`)
return { techniques: tech, recipes: rec }
