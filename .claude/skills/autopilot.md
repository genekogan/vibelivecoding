# Livecode Autopilot — Agent Guide

## What This Is

An autonomous improvisation loop on top of the livecode system. Once started,
an agent (you) wakes up every ~1 minute, looks at what's currently on the
canvas, and either evolves the current scene or transitions to a fresh
concept — visuals and music together. The user steers the trajectory by
typing messages into the same chat session.

When the user says "start the autopilot", "run the autopilot", "kick off the
loop", or similar, follow this doc to launch.

## Architecture

Three long-lived pieces, all in the project root:

1. **`livecode.py`** — the server (WebSocket 8765 + HTTP/REST 8766)
2. **`autopilot_host.py`** — a Playwright Chromium that bootstraps the
   browser, clicks "Start", keeps the page alive, and periodically writes
   a downscaled snapshot to `autopilot/snapshots/latest.png`
3. **`/loop` skill** — you, in dynamic self-paced mode, waking via
   `ScheduleWakeup` once a minute to do one round of improvisation

Working files in `autopilot/`:

- **`instructions.md`** — live creative steering. Re-read FULL every round.
  The user edits this to change permanent direction (mood, music palette,
  performance rules).
- **`journal.md`** — append-only log of rounds. Each entry tags its category
  so future rounds can avoid repeating recent ones. Read the **tail (~12
  entries)** every round.
- **`ideas.md`** — a brainstorm pool of scene concepts. Skim it when picking
  a fresh concept.
- **`snapshots/latest.png`** — what the canvas looks like right now.
  Read it every round to *see* what you're working on. The host also rotates
  `prev1.png`–`prev3.png` for short-term history if you want to compare
  against the prior round.

## How to Launch

```bash
PY=~/.pyenv/versions/3.11.0/bin/python
# kill any stale instances + free ports
pkill -9 -f livecode.py 2>/dev/null; pkill -9 -f autopilot_host.py 2>/dev/null
lsof -ti tcp:8765 tcp:8766 2>/dev/null | xargs -r kill -9
sleep 1
# launch detached
nohup "$PY" livecode.py >autopilot/server.log 2>&1 & disown
sleep 3
nohup "$PY" autopilot_host.py >autopilot/host.log 2>&1 & disown
sleep 5
curl -s localhost:8766/status   # should return {"ready": true, ...}
```

Then reload the sample packs once per session (they don't persist across
server restarts):

```bash
curl -X POST localhost:8766/strudel/send -d '{"code":"samples(\"https://strudel.b-cdn.net/tidal-drum-machines.json\"); samples(\"https://strudel.b-cdn.net/piano.json\"); samples(\"https://strudel.b-cdn.net/vcsl.json\")"}'
```

