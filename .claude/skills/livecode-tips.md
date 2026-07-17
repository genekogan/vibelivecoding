# Livecode Performance Tips — Music + Visuals

## Starting the System

### Option A: Python script (for compositions)
```python
from livecode_server import LivecodeController
import time

ctrl = LivecodeController()
ctrl.start()
# Open http://localhost:8766/livecode.html, click "Start Audio & Visuals"
ctrl.wait_for_browser()
```

### Option B: curl (fastest, ~10ms per call — preferred for agent use)
Start the server first: `python livecode.py`
Then send commands via curl to localhost:8766.

### Option C: Livestreaming (to X or Twitch)
**Current method = manual OBS Studio.** Full runbook (sources, audio routing,
the Restart-capture gotcha, per-platform ingest URLs, verification):
→ **`docs/livestreaming-obs.md`**

The old automated `stream.py` (headless browser + FFmpeg → Twitch, needed BlackHole)
is **defunct** — see `docs/archive/headless-browser-streaming.md`.

## curl Quick Reference

```bash
# Music
curl localhost:8766/strudel/track -d '{"name":"kick","code":"s(\"bd*4\").bank(\"RolandTR909\").shape(.3).gain(.9).play()"}'
curl localhost:8766/strudel/cps -d '{"cps":0.5}'
curl -X POST localhost:8766/strudel/hush

# Visuals
curl localhost:8766/p5/layer -d '{"name":"bg","code":"background(0);"}'
curl localhost:8766/p5/layer -d '{"name":"shape","code":"fill(255,0,0); circle(width/2,height/2,200);"}'
curl -X POST localhost:8766/p5/clear

# Status
curl localhost:8766/status
```

## EDM Production Cheatsheet

### Tempo (CPS → BPM)
- 0.5 = ~120 BPM (house)
- 0.55 = ~132 BPM (techno, acid)
- 0.65 = ~156 BPM (DnB half-time)
- 0.85 = ~200 BPM (jungle, fast DnB)

### Essential Track Structure (3-5 tracks max)
1. **Drums** — kick/snare/hat with groove (NEVER perfectly quantized)
2. **Bass** — filtered sawtooth or sine sub
3. **Chords/Pad** — slow filter sweep, reverb
4. **Lead/Melody** — sparse, with delay/reverb
5. **Percussion** (optional) — rim/clap with dub delay

### Making It Sound Good (not robotic)
- Use `.gain("1 .6 .8 .6 1 .6 .9 .6")` for ghost notes
- Use `.every(4, x => x.fast(2))` for fills
- Use `sine.range(200, 4000).slow(8)` for filter sweeps
- Use `.room(.15-.5)` on everything (dry = bad)
- Use `.shape(.2-.4)` for warm saturation
- Use `.orbit(N)` to separate effect buses
- Use `.late(.02)` for behind-the-beat lazy feel

### Best Drum Machines
- **RolandTR909** — house/techno (punchy, bright)
- **RolandTR808** — hip-hop/trap (deep, boomy)
- **RolandTR707** — funk/pop (crisp, clean)

### Synth Oscillators (always available)
- `sawtooth` — bass, pads, leads (bright/buzzy)
- `square` — stabs, retro leads (hollow)
- `triangle` — gentle leads (soft)
- `sine` — sub bass (pure)
- `supersaw` — epic pads (big/detuned)

### Acid Bassline Recipe
```
note("[c2 c2 <eb2 c2> c2 [c2 g2] c2 <f2 eb2> c2]*2")
  .s("sawtooth").ftype('24db')
  .lpf(sine.range(200, 1500).slow(8))
  .lpenv(sine.range(1, 8).slow(16))
  .lpq(sine.range(4, 14).slow(12))
  .shape(.35).gain(.35)
```

### Dub Delay on Percussion (signature sound)
```
s("~ rim ~ [~ rim]").bank("RolandTR707")
  .delay(.7).delaytime(.375).delayfeedback(.55)
  .room(.6).roomsize(4).orbit(2)
```

## Quirky Visuals Cheatsheet

### Canvas defaults to HSB: `colorMode(HSB, 360, 100, 100, 100)`

### Core Animation Patterns
- **Oscillation:** `sin(frameCount * 0.05) * amplitude`
- **Rotation:** `rotate(frameCount * 0.02)`
- **Color cycling:** `(frameCount * 2) % 360` as hue
- **Noise field:** `noise(x * 0.01, y * 0.01, frameCount * 0.01)`
- **Trails:** `background(0, 0, 0, 10)` instead of `background(0)`

### Layer Strategy
1. `bg` — background (solid or trail fade)
2. `shapes` — main geometry
3. `fx` — particles, sparkles
4. `ui` — text overlay (optional)

### Use `window.state` for persistence
```javascript
if (!state.ps) state.ps = [];
state.ps.push({x: random(width), y: random(height), life: 255});
```

### Quirky Visual Ideas
- **Kaleidoscope:** 8-segment rotational symmetry with color cycling
- **Warped grid:** Perlin noise displacement on a grid of points
- **Hypnotic spirals:** Polar coordinates + frameCount offset
- **Particle rain:** Accumulating particles with fade-out life
- **Lissajous curves:** `sin(t*a)` for x, `cos(t*b)` for y
- **Reactive geometry:** Shapes that pulse/rotate with mathematical relationships
- `blendMode(ADD)` for glowy effects

### Making Visuals That Match Music
- Use similar cycle lengths (e.g., `slow(8)` in music ↔ `sin(frameCount * 0.01)` in visuals)
- Dark backgrounds with bright saturated shapes
- Motion trails create a dreamy/club feel
- Geometric patterns (circles, spirals) feel "electronic"
- Color cycling through HSB hue = instant psychedelia

## Critical Gotchas
- Track code MUST end with `.play()`
- `gm_*` instruments DON'T work (no soundfonts in CDN)
- Use `ctrl.set_cps()` or `/strudel/cps` for global tempo. `.cps()` is only a deliberate per-pattern transform.
- Don't call `createCanvas()` in p5 layers — canvas already exists
- p5 layers run inside `draw()` every frame
- Load samples with `ctrl.send("samples(...)")` + wait 2-3s before using
- Each layer gets auto `push()`/`pop()` — transforms are isolated
