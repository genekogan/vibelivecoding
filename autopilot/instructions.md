# Autopilot Instructions

This file is **read fresh every round**. Edit it anytime — the next round honors
it without restarting anything. This is the steering wheel.

## 💬 User messages — read in the conversation, not from a file

The user steers the trajectory by typing messages into the same chat session
this loop is running in. Those messages will appear in your context naturally
when you next take a turn — either immediately (if you happen to be awake
when they type) or at the next `ScheduleWakeup` firing.

There is no separate breadcrumbs file or queue. Just scan recent chat
messages each round for user directives like "more disco", "show me a face",
"the visuals are too dark" — and honor them in that round's design choices.

## 🎬 VIDEO INTERLEAVE — play dropbox mp4s between sets

Another agent drops mp4s (with their own audio) into `~/Downloads/dropbox/`. Between
livecode sets, the autopilot switches to a fullscreen player for the unseen batch and
uses that time to author the next set. Full detail is in `.claude/skills/autopilot.md`
(Video Interleave section); the operational essentials:

### 📍 VIDEO BATCH POSITION (2026-05-30): next dropbox batch = **batch 33**
The user confirmed we're at batch 33 — that's the next poop batch to expect/play.

### ⭐⭐⭐ USER DIRECTIVE (2026-05-30, durable, GOVERNING): PREFER DROPBOX VIDEOS, LIVECODE ≤60s, EXTEND BATCHES
- **ALWAYS PREFER DROPBOX ("poop") VIDEOS when new ones exist.** Every round check `/video/scan`. If
  `new` is NON-EMPTY (`len(new) > 0`), play that dropbox batch — do NOT wait for `eligible`, do NOT
  keep livecoding. New videos take priority over everything.
- **Livecode visuals/music must NEVER be on for more than ~60 seconds.** One cron round ≈ 60s, so a
  livecode set lives ONE round then yields to videos. Do NOT ride a scene 2-3 minutes.
- **When a NEW dropbox batch plays, EXTEND it with 3 random backup videos** so the batch runs longer
  (gives more time to author/recycle the next set behind the curtain). Concrete sequence when a fresh
  dropbox batch is available:
  1. `curl -X POST localhost:8766/video/play -d '{"source":"dropbox_new"}'`  (plays the poop batch)
  2. `curl -X POST localhost:8766/video/append -d '{"source":"backup","count":3}'`  (extend +3 backups)
- **If `new` is EMPTY (no dropbox batch):** play a random group of FOUR backups instead:
  `curl -X POST localhost:8766/video/play -d '{"source":"backup","count":4}'`.
- Either way the server hushes music + fullscreen-plays the group; RESUME a fresh livecode set at
  `playlistDone`.
- **NEVER take time off / never dwell idle.** While the current scene plays (or videos play), you must
  ALWAYS be developing the NEXT livecode set. Don't sit on one animation waiting. If you don't have a
  fresh scene authored yet, **RECYCLE an old scene from yesterday's session** — there are ready-made
  runnable scripts in `/tmp/scene_queue/scene7.py … scene97.py`. Just fire one with
  `/usr/bin/python3 /tmp/scene_queue/sceneN.py` (pick one not used recently per the journal). Recycling
  is encouraged — better to recycle than to linger or go idle. Meanwhile author/refill new scenes via
  subagents so the queue stays fresh.
- So the steady rhythm is: ~60s livecode (fresh OR recycled) → dropbox batch (+3 backups) or 4 backups
  → ~60s livecode → videos … Fire ONE scene per livecode interval; always prep the next during video.
- **DIVERSITY MANDATE (2026-05-30, durable):** the set you resume AFTER a video must NOT be the same
  one that was playing BEFORE it. While videos play, author a NEW set behind the curtain and play that.
  If it's not ready at `playlistDone`, fire a RANDOM PAST scene from `/tmp/scene_queue/` (not used
  recently) — never re-show the pre-video visuals. Maximize variety across rounds.

### ⭐ USER DIRECTIVE (2026-05-29, durable): PREFER VIDEOS EAGERLY + (superseded interval) FLIP SCENES
- **Check `/video/scan` FIRST, every round — before any livecode evolve/transition.** If a fresh
  batch is `eligible:true`, SWITCH TO VIDEO immediately instead of building/continuing a livecode
  set. Never start a third consecutive livecode set while a batch is waiting. Don't bundle the scan
  into the same script as the build — check it, then branch (eligible⇒video, else⇒livecode).
- **(SUPERSEDED by the ≤60s rule above)** ~~Livecode scenes must flip every 2-3 MINUTES.~~ Now: a
  livecode set lives ~60s (one cron round), then a video group plays. Fire one fresh scene per
  livecode interval.
- **Prepare a QUEUE of 2-3 scenes in advance** — ideally while videos play (that idle time is free).
  Use parallel subagents to author scene scripts to `/tmp/scene_queue/sceneN.py` (same format as a
  recent working script: cps + 6 p5 layers + 5 strudel tracks; honor no-silence / no-monotonous /
  array-guard / whiteout rules). On each livecode round, FIRE the next queued scene (quick hard cut)
  rather than lingering. Verify each queued script for errors before firing.

