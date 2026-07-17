# Sage Jenson

- **Bio/context**: Media artist working in speculative biology and "emotive simulations" (handle **@mxsage**; they/them). Builds GPU-based simulations of natural phenomena — slime mold, snow, embryogenesis — in **C++ / GLSL / openFrameworks**, running entirely on the GPU. Widely regarded as "the undisputed master of physarum." Artist-in-residence at **Nervous System** (translating simulations into 3D prints, metal casts and 2D prints); releases generative editions on **fxhash** and **Feral File**.

- **Signature techniques**: The defining work is a **Physarum polycephalum** agent simulation after Jeff Jones (2010), split into an agent layer (**data map**) and a continuum layer (**trail map**). Each of ~5–10 million particles reads **three sensors** (left/center/right at a set sensor-distance and sensor-angle) from the trail map, **rotates toward the strongest** signal by a rotation angle, steps forward by step-size, and **deposits** onto the trail; every step the trail map is **diffused (3×3 mean blur) and multiplicatively decayed** — a tight ping-pong feedback loop. He drops Jones's collision constraint (favoring emergent pattern) and adds a **contagion/infection** behavior: waves of "infected" agents that locally mutate simulation parameters. Later work extends to multi-scale fields, curl advection, embryogenesis and snow.

- **Palette logic**: Gorgeous, high-dynamic-range color mapped from **trail intensity / agent velocity through a smooth gradient LUT** — dark ground with luminous filaments, often iridescent **teal→magenta→gold** or thermal ink ramps. Physical prints move toward near-monochrome ink-on-paper. Color reads as light emitted by density, not flat fill.

- **Mark-making / texture**: Fine **branching filaments and veined transport networks** built from additive glow accumulation — bright dense trunks fading to wispy tendrils, with an almost photographic, organic, biological quality. Extremely high spatial detail from the millions of depositing agents.

- **Motion/temporal qualities**: Continuous growth, branching and **reconfiguration** of the network; **contagion waves** sweep across the field mutating behavior; bursts of explosive dispersal that re-coalesce into fresh networks; maze-like path-finding. Slow, hypnotic, ever-evolving — the feedback loop guarantees it never settles or repeats.

- **Key works**: *physarum* (2019, the defining GPU slime-mold work) and its **36 Points** algorithm variant; *Embryogenesis* (fxhash generative edition); *dismantling*, *shadowbox*, *particle studies*; Nervous System **biofabrications** — *tapestries*, *the dissolve*, *growth functors*, *nesting*, *digital morphologies*.

- **Links**: https://www.sagejenson.com · https://cargocollective.com/sagejenson/physarum · GitHub https://github.com/mxsage · Le Random https://www.lerandom.art/artists/sage-jenson · fxhash / Feral File
