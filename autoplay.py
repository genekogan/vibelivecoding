"""Autoplay driver — load a show and advance steps on a clock.

Examples:
  python autoplay.py --show shows/disco_set.show.json --dwell 16beats
  python autoplay.py --show shows/full_show.show.json --dwell auto --loop
  python autoplay.py --show shows/X.show.json --dwell 8s --start-at 5

Dwell formats:
  Ns          absolute seconds (e.g. 4s)
  Nbeats      N quarter-notes at current CPS (e.g. 16beats)
  Nbars       N bars; bar = 4 beats = 1 cycle (e.g. 2bars)
  Ncycles     N strudel cycles (1/cps seconds each)
  auto        use per-step `dwell` field, else show `default_dwell`, else 16beats

CLI --dwell overrides everything except per-step `dwell` (set by show author).
Tempo is re-read from the server before each step, so mid-show CPS changes
feel right.
"""

import argparse
import json
import re
import sys
import time
import urllib.request


parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--show", required=True, help="Path to .show.json")
parser.add_argument("--port", type=int, default=8766)
parser.add_argument("--dwell", default="auto",
                    help="Per-step pause: Ns / Nbeats / Nbars / Ncycles / auto")
parser.add_argument("--loop", action="store_true",
                    help="Restart from step -1 when reaching the end")
parser.add_argument("--start-at", type=int, default=-1,
                    help="Step index to start from (default: -1, before first)")
parser.add_argument("--respect-step-dwell", action="store_true",
                    help="If --dwell is also set, prefer the per-step dwell from the show")
args = parser.parse_args()

BASE = f"http://localhost:{args.port}"

DWELL_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(s|beats?|bars?|cycles?)?\s*$")


def parse_dwell(spec: str, cps: float) -> float:
    """Convert a dwell spec to seconds given the current cps."""
    if spec is None:
        spec = "16beats"
    spec = spec.strip().lower()
    if spec == "auto":
        spec = "16beats"
    m = DWELL_RE.match(spec)
    if not m:
        raise ValueError(f"unrecognized dwell spec: {spec!r}")
    n = float(m.group(1))
    unit = m.group(2) or "s"
    if not cps:
        cps = 0.5  # safe default
    if unit == "s":
        return n
    if unit.startswith("beat"):
        return n / (cps * 4)
    if unit.startswith("bar") or unit.startswith("cycle"):
        return n / cps
    raise ValueError(f"unknown dwell unit: {unit}")


def post(path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload or {}).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def get(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return json.loads(r.read())


def wait_ready(timeout: float = 60):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if get("/status")["ready"]:
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise TimeoutError("browser never connected")


# ── load show ────────────────────────────────────────────────────

wait_ready()
print(f"Loading {args.show}…")
result = post("/show/load_file", {"path": args.show})
if not result.get("ok"):
    print(f"  ERROR: {result.get('error')}", file=sys.stderr)
    sys.exit(1)

# Re-read show to access per-step dwells and default_dwell
with open(args.show) as f:
    show_doc = json.load(f)
default_dwell = show_doc.get("default_dwell")
steps = show_doc.get("steps", [])
total = len(steps)
print(f"  {total} steps loaded ({result.get('name')})")

# Reset to start position
if args.start_at >= -1:
    post("/show/goto", {"step": args.start_at})

# ── loop ─────────────────────────────────────────────────────────


def pick_dwell(step_idx: int) -> str:
    """Choose the dwell spec for the upcoming step (index just advanced to)."""
    # Step-level override always wins
    if 0 <= step_idx < total:
        step_dwell = steps[step_idx].get("dwell")
        if step_dwell:
            return step_dwell
    # Then CLI (unless explicitly told to respect step dwell only)
    if args.dwell and args.dwell != "auto":
        return args.dwell
    # Then show-level default
    if default_dwell:
        return default_dwell
    return "16beats"


while True:
    status = get("/status")
    cps = status.get("cps") or show_doc.get("cps_at_start") or 0.5
    cur = status["step"]

    # advance
    result = post("/show/next", {})
    if not result.get("ok"):
        if args.loop:
            print("End reached — looping back to start.")
            post("/show/goto", {"step": -1})
            continue
        print("End reached. Done.")
        break
    new_step = result.get("step", cur + 1)
    label = result.get("label", "")
    spec = pick_dwell(new_step)
    seconds = parse_dwell(spec, cps)
    print(f"  step {new_step:3}/{total}  cps={cps:.2f}  dwell={spec:>10}  ({seconds:.2f}s)  {label}")
    time.sleep(seconds)
