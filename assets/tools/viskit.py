#!/usr/bin/env python3
"""Visual KIT — a layered composition of catalog visual components, parameterized
together. The visual analog of a music kit (kit:stems :: viskit:components).

A viskit binds component-ids to slots and carries a `shared` param block whose
keys (hue/energy/speed/scale/density/…) fan out to EVERY layer whose component
declares that param — so one dial moves the whole scene. Per-layer `params`
override the shared value.

  python assets/tools/viskit.py play  <id|path> [--port 8766] [--set hue=200 ...]
  python assets/tools/viskit.py list
  python assets/tools/viskit.py show  <id|path>

Kits live in assets/visual/kits/<id>.viskit.json  (format livecode-viskit-v1).
`--set` on play overrides the kit's shared block at fire time (live tweak).
"""
import argparse, glob, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KITDIR = os.path.join(ROOT, "assets", "visual", "kits")
FIRE = os.path.join(ROOT, "assets", "tools", "fire_visual.py")

def find_kit(ident):
    if ident.endswith(".json") and os.path.exists(ident): return ident
    p = os.path.join(KITDIR, f"{ident}.viskit.json")
    if os.path.exists(p): return p
    p2 = os.path.join(KITDIR, f"kit.{ident}.viskit.json")
    if os.path.exists(p2): return p2
    sys.exit(f"viskit not found: {ident}")

def component_path(cid):
    hits = glob.glob(os.path.join(ROOT, "assets", "visual", "*", f"{cid}.json"))
    if not hits: sys.exit(f"component not found: {cid}")
    return hits[0]

def component_params(cid):
    d = json.load(open(component_path(cid)))
    return set((d.get("params") or {}).keys())

def play(ident, port, overrides, over=False):
    import requests
    doc = json.load(open(find_kit(ident)))
    if not over:
        try: requests.post(f"http://localhost:{port}/p5/clear", json={}, timeout=3)
        except Exception: pass
    shared = dict(doc.get("shared", {})); shared.update(overrides)
    print(f"▶ {doc.get('id')} — {doc.get('name','')}  ({len(doc['layers'])} layers)")
    for L in doc["layers"]:
        cid, slot = L["component"], L["slot"]
        decl = component_params(cid)
        params = {k: v for k, v in shared.items() if k in decl}   # fan-out
        params.update(L.get("params", {}))                        # per-layer wins
        cmd = ["python3", FIRE, cid, "--slot", slot, "--port", str(port)]
        for k, v in params.items():
            cmd += ["--set", f"{k}={json.dumps(v) if not isinstance(v,str) else v}"]
        subprocess.run(cmd, cwd=ROOT, check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  · {slot:6} ← {cid:26} {params}")

def show(ident):
    doc = json.load(open(find_kit(ident)))
    print(json.dumps(doc, indent=1))

def ls():
    for p in sorted(glob.glob(os.path.join(KITDIR, "*.viskit.json"))):
        d = json.load(open(p))
        print(f"{d['id']:22} {len(d['layers'])}L  {d.get('name','')}  · {d.get('desc','')[:60]}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("play"); p.add_argument("id"); p.add_argument("--port", type=int, default=8766); p.add_argument("--set", action="append", default=[]); p.add_argument("--over", action="store_true", help="layer over current scene instead of clearing first")
    sub.add_parser("list")
    s = sub.add_parser("show"); s.add_argument("id")
    a = ap.parse_args()
    if a.cmd == "play":
        ov = {}
        for kv in a.set:
            k,_,v = kv.partition("="); 
            try: ov[k] = json.loads(v)
            except: ov[k] = v
        play(a.id, a.port, ov, a.over)
    elif a.cmd == "list": ls()
    elif a.cmd == "show": show(a.id)
