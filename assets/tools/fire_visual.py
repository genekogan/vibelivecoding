#!/usr/bin/env python
"""Fire a visual asset onto a slot: bind __SLOT__, push params, deploy layer.

  python scratchpad/fire_visual.py <asset_id_or_path> [--slot bg] [--port 9766]
                                   [--set energy=0.8 --set hue=200]
                                   [--bind hue=keyHue] [--bind auto]

Params default to the asset's declared defaults; --set overrides. Sends params
BEFORE the layer so the first drawn frame already reads them.

--bind attaches conductor bindings for the slot (features: keyHue, energy,
bpm, cps — see assets/CONTRACT.md). --bind auto maps hue→keyHue and
energy→energy for params the asset declares. Every fire RESETS the slot's
binds: no --bind means the slot is unbound.
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
    ap.add_argument("--bind", action="append", default=[], metavar="PARAM=FEATURE",
                    help="conductor binding (repeatable), or 'auto'")
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

    binds = {}
    for spec in args.bind:
        if spec == "auto":
            if "hue" in params:
                binds["hue"] = "keyHue"
            if "energy" in params:
                binds["energy"] = "energy"
            continue
        k, sep, feat = spec.partition("=")
        if not sep or not feat:
            sys.exit(f"--bind needs PARAM=FEATURE or 'auto' (got {spec!r})")
        binds[k] = feat
    # Seed a bound hue from the current key so the fired params JSON matches
    # what the binder will hold (the binder itself snaps on its first frame).
    # Skipped when --set hue was given explicitly — manual wins at fire time.
    if binds.get("hue") == "keyHue" and not any(kv.startswith("hue=") for kv in args.set):
        try:
            score = requests.get(base + "/conductor", timeout=5).json().get("score") or {}
            key = score.get("key")
            if key and isinstance(key.get("pc"), int):
                params["hue"] = ((key["pc"] * 7) % 12) * 30  # CONTRACT.md keyHue formula
        except Exception:
            pass

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
    # Only bg-slot assets call background(); every other slot assumes something
    # below it clears the frame. Firing a subject/set/fx onto an empty canvas
    # therefore SMEARS (each frame paints over the last). If nothing holds the
    # bg slot yet, drop in a near-black clear so motion stays crisp.
    if slot != "bg":
        st = requests.get(base + "/status", timeout=10).json()
        if "bg" not in (st.get("layers") or []):
            requests.post(base + "/p5/layer", json={
                "name": "bg", "code": "background(232,25,10);"}, timeout=10)
    requests.post(base + "/p5/state", json={"key": f"P.{slot}", "value": params}, timeout=10)
    # Binds are per-fire ownership: always push (empty {} un-binds the slot).
    requests.post(base + "/p5/state", json={"key": f"binds.{slot}", "value": binds}, timeout=10)
    code = d["code"].replace("__SLOT__", slot)
    r = requests.post(base + "/p5/layer", json={"name": slot, "code": code}, timeout=15)
    bind_note = f" binds={json.dumps(binds)}" if binds else ""
    print(f"{d['id']} -> slot {slot} [{r.status_code}] params={json.dumps(params)[:160]}{bind_note}")


if __name__ == "__main__":
    main()
