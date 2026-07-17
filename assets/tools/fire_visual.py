#!/usr/bin/env python
"""Fire a visual asset onto a slot: bind __SLOT__, push params, deploy layer.

  python scratchpad/fire_visual.py <asset_id_or_path> [--slot bg] [--port 9766]
                                   [--set energy=0.8 --set hue=200]

Params default to the asset's declared defaults; --set overrides. Sends params
BEFORE the layer so the first drawn frame already reads them.
"""
import argparse, glob, json, sys
import requests


def find_asset(ident):
    if ident.endswith(".json"):
        return ident
    hits = glob.glob(f"assets/visual/*/{ident}.json")
    if not hits:
        sys.exit(f"asset not found: {ident}")
    return hits[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("asset")
    ap.add_argument("--slot")
    ap.add_argument("--port", type=int, default=9766)
    ap.add_argument("--set", action="append", default=[], metavar="K=V")
    args = ap.parse_args()

    path = find_asset(args.asset)
    d = json.load(open(path))
    slot = args.slot or (d.get("slots") or ["bg"])[0]
    base = f"http://localhost:{args.port}"

    params = {k: v.get("default") for k, v in (d.get("params") or {}).items()}
    for kv in args.set:
        k, _, v = kv.partition("=")
        try:
            params[k] = json.loads(v)
        except json.JSONDecodeError:
            params[k] = v

    # Dispose the outgoing asset's private state first. Slot state is never cleared
    # on swap, so a new asset inherits the previous one's keys — leaking its
    # createGraphics buffers and crashing it outright on type collisions
    # (observed: genart.godrays reading a leftover array every frame).
    requests.post(base + "/p5/send", json={"code": (
        f"(function(){{var s=window.state.{slot}||{{}};"
        f"for(var k in s){{var v=s[k];if(v&&v.elt&&v.remove){{try{{v.remove()}}catch(e){{}}}}}}"
        f"window.state.{slot}={{}};}})()"
    )}, timeout=10)
    # window.state.P is never initialized by the engine — `state.P.<slot> = …`
    # throws on a fresh canvas, silently leaving the asset on its D defaults.
    requests.post(base + "/p5/send", json={"code": "window.state.P = window.state.P || {};"}, timeout=10)
    requests.post(base + "/p5/state", json={"key": f"P.{slot}", "value": params}, timeout=10)
    code = d["code"].replace("__SLOT__", slot)
    r = requests.post(base + "/p5/layer", json={"name": slot, "code": code}, timeout=15)
    print(f"{d['id']} -> slot {slot} [{r.status_code}] params={json.dumps(params)[:160]}")


if __name__ == "__main__":
    main()
