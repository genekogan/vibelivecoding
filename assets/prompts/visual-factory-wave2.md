# Visual Factory — Wave 2 (triple the p5 catalog)

> Paste this whole file as the opening prompt of a fresh Claude Code session in
> `/Users/gene/Dev/livecode`. It is written to be run **unsupervised**.

---

## STEP 0 — DO NOTHING UNTIL 06:30 LOCAL. THIS IS THE FIRST INSTRUCTION.

Gene is asleep. **Do not author, do not read the codebase, do not touch a
server, do not spawn an agent until 06:30 America/New_York.** Your very first
action in this session is to arm the wait and then stop talking:

```bash
# Bash tool, run_in_background: true  (a FOREGROUND sleep is blocked by the harness,
# and it would exceed the 10-minute Bash timeout anyway)
python3 -c "
import time, datetime
t = datetime.datetime.now().replace(hour=6, minute=30, second=0, microsecond=0)
if t <= datetime.datetime.now(): t += datetime.timedelta(days=1)
d = (t - datetime.datetime.now()).total_seconds()
print(f'sleeping {d/3600:.2f}h until {t:%H:%M}')
time.sleep(d)
print('06:30 — BEGIN THE FACTORY')
"
```

That command exits at 06:30 and re-invokes you automatically. Say one short line
("armed — starting at 06:30"), then **do not do anything else until it fires.**
When it fires, begin at STEP 1 and run to completion without further prompting.

---

## STEP 1 — Mission

**Triple the p5.js visual catalog: 334 → ~1000 indexed assets (+666 new.)**

Gene's exact standing brief for this run:

- **Exploration over exploitation.** Do some exploitation (density: fill the gaps
  *between* existing pieces, hybridize two catalog concepts) — but **emphasize
  exploration much more**: new objects, scenes, algorithms, settings, generative-art
  families, techniques, aesthetics. Go where the catalog isn't.
- **Overindex full-screen work with segments, depth, layers, motion, texture, and
  subtle generative qualities.**
- **Underindex "cartoon"-like characters and objects — there are already enough.**
  The `subject`/`crowd` families are near-frozen this wave (see quotas).
- Everything must be **steerable / customizable, internally varied and dynamic,
  parameterized, well-described, searchable, and indexed in the docs and in the
  browser** — the same bar the music catalog holds.
- **Every asset must actually render before you hand it off.** Not "the gate
  returned 200" — you must *look at the pixels*. See STEP 5.
- **You have Gene's full trust. Do not ask for clarification, sign-off, or
  permission. Make the call and keep moving.** He is asleep and will read the
  report when he wakes.

---

## STEP 2 — Read first, in this order

1. `.claude/skills/p5.md` — the visual system guide (run/author/validate/grade/extend). **The map.**
2. `assets/CONTRACT.md` — the spec: P-block preamble (D/P/S/K/A), `__SLOT__`, kind→slot z-order, universal params, file formats, gates.
3. `assets/prompts/author-brief.md` — the authoring checklist: exact gate numbers, universal params, **the aesthetic mandate (escape the cartoon default)**, motion/luminance lessons.
4. `assets/prompts/generative-factory.md` — how a wave-based +100 build is run (Ralph-loop doctrine).
5. `assets/visual/FACTORY_STATE.md` — prior sessions' resume state + learned traps.
6. `research/generative/FINAL_REPORT.md` — what's in the genart catalog now, ranked.
7. **Dedup pass (mandatory):** read `assets/visual/index.jsonl` end-to-end and skim
   `assets/visual/INDEX.md`. You cannot "explore" without knowing the 334 things
   that already exist. Every shard brief you write must name what it is NOT duplicating.

Also read `assets/music/FACTORY_STATE.md` § SESSION 5 — the music wave that just
ran at the same scale. Its process notes (staging dependents outside the inbox,
per-agent dedup briefs, watching the right failure signal) transfer directly.

---

## STEP 3 — The four shards

Split the +666 into **4 independent shards**, one per subagent, ~167 each. Shards
are chosen so two agents never collide on a concept:

| Shard | Territory | Examples of *unexplored* ground (go beyond these) |
|---|---|---|
| **A — Fields, Flows & Continua** | full-screen continuous fields; the "no objects, just medium" shard | reaction-diffusion (Gray-Scott families), advection/semi-Lagrangian fluid, curl-noise flow, wave-equation ripples, interference & moiré, caustics, plasma, domain-warped gradients, iso-contour bands, phase fields, anisotropic diffusion |
| **B — Structure, Tiling & Architecture** | segments, panels, depth, perspective, built space | aperiodic/substitution tilings (Penrose, Ammann, hat/spectre), Truchet families, Wang tiles, girih, mazes & labyrinths, circuit/PCB, isometric cities, corridors & tunnels, one/two/three-point perspective grids, nested frames, brutalist facades, cross-sections, exploded diagrams |
| **C — Growth, Agents & Emergence** | process pieces that *become* rather than *are* | physarum/slime-mold transport networks, DLA & dendrites, L-systems, Lenia & continuous CA, reaction networks, n-body & gravitational, erosion/hydrology, crack propagation, phyllotaxis beyond the existing one, differential growth, space colonization, flocking-as-texture (not as cartoon birds) |
| **D — Texture, Material, Atmosphere & Composite** | the "less cartoon, more material" shard; also the compositing families | paper/ink/risograph/halftone/screenprint, engraving & hatching, film grain & bloom, volumetric light/fog/godrays, weathering & patina, cloth & drape, fake-refraction glass, dust & atmosphere, plus the `post` / `fx` / `floor` / `palette` families and layers built to composite *under/over* other layers |

