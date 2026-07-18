# Music Catalog System — START HERE (for music)

The music equivalent of `.claude/skills/p5.md`. If you're going to **run, use,
author, verify, or grade** the Strudel music catalog, read this first — it's the
map to everything else.

> **What it is:** a *retrieval-based performance library*, not a live-coding
> improviser. Performance = **grep the index → fill params → fire a curl**, never
> generating Strudel from scratch on stage. Everything is pre-written, verified,
> parametric code.

**Current catalog:** 707 stems · 132 kits · 12 arcs · 92 genres · 851 indexed
assets. (Live count: `wc -l assets/music/index.jsonl`. Coverage: `assets/music/INDEX.md`.)

---

## The three asset types

| Type | What it is | Lives in | Format |
|------|-----------|----------|--------|
| **stem** | one instrument part as parametric Strudel code, in 3 intensity variants (`sparse`/`full`/`peak`) | `stems/<slot>/*.json` | `livecode-stem-v1` |
| **kit** | a curated bundle: one stem per slot at a home key+cps, with recommended arcs — **the primary stage unit** | `kits/*.kit.json` | `livecode-kit-v1` |
| **arc** | a section script (intro→build→drop→…) that weaves each slot's variants into one self-evolving `arrange()` form so the music breathes for minutes untouched | `arcs/*.arc.json` | `livecode-arc-v1` |

**Slots → orbits (fixed):** `drums=1 perc=2 bass=3 chords=4 lead=5 pad=6 texture=7 vox=8`.
One stem per slot; each stem sets `.orbit(N)` and owns that orbit's room/delay.

The full spec (stem/kit/arc JSON fields, gain budgets, transpose methods, cps
windows, validation gates) is **`assets/CONTRACT.md` → "Music contract"**. Read it
before authoring.

---

## Quick start — run & perform

```bash
# 1. start the server + a browser that plays audio (port 9766 by convention —
#    see "Ports" below). Wait for /status -> {"ready": true}.
nohup python livecode.py --port 9766 > /tmp/lc_music_server.log 2>&1 &
nohup python autopilot_host.py --url http://localhost:9766/livecode.html \
      --snapshots-dir autopilot/snapshots_music --interval 10 > /tmp/lc_music_host.log 2>&1 &
curl -s -X POST localhost:9766/show/recording -d '{"enabled":false}'   # factory sessions only

# 2. audition + perform + grade in the browser:
open http://localhost:9766/assets/music/browse.html
```

**Three ways to fire sound** (the server's curl API is documented in the root
`AGENTS.md`; music routes are `/strudel/track|stop|hush|cps|send`):

- **browse.html** (the explorer): arrow-key through concepts, `space` to solo,
  sliders retune params live, kits get an arc picker, and `1/2/3` grade. Best
  for auditioning and taste-curation.
- **A single stem/kit by curl:** compile the variant you want (substitute
  `${param}` defaults) and POST `/strudel/track {name:<slot>, code:<...>}`.
- **A kit through an arc (the money shot):**
  ```bash
  python assets/tools/arc_compile.py <kit_id> <arc_id> --fire --port 9766
  ```
  weaves per-slot `arrange()` forms + pushes the visual handshake; the form then
  evolves for minutes with zero further commands.

**Retrieval flow on stage:** Gene types prose → grep `index.jsonl` by tag/genre →
pick a kit (or sample stems per slot) → fill params → fire. Tags are the whole
retrieval surface, so they're generous (synonyms, moods, instruments, genres).

---

## Directory map

```
assets/music/
  README.md          ← you are here (the guide)
  CONTRACT.md is at assets/CONTRACT.md  ← the asset SPEC (music + visual)
  BUNDLE.md          ← verified @strudel/web 1.0.3 feature matrix + BANNED list + loudness recipe
  packs.json         ← the ONLY legal sample-pack deps (name → exact samples() snippet)
  index.jsonl        ← GENERATED retrieval index (one line per verified asset) — never hand-edit
  INDEX.md           ← GENERATED grep-friendly catalog listing
  grades.jsonl       ← Gene's taste record (bad/ok/good per id) — durable, keep it
  browse.html        ← the keyboard sound-space explorer + grader
  stems/<slot>/*.json · kits/*.kit.json · arcs/*.arc.json   ← the catalog
  inbox/             ← unverified assets awaiting validate.py
  inbox_failed/      ← twice-failed assets (quarantine)
  graveyard/         ← bad-graded assets (soft-deleted, kept as a taste signal)
  FACTORY_STATE.md   ← session/build history + resume state (log, not onboarding)
  PLAN.md            ← the original 198-entry build plan (historical)
assets/prompts/music-factory.md   ← the mass-authoring FACTORY process spec
assets/tools/*.py                 ← the toolchain (below)
.claude/skills/strudel.md         ← the Strudel CRAFT guide (syntax, genre recipes, cookbook)
docs/strudel-*.md                 ← raw Strudel API reference + examples
```

