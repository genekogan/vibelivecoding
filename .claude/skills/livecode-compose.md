# Livecode Composition & Step-Through

How to **build**, **record**, and **replay** audiovisual performances against the livecode server. Companion to `strudel.md` (music syntax) and `p5.md` (visuals syntax).

## TL;DR

```bash
# Start server
python livecode.py
# (open http://localhost:8766/livecode.html, click Start)

# A. Replay a saved show
python autoplay.py --show shows/disco_set.show.json --dwell 16beats

# B. Author + record a show
python compositions/my_show.py --step          # collects steps, uploads to server
curl localhost:8766/show/save_file -d '{"path":"shows/unsorted/my_show.show.json"}'

# C. Live: just send commands — server auto-records to shows/unsorted/jam_<ts>.show.json
```

Arrow keys ← → in the browser advance/back sections.

## Architecture

```
.claude/skills/livecode-compose.md   ← this file (knowledge)
scenes/                              ← reusable primitives (pure functions returning code)
compositions/                        ← recipes (combine primitives + mark sections)
shows/*.show.json                    ← curated artifacts (immutable, self-contained)
shows/unsorted/*.show.json           ← auto-captures from every session (sequestered)
autoplay.py                          ← driver that advances a show on a clock
```

**Reproducibility rule:** a `.show.json` captures literal code strings, not references. The scene library can evolve; old shows still play identically because they don't import anything.

## Show file format (`livecode-show-v1`)

```json
{
  "format": "livecode-show-v1",
  "name": "disco_set",
  "created": "2026-05-25T20:30:00",
  "source": "compositions/disco_set.py",
  "cps_at_start": 0.52,
  "default_dwell": "16beats",
  "steps": [
    {"route": "/strudel/cps", "payload": {"cps": 0.52}, "label": "Drums"},
    {"route": "/strudel/track", "payload": {"name": "drums", "code": "..."}},
    {"route": "/p5/layer", "payload": {"name": "floor", "code": "..."}, "dwell": "8beats"}
  ]
}
```

- `label` on a step marks a **section boundary** — `→` advances to the next labeled step (playing everything in between).
- `dwell` overrides the global dwell for one step. Optional everywhere.
- Routes accepted in steps: `/strudel/{track,stop,hush,cps,send}`, `/p5/{layer,remove,clear,setup,state,fps,send}`, `/show/mark` (no-op marker).

## Operating modes

| Mode | What it is | Output |
|------|------------|--------|
| **Replay** | `autoplay.py --show shows/X.show.json --dwell N` advances steps on a timer | uses existing show |
| **Compose** | Write `compositions/Y.py` → run with `--step` → save | new show file |
| **Live** | Send commands directly; server auto-records | `shows/unsorted/jam_<timestamp>.show.json` |
| **Riff** | Read existing `shows/*.show.json`, splice arrays, POST `/show/load`, save | new show file |

All modes produce the same artifact shape. Replay is uniform regardless of how the show was created.

## Composition pattern

```python
# compositions/my_show.py
from scenes import disco, jazz
from scenes._common import Composition

with Composition("my_show") as show:
    show.mark("Drums")
    show.track(**disco.drums())
    show.cps(0.52)

    show.mark("Bass")
    show.track(**disco.bass())

    show.mark("Visuals")
    show.layer(**disco.floor())
    show.layer(**disco.ball())
```

`Composition` is a context manager that handles `--step` mode (collect into list, upload via `/show/load`) vs default mode (post immediately). It also handles `wait_ready()` and final save.

Run with `--step` to collect + load (does not auto-play). Run plain to perform live.

## Scene catalog (current)

Each function returns `{"name": str, "code": str}` for `/strudel/track` or `/p5/layer`.

### `scenes/disco.py` (CPS 0.52, 125 BPM)
- `drums()` — 4-on-floor 909, clap on 2&4, offbeat oh, 16th hats
- `bass()` — pumping octave saw, Cm→Fm→Ab→Gm
- `strings()` — lush detuned saw chords, slow attack
- `wah()` — square wave resonant filter sweep
- `clav()` — 16th funk riff
- `shimmer()` — high triangle pad, huge reverb
- `floor()` — beat-pulsing checkerboard tiles (p5)
- `beams()` — 8 rotating light beams (p5)
- `ball()` — disco ball with reflective tiles (p5)
- `sparkles()` — 4-way mirrored particle bursts (p5)
- `dancers()` — 7 choreographed Staying Alive dancers (p5)

### `scenes/jazz.py` (CPS 0.38–0.50)
- `drums()`, `walking_bass(scale)`, `chord_stabs(progression)`, `pentatonic_lead()`, `pad()`

### `scenes/jungle.py` (CPS 0.85)
- `chopped_breaks()` — clean-breaks chopped 16, needs `samples('github:yaxu/clean-breaks')`
- `reese_bass()` — detuned saw with filter LFO
- `amen_fills()`, `breakdown_kick()`, `riser()`

### `scenes/visuals.py` (generic)
- `bg(color=0)`, `noise_field()`, `particles(emit_rate)`, `strobe(period)`

### `scenes/campfire.py`
- `full_scene()` — EUC riders circling fire

### `scenes/building.py`
- `desert_pallet_rack()` — desert building w/ palette panels
- `projection_mural()` — recursive scene with Voronoi

> When you add a scene, drop a one-liner here. Skill is the index; `scenes/*.py` is the body.

## Inline cookbook (zero-dep, paste-and-go)

For agents that want to skip the scenes/ import and emit code directly.

