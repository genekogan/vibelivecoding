# Livecode Project

AI-driven live coding — **music** (Strudel) and **visuals** (p5.js).

> **⛔ UNBREAKABLE PERFORMANCE RULE — never create unintended silence.**
> When performing (Improv/Autopilot/Showrunner), NEVER hush/stop/clear the
> current music before the next section is written and ready to turn on in the
> same breath. Write the next thing FIRST, then swap — ideally by replacing a
> track by name (atomic, gapless) or queuing the stop + the replacement to the
> same bar line. You do your thinking over a LIVE groove, never over silence.
> The only allowed bare silence is when the user explicitly says "stop"/"hush".
> Full doctrine: `.claude/skills/livecode-improv.md` §4.5.

> **Performance doctrine — every performing session (music seat, visual seat,
> solo) starts under these three rules:**
> 1. **Never silence** — the unbreakable rule above. The next thing is written
>    and ready before anything currently playing stops.
> 2. **Compose for dynamics.** Every fired section carries its own future:
>    verses/choruses, builds and breakdowns, slow LFOs, 8/16/32-bar variation —
>    enough internal change to stay interesting until the NEXT set is figured
>    out (minutes, not bars). A static loop is a countdown to boredom.
> 3. **Terse on stage.** Gene instructs; you translate to live code and pick up
>    his next instruction. English is the minimum needed to reason through the
>    move and make the code good, fast. No status reports, no recaps of what
>    you did, no restating his instruction or the state of things. Code first.

There are **four ways** to drive the server, layered on the same `livecode.py`
backend. Pick based on what the user asks for:

| Mode | When user says… | What it is | Skill |
|------|-----------------|------------|-------|
| **Manual** | "play this loop", "drop a kick" | Send single curl commands directly | `livecode-tips.md` |
| **Showrunner** | "play the disco set", "step through the show", "record a show" | Author/record/replay a deterministic timeline of saved sections (`shows/*.show.json`); arrow keys ← → step through it | `livecode-compose.md` |
| **Autopilot** | "start the autopilot", "kick off the loop" | YOU run `/loop` in this chat — wake every ~1 min via `ScheduleWakeup` to evolve visuals + music autonomously; user steers by typing messages | `autopilot.md` |
| **Improv** | "improvise", "jam", "keep going", "mix it up", "make something like X but new", "you got dis" | YOU perform continuously in-chat: **hand-write your own Strudel/p5 by default** (the catalog is context/inspiration, not the vocabulary you fire — writing-your-own forces diversity), terse English (code first, no narration beyond a line of musical reasoning), plan the next section while the current one plays, never idle, transition on bar lines. Fire a catalog asset verbatim only when the user names one or points at a past show. | **`livecode-improv.md`** |

Showrunner is **deterministic & step-able**; Autopilot is **timer-driven**;
Improv is **continuous & hand-played** (no `ScheduleWakeup` — you never stop
between sections). Don't conflate them — different surfaces, same server.

**Improv mode is where the hard-won stage lessons live** — transition doctrine
(land on bar lines, phase in, keep the beat across the seam, never hush), the
silent-failure catalog (`/status` 200 ≠ audible/visible), and the load/fps traps.
Read `.claude/skills/livecode-improv.md` before performing.

