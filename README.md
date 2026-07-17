# Livecode

AI-driven live coding platform for **music** ([Strudel](https://strudel.cc)) and **visuals** ([p5.js](https://p5js.org)) with a simple curl/REST interface.

Send music patterns and visual sketches from your terminal, scripts, or AI agents — they play instantly in the browser.

## Quick Start

```bash
# Install dependencies
pip install websockets

# Start the server
python livecode.py

# Open http://localhost:8766/livecode.html in Chrome
# Click "Start Audio & Visuals"
```

Once connected, send commands via curl:

```bash
# Play a bass note pattern
curl localhost:8766/strudel/track -d '{"name":"bass","code":"note(\"c2 e2 g2\").s(\"sawtooth\").play()"}'

# Draw a red circle
curl localhost:8766/p5/layer -d '{"name":"shape","code":"fill(255,0,0); circle(width/2,height/2,200);"}'

# Stop music
curl -X POST localhost:8766/strudel/hush

# Clear visuals
curl -X POST localhost:8766/p5/clear
```

### Browse all three catalogs in one window

```bash
python livecode.py --catalog --kiosk
```

This opens `http://localhost:8766/catalog.html`, with dedicated Three.js, p5.js,
and Strudel pages on one server. The p5 and Three.js catalogs work immediately;
click **Enable audio** once before auditioning Strudel assets.

## Three Ways to Drive It

| Mode | What it is |
|------|-----------|
| **Manual** | Send curl commands directly — see "Quick Start" above |
| **Showrunner** | Author + record + replay a stepped composition. Build with `compositions/*.py`, save as `shows/*.show.json`, play with `python autoplay.py --show ...`. Arrow keys ← → step sections in the browser. See [.claude/skills/livecode-compose.md](.claude/skills/livecode-compose.md). |
| **Autopilot** | An autonomous improvisation loop. Tell Claude Code "start the autopilot" — it wakes every ~1 min via `ScheduleWakeup`, evolves the canvas + music, and listens to your messages between rounds. See [.claude/skills/autopilot.md](.claude/skills/autopilot.md). |

## How It Works

The server (`livecode_server.py`) runs two services:

- **WebSocket** on port 8765 — real-time communication with the browser
- **HTTP + REST API** on port 8766 — serves the HTML client and accepts curl commands

The browser client (`livecode.html`) renders a full-screen p5.js canvas and runs the Strudel audio engine. Code sent via the API is evaluated live in the browser.

## REST API

### Music (Strudel)

| Method | Route | Body | Description |
|--------|-------|------|-------------|
| POST | `/strudel/track` | `{"name": "bass", "code": "note(\"c2\").s(\"sawtooth\").play()"}` | Set/update a named track |
| POST | `/strudel/stop` | `{"name": "bass"}` | Stop a single track |
| POST | `/strudel/hush` | `{}` | Stop all tracks |
| POST | `/strudel/cps` | `{"cps": 0.5}` | Set tempo (cycles per second) |
| POST | `/strudel/reset` | `{"quantumCycles": 1}` | Reset at the next AudioContext-clocked cycle boundary |
| POST | `/strudel/send` | `{"code": "...", "evaluate": true}` | Send raw Strudel code |

### Visuals (p5.js)

| Method | Route | Body | Description |
|--------|-------|------|-------------|
| POST | `/p5/layer` | `{"name": "bg", "code": "background(0);"}` | Set/update a named layer |
| POST | `/p5/remove` | `{"name": "bg"}` | Remove a layer |
| POST | `/p5/clear` | `{}` | Remove all layers |
| POST | `/p5/setup` | `{"code": "..."}` | Hard recompile (recreates canvas) |
| POST | `/p5/send` | `{"code": "..."}` | Evaluate raw p5 code |
| POST | `/p5/state` | `{"key": "x", "value": 100}` | Set persistent state |
| POST | `/p5/fps` | `{"fps": 30}` | Set frame rate |

### Status

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/status` | Returns `{ready, tracks[], layers[], cps, transportGeneration, reconnectPolicy, step, totalSteps, recording}` |
| GET | `/state` | Full code dump (tracks + layers code, cps, setup) — used by autopilot for self-correction |
| GET | `/errors` | Recent browser-side runtime errors (deque, maxlen 50) |
| GET | `/transport` | Fresh owned scheduler/audio/output frame, including provenance and confidence |

### Step-Through / Show Control

Every accepted Strudel/p5 command auto-records into a timeline. Arrow keys ← → in the browser advance/back sections. Autosaves to `shows/unsorted/jam_<ts>.show.json` every 60s and on shutdown.

| Method | Route | Body | Description |
|--------|-------|------|-------------|
| GET | `/show/steps` | — | List current timeline (truncated codes) |
| GET | `/show/save` | — | Return the timeline as a JSON doc |
| POST | `/show/next` / `/show/prev` | `{}` | Advance / step back |
| POST | `/show/goto` | `{"step": N}` | Jump to a step |
| POST | `/show/mark` | `{"label": "drop"}` | Insert a section boundary |
| POST | `/show/recording` | `{"enabled": true}` | Toggle auto-recording |
| POST | `/show/load` | `{"steps": [...]}` | Load a timeline in memory |
| POST | `/show/load_file` | `{"path": "shows/foo.show.json"}` | Load a show from disk |
| POST | `/show/save_file` | `{"path": "shows/foo.show.json"}` | Write timeline to disk |

## Python API

You can also control everything from Python:

```python
from livecode_server import LivecodeController

ctrl = LivecodeController()
ctrl.start()
ctrl.wait_for_browser()

# Music
ctrl.set_track("bass", 'note("c2 e2").s("sawtooth").play()')
ctrl.set_cps(0.5)
ctrl.hush()

# Visuals
ctrl.set_layer("bg", "background(0);")
ctrl.set_layer("shape", "fill(255,0,0); circle(width/2, height/2, 200);")
ctrl.clear()

ctrl.close()
```

## Key Concepts

### Tracks (Music)
- Each track is a named Strudel pattern
- Tracks are stacked — updating one replays all as a combined pattern
- Code must end with `.play()`
- Use `.bank()` with real samples for drums, not synth oscillators

### Layers (Visuals)
- Each layer is an independent p5.js code block running every frame
- Updating one layer does NOT affect others
- Use `window.state` for data that persists across layer updates
- Canvas uses `colorMode(HSB, 360, 100, 100, 100)` by default
- Press `C` in the browser to toggle code overlay, `L` for execution log

## Livestreaming

**To stream (X or Twitch), use manual OBS** — see the runbook
[`docs/livestreaming-obs.md`](docs/livestreaming-obs.md) (sources, audio routing, the
Restart-capture gotcha, per-platform ingest URLs, verification).

### Automated `stream.py` — DEFUNCT

> The old automated streamer below (headless browser + FFmpeg → Twitch) is **defunct**
> and unmaintained. Kept for reference only — see
> [`docs/archive/headless-browser-streaming.md`](docs/archive/headless-browser-streaming.md).

`stream.py` streamed the *legacy* Strudel-only page to Twitch with chat integration.

```bash
# Install extra dependencies
pip install python-dotenv playwright twitchAPI
playwright install chromium

# Configure credentials
cp .env.example .env  # Edit with your Twitch credentials

# Run
python stream.py
```

Required environment variables for streaming:
- `TWITCH_APP_ID`
- `TWITCH_APP_SECRET`
- `TWITCH_STREAM_KEY`
- `TWITCH_CHANNEL`

## Standalone Systems (Legacy)

The pre-unification Strudel-only and p5-only servers live in `legacy/` and still run:

```bash
cd legacy/
python strudel_live.py        # music only — open http://localhost:8766/strudel.html
python p5_live.py             # visuals only — open http://localhost:8776/p5.html
```

Prefer the unified `livecode.py` above for new work.

## File Overview

| File | Purpose |
|------|---------|
| `livecode.py` | Entry point — starts unified server |
| `livecode_server.py` | `LivecodeController` — WebSocket + HTTP/REST server |
| `livecode.html` | Browser client — p5.js canvas + Strudel audio |
| `legacy/` | Retired standalone Strudel-only + p5-only servers, REST APIs, and senders |
| `stream.py` | Twitch streaming + chat (uses legacy strudel) |
| `autopilot_host.py` | Playwright host for the autonomous improv loop |
| `autopilot/` | Steering + journal + ideas for the autopilot |
| `scenes/`, `compositions/`, `shows/`, `autoplay.py` | Showrunner system |
| `performances/` | Archival MP4 recordings of past shows |
| `test_steps.py` | Playwright regression test (101 checks across 14 phases) |
| `AGENTS.md` | Pointer to `CLAUDE.md` for non-Claude coding agents |

## Requirements

- Python 3.10+
- `websockets` (`pip install websockets`)
- A modern browser (Chrome recommended)
- For streaming: `python-dotenv`, `playwright`, `twitchAPI`, FFmpeg

## License

MIT
