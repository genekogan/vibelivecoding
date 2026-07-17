# Szenia Zadvornykh

- **Bio/context**: Amsterdam-born creative developer / creative coder (self-described interest in art + game design), later tech lead at dpdk in NYC. Medium is browser WebGL via **three.js + GLSL vertex shaders** (JavaScript), plus write-ups on Medium ("Into Vertex Shaders" series). Active ~2014–present. Author of **three.bas** (THREE.js Buffer Animation System, ~1k★), the widely-copied library that made GPU-side mesh/particle animation approachable.

- **Signature techniques**: **GPU "buffer / prefab" animation** — bake per-vertex animation parameters (per-instance `delay`, `duration`, start/end position, Bézier control points, axis/angle) into extra `BufferGeometry` attributes, then advance the *entire* system from one `uTime` uniform inside a vertex shader, so nothing is updated per-frame on the CPU. **Prefab duplication**: thousands of copies of a base mesh (tetrahedron, quad, letter glyph), each independently transformed on-GPU. **Point-cloud morphing**: sample the pixels of an image or rasterized text into tens of thousands of points, then fly them between source and target configurations along quadratic/cubic Bézier paths with GLSL-ported easing. Typography exploded into particles/prefabs that assemble and disperse. Related repos: **three.portals** (stencil-buffer portal rendering), **three-fuzzy-mesh**, **three-color-trail** (ribbon/mesh trails).

- **Palette logic**: Not a fixed-palette artist — color usually comes from the *source* (image-transition demos keep the photo's own colors) or from a single hue rendered with **additive blending** so overlapping points bloom to white-hot cores over a dark ground. Frequent near-monochrome point clouds sampled from a source image's luminance.

- **Mark-making / texture**: Millions of tiny additive-blended GPU point sprites forming volumetric, smoke-like clouds; thin instanced triangles/tetrahedra catching flat low-poly shading; trail smears from color-trail meshes. No brush strokes — the "texture" is the density and stagger of countless small marks.

- **Motion/temporal qualities**: Everything is a **timed A→B transition** governed by one normalized 0..1 progress. **Staggered per-particle delays** create sweeping wave reveals across the field; ease-in-out Bézier flights; loopable A→B→A morphs; explosive scatter-and-reform on a beat. Ideal reference for a VJ layer that morphs a particle cloud between shapes/words on musical cues.

- **Key works**: **three.bas** (library + canonical examples: `points_animation` cat→cat point-cloud morph, `image_transition` spring↔winter dissolve); the **"THREE.js Text Animations"** CodePen collection (letters coalescing from particles/prefabs); **three.portals**, **three-fuzzy-mesh**; the **"Into Vertex Shaders"** tutorial series (Medium).

- **Links**: zadvorsky.com (now parked) · github.com/zadvorsky (three.bas) · codepen.io/zadvorsky · medium.com/@Zadvorsky · x.com/zadvorsky
