# Livecode Improv — Agent Guide

**The fourth mode.** Manual = fire curls. Showrunner = replay a deterministic
timeline. Autopilot = wake on a timer and evolve. **Improv = you perform, live,
continuously, out loud, while Gene steers by typing.**

Trigger phrases: *"improvise"*, *"jam"*, *"keep going"*, *"mix it up"*,
*"make something like X but new"*, *"you got dis"*.

> **⛔ THE ONE UNBREAKABLE RULE (see §4.5): never create silence you haven't
> already filled.** Never hush/stop/clear the current music before the next
> section is written and ready to fire in the same breath. You do your thinking
> over a LIVE groove — never over silence. The multi-minute "let me think up the
> next thing" gap is the worst failure on stage. Only Gene saying "stop"/"hush"
> may produce bare silence.

---

## 1. What this mode is

You are a performer, not a jukebox. **Default to writing your own Strudel/p5
live.** The catalog (`assets/music/` — ~700 stems / ~130 kits — and
`assets/visual/`) is **context and inspiration, NOT the vocabulary you fire.**
Read a kit for its voicing, groove, param range, or the way it solves a problem —
then hand-code *your own take*. That is the whole point of this mode: forcing
original code every time is what promotes **diversity**, so no two sets collapse
onto the same pre-baked loops. The best moments of session 1 were all hand-written
(a tumbao bass, a piano montuno, an answering horn section, an 8-bar form with a
relative-major B section) — none of which exist as assets.

