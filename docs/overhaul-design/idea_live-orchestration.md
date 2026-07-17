# Performance-Time Orchestration: The Conductor/Fabricator Architecture

## Core stance

The show is run by **two planes that never block each other**: a *control plane* (the main chat session = the Conductor, doing only retrieval, parameter pokes, and firing pre-verified bundles — hard budget: nothing it does inline may take longer than 60s) and a *build plane* (parallel background Fabricator subagents that author and verify complete scene bundles against a shadow server, never the live one). The single most important rule, enforced structurally rather than by discipline: **the Conductor never writes novel Strudel/p5 code during a show.** Everything it fires already exists as a verified string. The 2–5 min reasoning latency doesn't get "optimized" — it gets *moved off the critical path entirely*, into practice sessions and mid-show background fabrication.

The load-bearing primitive is one the system already has: **atomic name-overwrite** (posting to an existing track/layer name replaces it in one frame, ~10ms curl). Zero engine changes are needed to make firing fast. The engine changes needed are for *buffering* and *safety* (5 small patches, listed below).

## 1. The Conductor: what it may do inline

The Conductor is the user-facing session running `/loop` with ScheduleWakeup. Its context is deliberately starved: the live card (~50 lines of stage rules), the asset index, the last directive, one snapshot. It does NOT re-read the 673-line `instructions.md` — those rules are baked into assets at build time (see §7).

**Allowed inline (whitelist):**
- `curl` to any REST route with a payload that is (a) verbatim from a library asset, (b) a library template with parameter slots filled by pure string substitution (key, palette name, cps, x/y/scale — no logic authoring), or (c) a `/p5/state` or `/strudel/cps` poke.
- Grep/read of `assets/index.jsonl` and bundle manifests.
- Firing a scene bundle via `scripts/fire.py` (below).
- Spawning Fabricator subagents (background Task).
- One-line journal appends (JSONL).

**Forbidden inline (must delegate):**
- Writing any new draw-body or pattern string longer than a parameter fill.
- Debugging a broken asset (fallback instead — §6).
- Anything requiring `docs/strudel-reference*.md` or the p5 cookbook in context. If the Conductor needs a reference doc, that's the tell the task is Tier 3.

## 2. Latency tiers (the budget)

| Tier | Action | Mechanism | Target | Owner |
|---|---|---|---|---|
| **T0** | Param tweak: energy/palette/cps/position, add-or-drop one fx layer | `/p5/state` poke; `/strudel/cps`; re-post cached variant of one slot | **< 2s** (decision + 1–3 curls) | Conductor |
| **T1** | Retrieve + rebind: swap subject/world/floor/one stem from library | grep index → fill params → post in slot order | **< 15s** | Conductor |
| **T2** | Assemble scene from parts: world + subject + props + fx + 3–5 music stems, all pre-verified, matched on cps/key via manifest fields | `fire.py <bundle>` — deps first, tracks in slot order, layers in z-slot order, removes last | **< 45s** including staged music swap | Conductor |
| **T3** | Novel fabrication: nothing in library covers it | background Fabricator + shadow verify; Conductor fires a T0/T1 **stopgap immediately** | **2–6 min, never blocks the canvas** | Fabricator |

**Heartbeat rule (kills the 10-minute stall):** every Conductor wakeup (60s cadence) must change *something* perceivable. If a T3 fabrication is pending and no directive arrived, fire a T0 mutation from a rotating menu (section-clock energy bump, palette shift via `/p5/state`, one fx overlay, drum-fill variant of the current kit). This is mechanical — a `heartbeat_menu` list in the live card, not a creative decision. Worst-case staleness drops from 10 min to one wake interval.

## 3. The scene buffer: filesystem queue primary, timeline secondary

**Verdict on reusing the show timeline as the queue: no, for live improv.** Verified against `livecode_server.py`: `/show/load` calls `load_steps` → `_reset_state()` (hush + clear — kills live audio, line 518-523); `_record_step` **truncates all forward steps** the moment a live command lands mid-timeline (lines 512-513); there is no append route. Since every Conductor curl auto-records, any improvised tweak while positioned before buffered sections would silently destroy them. The timeline's semantics are hostile to interleaved improv by design.

