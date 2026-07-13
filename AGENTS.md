# Livecode Project

AI-driven live coding — **music** (Strudel) and **visuals** (p5.js).

There are **three ways** to drive the server, layered on the same `livecode.py`
backend. Pick based on what the user asks for:

| Mode | When user says… | What it is | Skill |
|------|-----------------|------------|-------|
| **Manual** | "play this loop", "drop a kick" | Send single curl commands directly | `livecode-tips.md` |
| **Showrunner** | "play the disco set", "step through the show", "record a show" | Author/record/replay a deterministic timeline of saved sections (`shows/*.show.json`); arrow keys ← → step through it | `livecode-compose.md` |
| **Autopilot** | "start the autopilot", "start the improv loop", "kick off the loop" | YOU run `/loop` in this chat — wake every ~1 min via `ScheduleWakeup` to evolve visuals + music autonomously; user steers by typing messages | `autopilot.md` |

Showrunner is **deterministic & step-able**; Autopilot is **autonomous & improvised**.
Don't conflate them — they're different surfaces over the same server.

**For autopilot specifically** (`"start the autopilot"` etc.) — read
`.claude/skills/autopilot.md` FIRST. Don't go searching for `autonomous_ralph_loop.py`
(deleted legacy), don't run something from `compositions/` by mistake, don't
invoke `/schedule` (that's cloud cron, breaks in-session steering).

## Music Catalog System (stems / kits / arcs) — read the README

Beyond live improvisation there is a large **verified, parametric music catalog**
under `assets/music/` (407 stems · 44 kits · 12 arcs · 41 genres) that the
performing agent *retrieves and fires* rather than coding from scratch.
**`assets/music/README.md` is the START-HERE guide** — how to run, use, author,
verify, and grade it (the music counterpart to `.claude/skills/p5.md` for visuals).
Key facts: the catalog tooling runs on **port 9766** by convention (so it coexists
with the visual catalog on 8766); the browser explorer/grader is
`assets/music/browse.html`; a stem/kit is only "done" once it passes BOTH
`assets/tools/validate.py` AND `assets/tools/verify_arcs.py` (the kit×arc
section-audibility gate). Never hand off silent/too-quiet sound.

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
| GET | `/state` | Autopilot: full code dump (tracks + layers code, cps, setup) |
| GET | `/errors` | Autopilot: recent browser-side runtime errors (deque, maxlen 50) |
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
| `performances/` | Archival MP4 recordings of past performances — not loaded by code |
| `autoplay.py` | Driver — advances show on a clock (Ns/Nbeats/Nbars/Ncycles) |
| `.claude/skills/livecode-compose.md` | Composition skill (scene catalog + cookbook) |
| `test_steps.py` | Playwright regression (`python test_steps.py` — 101 checks, 14 phases; server must be running) |

## Autopilot — Autonomous Improv Loop

The autopilot is **the Claude session itself** running `/loop` in dynamic mode,
waking up via `ScheduleWakeup` every ~1 minute to evolve the canvas + music.
It's NOT a background script the user starts and walks away from — it lives
in the conversation, and the user steers by typing.

```bash
# Two long-running background pieces (the agent launches these via nohup):
python livecode.py                      # server
python autopilot_host.py                # Playwright headed browser that auto-clicks
                                        # Start and writes downscaled snapshots to
                                        # autopilot/snapshots/latest.png for the agent to see
# Then the agent invokes /loop in THIS chat (not /schedule, not a subagent).
```

| Path | Purpose |
|------|---------|
| `autopilot_host.py` | Playwright host — launches Chromium, clicks Start, samples snapshots |
| `autopilot/instructions.md` | **Live creative steering** — re-read every round, edit anytime |
| `autopilot/journal.md` | Append-only log of every round (scene name + category tag + recipe) |
| `autopilot/ideas.md` | Brainstorm pool of scene concepts to pick from |
| `autopilot/snapshots/latest.png` | Most recent canvas snapshot (the agent's "eyes"); `prev1.png`–`prev3.png` hold rolling history |
| `autopilot/run.sh` | Convenience launcher |
| `.claude/skills/autopilot.md` | **Autopilot skill** — how the agent launches & runs the loop |

User steers mid-loop simply by typing in chat — those messages land in the
agent's context naturally and influence the next round. No queue file needed.

## Standalone Systems (retired — preserved under `legacy/`)

These were the pre-unification Strudel-only and p5-only servers. They still
work if you `cd legacy/` and run them, but the unified `livecode.py` is the
supported path. Don't add features here.

### Strudel (Music)
| Component | Purpose |
|-----------|---------|
| `legacy/strudel_server.py` | `StrudelController` — WebSocket (8765) + HTTP file server (8766) |
| `legacy/strudel.html` | Browser client: Strudel @strudel/web@1.0.3 engine + console |
| `legacy/strudel_live.py` | HTTP REST API (8767) for external/agent control |
| `legacy/strudel_send.py` | One-shot CLI to send Strudel code via WebSocket |
| `stream.py` | Twitch streaming + chat (FFmpeg + Playwright) — points at legacy strudel |

### p5.js (Visuals)
| Component | Purpose |
|-----------|---------|
| `legacy/p5_server.py` | `P5Controller` — WebSocket (8775) + HTTP file server (8776) |
| `legacy/p5.html` | Browser client: full-screen p5.js 1.11.11 canvas + layer system |
| `legacy/p5_live.py` | HTTP REST API (8777) for external/agent control |
| `legacy/p5_send.py` | One-shot CLI to send p5.js code via WebSocket |
| `legacy/play_p5_demo.py` | Example visual composition |

### Standalone How to Run

```bash
cd legacy/
python strudel_live.py        # music only — open http://localhost:8766/strudel.html
python p5_live.py             # visuals only — open http://localhost:8776/p5.html
```

## Documentation

| Doc | Purpose |
|-----|---------|
| `.claude/skills/p5.md` | **p5.js visual-system guide — START HERE for visuals.** Run/author/validate/grade/extend the genart catalog; the map to CONTRACT + author-brief + factory docs |
| `assets/CONTRACT.md` | **The asset spec (visual + music)** — engine facts (clk/audio), P-block, slots, params, validation gates, file formats |
| `assets/prompts/author-brief.md` | **Visual authoring checklist** — exact gate numbers, universal params, aesthetic mandate, motion/luminance lessons |
| `assets/prompts/generative-factory.md` | **Generative-art factory pass** — how to run a wave-based +100-asset build (Ralph-loop doctrine) |
| `research/generative/FINAL_REPORT.md` | **What's in the genart catalog now** (166 pieces) — coverage by family, ranked self-grades, second-pass brief |
| `grade.html` | **Browser grader** (`localhost:8766/grade.html`) — live-render + bad/ok/good every genart, exports `visual-grades.jsonl` |
| **`assets/music/README.md`** | **Music catalog system — START HERE for music.** Run/use/author/verify/grade the stems+kits+arcs catalog; the map to CONTRACT + BUNDLE + the toolchain |
| `assets/music/browse.html` | **Music browser + grader** (`localhost:9766/assets/music/browse.html`) — audition the sound space by keyboard, fire kits through arcs, grade bad/ok/good → `assets/music/grades.jsonl` |
| `assets/music/BUNDLE.md` | Verified Strudel feature matrix + BANNED list + loudness recipe (music authoring) |
| `assets/prompts/music-factory.md` | **Music factory pass** — how to run a wave-based catalog build |
| `.claude/skills/strudel.md` | **Strudel CRAFT guide** — music syntax + sample packs + genre recipes (pair with the README for the *system*) |
| `.claude/skills/livecode-tips.md` | **Manual-mode tips** — starting the server, curl basics, streaming |
| `.claude/skills/livecode-compose.md` | **Showrunner skill** — author/record/replay shows w/ scenes lib |
| `.claude/skills/autopilot.md` | **Autopilot skill** — autonomous in-session improv loop |
| `docs/livestreaming-obs.md` | **Livestream runbook** — manual OBS → X/Twitch, audio routing, Restart-capture gotcha |
| `docs/archive/headless-browser-streaming.md` | **Defunct** — old `stream.py` headless-browser→FFmpeg→Twitch (archived, revival notes) |
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
