#!/usr/bin/env python3
"""arc_compile.py — compile kit + arc into per-slot self-evolving arrange() code.

The heart of long-form generative dynamics: an arc is a section script
({cycles, label, slots:{slot: variant|off, "*": default}} per section); this
tool resolves each kit slot's stem, substitutes param defaults, and weaves the
chosen intensity variants into ONE arrange([cycles, seg]...) pattern per slot.
Patterns tile infinitely, so the whole multi-minute form repeats — the music
breathes with zero further commands. Also emits the visual handshake
(secBeats, per-section intensity array, t0 reset) per assets/CONTRACT.md.

Usage:
  python assets/tools/arc_compile.py <kit_id> <arc_id>                 # print
  python assets/tools/arc_compile.py <kit_id> <arc_id> --fire --port 9766
Library:
  from arc_compile import load_asset, compile_arc, fire
"""
import argparse
import json
import re
import string
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MUSIC = ROOT / "assets" / "music"
SLOT_ORDER = ["drums", "perc", "bass", "chords", "lead", "pad", "texture", "vox"]


def load_asset(aid):
    """Find a kit/arc/stem JSON by id anywhere under assets/music/."""
    pools = [MUSIC / "kits", MUSIC / "arcs", *(MUSIC / "stems").glob("*")]
    for pool in pools:
        for p in pool.glob("*.json"):
            try:
                d = json.loads(p.read_text())
            except Exception:
                continue
            if d.get("id") == aid:
                return d
    raise SystemExit(f"asset {aid!r} not found under assets/music/")


def compile_stem(stem, variant, overrides=None):
    """Substitute ${param} defaults (validate.py-compatible) into a variant."""
    vals = {k: v.get("default") for k, v in (stem.get("params") or {}).items()}
    if overrides:
        vals.update(overrides)
    return string.Template(stem["code"][variant]).safe_substitute(vals)


def strip_play(code):
    return re.sub(r"\.play\(\)\s*$", "", code.rstrip())


def compile_arc(kit, arc, stems=None):
    """-> (tracks {slot: code}, meta {cps, secBeats, intensities, total_cycles})."""
    stems = stems or {s: load_asset(sid) for s, sid in (kit.get("stems") or {}).items()}
    sections = arc["sections"]
    tracks = {}
    for slot, stem in stems.items():
        segs = []  # [(cycles, variant)] merged
        for sec in sections:
            v = (sec.get("slots") or {}).get(slot,
                (sec.get("slots") or {}).get("*", "full"))
            if segs and segs[-1][1] == v:
                segs[-1][0] += sec["cycles"]
            else:
                segs.append([sec["cycles"], v])
        if all(v == "off" for _, v in segs):
            continue
        parts = []
        for cycles, v in segs:
            body = "silence" if v == "off" else strip_play(compile_stem(stem, v))
            parts.append(f"[{cycles}, {body}]")
        tracks[slot] = "arrange(" + ", ".join(parts) + ").play()"
    meta = {
        "cps": kit.get("cps", 0.5),
        "secBeats": sections[0]["cycles"] * 4,
        "intensities": [s.get("intensity", 0.6) for s in sections],
        "total_cycles": sum(s["cycles"] for s in sections),
    }
    return tracks, meta


def fire(tracks, meta, deps, port):
    import requests
    base = f"http://localhost:{port}"
    packs = json.loads((MUSIC / "packs.json").read_text())
    for dep in sorted(deps):
        snippet = packs.get(dep)
        if isinstance(snippet, str):
            requests.post(base + "/strudel/send", json={"code": snippet}, timeout=15)
    if deps:
        time.sleep(2.5)
    # visual handshake: section clock tracks the musical arc by construction
    for key, value in (("secBeats", meta["secBeats"]),
                       ("arc", meta["intensities"]), ("t0", None)):
        requests.post(base + "/p5/state", json={"key": key, "value": value}, timeout=10)
    requests.post(base + "/strudel/cps", json={"cps": meta["cps"]}, timeout=10)
    for slot in sorted(tracks, key=SLOT_ORDER.index):
        requests.post(base + "/strudel/track",
                      json={"name": slot, "code": tracks[slot]}, timeout=15)
    dur = meta["total_cycles"] / meta["cps"]
    print(f"fired {len(tracks)} slots · {meta['total_cycles']} cycles ≈ {dur:.0f}s per pass · cps {meta['cps']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("kit_id")
    ap.add_argument("arc_id")
    ap.add_argument("--fire", action="store_true")
    ap.add_argument("--port", type=int, default=9766)
    args = ap.parse_args()
    kit, arc = load_asset(args.kit_id), load_asset(args.arc_id)
    stems = {s: load_asset(sid) for s, sid in (kit.get("stems") or {}).items()}
    tracks, meta = compile_arc(kit, arc, stems)
    if args.fire:
        deps = {d for s in stems.values() for d in (s.get("deps") or [])}
        fire(tracks, meta, deps, args.port)
    else:
        print(json.dumps({"meta": meta, "tracks": tracks}, indent=2))


if __name__ == "__main__":
    main()
