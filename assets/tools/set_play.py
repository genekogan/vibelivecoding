#!/usr/bin/env python
"""Fire a saved SET — a kit x arc paired with a visual stack that worked.

  python assets/tools/set_play.py mechanism --port 9976
  python assets/tools/set_play.py set.mechanism --port 9976 --no-orphan-clean

A set is the unit a performance actually uses: which music kit, through which
arc, under which visuals, at which params. See assets/sets/*.set.json.

Transitions are SEAMLESS by construction: music tracks and visual layers are
replaced by NAME, so the outgoing set is overwritten in place. Nothing is ever
hushed or cleared. The one thing that is NOT automatic is orphan slots — see
below.
"""
import argparse, json, subprocess, sys, time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
SETS = ROOT / "assets" / "sets"


def load_set(ident):
    ident = ident if ident.startswith("set.") else f"set.{ident}"
    p = SETS / f"{ident}.json"
    if not p.exists():
        sys.exit(f"no such set: {ident}\navailable: "
                 + ", ".join(sorted(f.stem for f in SETS.glob("set.*.json"))))
    return json.loads(p.read_text())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("set_id")
    ap.add_argument("--port", type=int, default=9766)
    ap.add_argument("--no-orphan-clean", action="store_true",
                    help="skip stopping tracks the incoming kit has no slot for")
    ap.add_argument("--at", type=int, default=8, metavar="BARS",
                    help="wait for the next BARS-bar line before firing (0 = fire now). "
                         "Landing on the grid is what stops a transition sounding abrupt.")
    ap.add_argument("--phase", type=int, default=0, metavar="BARS",
                    help="phase the new set in: hold each slot BARS bars apart in "
                         "drums->perc->bass->chords->lead->pad->texture->vox order, "
                         "instead of swapping everything on one downbeat")
    ap.add_argument("--orphan-after", type=int, default=4, metavar="BARS",
                    help="let orphan slots ring for BARS bars after the new set is in, "
                         "so the old material leaves on a phrase end rather than a cut")
    args = ap.parse_args()

    d = load_set(args.set_id)
    base = f"http://localhost:{args.port}"
    py = sys.executable

    before = set(requests.get(base + "/status", timeout=10).json()["tracks"])
    t_fire = time.time() * 1000  # /errors is a rolling deque — only ours count

    # --- land on the grid --------------------------------------------------
    # Fire on a bar line, never mid-phrase. Costs at most one phrase of waiting.
    if args.at:
        try:
            sys.path.insert(0, str(ROOT / "assets/tools"))
            from boundary import wait_boundary
            wait_boundary(args.port, args.at)
        except Exception as e:
            print(f"(no clock yet — firing immediately: {e})")

    # --- music -------------------------------------------------------------
    kit_id, arc_id = d["music"]["kit"], d["music"]["arc"]
    subprocess.run([py, str(ROOT / "assets/tools/arc_compile.py"),
                    kit_id, arc_id, "--fire", "--port", str(args.port)], check=True)

    # --- visuals -----------------------------------------------------------
    for slot, spec in (d.get("visual") or {}).items():
        cmd = [py, str(ROOT / "assets/tools/fire_visual.py"), spec["asset"],
               "--slot", slot, "--port", str(args.port)]
        for k, v in (spec.get("params") or {}).items():
            cmd += ["--set", f"{k}={json.dumps(v)}"]
        subprocess.run(cmd, check=True)

    # --- orphan slots ------------------------------------------------------
    # arc_compile only fires the slots the INCOMING kit declares. Any track the
    # outgoing kit had that this one lacks keeps playing, in the old key — the
    # single most reliable way to turn a transition into a cacophony.
    if not args.no_orphan_clean:
        kit = json.loads((ROOT / f"assets/music/kits/{kit_id}.kit.json").read_text())
        orphans = sorted(before - set(kit["stems"]))
        if orphans and args.orphan_after:
            # let them ring to the end of a phrase — a slot yanked mid-bar is a seam
            try:
                sys.path.insert(0, str(ROOT / "assets/tools"))
                from boundary import wait_boundary
                wait_boundary(args.port, args.orphan_after, verbose=False)
            except Exception:
                pass
        for slot in orphans:
            requests.post(base + "/strudel/stop", json={"name": slot}, timeout=10)
        if orphans:
            print(f"stopped orphan slots: {', '.join(orphans)}")

    # --- verify ------------------------------------------------------------
    time.sleep(4)
    st = requests.get(base + "/status", timeout=10).json()
    errs = [e for e in requests.get(base + "/errors", timeout=10).json()["errors"]
            if e.get("ts", 0) >= t_fire]
    clk = requests.post(base + "/p5/send",
                        json={"code": "JSON.stringify(window.state.clk||{})"},
                        timeout=10).json()
    fps = "?"
    try:
        fps = round(json.loads(clk["response"]["result"]).get("fps", 0), 1)
    except Exception:
        pass
    print(f"\n{d['name']}: tracks={st['tracks']} layers={st['layers']} "
          f"cps={st['cps']} fps={fps} errors={len(errs)}")
    if not st["tracks"]:
        print("  WARNING: no tracks playing — transport may not be ready")
    if errs:
        print(f"  WARNING: {errs[-1]['message'][:90]}")


if __name__ == "__main__":
    main()