**Global family quotas** (the mix that produces the emphasis Gene asked for —
balance across waves so the totals land here):

| family | now | add | after |
|---|---|---|---|
| `genart` (bg, full-screen) | 166 | **+430** | ~600 |
| `world` (bg scenes) | 25 | +50 | ~75 |
| `fx` | 20 | +50 | ~70 |
| `set` | 20 | +40 | ~60 |
| `post` | 15 | +35 | ~50 |
| `floor` | 15 | +35 | ~50 |
| `palette` | 10 | +20 | ~30 |
| `subject` | 51 | **+6 only** | ~57 |
| `crowd` | 12 | **+0** | 12 |

`subject`'s six must be **abstract/architectural/organic silhouettes** — no
characters, no mascots, no cartoon props. If a shard wants to skip its subject
allocation entirely, skip it.

---

## STEP 4 — The Ralph loop (this is the whole execution model)

```
while indexed_assets < 1000:
    # ---- parallel: authoring is pure text, so this is where you fan out
    spawn 4 subagents (one per shard) IN ONE MESSAGE, each writing ~20-25
    assets to assets/visual/inbox/ — subagents NEVER touch the server
    # ---- serial: the canvas is single-threaded, you alone drive it
    gf_snap  → contact sheet → LOOK AT IT → validate → index → commit
    requeue duds WITH SPECIFIC CRITIQUE; twice-failed → graveyard/ + a note
```

**Do not stop between waves. Do not ask whether to continue. Do not wait for
Gene.** When a wave lands, immediately brief the next one — the previous wave's
contact sheet is the input to the next wave's briefs (that's the exploitation
half: what looked good gets a neighbourhood; what looked dead gets abandoned).

Per-wave rules that make this work:

- **Subagents never call the server** (no curl, no `livecode.py`, no `validate.py`,
  no `build_index.py`, no `pkill`). They write JSON files and a manifest. Only YOU
  drive the canvas, serially. This is what let 6 music agents run concurrently with
  zero collisions.
- **Give every subagent an explicit dedup list** — the ids in its territory that
  already exist, and the instruction to name what it is not cloning.
- **Each subagent maintains `scratchpad/gf/w<N>/<shard>_manifest.md`** (plan up
  top, appended per file) so a crash loses nothing.
- Existing wave tooling is in `scratchpad/gf/`: `gf_snap.py` (deploy + t/t+8s
  frames + motion/lum/fps → `metrics.jsonl`), `gf_sheet.py` (labeled contact
  sheet), `author_workflow.js` (the Workflow driver, if you prefer it to Agent
  fan-out). Reuse them; don't rebuild them.
- **Commit every wave.** `git add assets/visual assets/prompts scratchpad/gf && git commit`.
  Never `--no-verify`.

---

## STEP 5 — "It must render" — the acceptance bar

`/status` 200 and an empty `/errors` prove the code **ran**. They do not prove it
**looks like anything**. The gates (author-brief.md has exact numbers): schema ·
clean deploy · **fps ≥ 25** · **motion** (320px snapshots 8 s apart differ > 0.004,
and don't strobe < 0.35) · **luminance** mean ∈ [0.02, 0.92] · **param poke** (first
two numeric params change the render).

**On top of the gates, you must LOOK.** Every wave: `gf_sheet.py` → contact sheet →
Read the PNG → vision-critique each tile → requeue the boring ones. A piece can pass
every gate and still be a grey smear. Gate numbers are a floor, not taste.

Regenerate the grader manifest whenever the catalog changes so `grade.html` picks
new work up:
```bash
python -c "…"   # see .claude/skills/p5.md §6 for the exact genart_manifest.json regen
```

---

## STEP 6 — Traps that have already cost real time (do not rediscover)

- **NO STROBE. This is a hard safety rule, not taste.** No high-contrast fast
  flicker (black/white ~3–15 Hz). Gene has flagged this on stage. Avoid
  `post.beat_flash`-like flashing, lightning, `rgb_glitch`, `shake`; avoid
  `1bit`/`mono`/`terminal`/`phosphor` style families; prefer soft gradients and low
  energy defaults; be conservative above cps 0.6. The motion gate's `< 0.35` ceiling
  is a backstop, **not** permission to approach it.
