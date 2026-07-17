# Overhaul TODOs — deliberately punted (2026-07-10)

Deferred from the catalog-factory phase. Revisit after the first factory runs
and a couple of performances with the new catalog.

- **Non-LLM control surface** — MIDI controller / browser hotkeys bound
  directly to `/p5/state` (the universal P params: hue/energy/speed/density)
  and `/strudel/cps`. Millisecond knob-turning with zero model in the loop.
  Gene wants to do this himself later.
- **Audition/cue channel** — previewing an incoming scene before it hits the
  audience (thumbnail in chat, or a second output). Going spontaneous for now.
- **Set-level dramaturgy** — tracking the 45-min macro-arc (peak time,
  breathers, finale) above scene granularity.
- **Conductor resilience + dress rehearsal** — watchdog process for the
  performing session (context compaction stalls, missed wakes), last-good
  auto-revert, browser-side stack revert patch, full-stack rehearsal on the
  stage laptop/projector/audio chain.
- **Persistent kiosk Chrome profile** — kiosk mode currently uses a fresh temp
  profile per launch, so the CacheStorage sample cache is cold every show.
  One-line change in `livecode.py` when doing the performance-loop rewrite.
- **`/show/append` route** — buffering primitive so fabricators can push
  pre-built sections onto a running show timeline (showrunner mode). ~12 lines
  in `livecode_server.py`.
- **Record `/strudel/send` as preamble steps** — sample loads are currently
  invisible to the timeline/restore; bites on browser reconnect and backward
  replay.
- **Performance-loop (autopilot skill) rewrite** — conductor protocol: triage
  (tweak / retrieve / fabricate-with-stopgap), ~50-line live card replacing the
  673-line instructions re-read, JSONL journal fingerprints, heartbeat rule.
  Depends on the catalogs existing first.