- **Each LIVECODING round, after reading state**, `curl -s localhost:8766/video/scan`.
  If `eligible:true` → `curl -X POST localhost:8766/video/play -d '{"source":"dropbox_new"}'`.
  The server hushes the music and fullscreen-plays the batch. This is the ONLY time the
  music stops — it is a deliberate full switch done server-side. You still never call
  `/strudel/hush` yourself, and the no-silence/no-hard-cut rules below govern LIVECODING,
  not this video switch.
- **While videos play** (`/status` → `video.playing:true`): AUTHOR A GENUINELY NEW set —
  send fresh `/p5/layer` content and verify with `snapshots/canvas.png` (NOT `latest.png`,
  which shows the video). Decide the next Strudel tracks but DON'T send them until the cut.
  **NEVER resume the same set/visuals that were playing BEFORE the video** — that staleness
  is the exact thing the user flagged. The post-video set must be different from the pre-video set.
- **When `/video/status` → `playlistDone:true`**:
  - If the NEW set is ready: `POST /video/stop`, then send the staged `/strudel/cps` +
    `/strudel/track` (music returns) — hard cut into the NEW set, never the pre-video one.
  - If the new set is NOT ready: do NOT return to the old/previous set. Instead pick a
    **RANDOM PAST scene from `/tmp/scene_queue/` history** (one not used recently per the
    journal) and fire it (`/usr/bin/python3 /tmp/scene_queue/sceneN.py`) for variety/diversity.
    You may briefly `POST /video/append {"source":"backup","count":2}` to buy a few seconds
    while you pick + fire the random scene — but once ready, cut into the random past scene,
    not the pre-video set. Never yank a mid-playing video.
- Dropbox videos are marked seen automatically (in `.seen.json`) as they finish — you
  don't manage that. After a video segment, a min-livecode gate keeps the next segment
  from triggering too soon (`scan.eligible` stays false until enough livecode time passes).
- **Tunables** (env vars at server startup): `LIVECODE_MIN_LIVECODE_SECONDS` (default 180),
  `LIVECODE_VIDEO_STABILITY_SECONDS` (default 10), `LIVECODE_DROPBOX_DIR`, `LIVECODE_BACKUP_DIR`.
- Empty dropbox ⇒ `scan` always `eligible:false` ⇒ pure livecoding, feature dormant.

## ⚠️ NEVER GO SILENT OR BLACK — SEAMLESS HANDOFF MANDATORY

**The output must be playing SOMETHING at all times. No silence. No black screen.
EVER.** Even a 5-second gap between scenes is unacceptable.

### 🔇 NO-SILENCE TRANSITION RULE (durable, user-mandated 2026-05-29)

The user called out a long silence during a disco → japanese-garden transition.
The cause: the new scene's `arrange()` section 0 was effectively silent
(intro = `note("~")` on melody/chords/harp, sub bass with 2s attack, just
wind on drums). When the tracks atomically replaced the old mix, the listener
heard near-silence for the entire ~10s intro section.

**HARD RULES — honor on EVERY transition:**

1. **Section 0 of EVERY track must produce audible sound from frame 1.** No
   `note("~")` intros. No 2-3 second slow attack swells where nothing is
   heard. If you want an "intro" feel, use sparse-but-audible (a soft kick
   pulse, a held pad note already ringing, a single bell hit) — not silence.
   At least 3 of the 5 tracks must be clearly audible in section 0.

2. **The new mix must be PRE-WARMED before the old fades.** Concrete recipe:
   - Don't reset `t0` to null at transition time. Instead, set
     `t0 = millis()/1000 - secLen*2` (or any non-zero offset) so the new
     arrange enters at section 2 or 3 (a fuller mix) right when the audio
     swaps. The visuals follow the same anchor so they sync.
   - Alternatively: send the new tracks while OLD tracks are still mid-PEAK,
     so the cross is instant. Don't wait for the old scene to wind down.

3. **NEVER call `/strudel/hush`.** Never `/p5/clear`. Atomic name-overwrite
   only — the server replaces in one frame so the new code is live on the
   next audio buffer. The only way silence happens is if YOUR new code
   itself is silent, which is what rule 1 prevents.

4. **If a scene genuinely needs a "silent intro" mood**, achieve it through
   the VISUAL pacing (mist, slow fade-in subjects) while keeping audio
   audible — e.g. a held bell + soft pad always present, even at the most
   contemplative moments. Silence is a tool of the past scene's outro, NOT
   of the next scene's intro.

5. **Verify after every transition: read snapshot AND listen-via-status**.
   Check `/state` to confirm at least 3 tracks contain non-`~` content in
   their first arrange section. If not, immediately re-send a non-silent
   version.

This is non-negotiable. A silent gap is the single worst failure mode of
the autopilot. Every scene starts LOUD enough to be heard.

Wrong (what causes gaps): tear down old scene first → then build new scene.
The build takes 20-40s of dead air.

Right — **build first, then sweep**:
1. **Send all NEW layer/track code while the OLD scene is still playing.**
   New scenes can use distinct names (`bg2`, `subject2`, etc.) so they coexist
   briefly with the old ones, OR reuse the same names (`__bg`, `drums`, `bass`)
   — the server replaces them atomically, so on the next frame the new code is
   live with no gap.