### Disco drums
```js
stack(
  s("bd bd bd bd").bank("RolandTR909").gain(.82).shape(.2).lpf(3000),
  s("~ cp ~ cp").bank("RolandTR909").gain(.55).room(.35),
  s("~ oh ~ oh ~ oh ~ oh").bank("RolandTR909").gain(.42).pan(.55).lpf(5000),
  s("hh*16").bank("RolandTR909").gain("[.45 .15 .30 .12]*4").pan(sine.range(.4,.6).slow(7)).lpf(6000)
).play()
```

### Disco floor (beat-pulsing tiles)
```js
push();
const beat = frameCount / 28.8;        // CPS 0.52 → 28.8 frames/beat at 60fps
const floorY = height * 0.70;
const tileSize = width / 10;
noStroke();
for (let i = 0; i < 10; i++) for (let j = 0; j < 4; j++) {
  const tilePulse = pow(max(0, sin((beat - (i+j)*0.15) * TAU)), 6);
  if ((i+j) % 2 === 0) {
    const h = (i*36 + j*90 + frameCount*2) % 360;
    fill(h, 60 + tilePulse*30, 30 + tilePulse*60);
  } else fill(0, 0, 8 + tilePulse*15);
  rect(i*tileSize, floorY + j*tileSize, tileSize, tileSize);
}
pop();
```

### Riff template (mix two existing shows)
```python
import json
a = json.load(open("shows/disco_set.show.json"))
b = json.load(open("shows/jungle_set.show.json"))
# Take disco drums section, jungle bass section, disco visuals
new_steps = (
    a["steps"][a_drums_start : a_drums_end]
    + b["steps"][b_bass_start : b_bass_end]
    + a["steps"][a_visuals_start :]
)
out = {**a, "name": "disco_jungle_riff", "steps": new_steps}
json.dump(out, open("shows/unsorted/riff.show.json", "w"), indent=2)
```

## Conventions

### Tempo (CPS → BPM)
- 0.36 (90 BPM) hip-hop · 0.42 (105) chill · 0.50 (125) house · 0.52 (130) disco · 0.65 (156) DnB · 0.85 (200) jungle

### Beat-sync formula in p5 layers
At 60fps: `frames_per_beat = 60 / (cps * 4)`. For CPS 0.52 → ~28.8 frames/beat. Use `const beat = frameCount / FRAMES_PER_BEAT;` then derive `pulse`, `kick`, etc. from `sin(beat * TAU)`.

### Layer Z-order (back to front)
`bg`, `floor`, `beams`, `rings`/`starburst`, `ball`, `sparkles`, `dancers`, `flash`

### Track names (so step replay can stop them)
Stable names per role: `drums`, `bass`, `chords`/`strings`, `lead`, `wah`, `clav`, `shimmer`, `pad`, `vox`, `riser`. Reuse across sections.

### Sample loading
Must precede tracks that use them, runs once:
```python
post("/strudel/send", {"code": "samples('https://strudel.b-cdn.net/tidal-drum-machines.json', 'https://strudel.b-cdn.net/tidal-drum-machines/machines/')"})
```

## Recording semantics

- Server **always records** every accepted command into the timeline (`_recording = True` by default)
- The list append happens on the request thread (O(1))
- The WebSocket broadcast is fire-and-forget (`run_coroutine_threadsafe`)
- A daemon thread autosaves the timeline to `shows/unsorted/<session_id>.show.json` every 60s and on shutdown
- Auto-captures are sequestered — curated shows live in `shows/`, never `shows/unsorted/`
- Promote a capture by moving it: `mv shows/unsorted/jam_xxx.show.json shows/my_jam.show.json` (and optionally hand-edit metadata)

## Autoplay

```bash
python autoplay.py --show shows/disco_set.show.json [--dwell 16beats] [--loop] [--port 8766]
```

- `--dwell`: `Ns` / `Nbeats` / `Nbars` / `Ncycles` / `auto` (use per-step `dwell` field, fallback to show's `default_dwell`, fallback to `16beats`)
- CLI value overrides anything in the show file
- Re-reads CPS from server before each step (so tempo changes mid-show feel right)
- `--loop` resets to step -1 at end and restarts

## Server endpoints (step-related)

| Method | Route | Body | Purpose |
|--------|-------|------|---------|
| POST | `/show/load` | `{steps: [...]}` | Load step list into timeline |
| POST | `/show/load_file` | `{path}` | Load from disk |
| POST | `/show/save_file` | `{path}` | Save current timeline to disk |
| GET | `/show/save` | — | Return current timeline as JSON |
| GET | `/show/steps` | — | List steps (truncated codes for inspection) |
| POST | `/show/next` | — | Advance to next section |
| POST | `/show/prev` | — | Back to previous section |
| POST | `/show/goto` | `{step}` | Jump to step index |
| POST | `/show/mark` | `{label}` | Insert section boundary marker |

## Gotchas

- A step's `payload` for `/strudel/send` should be `{code, evaluate?}`. `samples()` calls use `evaluate=false` (default).
- `/show/mark` steps without other content are pure boundaries — they don't execute anything. Useful for labeling visual-only or pause sections.
- `dwell` strings must parse: `4s`, `16beats`, `2bars`, `1cycles`. `bar` = `cycle` = `4beats`.
- When replaying backward, the server does full reset + replay-up-to-target. So `←` from step 200 to step 199 still replays all 199 prior steps. Cheap for code, expensive for sample-heavy shows — load samples once outside the timeline if possible.