**For autopilot specifically** (`"start the autopilot"` etc.) — read
`.claude/skills/autopilot.md` FIRST. Don't go searching for `autonomous_ralph_loop.py`
(deleted legacy), don't run something from `compositions/` by mistake, don't
invoke `/schedule` (that's cloud cron, breaks in-session steering).

## Music Catalog System (stems / kits / arcs) — read the README

Beyond live improvisation there is a large **verified, parametric music catalog**
under `assets/music/` (707 stems · 132 kits · 12 arcs · 92 genres) that the
performing agent *retrieves and fires* rather than coding from scratch.
**`assets/music/README.md` is the START-HERE guide** — how to run, use, author,
verify, and grade it (the music counterpart to `.claude/skills/p5.md` for visuals).
Key facts: the catalog tooling runs on **port 9766** by convention (so it coexists
with the visual catalog on 8766); the browser explorer/grader is
`assets/music/browse.html`; a stem/kit is only "done" once it passes BOTH
`assets/tools/validate.py` AND `assets/tools/verify_arcs.py` (the kit×arc
section-audibility gate). Never hand off silent/too-quiet sound.

## Visual Catalog System (genart / worlds / subjects / fx …) — read the skill

The visual mirror of the music catalog: a large **verified, parametric p5.js
visual catalog** under `assets/visual/`
(374 genart · 81 world · 77 subject · 64 fx · 49 set · 42 floor · 49 post · 21 crowd · 46 palette · 803 indexed)
that the performing agent *retrieves and parameterizes* rather than coding from
scratch. **`.claude/skills/p5.md` is the START-HERE guide** — run, author,
validate, grade, extend.

**How to find a visual** (this is the retrieval surface — use it instead of
writing p5 from scratch on stage):

```bash
# BEST: ranked search from loose prose — scores tags>name>blurb, expands synonyms,
# and TELLS YOU which query concepts nothing covers (so you hand-write just that):
python3 assets/tools/find_visual.py "misty campfire night in the forest"
python3 assets/tools/find_visual.py --scene "underwater scene with submarine and pirates"
#   --scene groups winners by render slot → a complete fireable stack
#   --kind subject / -n 20 to narrow or widen

# fallback: grep the human-readable index (one line per asset)
grep -i 'fog\|haze\|atmosphere' assets/visual/INDEX.md     # prose → asset, grep-friendly
python3 -c "import json;[print(r['id'],'|',r['blurb']) for r in map(json.loads,open('assets/visual/index.jsonl')) if 'tiling' in r['tags']]"
```

Every row carries `{id, kind, slot, tags, blurb, params, path}`. `desc`+`tags` are
written to be grepped against Gene's stage prose. Fire one with
`assets/tools/fire_visual.py` (it disposes stale `window.state.<slot>` +
`window.state.P` first — raw `/p5/layer` inherits the outgoing asset's buffers).
Key facts: visuals own **port 8766** (music owns 9766 — never cross them); the
browser grader is `grade.html`; an asset is only "done" once `assets/tools/
validate.py` passes it (schema · clean deploy · fps ≥ 25 · motion · luminance ·
param poke) — and gates are a floor, not taste: **look at the pixels**.
Unverified assets sit in `inbox/` and never reach the index.

**Viskits** — layered visual compositions of catalog components (the visual
analog of a music kit): `assets/visual/kits/*.viskit.json`, played with
`assets/tools/viskit.py play <id> [--set hue=200 ...]`. A kit's `shared` param
block fans out to every layer that declares the param, so one dial moves the
whole scene.

## Three.js Live Surface (toggle p5 ↔ three.js) — read the skill

The third visual system: **200 parameterized threejs catalog scenes + the Little
Martians tributary (13 composite scenes, 110 archive models) + 594 Sketchfab
GLBs**, all indexed in `threejs/index.jsonl` (917 assets) and swappable onto the
live canvas with one renderer active at a time.
**`.claude/skills/three-live.md` is the START-HERE guide.**

```bash
python3 assets/tools/find_three.py "little martians flying home through space"
python3 surface.py preload flock     # warm heavy scenes in the background (p5 stays live)
python3 surface.py show flock        # ready-gated fade-in; p5 noLoop()'d underneath
python3 surface.py p5                # instant return; three frame parked at zero cost
```

Key facts: preload-then-show removes the visible 15s asset-load hole; parked
frames are display:none (no rAF, state kept → instant re-show, LRU cap 2);
`surface.py show scene.<id>` deep-links any catalog scene full-bleed
(`stageOnly=1`) with live Strudel audio (`audioSource=live-rendered-master`).
The server serves the 500-module threejs browser only because it speaks
HTTP/1.1 keep-alive with backlog 128 — don't downgrade `livecode_server.py`.

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

### Fresh Machine Setup (portability)

The repo is self-contained code/text — clone it (or copy the whole `livecode/`
directory) to a new machine and:

```bash
python3 -m venv .venv && source .venv/bin/activate   # any Python >= 3.10
pip install -r requirements.txt
playwright install chromium        # ONLY if using autopilot_host.py / test_steps.py / stream.py
python livecode.py                 # open http://localhost:8766/livecode.html
```

What does NOT travel via git (by design — see `.gitignore`):
- **Internet is required at runtime** — `livecode.html` loads p5.js + Strudel
  from CDNs (jsdelivr / esm.sh) and drum samples from `strudel.b-cdn.net`.
  Nothing is vendored; there is no offline mode.
- **`lm` symlink** — optional Little Martians three.js overlay. `lm_*.html`
  and most `surface.py` named scenes need it; core music+visuals run without
  it. Recreate per machine: `ln -s ~/Dev/littlemartians/3d-models lm`.
- **`.env`** — streaming secrets (Twitch) for `stream.py` only; copy by hand.
- **Media** (`performances/`, `*.png`, `*.mp4`, …) and `shows/unsorted/`
  auto-captures — travel via directory copy / Syncthing, never via git.

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

### lc wrapper (same API, no JSON quoting — for humans at a terminal)
```bash
./lc track bass 'note("c2 e2").s("sawtooth")'   # quoting handled for you
./lc layer bg 'background(0);'                  # code can also be @file or - (stdin)
./lc cps 0.55 && ./lc hush && ./lc clear
./lc status                                     # pretty state incl. last browser error
./lc errors -f                                  # follow browser-side errors live
./lc next / prev / goto 12 / mark drop / steps  # show navigation
./lc -p 9766 status                             # music-catalog server

# Conductor (quantized queue) — changes land ON bar lines, never mid-bar:
./lc track bass 'note("c2 e2").s("sawtooth")' --at 8      # next 8-bar line
./lc track pads '...' --at 8 --after 2                    # stagger: 2 bars later
./lc q                                          # pending + next-boundary ETAs
./lc qcancel q7                                 # or: qcancel all

# Conductor (score) — declared musicological intent, shared across sessions:
./lc con                                        # score + bar/bpm + boundary ETAs
./lc con key=am energy=.7 section=drop          # music seat declares (per change)
./lc con key=ab --at 8                          # declaration lands ON the bar line
./lc con note="drop at bar 160" from=music      # bar-stamped blackboard
./lc con clear
```
**The conductor keeps time via the queue and keeps intent via the score.**
Declared key/energy/section reach every visual asset through derived
`state.clk` fields (`keyHue` circle-of-fifths tint, `intensity` override,
`sectionName`/`sectionBars`) with zero per-asset wiring; per-slot param
bindings ride `fire_visual.py --bind` (spec: `assets/CONTRACT.md` §Conductor).
This is the interconnect for **two-seat performance** (one session on music,
one on visuals — protocol: `.claude/skills/livecode-improv.md` §3.2). Tempo
stays single-writer: `/strudel/cps`, never the score.

The server also prints a one-line log per accepted command (glyph · name ·
code size · latency) and surfaces browser-side runtime errors in the terminal
as they happen — watch that log during a performance.

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
| GET | `/q` | — conductor queue: transport position, next-boundary ETAs, pending + recent items |
| POST | `/q` | `{route, payload, at, offset}` or `{items:[...]}` — hold command(s), fire on the next `at`-bar line (+offset bars). Queueable: strudel track/stop/hush/cps, p5 layer/remove/fps/state, conductor |
| POST | `/q/cancel` | `{id}` or `{all: true}` |
| GET | `/conductor` | — conductor score + transport (bar/cps/bpm) + bar-line ETAs + pending count |
| POST | `/conductor` | `{key?, energy?, section?, tags?, note?, from?, clear?}` — partial merge; explicit `null` clears a field. Pushed into `window.state.conductor`; derived K fields reach all assets |

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
| `shows/visuals/*.visuals.json` | Visual-only bookmarks — `vis_bookmark.py save/load/list` (never touches music) |
| `surface.py` | Swap the visual surface between the p5 canvas and any three.js page (p5 keeps running underneath; `lm` scenes need the symlink) |
| `performances/` | Archival MP4 recordings of past performances — not loaded by code |
| `autoplay.py` | Driver — advances show on a clock (Ns/Nbeats/Nbars/Ncycles) |
| `.claude/skills/livecode-compose.md` | Composition skill (scene catalog + cookbook) |
| `test_steps.py` | Playwright regression (`python test_steps.py` — 118 checks, 15 phases incl. conductor score; starts its own server) |

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
| `research/generative/FINAL_REPORT.md` | **What's in the genart catalog now** (374 genart of 803 indexed visual assets) — coverage by family, ranked self-grades, second-pass brief |
| `grade.html` | **Browser grader** (`localhost:8766/grade.html`) — live-render + bad/ok/good every genart, exports `visual-grades.jsonl` |
| **`assets/music/README.md`** | **Music catalog system — START HERE for music.** Run/use/author/verify/grade the stems+kits+arcs catalog; the map to CONTRACT + BUNDLE + the toolchain |
| `assets/music/browse.html` | **Music browser + grader** (`localhost:9766/assets/music/browse.html`) — audition the sound space by keyboard, fire kits through arcs, grade bad/ok/good → `assets/music/grades.jsonl` |
| `assets/music/BUNDLE.md` | Verified Strudel feature matrix + BANNED list + loudness recipe (music authoring) |
| `assets/prompts/music-factory.md` | **Music factory pass** — how to run a wave-based catalog build |
| `.claude/skills/strudel.md` | **Strudel CRAFT guide** — music syntax + sample packs + genre recipes (pair with the README for the *system*) |
| `.claude/skills/livecode-tips.md` | **Manual-mode tips** — starting the server, curl basics, streaming |
| `.claude/skills/livecode-compose.md` | **Showrunner skill** — author/record/replay shows w/ scenes lib |
| `.claude/skills/autopilot.md` | **Autopilot skill** — autonomous in-session improv loop |
| **`.claude/skills/livecode-improv.md`** | **Improv skill — START HERE to perform live.** Transition doctrine (bar lines, phase-in, keep the beat), the silent-failure catalog, load/fps traps, saved sets, craft notes |
| `assets/sets/*.json` | **Saved sets** (`livecode-set-v1`) — a kit×arc + visual stack + params + grade that actually worked. `set_play.py` / `set_save.py` |
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