2. **Verify the new scene is playing** (snapshot + status) before removing
   anything.
3. **THEN** `/p5/remove` the orphan layers from the old scene and `/strudel/stop`
   any orphan tracks. Do this in one quick burst at the end.

If you reuse names, step 3 is mostly a no-op — the new scene already overwrote
the old. The only orphans are layers/tracks whose name didn't exist in the new
scene (e.g., the old scene had `kelp_fg` but the new one doesn't).

**Audio specifically**: never call `/strudel/hush`. Replace tracks one at a time
by name. Even on a hard genre cut, send the new `drums`/`bass`/etc. tracks
first, hear them taking over, then stop only the orphan tracks (e.g. an old
`stab` that the new scene doesn't reuse).

**CPS changes**: change `cps` AFTER the new tracks are loaded, not before.

## 🎵 MUSIC: PLAN LONG-FORM SECTIONS UP FRONT

### ⭐ USER DIRECTIVE (2026-05-29, durable): VISUAL SECTIONS that MIRROR the music
The user wants the visuals to arc through the same intro / build / drop / breakdown
sections the music does. Every scene must compute a section index from a shared
clock anchored in `window.state.t0` and modulate visual params accordingly:

```js
let cps = window.state.cps || 0.65;
if (window.state.t0 === undefined) window.state.t0 = millis()/1000;
let secLen = 4 / cps;                                  // MUST match music arrange section length (cycles)
let elapsed = millis()/1000 - window.state.t0;
let section = Math.floor(elapsed / secLen) % 8;        // 8 sections — pick 4 or 8 per scene
let intensity = [0.2,0.4,0.7,0.9,0.3,0.6,1.0,0.4][section];  // intro/build/drop/var/break/rebuild/peak/outro
let cyclePhase = (elapsed / (1/cps)) % 1;              // 0..1 within a cycle for beat-pulse
let beat = Math.max(0, Math.sin(cyclePhase*Math.PI*2));
```

Things that MUST respond to section every scene:
- **Element COUNT** (more cars/particles/birds/stars-moving in drop, fewer in breakdown)
- **Motion SPEED** (multiplier per section)
- **ADD-glow ALPHA** (lasers/halos/light-shafts off in intro, peak in drop, fade in breakdown)
- **Beat pulse** on a hero subject in the drop (sun halo, mirror ball, subject scale)
- **Color accent shift** (e.g. cooler in intro, hottest in drop)

Operational rules:
- Push cps to p5 state on every change: `curl /p5/state {"key":"cps","value":<n>}`.
- On scene transition, reset the section anchor by deleting t0 so it re-self-initializes:
  `curl /p5/state {"key":"t0","value":null}` — layers will set `t0 = millis()/1000` on
  their next frame, re-aligning the visual sections with the freshly-sent music arrange.
- Layer code is wrapped in push/pop but is NOT a function — do NOT use `return` to skip;
  use `if(section===N){ /* draw */ }` blocks instead.

### ⭐ USER DIRECTIVE (2026-05-29, durable): NO MONOTONOUS DRUMS / CYMBALS
The user called out hearing "only cymbals" because a drum track had a continuous
white-noise crackle layer on every section, plus `hh*16` doubled to ~32 hits/cycle
via `.every(2, x=>x.fast(2))`. Both sound like a non-stop cymbal wash that drowns
the mix.

**Rules:**
- **Never run a continuous noise/hiss layer** (`s("white").hpf(...).lpf(...)`,
  "vinyl crackle", "rain hiss") across all 8 sections of a drum track. If you
  want that texture, restrict it to 1-2 sections, or vary its gain heavily.
- **No `hh*16` or denser** as the default hi-hat pattern, especially not with
  `.every(2, x=>x.fast(2))` (which doubles it to 32 hits/cycle). Use varied
  patterns with RESTS: `hh ~ hh hh ~ hh ~ hh`, `[hh oh]*4`, `hh ~ ~ ~ hh ~ ~ ~`.
- **No `sd*8` or `sd*16` as a baseline pattern.** Snare rolls are FILLS, used
  briefly (one bar, a crescendo). A drum part shouldn't be a continuous snare
  roll for an entire section.
- **Vary the kick pattern across sections** — not the same `bd ~ ~ ~` for all 8
  sections. Try `bd ~ ~ bd ~ ~ bd ~`, `bd ~ bd ~ ~ bd ~ bd`, `bd bd ~ bd`, etc.
- **Use rests deliberately.** A real drum groove has SILENCE between hits. Density
  ≠ goodness. A sparse pattern with the right syncopation beats a dense pattern
  every time.

### ⭐ USER DIRECTIVE (2026-05-28, durable): MELODY-FORWARD + SONG-FORM
The user called the music "very monotonous." Standing fixes, honor EVERY scene:
- **Melodies must MOVE and CHANGE often.** No 1-bar lead looping unchanged for a
  whole scene. The lead/melody should develop — new phrases, call-and-response,
  contour changes — ideally every few cycles. A melody is the focal point, not
  a static ostinato.
- **Vary the chords too** — don't sit on one pad voicing; move the harmony
  (chord changes "here and there", reharmonize between sections).
- **Build explicit SONG-FORM sections** into every scene: verse / chorus /
  bridge (or A/B/intro/drop). Use `arrange([8, verse],[8, chorus], ...)` so the
  melody, chords, AND drums shift between sections on a fixed cycle clock. The
  chorus should feel like a lift (higher/denser melody, fuller chords); the
  verse sparser. Keep all tracks arranged on the SAME cycle counts so sections
  line up.

Single repeating patterns are monotonous. Every scene should have **2-4
sections** planned at creation time that play out over the scene's lifetime
(~1-2 min). Examples:

- **Intro → build → drop → outro** (electronic)
- **Verse → chorus → bridge** (song-form)
- **A theme → B theme → return to A** (classical/jazz)
- **Sparse → dense → climax → strip back** (cinematic)

Two ways to bake long-form structure in:

1. **In-pattern**: use Strudel's time-based functions so the section change is
   in the pattern itself. `.every(16, fn)` swaps something every 16 cycles;
   `cat()` or `arrange()` sequence whole sections. Examples:
   `.every(8, x => x.fast(2))` — double-time fill every 8 cycles.
   `arrange([4, p1], [4, p2], [4, p3])` — A/B/C song-form.
   `cat(p1, p2)` — alternating sections.

2. **Out-of-pattern**: when you build a scene, decide its sections, set a
   `frameCount`-based or time-based check, and have the round/loop fire
   subsequent `/strudel/track` updates at the right time. The journal can note
   the planned arc ("intro 0-30s; drop 30-60s; reprise 60-90s").

Either way: **decide the arc when designing the scene**, not on the fly.
Visuals should evolve with the audio sections (e.g. when the bass drops,
something happens visually).

## Vibe / mood

**Ambitious, representational, sophisticated, and surprising.** Explore real
visual *concepts*, not one tweaked scene forever. Faces and figures, characters,
creatures, places, machines, type — rendered with craft and generative
technique. Aim to **surprise and delight**: each new scene should make a viewer
go "whoa, what's this?".

Banned: lone breathing orbs, generic dot/particle fields with no subject,
concentric circles, plasma blobs. If it isn't *of* something, don't draw it.

(Change this line to redirect, e.g. "surrealist dreamscapes", "kinetic
typography", "portrait gallery", "creatures of the deep".)

## Cadence — FAST. New scene every ~1-2 minutes.

**Change the whole scene OFTEN.** Heartbeat is as fast as possible — host samples
~every 6s; rounds run back-to-back in-turn. Lingering on a concept >2 minutes is
the failure mode.

- A scene lives **2-4 rounds, then transition** to a brand-new concept.
  Transitions are SEAMLESS (see top section) — build the new layers and tracks
  first (reusing names like `__bg`/`drums` to atomically replace), confirm
  they're playing, THEN sweep orphans. Aim for a new scene every ~1-2 minutes.
- Each batch typically = (1-2 escalations of the current scene) + (1 hard cut to
  the next). It's OK for a whole batch to be hard-cut-after-hard-cut if the
  scenes are landing.
- **Make it EVENTFUL.** Something must visibly happen EVERY round —
  entrances/exits, transformations, things multiplying/shattering/assembling,
  **camera moves (pans, zooms, rotations)**, surprises. Static frames are the
  failure mode.
- **AUDIO evolves every round** too — even a small move (filter, fill, note
  change, drum mute). On a scene cut the audio mood shifts to match.
- **Never repeat a concept recently done.** Before a hard cut, scan the journal
  tail and pick a category NOT in the last ~10 entries. The journal IS the log.

## Visual concepts to explore (rotate widely — surprise & delight)

ROTATE through these categories aggressively. Tag each journal entry with its
category so you can avoid recent ones:

- **Faces / portraits** (expressive, morphing, made of lines/particles, masks)
- **Creatures** (real animals, mythical — dragons, octopi, foxes, owls, whales, beetles)
- **Cities / structures** (skylines, isometric blocks, lighthouses, bridges, cathedrals)
- **Nature** (forests, oceans, deserts, mountains, weather, storms, auroras)
- **Aliens / sci-fi** (UFOs, alien landscapes, retrofuturist worlds, neon space)
- **Isometric / 3D-ish** (voxel scenes, axonometric machines, pseudo-3D rooms)
- **Generative art patterns** (flow fields, L-systems, Voronoi/Delaunay,
  reaction-diffusion, differential growth, kaleidoscopes, mandalas, fractals,
  cellular automata, strange attractors)
- **Kinetic typography** (words/phrases flying, assembling, glitching)
- **Surreal / dreamlike** (floating eyes, melting clocks, fish in air, doors in fields)
- **Characters with a story** (silhouetted figures, a traveler, a kid flying a kite)

**Camera moves are explicitly wanted:** use `push/translate/scale/rotate` to
pan, zoom, rotate the whole scene. Slow zoom-ins, orbiting around a subject, a
360° rotation, a parallax pan — bake these in.

Use `window.state` for real generative systems that evolve over time. **Text**
is encouraged — a word, phrase, name, number — used with intent.

## Music — DEFAULT synthy/warm/gooey. Experimental as the spice.

**The user's preferred palette is SYNTHY / DISCO / WARM-GOOEY-PAD.**
M83 / Tangerine Dream / outrun / chillwave / italo / french-touch / dream-pop
territory. The "synthwave highway" scene was called out as the sweet spot —
copy that flavor often:

- **Bass**: octave-jumping `sawtooth` w/ lpf+resonance (TB-303-ish), or
  smooth `sine` sub for chillwave depth, or `square` for funk.
- **Chord pad**: `supersaw` lush 7th/9th chords w/ slow filter sweep
  (`cutoff(sine.range(800, 2400).slow(8))`) + room + dotted delay. The
  "warm gooey" sound.
- **Lead**: `supersaw` hummable melody + delay + occasional octave-add. OR
  `vcsl_glockenspiel` for sparkly synth-like top. Major-7/minor-7 tonal.
- **Arpeggio**: bright `square` or `supersaw` 16th-note pluck arps for
  movement. The classic "running line."
- **Drums**: 909 4-on-floor + offbeat hh + claps. Or LinnLM1 for soft
  chillwave. Or 808 for trap/hip-hop crossover.

**Balance rule**: every 3–4 scenes drop in something EXPERIMENTAL for
contrast — granular chops, `.vowel()` formant, polyrhythm, drone, microtonal,
musique concrète, krautrock motorik. But default = synthy/warm/poppy.
The experimental flavors are the spice, not the staple.

Genres that ALL count as "synthy/warm" default: synthwave, italo-disco,
chillwave, dream-pop, M83-style cinematic synth, house, deep house,
french-touch, vaporwave, nu-disco, downtempo, future-funk, hyperpop,
synth-pop, balearic.

Experimental flavors (use sparingly): dark ambient, krautrock motorik,
musique concrète, free jazz, witch house, drone-doom, polyrhythmic afrobeat,
microhouse glitch, throat-singing chant, field-recording soundscape.

The experimental techniques below are TOOLS in the toolkit, not mandates.
A typical 5-scene stretch might be:
1. Synthwave (poppy, 4-on-floor, sawtooth arp, big sine kick)
2. Drone / dark ambient (experimental — drone bass + granular)
3. Disco (poppy, 4-on-floor, octave-bass, string stabs, glock hook)
4. Polyrhythmic afrobeat (experimental — stacked drums)
5. Dream-pop / chillwave (poppy, lush major chords, soft kit, vocal-like lead)

If the previous 2 scenes used `.vowel()`, `.shape()`, `.speed(0.5)`,
granular chops, or polyrhythm, **the next scene MUST be straight & consonant**
— normal kit, normal bass, normal chords, hummable melody, major or minor
key but TONAL.

## Music — RICH + varied + EXPERIMENTAL (the toolkit). Not a MIDI machine.

The default "drums+bass+lead+pad with sawtooth/triangle/sine" template is the
failure mode. So is *always* doing "kit + walking bass + chord stab + flute
melody + supersaw pad" with different notes. Every scene needs a fresh
**INSTRUMENTAL & TECHNIQUE identity** — different timbres, processes, even
different definitions of what a "track" does.

### 🎹 USER FAVORITE INSTRUMENTS — rotate these often

### 🧭 LONG-TERM STEERING MANDATE (durable; do not regress)

These are the user's standing preferences for the autopilot. Honor them every
scene, not just when freshly mentioned.

**1. Instrument diversity — rotate WIDELY across these palettes every scene:**
- **Vibraphones** (`vcsl_vibraphone`) — in the mix on most scenes as melody, counter-line, or hook
- **Keys** — `s("piano")` walking lines, `vcsl_clavinet` funk, `vcsl_celesta` twinkle, supersaw shaped as Rhodes/Wurli
- **Strings** — `vcsl_violin`, `vcsl_pizz_violin`, `vcsl_pizz_cello`, `vcsl_double_bass`, `vcsl_harp` (esp. harp arpeggios)
- **Congas / hand percussion** — `RolandTR727` Latin kit, `vcsl_timpani`, `s("cb")` cowbell, `s("rim")` rim shot
- **Claps** — prominent on 2&4 (`cp*2`, `cp:1` ghosts, stacked claps); house-style clap-track energy
- **Chiptune** — `s("square")` lead arps, `s("triangle")` sub, bitcrush via `.coarse(8)`/`.crush(4)`, 8-bit blippy hooks, pentatonic gameboy lines
- **Walking bass** — piano (`s("piano")`) walking lines, `vcsl_double_bass` jazz walks, sawtooth-lpf bass walks in chromatic step
- **Experimental instruments** — granular `clean-breaks`, `vowel()` formants, `coarse/crush` bitcrush, microtonal scales (`bhairav`, `hirajoshi`), drones from `.attack(8).release(12)` sustains, noise (`white`/`pink`/`brown`) shaped into wind/breath

A "good mix" stacks ≥3 of these palette categories at once. The failure mode is
"another supersaw pad + sawtooth bass + glock melody + 909 kit" template.

**2. Syncopation & rhythm — experiment, don't always 4-on-floor straight:**
- Push offbeat accents, ghost notes, 16th-note swing, dotted-rhythm hocketing
- Polyrhythm: `s("bd*5, sd*4, hh*7")`, `[a b c]%5`, `[a b c d]/3` — make math feel weird
- Probabilistic: `.degradeBy(0.4)`, `.sometimesBy(rand, fn)`
- Section-level fills with `.every(8, x => x.fast(2))`, breakdowns
- Don't lock to one groove for >2 rounds — vary the kick pattern, snare placement, hi-hat density

**3. Genre rotation — dance mainstays + interspersed genres + occasional experimental:**

DANCE MAINSTAYS (the default lane; ~50–60% of scenes):
house, nu-disco, italo-disco, french-touch, deep-house, garage, synthwave,
chillwave, dream-pop, balearic, future-funk, hyperpop, synth-pop

INTERSPERSE these other genres regularly (~30–40% of scenes, rotate):
- **Drum & bass** — 170bpm-feel break loops, sub-bass wobbles, amen-style breaks (use `clean-breaks`, `s("amencutup")` if available, fast hh)
- **Hip-hop** — boom-bap kits (`RolandTR808`, swung 16ths, soulful chord stabs, vinyl crackle via `.coarse(6)`)
- **Soul** — Rhodes-style supersaw, walking piano bass, brass-stabs via `vcsl_trumpet`, gospel chords (maj7/min9)
- **Disco** — string-stabs, octave-bass sawtooth, 4-on-floor + cowbell, glockenspiel hooks
- **Jazz / bossa** — `vcsl_pizz_violin`/`vcsl_pizz_cello` comp, brushed kit, walking double-bass, swung 8ths

EXPERIMENTAL SPICE (~10–15% of scenes, every 4–5 scenes drop one in):
dark ambient drone, krautrock motorik, musique concrète sample mangle,
microhouse glitch, polyrhythmic afrobeat, free jazz, throat-singing chant,
witch-house slow piano, field-recording soundscape

**4. Cadence rule for genre changes**: if the previous 2 scenes were the same
genre family (e.g. 2 house scenes in a row), the next MUST swap families — even
within the dance lane (house → nu-disco → italo → french-touch, not house →
house → house).

The user explicitly named these as wanted in the mix more often:
- **Warm synths** — supersaw lush pads, sine sub bass, sawtooth with low cutoff
- **Bells** — `vcsl_tubular_bells` (deep, big decay), `vcsl_glockenspiel` (sparkle), `vcsl_celesta` (twinkly)
- **Vibraphones** — `vcsl_vibraphone` (mellow, jazzy, ECM-era)
- **Congas / hand percussion** — try `s("cb")` cowbell, `s("rim")` rim shot;
  for actual congas/bongos look in `RolandTR727` (`s("bd cp").bank("RolandTR727")`)
  which has a Latin perc kit, or layer `vcsl_timpani` for deep tom hits
- **Keyboards** — `s("piano")` (acoustic), `vcsl_clavinet` (funk), `vcsl_organ_pipe` (sustained), or supersaw set to short attack/release for "Rhodes/Wurlitzer" feel
- **Strings** — `vcsl_violin` / `vcsl_pizz_violin` / `vcsl_pizz_cello` / `vcsl_double_bass` / `vcsl_harp` (the harp is gorgeous for arpeggios)
- **Brass** — `vcsl_trumpet` / `vcsl_trombone` / `vcsl_french_horn` for warmer pads
- **Woodwinds** — `vcsl_flute` / `vcsl_clarinet` / `vcsl_oboe` for melodic top

**Bias picks toward these every scene**. A "great mix" looks like e.g.
piano walking bass + supersaw warm pad + vibraphone melody + congas + sub
sine. NOT another sawtooth/triangle/sine bass + drums + lead template.

### Reach for unusual instruments (don't always pick the same 5)

- **vcsl beyond marimba/glock/flute/clarinet**: try `vcsl_pizz_violin`,
  `vcsl_pizz_cello`, `vcsl_double_bass`, `vcsl_harp`, `vcsl_celesta`,
  `vcsl_tubular_bells`, `vcsl_timpani`, `vcsl_taiko`, `vcsl_oboe`,
  `vcsl_bassoon`, `vcsl_trumpet`, `vcsl_trombone`, `vcsl_french_horn`,
  `vcsl_tuba`, `vcsl_accordion`, `vcsl_banjo`, `vcsl_mandolin`,
  `vcsl_xylophone`, `vcsl_clavinet`, `vcsl_organ_pipe`, sustained
  `vcsl_violin`/`vcsl_cello`. If a name turns up silent, swap and remember it.
- **Drum-machine rotation, not always 909/808/707**: `RolandTR606` (lo-fi),
  `RolandTR505` (boxy), `RolandTR727` (Latin perc), `AceTone`, `CasioRZ1`,
  `AkaiLinn`, `LinnLM1`, `DMX` (Oberheim), `Yamaha RX5`.
- **Noise & raw waveforms**: `white`, `pink`, `brown` for hiss/wind/textures;
  filter heavily and you have wind, surf, breath. Far more interesting than
  another sawtooth pad.
- **`clean-breaks` samples**: `s("clean:0").loopAt(2).chop(16).pan(rand)` is a
  whole different universe from `s("piano").note(...)`. Use them as percussive
  beds, granular textures, or rhythmically-resampled atmospheres.
- **Stack** with mini-notation commas to pack many instruments into one track:
  `s("bd*4, [hh oh]*4, ~ cp ~ cp, sh*8, ~ ~ rim ~")`.

### Reach for COMPUTER-MUSIC techniques (the user explicitly wants these)

The piece should occasionally *sound like a computer*, not a MIDI sequencer:

- **Granular / chopped sampling**: `.chop(16)`, `.striate(32)`,
  `.slice(8, "0 3 1 5 2 7 4 6")`, `.loopAt(N)`. Take any sample and grain it.
- **Time / pitch mangling**: `.speed(0.5)`, `.speed(sine.range(0.3, 2))` (tape
  stop), `.fast(seq(1,2,4,8))` (stutter), `.cut(1)` (hard mono-cut).
- **Distortion / lo-fi**: `.shape(0.7)` waveshaper, `.coarse(8)` bitcrush,
  `.crush(4)` sample-rate reduction, `.vowel("a e o")` formants.
- **Polyrhythm / polymeter**: `s("bd*5, sd*4, hh*7")` (5:4:7), `[a b c]%5`,
  `[a b c d]/3`, separate cycles with `:`. Make the math feel weird.
- **Probabilistic & aleatoric**: `.degradeBy(0.4)`, `.sometimesBy(rand, fn)`,
  `rand.range(60, 90)` as a parameter, `irand(8)` integer rand, choosing
  patterns via `pick(rand, [p1, p2, p3])`.
- **Sidechain pumping**: `.gain(saw.range(0.2, 1).fast(2))` ducks on the beat;
  great for synth pads under a 4-on-floor kick.
- **Drone & spectral**: hold a note with `.attack(8).release(12)` and a slow
  filter sweep. `.detune(0.1)` for shimmer. Layer 5 detuned sines on tritones
  for inharmonic spectra.
- **Long evolving texture as a "track"**: a track doesn't have to be a rhythm.
  Sometimes a single 30-second pad swell IS the whole track.
- **Microtonal / non-equal**: `.scale("c:bhairav")`, `.scale("d:in")`,
  `.scale("e:hirajoshi")` for non-Western moods; `.add(0.5)` doesn't bend
  pitches but try scale-based pitching.
- **Aux per-track FX**: `.room(2)` long reverb, `.delay(0.6).delaytime(0.375)`
  dotted-eighth, `.pan(rand)` wild pan, `.tremolo(8)` for AM.

### Genre / mood rotation (avoid repeating recent ones)

ambient, house, techno, dnb, jungle, hip-hop, jazz, bossa, synthwave, dub,
breakbeat, glitch, IDM, choral, lofi, funk, gamelan, drone, **musique
concrète, dark ambient, krautrock motorik, free jazz, vaporwave, witch
house, hyperpop, 2-step garage, trap, dubstep, trance, phonk, footwork,
acid house, reggaeton, cumbia, afrobeat, marching band, music-box, drone-doom,
spaghetti-western, klezmer, throat-singing-style chant, polka, polyrhythmic
West African, gamelan, lullaby, field recording, sound design.**

Don't stay in one genre >2 min. **Every 3-4 scenes, do something WEIRD** —
an aleatoric drone scene, a polyrhythmic sample-mangle scene, a pure-noise
texture, a vaporwave slowed-down piano — not just another genre-correct kit.

### Section-level dynamics (see top of file)

Plan 2-4 sections per scene up front. Bake them via `.every(N, fn)`,
`cat()`/`arrange()`, or scheduled track replacements.

- **At least 1 audio move every round** — not just a filter wiggle: introduce
  or swap an instrument, add a fill, drop a track, change tempo, mangle a
  sample, etc.
- Follow `.claude/skills/strudel.md`; end every track with `.play()`.

## Visuals — technique

- Follow `.claude/skills/p5.md`. Code runs inside `draw()`; no `createCanvas`.
- Animate via `frameCount`; persist generative state in `window.state`. HSB color.
- Sync key motion to the beat where it fits (beat phase ≈ `sin(frameCount*0.462)`
  at cps 0.55) — but the concept leads, the beat accents.

## 🚫 NO MONOTONOUS WHITEOUTS

Big bright ADD-blended areas (laser cones, mirror-ball halos, lens flares,
"glow" ellipses sized `width` or larger) saturate the canvas to white and
wash out everything else. The viewer sees a flat white dome or sheet, not
a scene.

Rules:
- **ADD-blend alpha ≤ 35** for any shape covering more than 1/4 of the canvas.
- **Lasers / beams must terminate on-screen** with a finite endpoint, not
  off-canvas. Cap their length at ~`height*0.4` from the source.
- **Halos around bright subjects** (mirror balls, suns, lamps) max size
  `~3× subject diameter`, max alpha ~25.
- **Always include a fully-opaque background layer** that runs FIRST so ADD
  blends never get to accumulate against a blank/black canvas. The cached-bg
  pattern handles this — but if you're not caching, call `background(...)`
  at the top of `__bg`.
- **If a single layer covers >2/3 of the canvas with ADD blends, redesign it.**
  Break the effect into smaller localized glows.

## ⚡ PERFORMANCE — cache static content, target ≥20 fps

The render loop draws every layer every frame, with NO background-clear between
layers. A scene with 1000+ static draw ops per frame will tank to <10 fps.

**Diagnostic**: glance at the `fps` indicator in the status bar (bottom right
of the snapshot). <15 fps = redesign required. Goal is ≥20 fps.

### Rule 1: Cache STATIC visuals to an offscreen buffer.

Anything that doesn't change frame-to-frame (gradient bg, brick pattern, grid
floor, tree silhouettes, distant city, wallpaper, etc.) should be drawn ONCE
into a `createGraphics` buffer and blitted with one `image()` call. Pattern:

```js
if (!window.state.myBg || window.state.myBg.width !== width || window.state.myBg.height !== height) {
  let g = createGraphics(width, height);
  g.colorMode(HSB, 360, 100, 100, 100);
  g.noStroke();
  // ALL the heavy static drawing goes here — runs once
  for (let y=0; y<height; y+=2) { g.fill(...); g.rect(0,y,width,2); }
  for (let r=0; r<rows; r++) for (let c=0; c<cols; c++) g.rect(...);
  window.state.myBg = g;
}
image(window.state.myBg, 0, 0);           // 1 op per frame
// only dynamic stuff (flicker, animation) draws every frame below
```

Real win measured: noir-bg went from 4 fps → 24 fps (6×) just by caching the
brick wall + gradient.

### Rule 2: Particle budgets — fewer than you think.

Most particle systems look identical at 80 as they do at 200. Defaults:

| effect           | use ~     | hard cap |
|------------------|-----------|----------|
| rain             | 80        | 120      |
| snow             | 100       | 140      |
| dust / motes     | 80        | 120      |
| stars (static)   | 200-500   | 800      |
| sparks (active)  | 30        | 60       |
| fireflies        | 100       | 150      |
| smoke puffs      | 20-30     | 50       |

Static stars / motes that don't move can live in the offscreen bg buffer
(infinite budget for free).

### Rule 3: BlendMode hygiene — group ADD ops together.

Every `blendMode(ADD)` ⇄ `blendMode(BLEND)` toggle is a canvas state flush.
Don't sprinkle them throughout the layer. Group all ADD-blended drawing into
one block at the end of the layer:

```js
// regular drawing first…
fill(...); rect(...); ellipse(...);
// then ALL the ADD glow stuff in one block
blendMode(ADD);
fill(...); ellipse(...);  // halo
fill(...); ellipse(...);  // glow
fill(...); ellipse(...);  // shine
blendMode(BLEND);
```

ADD on full-screen-sized fills is the most expensive — minimize area.

### Rule 4: Avoid noise()/trig in tight inner loops.

Calling `noise()` 1000 times per frame inside a per-pixel loop is a perf sink.
For mountain silhouettes, snowflake jitter, etc., compute the noise values
ONCE into `window.state.someArray` and reuse.

### Rule 5: Check fps after every scene cut.

The status bar shows fps. If you transition to a new scene and fps drops
below 15, fix it next round (cache to buffer, cut particles, remove a heavy
layer). Don't ship a 5-fps scene as "good enough."

## Structure limits

- Keep **3–6 p5 layers** and **3–5 Strudel tracks** alive at once.
- On a scene transition, build the new ones first (often reusing names like
  `__bg`/`drums`/`bass` so they atomically replace the old), then remove only
  the orphans that the new scene doesn't reuse. NEVER tear down before building.
- Use `__bg` as the persistent background layer.

## Error handling

- Each round read `GET /errors`. If an error names a layer, **fix or remove it
  this round** — don't pile new code on a broken layer.
- Panic rule: if `/errors` floods or the snapshot is black/frozen for two
  rounds, cut to a simple known-good scene and rebuild.

## Taste

- Sophistication over decoration: depth, composition, restraint where it counts,
  intentional palette. Generative *systems*, not random noise.
- Faces should emote; type should mean something; motion should have purpose.
- Make the next scene a genuine surprise, not a remix of the last one.

## Composition — LAYER everything

- **Most scenes should have a clear foreground + midground + background.**
  Don't put a subject on a flat sky — add a foreground silhouette (branches,
  grass, rocks, a window frame, foreground crowd, parallax-near terrain) and a
  background plate (distant mountains, clouds, deep gradient, atmospheric haze).
- **Background FX every scene**: atmospheric particles (dust, snow, embers,
  fireflies, drifting motes, smoke, rain, plankton, light shafts, lens flare).
  ADD blend modes for glow. Subtle but always present.
- **Experiment**: occasionally do a pure background-only scene (texture/atmosphere
  with no central subject — like a wall of falling petals, a roiling fog bank, a
  swirling galaxy), or a pure foreground-driven shot (extreme close-up of a face
  or hand). Variety in compositional structure, not just subject.
- Use parallax: different layers move at different speeds → real depth.

## Operational notes

- Host samples a snapshot ~every 6s and **automatically downscales** it to
  ≤1280px wide so the Read tool never trips the LLM image-size limit (no matter
  how big the user's browser window is). Just read `autopilot/snapshots/latest.png`.
- The journal IS the done-log. Each entry should TAG its category (e.g.
  `SCENE: "Reef" — creature/nature`) so the next pick can deduplicate.
- Layer name `__bg` is convention for the persistent background; all other names
  are free.
