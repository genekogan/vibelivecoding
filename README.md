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
| GET | `/status` | Returns `{ready, tracks[], layers[], cps}` |

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

## Twitch Streaming (Optional)

`stream.py` can stream the browser output to Twitch with chat integration.

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

The Strudel and p5.js systems can also run independently:

```bash
# Music only
python strudel_live.py
# Open http://localhost:8766/strudel.html

# Visuals only
python p5_live.py
# Open http://localhost:8776/p5.html
```

## File Overview

| File | Purpose |
|------|---------|
| `livecode.py` | Entry point — starts unified server |
| `livecode_server.py` | `LivecodeController` — WebSocket + HTTP/REST server |
| `livecode.html` | Browser client — p5.js canvas + Strudel audio |
| `strudel_server.py` | Standalone Strudel server |
| `strudel.html` | Standalone Strudel browser client |
| `strudel_live.py` | Standalone Strudel REST API |
| `strudel_send.py` | CLI tool to send Strudel code |
| `p5_server.py` | Standalone p5.js server |
| `p5.html` | Standalone p5.js browser client |
| `p5_live.py` | Standalone p5.js REST API |
| `p5_send.py` | CLI tool to send p5.js code |
| `stream.py` | Twitch streaming + chat integration |

## Requirements

- Python 3.10+
- `websockets` (`pip install websockets`)
- A modern browser (Chrome recommended)
- For streaming: `python-dotenv`, `playwright`, `twitchAPI`, FFmpeg

## License

MIT