---

## The toolchain (`assets/tools/`)

| Tool | Purpose | Run |
|------|---------|-----|
| **validate.py** | mechanical gate: schema + all-3-variants deploy clean + `/errors` empty + audible (`audio.rms` > 0.01 full/peak, > 0.003 sparse) + (kits) combined rms > 0.02. Passing stamps `verified` and moves inbox→catalog. | `validate.py --port 9766 --inbox music` · `--audit music` (re-check whole catalog, demote silent) · `validate.py <file.json>` (one asset) |
| **verify_arcs.py** | **the section-audibility gate.** Fires every kit THROUGH every arc it lists, section by section, and fails on any silent/too-quiet section. validate.py never tests kits through arcs — this does. **RUN BEFORE ANY HANDOFF.** | `verify_arcs.py` · `--arcs slow_burn,waves` · `--kits kit.house_deep` · `--wait-load` |
| **build_index.py** | regenerate `index.jsonl` + `INDEX.md` from verified assets. Run after any add/prune. | `build_index.py music` |
| **arc_compile.py** | compile a kit+arc into per-slot self-evolving `arrange()` code; `--fire` plays it. **Only fires the slots the NEW kit declares — orphan slots from the outgoing kit keep playing in the old key.** | `arc_compile.py <kit> <arc> --fire --port 9766` |
| **set_play.py** | fire a **saved set** (`assets/sets/*.json` = kit×arc + visual stack + params). Waits for a bar line (`--at 8`), phases slots in (`--phase 2`), auto-stops orphan slots, verifies fps/errors. | `set_play.py weight --at 8 --port 9766` |
| **set_save.py** | bank a set that worked, with grade + notes. `--list` shows saved sets. | `set_save.py --list` |
| **boundary.py** | block until the next N-bar line — **transitions must land on the grid, never mid-bar**. | `boundary.py --bars 8 --port 9766` |
| **fire_visual.py** | deploy a visual asset to a slot: binds `__SLOT__`, disposes leaked slot state, inits `window.state.P`, pushes params. (No such tool existed before; arc_compile is music-only.) | `fire_visual.py genart.aurora --slot bg --port 9766` |
| **peek.py** | grab the live canvas → PNG, on demand. **`/status` 200 + no errors does NOT prove anything is visible** (a whiteout reports 60fps). Look before you claim. | `peek.py --port 9766 --out /tmp/p.png` |
| **valloop_music.py** | autonomous background loop: *drains* the inbox (auto-validates + indexes + commits when load is low) and *audits* the verified catalog hourly (demotes regressions). No LLM. | `nohup python assets/tools/valloop_music.py > /tmp/lc_music_valloop.log 2>&1 &` |
| **prune_graded.py** | apply Gene's grades: move `bad` assets to `graveyard/`, reindex. Refuses to break a kept kit by pruning a stem it uses. Dry-run by default. | `prune_graded.py` (plan) · `--apply` |
| **review.py** | *legacy* 1–5 CLI grader → `review.jsonl`. Superseded by browser `bad/ok/good` grading, but still works. | `review.py music --port 9766` |

---

## Verification is mandatory — never hand off broken sound

A stem/kit is **not done** until it passes BOTH gates:
1. `validate.py` — stem audible solo / kit audible at all-`full`.
2. `verify_arcs.py` — kit audible in **every section of every arc it recommends**.

The second gate exists because a kit can pass (1) and still be dead-silent for
20–30s when fired through an arc whose intro/breakdown/outro names slots the kit
lacks. Arcs carry a `"*":"sparse"` floor on their thin sections so any kit stays
audible; if you add a kit or arc, re-run `verify_arcs.py`.

---

## Grading & taste (browser)

In `browse.html`, grade any asset — `1` = ✗ **bad**, `2` = ○ **ok**, `3` = ★ **good**:
- **ok** — keep it in the vocabulary (the baseline "this is good enough").
- **good** — outstanding among the ok ones. Use as a **positive taste signal** to
  reinforce Gene's preferences on future authoring/inference.
- **bad** — delete it (hides immediately; `prune_graded.py --apply` moves it to
  `graveyard/`). Use as a **negative taste signal**.

