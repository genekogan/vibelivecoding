# PROBE.md — live capability budgets (generative factory)

_Measured on the live 8766 canvas (idle baseline), fresh run 2026-07-12._

## Raw measurements (solo layer, warm)

| probe | median fps | note |
|---|---|---|
| baseline_fill | 59.9 | vsync ceiling ~60 |
| pix_128x72 (per-pixel + upscale) | 58.1 | trivial |
| pix_192x108 | 60.1 | trivial |
| pix_256x256 (65k px/frame) | 59.2 | fine |
| domainwarp_128x72 3-octave sin-noise | 60.6 | fine |
| points_500 (beginShape POINTS) | 59.9 | fine |
| points_2000 | 64.3 | fine |
| heavy_150_add (150 ADD ellipses ¼-canvas) | 59.7 | fine |
| feedback_fullcanvas (half-res buffer self-stamp) | 60.2 | fine |
| shadowblur_24 (drawingContext.shadowBlur×24) | 60.2 | fine |
| marching_96x54 (grid scalar field) | 61.8 | fine |
| **3-layer heavy STACK** (256² px bg + feedback post + 150 ADD fx) | **59.2** | realistic worst case still 60fps |

**Everything pins at the ~60fps vsync ceiling — even the 3-layer heavy stack.**
This box (Apple Silicon, Chromium headed) has large headroom. Solo probes can't
reveal true per-frame cost because vsync caps at 60; the stack test is the honest
signal and it's still 60. Budgets below are generous but keep the stage floor
(20fps, up to 11 layers) safe.

## Derived budgets (what authors may safely spend)

- **Per-pixel buffers**: up to **256×256** (65k px) safe solo and in a 3-stack.
  Prefer **128×72 → 192×108** for heavy per-pixel math every frame (domain warp,
  reaction-diffusion, fluid). `image()`-upscaled to full canvas it still looks great.
  Rebuild the buffer only on size change (cache in `S`, key on `width+'x'+height`).
- **Domain-warp / fBm**: 3 octaves on a 128×72–192×108 buffer per frame = free; up
  to 4 octaves on 128×72. NEVER run per-pixel warp on the full canvas — coarse buffer + upscale.
- **Points**: `beginShape(POINTS)` up to **2000** free. Keep ≤ ~1500 at density=1 so density can push up.
- **Heavy alpha/ADD shapes**: ≤ **150** at ¼-canvas, alpha ≤ 35 (contract cap).
- **Feedback**: keep the buffer at **half canvas** (`width/2 × height/2`), self-stamp
  via `g.image(g,…)` with slight scale/rotate, upscale on draw. Free.
- **shadowBlur**: fine on **≤ ~30 shapes**. Always reset `drawingContext.shadowBlur=0` after.
- **Marching squares / iso-contour**: 96×54 free; up to 128×72.
- **NO full-canvas `filter()`** (~12ms/frame — banned). Fake blur with a pre-blurred
  small buffer stamp, layered translucency, or shadowBlur on few shapes.

## Engine reality (internalize before authoring)

- p5 **2D**, `pixelDensity(1)`, HSB 360/100/100/100 already set — never call `colorMode`/`createCanvas`.
- Clock driven by Strudel transport → **keep the `__clk` metronome running**
  (`sound("bd").gain(0.001).play()`) or `state.clk.t` freezes at 0 and EVERY visual
  reads static (motion gate 0.0000). It is running now.
- All rhythm from `K` (clk), never `frameCount`. Beat-locked motion re-phases at 8s
  (cps 0.5 → 16 beats) → reads static on the 8s gate. Every asset needs a **real-time
  `K.t` motion floor** (continuous drift/scroll/advect/rotate) on top of beat rhythm.
- genart owns `bg`, validated with **NO bed behind** → must fill the frame and hold
  luminance in [0.02, 0.92]. Default look opaque/rich (not the alpha mode).
- `A` audio (bass/mid/treble/rms/fft) blended ON TOP of a clk baseline, never sole motion.
- Params gate pokes the **first two numeric params to max** → order them so they make an
  obvious change (energy/scale/density first; never `hue` first — 360 wraps to red≈0).
