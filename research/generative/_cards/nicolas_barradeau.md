# Nicolas Barradeau

- **Bio/context**: Paris-based senior creative coder / graphic coder (handle "nicoptere"). Flash was his main tool 2007–2013; since then he works almost entirely in **HTML5 / WebGL / THREE.js / GLSL**. Artist-in-residence at the **Google Arts & Culture Lab** (machine learning, t-SNE maps). Gives workshops on generative graphics, computational geometry and parametric systems; interests are "motion, colors, life-like behaviors & dinos."

- **Signature techniques**: GPU **FBO / ping-pong particle systems** — positions and velocities packed into floating-point textures so millions of particles update in fragment shaders (repos `FBO`, `gpu-party`), advected along **curl-noise / flow fields** and morphed to sample target meshes. **Physarum** slime-mold agent simulation in JS+WebGL (agents deposit to a trail texture, sense 3 directions, rotate, diffuse+decay). **Raymarching SDFs** in fragment shaders (`raymarching-for-THREE`). **Marching squares / isolines** to vectorize scalar fields and image borders. Point-in-mesh **volume distribution**, instanced-geometry shells (`FluffyPredator`), and lathe/revolution surfaces. Later ML/generative-AI portraits ("Algorithmic Deities").

- **Palette logic**: Organic and "life-like" — typically a dark/black ground with luminous **additive** particle color (cyan, magenta, warm amber) building iridescent gradients where density accumulates. Smooth GPU color ramps rather than flat fills; his ML pieces shift to surreal photographic color.

- **Mark-making / texture**: Additive glow from overlapping point sprites, thin luminous isolines/curves, translucent accumulation (bright where many particles overlap, dark where sparse), and smooth shaded 3D surfaces. Marks are soft and emissive, not hard-edged — the image is built from light, not fills.

- **Motion/temporal qualities**: Real-time GPU advection — particles stream along noise/curl fields and **morph between mesh targets**; physarum networks grow, branch, decay and re-route in a tight feedback loop; raymarched forms rotate and blend. Everything is continuous, fluid and alive rather than looping; motion emerges from the simulation state each frame.

- **Key works**: *physarum* (JS/WebGL slime-mold simulation); *gpu-party* / *FBO* (GPU particle rendering & mesh-to-mesh morphing); *raymarching-for-THREE*; *FluffyPredator* (instanced-geometry fur); *volume_distribution* (3D vectors packed inside a mesh); *Algorithmic Deities* (ML-generated portraits); *marching squares* isoline vectorization studies.

- **Links**: https://www.barradeau.com · blog http://barradeau.com/blog · GitHub https://github.com/nicoptere · Behance https://www.behance.net/nicoptere
