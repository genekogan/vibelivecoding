#!/usr/bin/env python
"""Save the currently-playing set so it can be replayed later.

  python assets/tools/set_save.py mechanism --name "Mechanism" \
      --kit kit.idm_braindance --arc arc.tide \
      --bg genart.epicycles --bg-params '{"style":"spectral-glow","energy":0.55}' \
      --desc "Minimalist clockwork interlude." --note "sits before the peak" \
      --grade loved --port 9976

Why the kit/arc must be passed explicitly: the server only knows the compiled
Strudel code that is playing, not which kit x arc produced it. The performing
agent knows, so it says so. Key/cps/duration are read back from the kit+arc.

  --list   show saved sets
"""
import argparse, glob, json, sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
SETS = ROOT / "assets" / "sets"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("set_id", nargs="?")
    ap.add_argument("--name")
    ap.add_argument("--kit")
    ap.add_argument("--arc")
    ap.add_argument("--bg")
    ap.add_argument("--bg-params", default="{}")
    ap.add_argument("--fx")
    ap.add_argument("--fx-params", default="{}")
    ap.add_argument("--desc", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--tags", default="", help="comma-separated")
    ap.add_argument("--grade", default="ok", choices=["ok", "good", "loved"])
    ap.add_argument("--port", type=int, default=9766)
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list or not args.set_id:
        rows = []
        for p in sorted(SETS.glob("set.*.json")):
            d = json.loads(p.read_text())
            rows.append((d["id"], d.get("grade", ""), d["music"]["kit"],
                         d["music"]["arc"], d.get("name", "")))
        if not rows:
            print("no saved sets yet")
            return
        print(f"{len(rows)} saved set(s):")
        for r in rows:
            print("  %-22s %-6s %-24s %-18s %s" % r)
        return

    for req in ("name", "kit", "arc"):
        if not getattr(args, req):
            sys.exit(f"--{req} is required when saving")

    sid = args.set_id if args.set_id.startswith("set.") else f"set.{args.set_id}"
    kit = json.loads((ROOT / f"assets/music/kits/{args.kit}.kit.json").read_text())

    # duration: ask arc_compile what this pairing actually runs to
    sys.path.insert(0, str(ROOT / "assets/tools"))
    from arc_compile import compile_arc
    stems = {}
    for p in glob.glob(str(ROOT / "assets/music/stems/*/*.json")):
        s = json.loads(Path(p).read_text())
        stems[s["id"]] = s
    arc = json.loads((ROOT / f"assets/music/arcs/{args.arc}.arc.json").read_text())
    _, meta = compile_arc(kit, arc, stems)

    visual = {}
    if args.bg:
        visual["bg"] = {"asset": args.bg, "params": json.loads(args.bg_params)}
    if args.fx:
        visual["fxA"] = {"asset": args.fx, "params": json.loads(args.fx_params)}

    doc = {
        "format": "livecode-set-v1",
        "id": sid,
        "name": args.name,
        "desc": args.desc,
        "tags": [t.strip() for t in args.tags.split(",") if t.strip()],
        "music": {"kit": args.kit, "arc": args.arc},
        "visual": visual,
        "key": kit["key"],
        "cps": meta["cps"],
        "duration_s": round(meta["total_cycles"] / meta["cps"]),
        "grade": args.grade,
        "notes": args.note,
    }

    # best-effort: record what the canvas was actually doing when saved
    try:
        st = requests.get(f"http://localhost:{args.port}/status", timeout=5).json()
        doc["captured"] = {"tracks": st["tracks"], "layers": st["layers"]}
    except Exception:
        pass

    SETS.mkdir(exist_ok=True)
    out = SETS / f"{sid}.json"
    out.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"saved {out.relative_to(ROOT)}  ({doc['duration_s']}s/pass, "
          f"{doc['key']['root']} {doc['key']['mode']}, cps {doc['cps']})")
    print(f"replay: python assets/tools/set_play.py {sid} --port {args.port}")


if __name__ == "__main__":
    main()
