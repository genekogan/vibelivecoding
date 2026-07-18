# Three.js Live Surface — Agent Guide

**How to perform with three.js visuals on the livecode canvas: retrieve a scene,
preload it in the background while p5 keeps playing, swap on a bar line, and
never waste GPU on an idle renderer.** Read this first for any three.js work in
a live set. The p5 counterpart is `p5.md`; music is `strudel.md` + the music README.

The rule of the room: **one renderer visible at a time.** p5 and three.js never
both burn GPU — the surface manager enforces it.

---

## 1. The four tributaries (what you can put on screen)

| kind | count | what | fires via |
|------|-------|------|-----------|
| `scene` | 200 | Generated, parameterized, audio-reactive threejs catalog scenes (WebGPU, acts, seeded) — `threejs/` | `surface.py show scene.<id>` |
| `lmscene` | 13 | Little Martians composite pages — the flock, the five lore scenes, journey/library/space, splats | `surface.py show <name>` |
| `lmmodel` | 110 | LM archive models (ceramic scans, rigged characters) in the studio viewer | `surface.py show "/lm/index.html?model=<id>"` |
| `sketchfab` | 594 | Borrowed GLBs (props/environments/cosmic) — building blocks for scenes, browsable galleries | GLB path from the index; browse `/lm/sketchfab/lore.html` |

## 2. Retrieval — loose prose → fireable scene

```bash
python3 assets/tools/find_three.py "little martians flying home through space"
python3 assets/tools/find_three.py --kind scene "cathedral of negative light" -n 6
python3 assets/tools/find_three.py --kind sketchfab "overgrown ruined church"
python3 assets/tools/find_three.py --fire "the flock"     # just the commands
grep -i 'brass\|orrery' threejs/INDEX.md                  # grep fallback
```

Same engine as `find_visual.py`: literal name > tags > blurb, synonyms marked
`~`, and an explicit `!! no direct match` warning per uncovered concept. Every
hit prints its `fire:` line. Rebuild after registry changes:
`python3 assets/tools/build_three_index.py` (writes `threejs/index.jsonl` + `INDEX.md`).

## 3. The surface manager — preload, swap, park, drop

```bash
python3 surface.py preload flock     # warm in background — p5 keeps performing
python3 surface.py show flock        # wait-until-ready, then fade in + pause p5
python3 surface.py p5                # back to p5 instantly; three frame parked
python3 surface.py show flock        # again later: INSTANT (parked state kept)
python3 surface.py status            # {"live":..., frames:{...state/ready...}}
python3 surface.py drop flock        # free its GPU/memory
python3 surface.py drop all
```

Lifecycle & the resource story (all verified live):

- **WARMING** — hidden iframe (opacity 0) loads + ticks in the background. p5
  stays live the whole time. Auto-**parks** when ready if you haven't shown it.
- **LIVE** — visible; **p5 is `noLoop()`d + canvas hidden** (its draw work → ~0).
  `state.clk` freezes while paused, but it recomputes from the transport on
  resume — no drift. The **audio bridge keeps running** (it ticks in its own
  rAF), so three scenes stay audio-reactive over the live music.
- **PARKED** — `display:none`: Chromium stops the iframe's rAF entirely (zero
  CPU/GPU) but keeps JS + GPU state → re-show is instant. Max 2 parked (LRU drop).
- **DROPPED** — iframe removed, memory freed.

**Performance doctrine: preload the next scene while the current one plays**, the
same way you write the next Strudel section over the live groove. `show` on a
cold heavy scene blocks until ready (up to 90 s) — that's the tool telling you
that you should have preloaded. Ready is signalled by
`document.documentElement.dataset.appReady === 'true'` (the threejs browser and
all lm pages set it); arbitrary URLs fall back to load+settle.

## 4. threejs catalog scenes — the URL parameter surface

`surface.py show scene.<id>` builds:
`/threejs/browser/index.html?stageOnly=1&scene=<id>&audioSource=live-rendered-master`

- `stageOnly=1` — full-bleed stage, all chrome hidden (projector mode).
- `audioSource=live-rendered-master` — samples the parent livecode Strudel
  analyser directly (works iframed in livecode.html or in catalog.html).
- More knobs you can append via `surface.py show "/threejs/browser/index.html?...&scene=..."`:
  `camera=authored|intimate|wide|mirror|high-angle` · `lighting=<mode>` ·
  `motion=full|reduced|still` · `range=safe|expressive|extreme` ·
  `energy=0..1` · `seed=<s>` · `cps=0.25..1` · `dpr=0.5..2` ·
  `shadows=0` · per-scene param overrides (`p.<name>=` form — see
  `browser-state.mjs parameterOverridesFromQuery`).
- Scene metadata (acts, tags, thesis, param count): `threejs/browser/generated/scene-index.json`.
- The curation browser (with panels) is the same page without `stageOnly`.

## 5. LM tributary cheat sheet

- **flock** (Sporion Crossing) — `?n=<size>` flock size, `?light=1` skips the
  two 70–120 MB characters (use `flocklite`). `space` pause, `←→` speed.
- **scenes.html** (five lore scenes) — `?scene=1..5` (cultivator/lantern/
  recursion/brasscastle/kalama), `?t=SS` fast-forward choreography, keys `1–5` live.
- **lm viewer** — `/lm/index.html?model=<id>` (ids in `lm/manifest.json`);
  studio lighting, animation playback for rigged characters.
- **sketchfab** — GLBs under `lm/sketchfab/<path>`; `lore.html` browse,
  `gallery.html` fly-through ("yard"). Tiers: prop/environment/cosmic — the
  universe's scale-shift is canonical, scale freely. Licenses per
  `ATTRIBUTION.md` (all require credit).
- lm pages read `window.parent.state.audio` for reactivity (same-origin only).

## 6. Gotchas (hard-won)

1. **Module-graph pages need HTTP/1.1 + a deep backlog.** The threejs browser
   is 500+ ES modules fetched in a burst; `livecode_server.py` sets
   `protocol_version = "HTTP/1.1"` and `request_queue_size = 128`. Under the old
   HTTP/1.0 defaults the import graph silently failed and the page froze at
   "Preparing the dojo" forever. Don't revert those.
2. **`appReady` is the ready truth, not the load event.** Cold boot of the
   threejs browser ≈ 10 s (507 modules + WebGPU init); flock ≈ 15 s of GLBs. The
   settle-time fallback exists only for unknown pages — named scenes use 90 s
   settles so `appReady` always wins.
3. **Never raw-iframe a heavy page while performing** — that's the visible
   15-second hole this system exists to remove. Preload first.
4. **p5 pause is `noLoop()`** — anything reading `state.clk` inside p5 layers
   stops with it, by design. Strudel/music is completely independent.
5. **The old `surface.py flock` shorthand still works** (bare name = show).
6. WebGPU scenes fall back to WebGL automatically (`forceWebGL=1` to force).

## 7. Files

| path | role |
|------|------|
| `surface.py` | the surface manager CLI (all of §3) |
| `assets/tools/find_three.py` / `build_three_index.py` | retrieval / index build |
| `threejs/index.jsonl` + `threejs/INDEX.md` | the merged 917-asset index |
| `threejs/README.md` → `state/CURRENT.md` | the threejs production system's own docs |
| `lm/README.md` | LM archive + composite scene docs |
| `catalog.html?section=three` | unified curation shell (not the performance path) |
