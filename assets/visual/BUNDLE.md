# Visual bundle — engine capability probe findings

Probed live against `livecode.html` VERSION 2 (p5 1.11.11, 2D, `pixelDensity(1)`,
HSB 360/100/100/100) on 2026-07-10. All author agents can rely on these.

| Capability | Status | Notes |
|------------|--------|-------|
| `createGraphics(w,h)` | ✅ ok | Off-screen buffers work; cache in `S` keyed on `width+'x'+height` per CONTRACT. |
| `drawingContext.clip()` | ✅ ok | `save()/beginPath()/rect()/clip()/restore()` pattern works inside layers. |
| `drawingContext.shadowBlur/shadowColor` | ✅ ok | Works. Reset `shadowBlur = 0` when done — leaks past pop() otherwise. |
| `blendMode(ADD/MULTIPLY/SCREEN)` | ✅ ok | Always restore `blendMode(BLEND)` at layer end. |
| `text()` / `textFont()` | ✅ ok | System fonts by CSS name ('monospace', 'Georgia', etc.). No custom font files probed. |
| `loadImage('/path')` | ✅ ok | Static file serving from repo root works (`/assets/...`, `/autopilot/...`). Load once into `S`, guard with a flag — never call per-frame. |
| `filter(BLUR, 3)` full-canvas | ⚠️ ~11.6 ms/frame | Fps held 60 solo but that's 70% of the frame budget. **Never in a full-scene layer.** Blur small cached buffers at build time instead, or use `drawingContext.filter='blur(Npx)'` on limited regions. |

## Practical rules distilled

- Full-canvas `filter()` calls (BLUR, POSTERIZE, etc.) are effectively banned in
  composable assets — a post asset MAY use one only if its budget is declared
  `"heavy"` and there's no cheaper trick (e.g. pre-blurred sprite stamps).
- Glow: prefer layered translucent circles or `shadowBlur` on few shapes over
  full-canvas blur.
- `loadImage` is available but no curated image assets exist yet — code-drawn
  assets only for now; don't invent image paths.
- The canvas resizes at any time (window resize) — cached buffers MUST be keyed
  on size and rebuilt when it changes.
- Runtime errors observed in `/errors` are throttled to 1/s/layer and layer-tagged
  (`[fxA] runtime: ...`) — validation diffs this list.