Grades persist to `assets/music/grades.jsonl` (append-only, latest-per-id wins)
via `POST /music/grade {id, grade}`. `grades.jsonl` is the durable record of
Gene's taste — **keep it, learn from it** (good = reinforce, bad = avoid) when
authoring new assets. (Mirrors the visual side's `grade.html` → `visual-grades.jsonl`.)

---

## Golden rules (hard-won — violate these and things break on stage)

- **Only `BUNDLE.md` PASS features** may appear in stems. The **BANNED** list is
  real (they threw live errors or are silent): `.duck*`/sidechain (absent — use
  the pump idiom `.gain(saw.range(floor,top).fast(4))`), `.swing`/`.swingBy`
  (use elongation or `.late`), `.scrub`, the `tremolo*` family, `gm_*`
  soundfonts, `setcps()`, and `.cps()` inside a stem (the server owns tempo).
- **Only `packs.json` deps.** `clean-breaks` has named breaks (amen/think/…), NO
  `clean:N`. `mridangam` loads single-arg. shabda-vox is an external TTS service
  (~5s, flaky — accent only, never a backbone).
- **Loudness:** under-loudness is the #1 failure. Levers, biggest first:
  `.shape(.3–.6)` (harmonic energy → RMS), gain → slot ceiling, raise pump floors
  `saw.range(.6,.9)`, denser full/peak. The analyser reads subs fine; a 0.000–0.008
  read means the CODE is too quiet, not a measurement blind spot.
- **Load gate:** validate/verify only when `loadavg < ~4.5`. Above it the browser
  audio thread starves and a genuinely loud stem reads rms 0.0000 sporadically.
  `valloop_music.py` and `verify_arcs.py --wait-load` enforce this. Never lower a
  gate to compensate; check `uptime` before trusting a silent read.
- **Ports:** the catalog tooling defaults to **9766** (so music can run alongside
  the visual system on **8766**). If only music is running you *can* use the
  default 8766, but the tools assume 9766 — pass `--port` consistently.
- **Never** hand-edit `index.jsonl` (it's generated), never `/tmp` (assets are
  in-repo/durable), keep `/show/recording` false in factory sessions, and leave
  the server idle (`/strudel/hush`) when you pause.

---

## Adding new assets (the loop)

1. **Author** JSON to `assets/music/inbox/` following `CONTRACT.md` (3 variants,
   `${param}` templates, `.orbit(N)`, ends `.play()`, gain ≤ budget, deps ⊆
   packs.json, ≥8 tags, honest key/cps). Craft help: `.claude/skills/strudel.md`.
   Loudness + legal features: `BUNDLE.md`. For a big parallel build, follow
   `assets/prompts/music-factory.md` (subagents write JSON only; never call the server).
2. **Validate:** `validate.py --port 9766 --inbox music` → passes move to the
   catalog. Rescue under-loudness fails with the loudness levers above.
3. **Index:** `build_index.py music`.
4. **Kits/arcs:** author kits referencing verified stems (kit cps must fall inside
   *every* referenced stem's cps window). Then **`verify_arcs.py`** — mandatory.
5. **Commit** the batch (`git add assets/music && git commit`).
   (The `valloop_music.py` loop automates 2–3 + commit when running.)

---

## Doc index

| Doc | What it's for |
|-----|---------------|
| **`assets/music/README.md`** | **this file** — the music-system hub |
| `assets/CONTRACT.md` | the asset SPEC (stem/kit/arc formats, slots, gates) — authoritative |
| `assets/music/BUNDLE.md` | verified Strudel feature matrix + BANNED + loudness recipe |
| `assets/music/packs.json` | legal sample-pack deps (`_meta` documents each) |
| `assets/music/INDEX.md` | generated grep-friendly catalog listing |
| `.claude/skills/strudel.md` | Strudel CRAFT guide (syntax, genre recipes, cookbook) |
| `assets/prompts/music-factory.md` | the mass-authoring FACTORY process |
| `assets/music/FACTORY_STATE.md` | build/session history + resume state (a log) |
| `assets/music/PLAN.md` | the original build plan (historical) |
| `docs/strudel-reference.md` · `docs/strudel-examples.md` | raw Strudel API + examples |

## Gotchas the hard way (see FACTORY_STATE.md for full detail)

- **DSP worklets need `initAudio()`:** `.shape/.coarse/.crush` go SILENT unless
  `livecode.html`'s start handler calls `window.initAudio()` (owned_transport skips
  the worklet registration). Hard-reload the browser once after any change.
- **Audio bridge & reverb:** the analyser tap must exclude `OfflineAudioContext`
  (superdough renders reverb IRs there) or `state.audio` freezes on the first `.room()`.
- **`arrange()`** is the arc compiler's backbone — keep it PASS.
- **Kits fire as one `stack()`:** one malformed stem silences everything, so
  validation is per-stem AND per-kit AND (via verify_arcs) per-section.
