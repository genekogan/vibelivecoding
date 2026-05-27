# Livecode Project

AI-driven live coding — **music** (Strudel) and **visuals** (p5.js).

## Unified System (preferred)

| Component | Purpose |
|-----------|---------|
| `livecode_server.py` | `LivecodeController` — single WS (8765) + HTTP/REST (8766) |
| `livecode.html` | Browser client: full-screen p5.js canvas + Strudel audio engine |
| `livecode.py` | Entry point: starts controller, waits for browser, keeps alive |

### How to Run
```bash
python livecode.py
# Open http://localhost:8766/livecode.html, click "Start Audio & Visuals"
```

### curl Interface (primary — ~10ms per call)
```bash
# Strudel (music)
curl localhost:8766/strudel/track -d '{"name":"bass","code":"note(\"c2 e2\").s(\"sawtooth\")"}'
curl localhost:8766/strudel/cps -d '{"cps":0.5}'
curl -X POST localhost:8766/strudel/hush

# p5 (visuals)
curl localhost:8766/p5/layer -d '{"name":"bg","code":"background(0);"}'
curl localhost:8766/p5/layer -d '{"name":"shape","code":"fill(255,0,0); circle(width/2,height/2,200);"}'
curl -X POST localhost:8766/p5/clear

# Status
curl localhost:8766/status
```

### REST API Routes
| Method | Route | Body |
|--------|-------|------|
| GET | `/status` | — |
| POST | `/strudel/track` | `{name, code}` |
| POST | `/strudel/stop` | `{name}` |
| POST | `/strudel/hush` | `{}` |
| POST | `/strudel/cps` | `{cps}` |
| POST | `/strudel/send` | `{code, evaluate?}` |
| POST | `/p5/layer` | `{name, code}` |
| POST | `/p5/remove` | `{name}` |
| POST | `/p5/clear` | `{}` |
| POST | `/p5/setup` | `{code}` |
| POST | `/p5/send` | `{code}` |
| POST | `/p5/state` | `{key, value}` |
| POST | `/p5/fps` | `{fps}` |

### Step-Through System
| Method | Route | Body |
|--------|-------|------|
| GET | `/status` | step + totalSteps in response |
| GET | `/show/steps` | list current timeline (truncated codes) |
| GET | `/show/save` | return current timeline as JSON doc |
| POST | `/show/load` | `{steps: [...]}` |
| POST | `/show/load_file` | `{path}` — load .show.json from disk |
| POST | `/show/save_file` | `{path}` — write timeline to disk |
| POST | `/show/next` | advance to next section (or single step) |
| POST | `/show/prev` | back to previous section |
| POST | `/show/goto` | `{step}` |
| POST | `/show/mark` | `{label}` — insert section boundary |
| POST | `/show/recording` | `{enabled}` |

Every accepted strudel/p5 command auto-records into the timeline.
`shows/unsorted/jam_<timestamp>.show.json` autosaves every 60s and on
shutdown. Arrow keys ← → in the browser advance/back sections.

## Composing & Replaying Shows

```bash
# Replay a saved show
python autoplay.py --show shows/full_show.show.json --dwell 16beats

# Author a new show (uses scenes lib + Composition context manager)
python compositions/disco_set.py --step --save shows/unsorted/my_show.show.json

# Live: any session is auto-recorded — promote a capture by moving it:
mv shows/unsorted/jam_<ts>.show.json shows/my_set.show.json
```

| Path | Purpose |
|------|---------|
| `scenes/{disco,jazz,hiphop,dnb}.py` | Pure code-returning scene primitives |
| `scenes/_common.py` | `Composition` context manager (collect/save/perform) |
| `compositions/*.py` | Recipes that combine scenes; --step --save creates a show |
| `compositions/scripts/*.py` | Sub-script visuals/sections inlined by full_show.py |
| `shows/*.show.json` | Curated, immutable, replayable performances |
| `shows/unsorted/*.show.json` | Auto-captures (gitignored, sequestered) |
| `autoplay.py` | Driver — advances show on a clock (Ns/Nbeats/Nbars/Ncycles) |
| `.claude/skills/livecode-compose.md` | Composition skill (scene catalog + cookbook) |
| `test_steps.py` | Playwright regression test (101 checks, 14 phases) |

