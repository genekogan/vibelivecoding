#!/usr/bin/env bash
# Launch the livecode server + the autopilot browser host (the projector window).
# After both are up, paste the printed /loop command into Claude Code to start
# the autonomous improvisation.
#
# Usage:  autopilot/run.sh [extra autopilot_host.py args, e.g. --fullscreen]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
mkdir -p autopilot/snapshots

# Use the interpreter that has websockets + playwright installed.
# Override with:  PYTHON=/path/to/python autopilot/run.sh
PY="${PYTHON:-python}"
if ! "$PY" -c "import websockets, playwright" 2>/dev/null; then
  echo "ERROR: '$PY' is missing websockets/playwright." >&2
  echo "Set PYTHON to an interpreter that has them, e.g.:" >&2
  echo "  PYTHON=~/.pyenv/versions/3.11.0/bin/python autopilot/run.sh" >&2
  exit 1
fi

SERVER_LOG="autopilot/server.log"
HOST_LOG="autopilot/host.log"

echo "Starting livecode server (-> $SERVER_LOG)..."
"$PY" livecode.py >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!

echo "Starting autopilot browser host (-> $HOST_LOG)..."
"$PY" autopilot_host.py "$@" >"$HOST_LOG" 2>&1 &
HOST_PID=$!

cleanup() {
  echo "Stopping (server $SERVER_PID, host $HOST_PID)..."
  kill "$HOST_PID" "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

cat <<'EOF'

──────────────────────────────────────────────────────────────────────────────
Server + browser host are starting. A visible Chromium window is your projector
output. Once it shows "Connected", start the autonomous loop in Claude Code by
pasting this (self-paced /loop — no interval):

/loop You are the livecode autopilot. Run ONE round, then schedule the next.
  1. curl -s localhost:8766/status — if ready is false, ScheduleWakeup ~45s and stop.
  2. Read autopilot/instructions.md (all) and the tail (~last 8 entries) of
     autopilot/journal.md.
  3. curl -s localhost:8766/state and curl -s localhost:8766/errors.
  4. Read autopilot/snapshots/latest.png (and prev1.png) to see current output.
  5. Decide ONE move per instructions + history + what you see + errors. If an
     error names a layer/track, fix or remove it this round.
  6. Send it via curl to the REST API (see CLAUDE.md; follow .claude/skills/
     p5.md and strudel.md). Prefer mutation over clear/hush.
  7. Wait ~20s for a fresh snapshot, re-read latest.png + /errors; revert/repair
     if it broke.
  8. Append a journal entry to autopilot/journal.md in the documented format.
  9. ScheduleWakeup with a delay honoring the cadence (60-120s; shorter if
     recovering), passing this same /loop prompt to continue.

Stop the show: Ctrl+C here (kills server + browser) and stop the loop in Claude.
──────────────────────────────────────────────────────────────────────────────

EOF

wait