Then **invoke the `/loop` skill in THIS session** (the same chat the user
typed "start the autopilot" in) using the Skill tool with the canonical
prompt below. **Do NOT:**
- delegate to a sub-agent via the Agent tool (the user can't talk to it)
- launch the loop in a separate process / `nohup` it (they can't reach it)
- call `/schedule` (that's the cloud cron, runs without their input)

The loop must run as YOU, in this conversation, so user messages can
naturally steer it.

## The Canonical /loop Prompt

Keep this prompt tight — creative direction belongs in `instructions.md`,
not baked into the loop prompt (so edits to instructions take effect without
restarting the loop).

```
/loop Livecode autopilot — one round per wakeup.

Each round:
1. Read `autopilot/instructions.md` (FULL — live steering, re-read every round).
2. Read tail (~12 entries) of `autopilot/journal.md` — avoid recent categories.
3. After a scene transition, optionally scan `autopilot/ideas.md` for fresh concepts.
4. `curl -s localhost:8766/status` → if `ready:false`, ScheduleWakeup 60s and skip.
5. `curl -s localhost:8766/state` to see current tracks + layers.
6. Read `autopilot/snapshots/latest.png` to SEE the canvas.
7. Decide: evolve the current scene OR transition to a fresh concept.
   **ALL transitions are SEAMLESS** — atomic name-overwrite, never `/p5/clear`
   or `/strudel/hush`. New code replaces old code on the same layer/track names
   so the canvas + audio cross over with no gap.
   **MUSIC SAFETY: never replace more than 2 tracks in one round**, never
   call `/strudel/hush`, and after every `/strudel/track` send, recheck
   `/status` to confirm the track is still in the list (silent JS errors
   drop it). At least 2 tracks must always be playing.
8. Send via curl: `/p5/layer {name,code}`, `/p5/remove {name}`, `/p5/setup`,
   `/strudel/track {name,code}`, `/strudel/stop {name}`, `/strudel/cps {cps}`.
   Follow `.claude/skills/p5.md` and `.claude/skills/strudel.md`.
9. Wait ~6-8s, re-read snapshot to confirm fps + visuals + zero whiteout.
   Re-check `/status` — if track count dropped below previous, restore.
10. Append a journal entry with category tag.
11. ScheduleWakeup 60s for the next round.

All creative direction lives in `autopilot/instructions.md` — do not bake
mandates into this loop prompt.
```

(Quote it back to the user when they say "start the autopilot" so they can
see what's running.)

## Cadence — 60 seconds

**One round per minute.** That's the floor the runtime allows for
`ScheduleWakeup` and it's the right cadence: fast enough to keep the canvas
alive (visible change every minute), slow enough that each round can do real
work (read state, design a transition, write code, verify).

Do **one round per wakeup**, not back-to-back batches. Each wakeup = one
seamless evolution or one seamless category transition. Then schedule the
next wakeup at 60s.

## No Hard Cuts — Ever

A "hard cut" (calling `/p5/clear` then building a new scene from scratch,
or `/strudel/hush` then sending fresh tracks) creates a black screen +
silence gap that takes 20-40s to fill while you write new code. Unacceptable.

**Every transition is a SEAMLESS HANDOFF**: reuse the same layer/track names
so the server atomically replaces the old code with the new code in one
frame. No `/p5/clear`, no `/strudel/hush`. If the new scene has fewer
layers/tracks than the old one, remove only the orphans AFTER the new code
is in and you've verified it's playing.

Names like `__bg`, `drums`, `bass`, `chords`, `melody`, `vibes`, `fg` can
mean whatever the scene needs — they're identifiers, not semantic labels.
Don't worry if "balloons" is drawing brass gauges this round; what matters
is no-gap transitions.

## 🔇 NEVER GO SILENT — hard mandate

Audio silence has happened in past runs and is unacceptable. Defend against
it with these rules:

1. **NEVER call `/strudel/hush`.** Not even "briefly." There is no scenario
   where it's the right tool while the loop is running. Use `/strudel/track`
   to replace code atomically; use `/strudel/stop {name}` only after a
   replacement track is confirmed audible.

2. **At least 2 tracks must be playing at all times.** Before any track
   change, `curl -s localhost:8766/status` — if the track list is empty or
   has only 1 track, your priority for this round is FIX THE AUDIO, not
   anything visual. Send simple known-good tracks immediately.

3. **Stagger track replacements across 2 rounds when switching genres.**
   Don't replace all 5 tracks in one round. Round N: swap drums + bass to
   the new style. Round N+1: swap chords + melody + vibes. This way if any
   of your new code has a JS error, the rest of the mix is still playing
   while you debug.

4. **Use only verified Strudel patterns.** If you're about to send code
   that includes a sample name you haven't used before (e.g. `vcsl_choir`),
   keep one of the existing tracks UNTOUCHED in the same round as a safety
   net — that way even if the new code silently fails to produce audio, the
   user still hears something.

5. **After every `/strudel/track` send, re-check `/status` 2 seconds later.**
   The track must still appear in the `tracks` array. If it vanished, your
   code had a parse error; restore the previous track immediately from
   memory or a generic fallback like:
   `s("bd*4, ~ cp ~ cp, hh*8").bank("RolandTR909").gain(0.6).room(0.5).play()`

## How the User Steers Mid-Loop

The user is in the same chat session. They can type messages anytime —
their messages land in your context and you can act on them either:

- **Immediately** if you happen to be awake when they type, OR
- **On the next wakeup** if you were sleeping (their message will be the
  first thing you see when ScheduleWakeup fires)

So directives like "more disco music", "show me a portrait next",
"the visuals are too dark" — just type them. You'll honor them the
moment you next take a turn. No special file or queue needed; the
conversation IS the queue.

For PERMANENT shifts in taste (default music palette, performance rules,
banned imagery), edit `autopilot/instructions.md`. That's re-read every
round so it takes effect immediately.

## How to Stop

User says "stop" → run:

```bash
curl -s -X POST localhost:8766/strudel/hush -d '{}' >/dev/null 2>&1
curl -s -X POST localhost:8766/p5/clear -d '{}' >/dev/null 2>&1
pkill -9 -f livecode.py 2>/dev/null
pkill -9 -f autopilot_host.py 2>/dev/null
sleep 1
lsof -ti tcp:8765 tcp:8766 2>/dev/null | xargs -r kill -9
```

Don't ScheduleWakeup. The loop is done.

## Common Gotchas

- **A `livecode.py` from another worktree/install may already own port 8766.**
  Check with `ps -ef | grep livecode` and `lsof -i tcp:8766`. Kill it first
  or your new server will run silently with no clients.
- **`/state` returns the full code dump** (tracks + layers source, cps,
  setup) — use it for self-correction. **`/errors`** returns recent browser
  runtime errors (deque, maxlen 50) — check it after any code send.
- **JavaScript syntax errors in a layer** are caught per-layer (push/pop
  wrap) so they don't break other layers — but the broken layer just
  silently fails to draw. If you see a layer disappear, check its code.
- **The cached `createGraphics` bg pattern** is the single biggest perf
  win — see `autopilot/instructions.md` perf section. Use it for any
  static decoration (gradients, brick walls, distant skylines, palm trees,
  star fields).