## Standalone Systems (legacy, still work independently)

### Strudel (Music)
| Component | Purpose |
|-----------|---------|
| `strudel_server.py` | `StrudelController` — WebSocket (8765) + HTTP file server (8766) |
| `strudel.html` | Browser client: Strudel @strudel/web@1.0.3 engine + console |
| `strudel_live.py` | HTTP REST API (8767) for external/agent control |
| `strudel_send.py` | One-shot CLI to send Strudel code via WebSocket |
| `stream.py` | Twitch streaming + chat integration (FFmpeg + Playwright) |

### p5.js (Visuals)
| Component | Purpose |
|-----------|---------|
| `p5_server.py` | `P5Controller` — WebSocket (8775) + HTTP file server (8776) |
| `p5.html` | Browser client: full-screen p5.js 1.11.11 canvas + layer system |
| `p5_live.py` | HTTP REST API (8777) for external/agent control |
| `p5_send.py` | One-shot CLI to send p5.js code via WebSocket |
| `play_p5_demo.py` | Example visual composition |

### Standalone How to Run

#### Music
```bash
python strudel_live.py
# Open http://localhost:8766/strudel.html, click "Start Audio & Connect"
# Then send: python strudel_send.py 'note("c3 e3 g3").s("sawtooth").play()'
```

#### Visuals
```bash
python p5_live.py
# Open http://localhost:8776/p5.html, click "Start & Connect"
# Then send: python p5_send.py --layer bg 'background(0); fill(255,0,0); circle(width/2, height/2, 200);'
```

#### Both Together
Run `strudel_live.py` and `p5_live.py` in separate terminals. Open both browser tabs.

## Documentation

| Doc | Purpose |
|-----|---------|
| `.claude/skills/strudel.md` | **Strudel agent guide** — Python API + how to write music |
| `.claude/skills/p5.md` | **p5.js agent guide** — Python API + how to write visuals |
| `docs/strudel-reference.md` | Complete Strudel API reference |
| `docs/strudel-examples.md` | Genre-organized music examples |
| `docs/strudel-examples-raw.md` | Raw community examples from tunes.mjs |
| `docs/strudel-reference-raw.md` | Raw reference from strudel.cc docs |

## Quick Rules — Strudel
- Each `set_track(name, code)` code must end with `.play()`
- Use real drum samples with `.bank()`, not synth oscillators for percussion
- Load sample packs with `ctrl.send("samples('...')")` before using them
- `gm_*` instruments don't work (requires @strudel/soundfonts, not in CDN bundle)
- Use `.cps()` or `ctrl.set_cps()` for tempo, not `setcps()`

## Quick Rules — p5.js
- Use `set_layer(name, code)` — layers are independent, updating one doesn't touch others
- Code runs inside `draw()` every frame — don't call `createCanvas()` or `setup()` in layers
- Use `window.state` for persistent data (survives layer updates)
- `push()`/`pop()` wraps each layer automatically — transforms are isolated
- Press `C` in browser to toggle code overlay, `L` for execution log
- `clear()` removes all layers (equivalent to `hush()`)

## Port Map

### Unified (livecode.py)
| Port | Service |
|------|---------|
| 8765 | WebSocket |
| 8766 | HTTP file server + REST API |

### Standalone (legacy)
| Port | System | Service |
|------|--------|---------|
| 8765 | Strudel | WebSocket |
| 8766 | Strudel | HTTP file server |
| 8767 | Strudel | REST API |
| 8775 | p5.js | WebSocket |
| 8776 | p5.js | HTTP file server |
| 8777 | p5.js | REST API |