- **Motion re-phasing is the #1 silent failure.** The gate compares frames 8 s
  apart, so anything driven only by `K.beat`/`K.pulse`/`K.cyc` reads as frozen — and
  a single-frequency `K.t` term whose period lands near 8 s (e.g. `sin(K.t*0.8)`)
  self-cancels too. Drive the motion floor with **incommensurate real-time `K.t`
  frequencies**: `0.9*sin(K.t*0.61) + 0.5*sin(K.t*1.43+1.7) + 0.32*sin(K.t*2.29)`.
- **`window.state.<slot>` is never cleared on swap** and **`window.state.P` is never
  initialized** — an incoming asset inherits the outgoing one's keys and
  `createGraphics` buffers. `assets/tools/fire_visual.py` disposes both first; use it
  rather than raw `/p5/layer` when swapping.
- **fps is meaningless under load.** `uptime` first — need loadavg < ~4.5 to trust ANY
  fps number, and `ps -A -o %cpu,comm | sort -rn | head -5` to find the hog. Two bogus
  asset bug-reports were once filed because a stale process was burning ~390% CPU
  (`genart.girih`: 2.9 fps under load, 8.6 fps clean).
- **Port discipline.** Visuals own **8766**. A music factory owns **9766** — never
  touch it. `pkill -9 -f livecode.py` matches **every** instance regardless of
  `--port` and has killed a live show; always scope it:
  `pkill -f "livecode.py --port 8766"`.
- **The machine is yours at 06:30.** A music wave-2 finisher was running overnight on
  9766; it holds a **06:15 curfew** and pauses itself before you start — stopping its
  validator, hushing its transport and killing its browser, leaving only an idle
  python server on 9766. You should therefore find a calm machine. Sanity-check at
  start (`uptime`, `pgrep -f "verify_arcs|valloop_music|finisher.py"`); if any of
  those are somehow still alive, **stop them** (`pkill -f verify_arcs; pkill -f
  valloop_music; pkill -f "scratchpad/wave2/finisher.py"`) rather than competing for
  the CPU — that work is resumable by design and Gene will restart it later.
  **Do not kill the 9766 server itself, and never write to `assets/music/**`.**
- **One browser client only.** Each connect declares a hard reset that hushes the
  transport and wipes layers. Many browsers on one server = chaos.
- **The clock is transport-driven** — with no track playing, `clk.t` can sit frozen
  and every visual reads static. Keep the near-silent metronome running while
  authoring/validating (`.gain(0.001)`), and `POST /show/recording {"enabled":false}`.
- **Canvas is serial.** `gf_snap` / `validate.py` / the grader all drive the one
  canvas — never concurrently. Parallelize authoring (text), not rendering.
- **Dead black space fails** the luminance floor and reads as nothing on stage.
  Point-cloud/attractor pieces need 40–80k bright iterates/frame into a log-density
  buffer; target frame-mean luminance ~0.15–0.5.
- **Param order matters** — the validator pokes the first two numeric params to max.
  Lead with `energy`/`scale`/`density`; never `hue` first (360 wraps to red ≈ default).
- **2D only.** p5 1.11.11 global mode, no WebGL/GLSL. Fake shader looks by computing a
  field into a coarse `createGraphics` (≤256², prefer 128–200 wide) and `image()`-upscaling.
  No full-canvas `filter()` (~12 ms/frame).

---

## STEP 7 — Before you hand off

1. **Docs must not go stale.** The music wave shipped `assets/tools/refresh_counts.py`,
   which rewrites the catalog-count line in `README.md`/`AGENTS.md` from `index.jsonl`
   (`--check` exits 1 if stale). **Extend it to the visual domain** and run it, so
   `.claude/skills/p5.md`, `AGENTS.md`, and `research/generative/FINAL_REPORT.md` can
   never again advertise "166 pieces" over a 600-piece catalog. `INDEX.md` and
   `index.jsonl` are generated — never hand-edit.
2. Update `assets/visual/FACTORY_STATE.md` with a SESSION entry: what ran, the shard
   map, totals by family, what you learned, and the resume point.
3. Rebuild the grader manifest and confirm new work appears in `grade.html`.
4. **Final report to Gene:** totals by family/shard vs. the quota table, your 10 best
   pieces (with why), the weakest areas, anything quarantined and why, and any taste
   calls you made on his behalf.

**Grade honestly and never record a taste signal Gene didn't give.** `selfgrade.jsonl`
is your own assessment; `visual-grades.jsonl` is *his*. Don't write to his file.

---

## If you run low on context

Commit, write the resume point into `assets/visual/FACTORY_STATE.md` (done / queued /
learned), and relaunch yourself from this file. It is designed to be resumable.