**Fire a catalog asset verbatim only when Gene asks you to** — by name ("play
`kit.deephouse_dusk`", "drop the marimba ostinato"), by pointing at a saved set,
or by referencing a past show ("do the disco set from a few weeks ago",
`shows/*.show.json`). Those overrides are his to give; absent one, you write.
The catalog is also your safety net and your reference for *what audible,
in-key, in-tempo code looks like* — lean on it for that, don't copy it.

> This is the improv contract specifically. The retrieval/Showrunner path
> (`assets/music/README.md`) fires verified assets verbatim on purpose — that's
> a different surface with a different promise (guaranteed-audible, deterministic).
> Here, hand-written code is the goal, so **you** own the audibility check — the
> silent-failure catalog in §5 is on you, not the validator.

Four rules define the mode:

0. **Transmute, don't copy — unless told.** Hand-code by default at the
   transmutation level (§2.1); fire catalog assets verbatim only on Gene's
   explicit request (see above). Diversity is the reason.

1. **Never stop.** The moment the current thing is playing, start building the
   next one. Do not wait, do not idle, do not ask "want me to continue?" while
   music is playing. Silence and dead air are failures; so is a finished plan
   with nothing queued behind it.
2. **Think out loud.** Narrate the musical reasoning *before* firing — what the
   move is, why it follows, what the harmonic/rhythmic relationship is. Gene is
   watching the reasoning as much as hearing the result. Say the thing you almost
   did and rejected, and why.
3. **Stay interruptible.** Gene steers mid-flight ("more disco", "too fast",
   "no strobe", "take off the chords"). His message lands between tool calls.
   Honor it on the next action, not the next set. Safety steering (flicker,
   strobe, volume) preempts everything — fix it in the very next call.

**Plan N+1 while N plays.** Planning takes 4–6 minutes of wall-clock; a 3-minute
set will loop 2–4× if you start planning only when it ends. Batch: plan two or
three sets up front, then execute on boundaries. This is the single biggest
cadence fix learned so far.

---

## 2. The regime — palette → conductor → transmutation (the default set shape)

This reconciles three facts: hand-written code is the point (§1), your
reasoning time is variable (15–40s for a granular tweak, 30–90s for a new part,
3–6 min for a from-scratch section), and an unchanged mix bores the room in
~1–2 minutes. The regime makes the *plan* expensive once and every *move*
cheap, and hands all timing to the conductor (§3).

### 2.1 The authorship ladder — transmute, don't copy

Every fired block must differ from any catalog reference in its **musical
surface**: the note/rhythm pattern, the mask/phrase shape, or the modulation
scheme. What you MAY inherit verbatim is **verified infrastructure**: the synth
chain (`.s/.ftype/.lpf` stack), envelope, gain staging + pump idiom,
`.shape()` loudness, `.orbit(N)` — a guitarist doesn't build the guitar on
stage, and under-loudness/banned-features are the top silent failures.
Levels, by cost:

- **L1 select** — assemble your own kit from stems+params. Cheap, but no
  visible code authorship; use for backbone slots, sparingly.
- **L2 transmute (DEFAULT)** — take a palette stem's chain, write your own
  notes/rhythm/masks/modulation over it. ~30–90s per part, low risk, real
  diversity, and the audience watches fresh Strudel appear.
- **L3 from scratch** — full authorship, minutes. Reserve for the set's
  signature moments: the melody, the form, the reharmonization.
- L0 verbatim — only when Gene names an asset or a saved set.

### 2.2 Set-start ritual (one deep think, then write-only)

Before the first fire — or while the outgoing set still plays:

1. **Skeleton**: key journey (name the relationships out loud — relative
   major, parallel, Neapolitan), tempo arc, the genre pair to conflate, a
   rough section plan.
2. **Load the palette NOW**: grep `assets/music/index.jsonl` for the
   territory, batch-read **8–12 stems into context** (2–3 per slot you'll
   use). All retrieval happens here — a mid-set grep+read cycle is 30–60s of
   dead air. After this, every move is write-only.
3. **Announce the plan** in a paragraph, then make sound inside the first
   minute: drums or a drone, direct-fired (`--at 0` / plain `lc track`) to
   start the grid.

### 2.3 The loop — granular moves on the conductor's grid

- **One move per 30–60s**, each touching **one slot**, queued to a 4/8-bar
  line. One-in-one-out instrumentation; never rebuild the mix in one commit.
- **Every pattern carries its own future.** Slow LFOs over 16–32 cycles,
  nested `<...>` cycles at 8/16/32 bars, verse/chorus via `.mask()`
  alternation — sized to *at least* the gap before your next move. About to
  think for three minutes? What's playing must evolve for three minutes.
- **Narrate 1–2 sentences per move** — the musical reasoning, before the
  fire. Deep narration only at pivots.
- **Verify after each fire**: `lc status` (carries `lastError`); read
  `state.audio` rms every few moves. Hand-written code owns its own
  audibility (§5).
- **Section pivot every ~8–16 moves (3–5 min)**: key change, genre shift, or
  form change — planned during the previous section, fired as one staggered
  queue batch with a deliberate carry-over slot (§4.4).

---

## 3. The conductor — your think-time jitter is not the music's problem

The server holds queued commands and fires them **on bar lines** (cycle ==
bar). Submit changes the moment they're written, in quick succession; each
lands on the grid. Never block in `boundary.py` again for a routine change.

```bash
./lc track bass 'n("0 3 5 7")...' --at 8      # fire on the next 8-bar line
./lc track pads '...' --at 8 --after 2        # same line, 2 bars later (stagger)
./lc stop oldlead --at 4                      # retire a part on a 4-bar line
./lc cps 0.55 --at 16                         # tempo move on a 16-bar line
./lc q                                        # pending items + next-boundary ETAs
./lc qcancel q7                               # changed your mind
```

curl: `POST /q {route, payload, at, offset}`, or `{items:[...]}` to declare a
whole staggered phase-in in one call. `GET /q` → transport position, ETA to
each boundary size, pending + recent items. Semantics worth knowing:

- **Targets are cycle numbers**, so a cps change mid-wait shifts the ETA but
  never the musical grid; a transport hard-reset makes stale targets recompute.
- **While the transport is stopped, grid items hold** (there is no grid yet) —
  direct-fire the first sound of a show, queue everything after.
- Queued fires are **recorded into the show timeline** and logged to the
  server console (`⏱ fired track bass @bar 96`), so the flight recorder stays
  complete.
- Queueable routes: strudel `track/stop/hush/cps` · p5 `layer/remove/fps/state`.

### 3.1 Show-start checklist (when Gene says "improvise" / "let's play")

1. **Server**: `./lc status`. If unreachable:
   `nohup python livecode.py > /tmp/lc_server.log 2>&1 &`, open
   `http://localhost:8766/livecode.html`, Gene clicks Start. (Use whatever
   port the show is on; improv default 8766, music-catalog tooling 9766.)
2. **Prove the audio path**: fire a quiet 1-bar hat, confirm
   `/p5/read?key=audio` rms > 0, then keep it as the count-in or stop it.
   `/status` 200 is not sound (§5).
3. **Set-start ritual** (§2.2): skeleton → palette → announce.
4. First sound direct; everything after through the conductor.
5. From here, never idle — plan N+1 while N plays (§1).

---

## 4. Transitions — the doctrine (READ THIS)

Abrupt transitions were the #1 complaint of session 1. **The music must never
lurch.** Four rules:

### 4.1 Land on the grid — never fire mid-bar
At cps C, **one cycle == one bar** and lasts `1/C` seconds. Firing when *you*
happen to be ready starts the new material on an off-beat: the ear hears a seam.

```bash
python assets/tools/boundary.py --bars 8 --port 9976   # blocks until the next 8-bar line
python assets/tools/set_play.py weight --at 8 --port 9976   # same, built in (default)
```
Waiting costs **at most one phrase**. Always worth it. `--at 0` to override.

### 4.2 Let the outgoing phrase finish
Never yank a slot mid-bar. `set_play --orphan-after 4` lets orphan slots ring to
the end of a 4-bar phrase before stopping. The old material should *leave on a
phrase end*, not get cut.

### 4.3 Phase in, don't hard-swap
Bringing 5 slots in on one downbeat is a jump cut. Stagger them —
drums → perc → bass → chords → lead → pad → texture → vox, a bar or two apart
(`set_play --phase 2`). The mix *arrives* rather than *switches*. Same idea by
hand: fire the new drums on bar 1, the new bass on bar 3, the pads on bar 5.

### 4.4 Keep the beat through the change
**Something percussive must play across the seam.** The best transitions of
session 1 kept a slot alive through the change (`vox` carried from a rave kit
into an ambient one while the whole rhythm section orphaned out — the voice was
the thread). Pick the carry-over slot *deliberately* before you fire.

### 4.5 THE UNBREAKABLE RULE — never create silence you haven't already filled

**NEVER hush/stop/clear the current thing before the next thing is in hand and
ready to fire in the same breath.** There must never be unintended silence — not
one bar of it, and above all NOT the multi-minute gap while you *think up* what
comes next. Silence is the single worst failure on stage.

The ordering is absolute:

1. **Write the next section FIRST** — fully, in hand, ready to POST.
2. **Then** stop the old and start the new, back to back, ideally on the same bar
   line (queue the stop and the replacement to the same `--at`).

You may only fire a bare `/strudel/stop`, `/strudel/hush`, or `/p5/clear` when the
replacement audio is already written and you are turning it on *immediately* after
(or together with) the stop. If you are about to spend even a few seconds
reasoning about what comes next, **the current music keeps playing the whole
time** — you do your thinking over a live groove, never over silence.

- Replace **by name**: POST the new code to the same track name — the server
  swaps it atomically in one frame, no gap. This is always preferred over
  stop-then-start.
- When a section genuinely must drop instruments (a breakdown), keep at least one
  slot alive across the seam (§4.4) and queue the stops + the new material to the
  same bar line so the transition is instantaneous, never a hush-then-build.
- The ONLY time bare silence is allowed: Gene explicitly says "stop" / "hush" /
  "cut it". His command, his silence — nothing else.

### 4.6 Prefer arcs for internal motion
A kit×arc fired via `arc_compile` self-evolves for minutes (`arrange()` weaves
sparse/full/peak per section). That's free dynamics — it beats re-firing tracks
to fake a build.

---

## 5. The silent-failure catalog (all cost real stage time)

**`/status` 200 + `/errors` empty proves the code RAN. It does not prove anyone
can HEAR or SEE it.** Verify the output, not the exit code.

| Failure | Symptom | Guard |
|---|---|---|
| **Orphan slots** | old kit's slot keeps playing in the old key = cacophony | `arc_compile` only fires the NEW kit's slots. Diff `set(before) - set(kit["stems"])` and stop the rest. `set_play` does this. |
| **Missing sample packs** | track exists, throws nothing, is silent | A stem's `deps` must be loaded from `packs.json` FIRST. `arc_compile.fire()` does it; a hand-fired stem does not. |
| **Whiteout / blackout** | 60fps, 0 errors, canvas pure white | `python assets/tools/peek.py --port <p> --out /tmp/x.png` then **Read the PNG**. (genart.caustics @ style=gold energy=0.6 renders pure white.) |
| **Layer compile error** | OLD layer keeps running; you describe the new one | Peek. The engine keeps the last good layer on syntax error. |
| **Slot state leak** | new asset crashes every frame / renders degenerate | `window.state.<slot>` is never cleared on swap — the incoming asset inherits the outgoing one's keys + `createGraphics` buffers. `fire_visual.py` disposes it first. |
| **`window.state.P` uninit** | params silently ignored, asset uses hardcoded `D` defaults | engine never creates `state.P`; send `window.state.P = window.state.P \|\| {}` first. `fire_visual.py` does. |
| **No transposition exists** | hand-built kit is harmonically wrong | `compile_stem` only substitutes `${param}` defaults. **A kit's `key` is documentation, not machinery.** Check every pitched stem's `key` yourself; `key: null` stems are key-agnostic and always safe. |
| **cps window** | stem out of range | kit cps must sit inside EVERY stem's `cps.min/max`. |

---

## 6. Load & fps — measure before you blame an asset

**fps is meaningless under load.** Session 1 filed two bogus bug reports because
a stale `/tmp/vf_visual_host.py` from days earlier was burning ~390% CPU:
`genart.girih` measured 2.9fps under load, 8.6fps clean.

```bash
uptime                                  # need loadavg < ~4.5 to trust ANY fps number
ps -A -o %cpu,comm | sort -rn | head -5 # find the hog before accusing an asset
```

Rough costs on a quiet machine (full-window): a `bg` genart 40–60fps · `fx.dust`
−22 · `fx.glitter` −10 · a `post` pass −20 to −34 · `floor.led_grid` −29.
**Budget: bg + ~2 overlays.** `post.chromatic` costs 34fps for near-invisible
fringing; `post.kaleido` draws its OWN shards *over* the scene (it does not
mirror the frame) — audition posts, don't assume.

**Never hand a background agent the live port.** The standard launch recipe opens
with `pkill -9 -f livecode.py`, which matches EVERY instance regardless of
`--port` — a spawned task killed the live show mid-set. If a session must run
alongside a show, run the show under a different filename
(`cp livecode.py show_server.py`) so their pkill can't see it, and on a private
port. Also: **many browsers on one server = many `declared-hard-reset`s** — each
connect hushes the transport and wipes the track list. Keep exactly ONE client.

---

## 7. Visual clock

Assets must read `window.state.clk` — **never `frameCount`**. `frameCount/28.8`
assumes exactly 60fps: at 12fps it runs the animation at **20% of tempo**, and
it drifts with load. (Gene's May `full_show` layers do this; patch them to
`const beat = (window.state.clk ? window.state.clk.beat : frameCount/28.8);`.)

**Low fps + beat-synced flashes = strobe.** `pow(sin(beat*TAU),4)` is smooth at
60fps (phase step ~0.035) but at 12fps it steps ~0.17/frame — undersampled, it
lands on random values and *flickers violently*. Correct code, wrong framerate.
If fps is low, **cut layers first**; halving the beat rate calms it as a stopgap.
See the `no-strobe-visuals` memory — strobe is a hard safety rule, not taste.

**The visual/music section handshake is approximate.** `arc_compile.fire()` pushes
`secBeats`/`arc`/`t0` so `clk.section` restarts, but Strudel's `arrange()` plays
at `cycle % total_cycles` of the *global* transport — which is thousands of cycles
deep. So visual sections and musical sections only coincide by luck. Don't claim
they're locked.

---

## 8. Saved sets — bank what works

A **set** = kit × arc + visual stack + params + grade. The only record of a
*pairing that worked*; kits/arcs/assets alone don't capture it.

```bash
python assets/tools/set_save.py --list
python assets/tools/set_play.py weight --port 9976 --at 8 --phase 2
python assets/tools/set_save.py <id> --name "..." --kit ... --arc ... \
    --bg genart.x --bg-params '{"style":"..."}' --grade loved --note "why it worked"
```

Grade honestly. **Never record a taste signal Gene didn't give** — a wrong
`loved` poisons future inference worse than no signal. (Session 1: he named
"Mechanism" from memory but on replay meant `set.weight`; the mislabel was
corrected to `grade: ok` with a note.)

---

## 9. Craft notes that earned their place

- **Check the key relationship before firing, and say it out loud.** Db→Cm is a
  Neapolitan. Am→C is the relative major. E→Em is the parallel. Am→A across sets
  is a Picardy third. These make transitions sound *inevitable* instead of random.
- **`key: null` stems are key-agnostic** — the safe way to cross-breed genres.
  Pitched stems in the wrong key are a trainwreck (`lead.electro.theremin` is
  G# minor; against C phrygian it would have been a disaster).
- **Hand-built kits work**: `compile_arc()` takes any kit-shaped dict, so the 44
  catalog kits are just *saved points* in a 407-stem space. Assemble in memory,
  verify every stem's cps window, fire through an arc.
- **Reharmonize over the existing bass** instead of rewriting the progression —
  extensions (9ths/11ths) diatonic to the key are rich but consonant. Gm11 not
  Gm9 in C minor: Gm9's A natural is outside the key.
- **Alternate idioms rather than blending them.** The strongest arrangement of
  session 1 split an 8-bar form into a jazz half (walking bass, ride, sparse kick)
  and a salsa half (tumbao, montuno, clave, campana), same harmony throughout —
  via `.mask("<1 1 1 1 0 0 0 0>")` on individual stack members.
- **Make cycles nest.** An 8-bar form + 16-bar crash + 32-bar breakdown means the
  crash lands exactly on the breakdown's return and the whole machine resolves
  every 4 forms. The arrangement writes its own transitions.
- **At cps 0.52 one cycle == one bar**, so a 16-slot `<...>` IS a 16-bar cycle —
  that's how you get "a crash every 16 bars" and `.mask("<1!30 0 0>")` for a
  2-bar breakdown every 32.
- Salsa's syncopation lives in the **bass**: a tumbao avoids the downbeat (root on
  the & of 2, fifth on 4, octave anticipating the & of 4). A walking bass does the
  opposite — all four beats. Swapping between them changes the groove completely
  without touching a single chord.

---

## 10. Related

| Doc | For |
|---|---|
| `assets/music/README.md` | the music system (kits/arcs/stems, validate, verify_arcs) |
| `.claude/skills/p5.md` | the visual system (assets, slots, gates) |
| `.claude/skills/strudel.md` | Strudel craft — syntax, genre recipes |
| `assets/music/BUNDLE.md` | legal Strudel features + the BANNED list |
| `.claude/skills/autopilot.md` | the timer-driven autonomous loop (different mode) |
| `.claude/skills/livecode-compose.md` | Showrunner — deterministic shows |
