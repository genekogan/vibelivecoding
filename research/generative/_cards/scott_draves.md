# Scott Draves

- **Bio/context**: American artist-programmer (b. 1968), aka "Spot"; invented the **Fractal Flame** algorithm in 1992 and has run the distributed **Electric Sheep** since 1999. Medium: C reference implementations (`flam3`), distributed client/server compute, GPU. A foundational figure in generative/software art; his flame code underlies Apophysis, Chaotica and JWildfire.

- **Signature techniques**: **Fractal flames** generalize the Iterated Function System chaos game — iterate a randomly chosen affine map from a set, but post-compose each with nonlinear *variation* functions (linear, sinusoidal, spherical, swirl, horseshoe, julia… 49 in the spec, often blended). Three signature moves give the look: (1) **log-density tone mapping** — accumulate a histogram of hit counts and display its log, so bright cores don't blow out and faint filaments survive; (2) **structural coloring** — carry a color coordinate per point and blend it along the orbit, then look it up in a 256-entry palette; (3) supersampling + density estimation for smooth, anti-aliased glow. **Electric Sheep** wraps this in a genetic algorithm: clients render frames, genomes ("sheep") mutate/crossbreed, and human up/down votes steer aesthetic evolution; frames interpolate between genomes to animate. Earlier **Bomb** (1993) used reaction-diffusion + CA feedback as a live "video organism".

- **Palette logic**: indexed 256-color palettes sampled by the per-point color coordinate, producing smooth gradients that follow the fractal filaments. Deep black background; log-density + additive accumulation burn bright cores to white while thin tendrils glow saturated — an electric neon-on-black, often jewel-toned or thermal look.

- **Mark-making / texture**: no strokes at all — pure point-accumulation density fields. Billions of plotted points build smoke/plasma/filament texture: self-similar tendrils, gaseous volume, high dynamic range, fully anti-aliased.

- **Motion/temporal qualities**: Electric Sheep morphs continuously by interpolating flame genome parameters — the form writhes, unfolds, rotates and breathes in seamless loops; slow and hypnotic. At population scale the genetic evolution plays out over days and weeks.

- **Key works**: the *Fractal Flame* algorithm (1992) & open-source `flam3`; *Bomb* (1993); *Electric Sheep* (1999–); *Dreams in High Fidelity* (HD flame paintings). Widely exhibited internationally.

- **Links**: https://scottdraves.com/ · https://electricsheep.org/ · algorithm paper https://flam3.com/flame_draves.pdf · https://github.com/scottdraves/electricsheep · https://en.wikipedia.org/wiki/Fractal_flame
