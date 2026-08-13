# Livecode

AI-driven live coding for **music** ([Strudel](https://strudel.cc)) and **visuals** ([p5.js](https://p5js.org) + [three.js](https://threejs.org)), driven over a plain curl/REST interface.

Send patterns and sketches from your terminal, your scripts, or an AI agent — they play instantly in the browser. On top of the live surface sits a large **verified asset catalog** (803 visual assets, 707 music stems, 917 three.js scenes) that a performing agent retrieves and parameterizes instead of coding every scene from scratch.

## Quick Start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python livecode.py
```

Open <http://localhost:8766/livecode.html> and click **Start Audio & Visuals**. Then:

```bash
# Play a bass pattern
curl localhost:8766/strudel/track -d '{"name":"bass","code":"note(\"c2 e2 g2\").s(\"sawtooth\").play()"}'

# Draw a red circle
curl localhost:8766/p5/layer -d '{"name":"shape","code":"fill(255,0,0); circle(width/2,height/2,200);"}'

curl -X POST localhost:8766/strudel/hush   # stop music
curl -X POST localhost:8766/p5/clear       # clear visuals
```

> **Internet is required at runtime.** `livecode.html` loads p5.js and Strudel from CDNs and drum samples from `strudel.b-cdn.net`. Nothing is vendored; there is no offline mode.

### `lc` — the same API without the JSON quoting

```bash
./lc track bass 'note("c2 e2").s("sawtooth")'
./lc layer bg 'background(0);'
./lc cps 0.55 && ./lc hush && ./lc clear
./lc status                       # pretty state incl. last browser error
./lc errors -f                    # follow browser-side errors live
./lc track pads '...' --at 8      # land the change on the next 8-bar line
./lc q                            # pending queue + next-boundary ETAs
```

### Browse all three catalogs in one window

```bash
python livecode.py --catalog --kiosk
```

Opens `catalog.html` with dedicated three.js, p5.js, and Strudel pages on one server. The p5 and three.js catalogs work immediately; click **Enable audio** once before auditioning Strudel assets.

## Four Ways to Drive It

| Mode | What it is | Guide |
|---|---|---|
| **Manual** | Send curl / `lc` commands directly — see Quick Start | [livecode-tips.md](.claude/skills/livecode-tips.md) |
| **Showrunner** | Author, record, and replay a deterministic timeline of sections (`shows/*.show.json`). Step it with arrow keys or the show browser. | [livecode-compose.md](.claude/skills/livecode-compose.md) |
| **Autopilot** | An autonomous improv loop. Tell Claude Code "start the autopilot" — it wakes every ~1 min, evolves music + visuals, and listens to your messages between rounds. | [autopilot.md](.claude/skills/autopilot.md) |
| **Improv** | Continuous hand-played performance: the agent writes its own Strudel/p5 live, plans the next section while the current one plays, and transitions on bar lines. | [livecode-improv.md](.claude/skills/livecode-improv.md) |

Showrunner is deterministic and step-able; Autopilot is timer-driven; Improv is continuous. Same server underneath.

## How It Works

`livecode_server.py` runs two services:

- **WebSocket** on port 8765 — real-time channel to the browser
- **HTTP + REST** on port 8766 — serves the client and accepts commands

`livecode.html` renders a full-screen p5.js canvas and hosts the Strudel audio engine. Code sent via the API is evaluated live in the browser. Every accepted command is auto-recorded into a timeline.

### The conductor — changes that land in rhythm

Commands can be **queued to a bar line** instead of firing mid-bar, so transitions stay musical:

```bash
./lc track bass 'note("c2 e2").s("sawtooth")' --at 8   # next 8-bar line
./lc con key=am energy=.7 section=drop                 # declare musical intent
```

The **queue** keeps time; the **score** keeps intent. Declared key/energy/section reach every visual asset through derived `state.clk` fields (circle-of-fifths hue, intensity, section name) with no per-asset wiring — which is what makes **two-seat performance** work: one session on music, one on visuals, sharing state.

## Asset Catalogs

Large parametric, **verified** catalogs the performing agent retrieves from rather than authoring from scratch. An asset only enters the index once it passes automated gates (schema, clean deploy, fps ≥ 25, motion, luminance, param poke for visuals; section-audibility for music).

| Catalog | Size | Start here |
|---|---|---|
| **Visual** (p5.js) | 803 indexed — 374 genart, 81 world, 77 subject, 64 fx, 49 set, 49 post, 46 palette, 42 floor, 21 crowd | [`.claude/skills/p5.md`](.claude/skills/p5.md) |
| **Music** (Strudel) | 707 stems · 132 kits · 12 arcs · 92 genres | [`assets/music/README.md`](assets/music/README.md) |
| **Three.js** | 917 assets — 200 catalog scenes, 13 composite scenes, 594 GLBs | [`.claude/skills/three-live.md`](.claude/skills/three-live.md) |

```bash
# Ranked search from loose prose — tells you which concepts nothing covers
python3 assets/tools/find_visual.py "misty campfire night in the forest"
python3 assets/tools/find_visual.py --scene "underwater scene with submarine"
python3 assets/tools/find_three.py "flying home through space"
```

Fire one with `assets/tools/fire_visual.py`. **Viskits** (`assets/visual/kits/*.viskit.json`) are layered compositions whose shared param block fans out to every layer, so one dial moves the whole scene.

The visual catalog owns port **8766**, the music catalog tooling port **9766** — never cross them. Browser graders: `grade.html` (visual) and `assets/music/browse.html` (music).

> The three.js asset tree (`threejs/`) is **not** in git — it is large generated/binary content. `assets/tools/find_three.py` and the named `surface.py` scenes need it present locally.

## Three.js Live Surface

One renderer is active at a time; p5 keeps its state underneath.

```bash
python3 surface.py preload flock   # warm heavy scenes in the background
python3 surface.py show flock      # ready-gated fade-in
python3 surface.py p5              # instant return
```

Preload-then-show removes the visible asset-load hole; parked frames are `display:none` (no rAF, state kept, LRU cap 2).

## Shows, Setlists, and the Show Browser

A **show** is a bookmark that recreates something you already played and chose to keep — just code and metadata, so shows are small and diff-able. `/show/mark` cuts the timeline into named sections; arrow keys step between them.

```bash
localhost:8766/shows.html        # browse, load, and step saved shows
python autoplay.py --show shows/disco_hall.show.json --dwell 16beats
```

Stepping a show behaves like live coding it: `/show/goto` collapses the target's **net state**, diffs it against the live stage, and lands only the differences on the next bar line. Unchanged tracks are never touched, so the groove carries across the seam and the transport never resets.

**Setlists** treat a show *section* as the atomic unit, so you can recombine sections from any show as plain text:

```
name: Friday closing set
seam: 4
gqom_weight#1
disco_hall#1  cps=0.56 label="Jazzy but faster"
disco_hall#13 only=drums,bass
```

```bash
python3 setlist.py list <show>          # numbered sections
python3 setlist.py play <f.setlist>     # compile + load
```

A compiled setlist is an ordinary `.show.json` — steppable, and itself a valid setlist source.

## REST API

### Music (Strudel)

| Method | Route | Body |
|---|---|---|
| POST | `/strudel/track` | `{"name":"bass","code":"...play()"}` — set/update a named track |
| POST | `/strudel/stop` | `{"name":"bass"}` |
| POST | `/strudel/hush` | `{}` — stop all tracks |
| POST | `/strudel/cps` | `{"cps":0.5}` — tempo (cycles per second) |
| POST | `/strudel/mute` | `{"on":true}` — latch the audio tap's monitor gain at 0 |
| POST | `/strudel/drain` | `{"maxMs":8000}` — mute until the analyser reports quiet |
| GET | `/strudel/drain_state` | `{rms, peak, elapsed, timedOut}` |
| POST | `/strudel/reset` | `{"quantumCycles":1}` — reset on the next clocked cycle boundary |
| POST | `/strudel/send` | `{"code":"...","evaluate":true}` |

### Visuals (p5.js)

| Method | Route | Body |
|---|---|---|
| POST | `/p5/layer` | `{"name":"bg","code":"background(0);"}` |
| POST | `/p5/remove` | `{"name":"bg"}` |
| POST | `/p5/clear` | `{}` |
| POST | `/p5/setup` | `{"code":"..."}` — hard recompile (recreates canvas) |
| POST | `/p5/send` | `{"code":"..."}` |
| POST | `/p5/state` | `{"key":"hue","value":200}` — persistent state |
| POST | `/p5/fps` | `{"fps":30}` |
| GET | `/p5/read` | read back live canvas/layer state |

### Conductor

| Method | Route | Body |
|---|---|---|
| GET | `/q` | transport position, next-boundary ETAs, pending + recent items |
| POST | `/q` | `{route, payload, at, offset}` — hold and fire on the next `at`-bar line |
| POST | `/q/cancel` | `{"id":"q7"}` or `{"all":true}` |
| GET | `/conductor` | score + transport (bar/cps/bpm) + bar-line ETAs |
| POST | `/conductor` | `{key?, energy?, section?, tags?, note?, from?, clear?}` — partial merge |

### Status

| Method | Route | Description |
|---|---|---|
| GET | `/status` | `{ready, tracks[], layers[], cps, transportGeneration, step, totalSteps, recording, ...}` |
| GET | `/state` | Full code dump (tracks + layers + cps + setup) — used by autopilot for self-correction |
| GET | `/errors` | Recent browser-side runtime errors (deque, maxlen 50) |
| GET | `/transport` | Owned scheduler/audio/output frame, with provenance and confidence |

### Shows

| Method | Route | Body |
|---|---|---|
| GET | `/shows/list` | catalog saved shows + visual bookmarks — powers `shows.html` |
| GET | `/show/steps` | list current timeline (truncated codes) |
| GET | `/show/save` | return the timeline as a JSON doc |
| POST | `/show/next` · `/show/prev` | `{}` |
| POST | `/show/goto` | `{"step":N, "at":8, "hard":false}` |
| POST | `/show/mark` | `{"label":"drop"}` |
| POST | `/show/recording` | `{"enabled":true}` |
| POST | `/show/load` · `/show/load_file` · `/show/save_file` | `{steps:[...]}` / `{"path":"shows/foo.show.json"}` |

Autosaves to `shows/unsorted/jam_<ts>.show.json` every 60s and on shutdown. **Save before you stop** — autosave-on-shutdown does not always fire if the server is killed.

## Python API

```python
from livecode_server import LivecodeController

ctrl = LivecodeController()
ctrl.start()
ctrl.wait_for_browser()

ctrl.set_track("bass", 'note("c2 e2").s("sawtooth").play()')
ctrl.set_cps(0.5)
ctrl.set_layer("bg", "background(0);")
ctrl.hush(); ctrl.clear(); ctrl.close()
```

## Key Concepts

**Tracks (music)** — each is a named Strudel pattern; tracks are stacked, so updating one replays all as a combined pattern. Code must end with `.play()`. Use `.bank()` with real samples for drums, not synth oscillators. Load sample packs before use; `gm_*` soundfont instruments are not in the CDN bundle.

**Layers (visuals)** — each is an independent p5.js block running every frame; updating one does not touch the others. Code runs inside `draw()`, so never call `createCanvas()` or `setup()` in a layer. `push()`/`pop()` wraps each layer automatically. Use `window.state` for data that must survive layer updates. Canvas defaults to `colorMode(HSB, 360, 100, 100, 100)`. Press `C` for the code overlay, `L` for the execution log.

## Livestreaming

**Use manual OBS** — see the runbook [`docs/livestreaming-obs.md`](docs/livestreaming-obs.md) (sources, audio routing, the Restart-capture gotcha, per-platform ingest, verification).

> **`stream.py` is defunct** — the old headless-browser + FFmpeg → Twitch streamer is unmaintained and points at the legacy Strudel-only page. Kept for reference: [`docs/archive/headless-browser-streaming.md`](docs/archive/headless-browser-streaming.md). It reads `TWITCH_APP_ID`, `TWITCH_APP_SECRET`, `TWITCH_STREAM_KEY`, and `TWITCH_CHANNEL` from `.env` (see `.env.example`).

## Testing

```bash
python test_steps.py     # Playwright regression — 119 checks across 15 phases
```

Starts its own server. Needs `playwright install chromium`. The `e2e/` harness (Playwright MCP, isolated ports) is described in [`E2E.md`](E2E.md).

## Repo Layout

| Path | Purpose |
|---|---|
| `livecode.py` · `livecode_server.py` · `livecode.html` | Entry point · controller (WS + HTTP/REST) · browser client |
| `lc` | Shell wrapper over the REST API |
| `surface.py` | Swap the visual surface between p5 and three.js |
| `setlist.py` · `shows.html` · `autoplay.py` | Setlist compiler · show browser · clock-driven replay |
| `assets/` | Visual + music catalogs, `assets/CONTRACT.md` (the asset spec), authoring prompts, tooling |
| `shows/` | Curated replayable shows (`unsorted/` holds gitignored auto-captures) |
| `scenes/` · `compositions/` | Scene primitives and recipes for the Showrunner |
| `autopilot/` · `autopilot_host.py` | Steering, journal, ideas + the Playwright host |
| `.claude/skills/` | Agent guides — improv, compose, autopilot, p5, strudel, three-live |
| `docs/` | Strudel reference/examples, livestream runbook, design archive |
| `legacy/` | Retired standalone Strudel-only and p5-only servers |
| `AGENTS.md` | Full project instructions for coding agents (`CLAUDE.md` points here) |

## Requirements

- Python 3.10+ (developed on 3.11) — `pip install -r requirements.txt`
- A modern browser (Chrome recommended)
- Internet access at runtime (CDN-loaded p5.js, Strudel, and samples)
- `playwright install chromium` for `autopilot_host.py` and `test_steps.py`

Not carried by git, by design: the `threejs/` asset tree, media (`performances/`, `*.mp4`, `*.png`, …), `shows/unsorted/` captures, `.env`, and the optional `lm` symlink (`ln -s ~/Dev/littlemartians/3d-models lm`).

## License

MIT — see [LICENSE](LICENSE).