**Primary buffer: `assets/queue/` in-repo** (durable — the `/tmp/scene_queue` library died on reboot precisely because it wasn't):

```
assets/
  index.jsonl              # one line per asset/bundle: id, kind, tags, cps, key, slots, deps, verify status
  library/                 # practice-built parts (stems, characters, worlds, fx) — hundreds
  queue/NNN_<slug>/        # fabricator output, FIFO by number prefix
    scene.json             # ordered fire list: [{route, payload, slot}, ...]
    manifest.json          # cps, key, slots claimed, sample-pack deps, verify report, stopgap_of
    thumb.png              # shadow-server snapshot
  live/last_good/          # per-slot last verified-live code (fallback source, §6)
```

**Handshake:** Fabricator writes the bundle dir atomically (tmp + rename), with `manifest.verify.status ∈ {building, passed, failed}`. The Conductor's wake protocol includes one `ls assets/queue/*/manifest.json | xargs grep -l '"passed"'` — a passed bundle is fireable, a failed one is skipped and journaled. No sockets, no IPC: fabricators are subagents that end their turn after writing; the Conductor polls on wake. Firing a bundle moves it to `assets/library/fired/` and updates `live/last_good/`.

**Secondary: add `/show/append`** (~12 lines: extend `controller._steps` with labeled steps, no execute, no reset, return start index) so *showrunner mode* gets buffering too — fabricators can push sections onto a running arrow-key/autoplay set. Since fired curls auto-record anyway, the recorded timeline becomes the **archive** of the improvised show (harvestable into the library afterward), not the queue.

## 4. Direction triage

On any Gene message the Conductor classifies in one shot — no deliberation, a lookup against the index:

1. **TWEAK** (params of what's on screen): T0, execute now.
2. **RETRIEVE**: decompose the request into slot-parts (subject / props / world / floor / fx / stems) and query the index per part. Full coverage → T1/T2, execute now. *"Penguin DJ under a disco ball"* = character:penguin + prop:dj-booth + fx:mirror-ball + floor:checker — four index hits, fired in <30s.
3. **FABRICATE** (any part missing): fire the **nearest-neighbor stopgap immediately** (closest character with penguin palette, or the disco parts alone), spawn a Fabricator with the exact directive + the stopgap's slot map, keep going. When the bundle lands `passed`, hot-swap via name-overwrite on the same slots — the audience sees a refinement, not a wait.

**Queued directions never stall the canvas** because fabrication is fire-and-forget: N pending directives = N parallel fabricators, each claiming *disjoint slots* declared in a `claims.json` scratch file so two fabricators never author the same track/layer name. The Conductor processes newest-directive-first on each wake; the heartbeat rule covers the gaps. Slot vocabulary is formalized (music: drums/bass/chords/lead/pad/vox → orbits 2/3/4/5/6/8; visual z-slots: bg=00, floor=10, subject=50, props=60, fx=80, post=99, encoded as layer-name prefixes `50_penguin`, with `fire.py` posting in prefix order since z = insertion order).

## 5. Minimal server patches (all in `livecode_server.py` unless noted)

1. **`ThreadingHTTPServer` + a `threading.Lock` around `_steps`/`_tracks`/`_layers` mutation** — reads (`/status`, `/state`, static assets) stop serializing behind mutations; fabricator/watchdog traffic can't queue-block a live fire.
2. **`/show/append`** — the missing buffering primitive.
3. **`/strudel/cps` also pushes `window.state.cps` and re-arms `t0`** — makes the whole visual library tempo-portable via the wall-clock beat contract (the autopilot assets' convention wins; `frameCount/28.8` is deprecated at build-lint time).
4. **Browser-side last-good stack revert** (~15 lines in `livecode.html`): keep the previous evaluate string; if `window.evaluate` throws, re-evaluate it. This defuses the worst live failure — one bad track silencing the entire music stack.
5. **Record `/strudel/send`** (sample loads) as steps with a `preamble: true` flag that replay executes once, outside back-step replays — fixes both the invisible-sample-load bug and the backward-replay re-load gotcha.

Kiosk mode additionally gets a **persistent Chrome user-data-dir** so the CacheStorage sample cache survives launches — practice sessions pre-warm every pack the library declares in `deps`, making show-night sample loads instant.

## 6. Live failure handling: the watchdog

A dumb background *process* (not a model), `scripts/watchdog.py`, polls every 5s: `/errors` delta, `/status` track count, snapshot mtime, and the fps readout `autopilot_host.py` already writes. Automatic responses, no LLM in the loop:

- **Strudel stack broken / track count dropped** → re-post every file in `assets/live/last_good/tracks/` (curl per track, ~50ms total). With patch 4 this becomes belt-and-suspenders.
- **Layer compile error** → server already keeps the old layer running (safe); watchdog just journals it so the Conductor doesn't retry the same string.
- **Layer runtime-erroring every frame (draws nothing)** → detected via `/errors`; re-post `last_good/layers/<slot>` for that slot.
- **fps < 12 for 2 consecutive samples** → shed in documented order: post-slot → fx-slot → props-slot (never bg/subject/music). Shed order lives in the live card and the watchdog.
- **Snapshot mtime stale > 20s** (browser hung) → watchdog alerts the Conductor's next wake; reconnect `_restore_all` recovers tracks+layers, watchdog re-sends the non-restored surface (setup/state/fps/sends) from the live bundle manifest.

Because *every* fire updates `last_good/`, "previous scene" is always one script invocation away — the audience-facing guarantee is: the canvas can regress, but never freeze or silence.

## 7. Model/effort allocation

- **Conductor**: the heavy model the chat runs on, but **low reasoning effort / minimal thinking** — its round is triage + grep + curl, mechanical by construction. Target full round < 30s. It stays heavy only because it's the user-facing session and must parse loose stage-shouted directives correctly.
- **Fabricators**: heavy model, **high effort, parallel** (background subagents). They carry the fat context — strudel/p5 skills, whiteout rules, taste directives — so the Conductor never does. 2–4 concurrent is the practical ceiling (CPU contention with the live browser).
- **Verifier**: **no model at all** for the gate — a Playwright script against a shadow livecode instance (alt ports 9765/9766, `autopilot_host.py --headless` reused as harness): compile check, `/errors` empty, ≥3 audible tracks at t+2s, fps ≥ 20, snapshot not >90% white or >95% black, section-clock keys present. Optionally one cheap-model vision call ("is there a penguin; is it on-subject") per bundle.
- **Practice sessions** (library building): unbounded parallel heavy fabricators walking `ideas.md` — latency-irrelevant, this is where the hundreds of assets come from.

## 8. Autopilot skill rewrite (what this implies)

- The `/loop` round protocol shrinks from 11 serial steps to 5: **read directive+snapshot → triage → act from library (T0–T2) or spawn+stopgap (T3) → 1-line JSONL journal → wake in 60s.** The mandated full re-read of `instructions.md` is deleted; it's replaced by the ~50-line **live card** (never-silent, never-clear, heartbeat menu, shed order, ≤2-track-swap rule *for unverified code only* — pre-verified bundles may hard-swap a whole stack because verification already proved audibility-from-frame-1).
- All accreted taste/safety directives move to **build-time**: a fabricator checklist plus the mechanical verifier. An asset in the library is *definitionally* rule-compliant.
- Journal becomes `journal.jsonl` (`{ts, scene_id, category, genre, cps}`) so recency-dedupe is a 12-line tail read, not a 456KB prose parse; the old journal is mined once into the library index.
- The `run.sh` vs `autopilot.md` prompt divergence is resolved by making the skill the single source and `run.sh` print `see autopilot.md`.
- Steering stays in-session (user mandate): fabricators author, the Conductor performs, Gene's messages land in the Conductor's context as before — but now a message can be *acted on* in the same minute it arrives.

EXAMPLES
### EX
**`/show/append` + threading patch (livecode_server.py)** — the two smallest high-leverage server changes:
```python
# line 266: HTTPServer -> ThreadingHTTPServer, plus a lock
self._httpd = http.server.ThreadingHTTPServer((self.host, self.http_port), LivecodeHTTPHandler)
self._steps_lock = threading.Lock()   # wrap _record_step, load_steps, append_steps

# new route in do_POST, next to /show/load:
elif path == "/show/append":
    start = controller.append_steps(d["steps"], d.get("label", ""))
    return self._reply({"ok": True, "start": start, "total": len(controller._steps)})

# controller method — extend WITHOUT executing or resetting:
def append_steps(self, steps: list, label: str = "") -> int:
    with self._steps_lock:
        start = len(self._steps)
        if label:
            self._steps.append({"route": "/show/mark", "payload": {}, "label": label})
        self._steps.extend({"route": s["route"], "payload": dict(s["payload"]),
                            "label": s.get("label", ""), **({"dwell": s["dwell"]} if "dwell" in s else {})}
                           for s in steps)
        return start
```
Fabricators buffer labeled sections onto a running show; arrow keys / autoplay.py consume them with zero further changes (autoplay already re-reads per-step dwell).

### EX
**Scene bundle for "penguin DJ under a disco ball"** (`assets/queue/041_penguin_dj/manifest.json`) — what a Fabricator deposits and the Conductor fires:
```json
{
  "id": "041_penguin_dj", "created": "2026-07-10T21:14:02",
  "stopgap_of": null,
  "tags": ["character:penguin", "prop:dj-booth", "fx:mirror-ball", "genre:disco", "energy:4"],
  "cps": 0.52, "key": "C:minor",
  "deps": ["strudel.b-cdn.net/tidal-drum-machines"],
  "slots": {
    "layers": ["00_bg", "10_floor", "50_penguin", "60_booth", "80_ball", "80_beams"],
    "tracks": {"drums": 2, "bass": 3, "chords": 4, "lead": 5}
  },
  "fire_order": ["deps", "p5:asc-slot-prefix", "strudel:drums,bass", "wait:1beat", "strudel:chords,lead", "remove:orphans"],
  "orphans": ["50_owl", "80_moths"],
  "verify": {"status": "passed", "fps": 24, "audible_tracks": 4,
             "whiteout": false, "errors": 0, "thumb": "thumb.png",
             "shadow_host": "localhost:9766", "at": "2026-07-10T21:16:40"}
}
```
`scene.json` beside it holds the ordered `[{route, payload, slot}]` list with final literal code strings — self-contained, so firing it also archives cleanly into the recorded show (reproducibility doctrine preserved: playback never references the library).

### EX
**Conductor triage in action — timeline of the penguin request** (the new autopilot round, replacing today's 2–5 min):
```
t+0s    Gene types: "draw a penguin DJ under a disco ball"
t+2s    Conductor greps assets/index.jsonl:
          character:penguin -> MISS | prop:dj-booth -> HIT | fx:mirror-ball -> HIT
          floor:checker -> HIT | music genre:disco energy:4 -> HIT (4 stems, key C:minor, cps .52)
        => classify FABRICATE (one part missing), stopgap available
t+8s    Stopgap fired (T2): world+floor+booth+ball layers posted in slot order,
          50_subject = library character 'dancer' with palette:{body:'#111', belly:'#fff'} param fill,
          drums+bass posted, 1-beat wait, chords+lead posted.  Canvas is on-topic.
t+10s   Spawn Fabricator (background subagent): directive + slot map + claims.json entry
          {claims: ["50_penguin"]}. Conductor turn ends; ScheduleWakeup 60s.
t+70s   Wake: no new directive; queue has nothing 'passed' yet -> heartbeat: /p5/state
          {key:'params.ballSpin', value:2.0} + energy bump. Journal 1 line. Sleep.
t+~3m   Fabricator finishes: shadow-verified penguin (fps 24, on-subject), writes
          assets/queue/041_penguin_dj marked passed.
t+next wake  Conductor sees 'passed', fires 50_penguin over 50_subject (one curl,
          atomic name-overwrite), removes orphans, updates live/last_good. Journal. Done.
```
Gene's request is *visibly acknowledged in 8 seconds* and *fully satisfied in ~3 minutes*, with the canvas moving at every wake in between.

### EX
**`scripts/watchdog.py` core loop** — modelless live-failure fallback (runs as a third long-lived process next to livecode.py and autopilot_host.py):
```python
LAST_GOOD = Path("assets/live/last_good")
SHED_ORDER = ["99_", "80_", "60_"]  # post -> fx -> props; never bg/subject/music
seen_errors, low_fps_strikes = 0, 0
while True:
    st = get("/status"); errs = get("/errors")["errors"]
    # 1. music stack died (whole-stack re-eval failure or silent parse drop)
    if len(st["tracks"]) < 2 or any(e["system"] == "strudel" for e in errs[seen_errors:]):
        for f in sorted(LAST_GOOD.glob("tracks/*.json")):
            post("/strudel/track", json.loads(f.read_text()))      # ~50ms total, audible again
    # 2. layer erroring every frame = invisible to audience
    for e in errs[seen_errors:]:
        if e["system"] == "p5" and (m := re.match(r"\[(\w+)\]", e["message"])):
            lg = LAST_GOOD / f"layers/{m[1]}.json"
            if lg.exists(): post("/p5/layer", json.loads(lg.read_text()))
    seen_errors = len(errs)
    # 3. fps collapse -> shed one layer per strike, in order
    fps = read_fps("autopilot/snapshots/latest.png")   # host already stamps it
    low_fps_strikes = low_fps_strikes + 1 if fps and fps < 12 else 0
    if low_fps_strikes >= 2:
        victim = next((l for p in SHED_ORDER for l in st["layers"] if l.startswith(p)), None)
        if victim: post("/p5/remove", {"name": victim}); low_fps_strikes = 0
    # 4. frozen browser -> stale snapshot mtime; _restore_all recovers tracks/layers,
    #    we re-send the non-restored surface (state keys, fps, sample loads) from manifest
    time.sleep(5)
```
The Conductor is freed from mid-show debugging entirely: by its next wake the watchdog has already regressed to last-good, and the journal tells it what fell over.

RISKS
- Strudel's whole-stack re-eval means per-stem verification is insufficient: two individually 'passed' stems can break or clash (orbit fx fights, gain clipping, key mismatch) only in combination. The verifier must test each bundle's full stack against the canonical baseline, and cross-bundle T1 stem swaps remain the one path where unverified combinations reach the live stack — the browser-side last-good revert (patch 4) is the only net under that.
- Shadow verification runs a second Chromium + audio engine on the same laptop that renders the live show; 2-4 parallel fabricators verifying concurrently could drag the live canvas below the 20fps floor mid-performance. Needs CPU pinning/niceness, a max-1-concurrent-verify semaphore during shows, or verification deferred to video-interleave gaps.
- The ThreadingHTTPServer change makes previously-serialized controller state (_steps, _tracks, _layers, _cps, the ws round-trip futures) genuinely concurrent — a sloppy locking job could corrupt the recorded timeline or interleave two _replay_all stack builds, which is a worse failure than today's queuing. This patch needs the Playwright regression (test_steps.py) extended with a concurrent-writes phase before it ships.
- Triage quality is the new bottleneck: a Conductor on low reasoning effort may misclassify FABRICATE as RETRIEVE (firing a wrong-but-available asset and never spawning the real build) or pick tonally-wrong nearest-neighbor stopgaps ('generic dancer painted black and white' may read as half-hearing Gene on stage). Mitigations — index quality, a stopgap_of field so the real asset always supersedes, journaling every MISS for post-show library gap-filling — reduce but don't eliminate this.
- The heartbeat rule guarantees motion, not interest: a show where fabrication repeatedly misses lands as 45 minutes of palette shifts and energy bumps. The real dependency is library breadth (hundreds of verified parts across the ideas.md taxonomy) — the orchestration layer only converts library coverage into latency; it cannot manufacture novelty at T0.
- ScheduleWakeup's ~60s floor caps Conductor responsiveness between Gene's messages; if a fired bundle degrades right after a wake, the watchdog regresses it but the aesthetic decision waits a full minute. If the wake floor ever rises (platform change), the whole T0/T1 budget degrades with it.
- Recording pollution and truncation remain live hazards: every Conductor curl auto-records, so a mid-show arrow-key back-step followed by any improvised poke still truncates all forward (appended) sections — /show/append makes buffering possible but does not fix the truncate-on-live-command semantics; performers must treat back-stepping during improv as destructive until a non-truncating branch mode exists.