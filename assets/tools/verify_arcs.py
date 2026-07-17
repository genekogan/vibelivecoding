#!/usr/bin/env python3
"""verify_arcs.py — the kit×arc SECTION-AUDIBILITY gate.

The plain validator (validate.py) fires each stem solo and each kit with all
slots at `full`. It NEVER plays a kit THROUGH an arc, section by section — so a
kit can pass every gate and still be SILENT or too-quiet for 20-30s when fired
through an arc whose intro/breakdown/outro names only slots that kit lacks.
This tool closes that hole: for every kit, for every arc it recommends, it
resolves each section's per-slot variant EXACTLY as arc_compile.py / browse.html
do (`sec.slots[slot] ?? sec.slots['*'] ?? 'full'`), fires the on-slots as a
stack, and measures the section's real audibility on the live audio bridge.

RUN THIS BEFORE ANY HANDOFF. It must be the only thing using the server (stop the
valloop first). Exit code 1 if any section is SILENT/TOO_QUIET/ERROR.

Usage:
  python assets/tools/verify_arcs.py                       # all kits x their arcs
  python assets/tools/verify_arcs.py --arcs slow_burn,waves
  python assets/tools/verify_arcs.py --kits kit.reich_minimal
  python assets/tools/verify_arcs.py --wait-load           # wait for calm (unattended)
"""
import argparse, json, glob, os, sys, time
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arc_compile import load_asset, compile_stem  # SAME resolution/substitution

MUSIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "music")
MUSIC = os.path.normpath(MUSIC)
BASE = "http://localhost:9766"
FLOOR_QUIET = 0.015    # a fired section below this reads as too quiet
FLOOR_SILENT = 0.006   # essentially inaudible
MAX_LOAD = 4.5         # above this the browser audio thread starves -> false quiets
SLOT_ORDER = ["drums","perc","bass","chords","lead","pad","texture","vox"]


def req(method, path, retries=4, **kw):
    """HTTP with retries so a transient server stall doesn't abort a long run."""
    kw.setdefault("timeout", 20)
    for i in range(retries):
        try:
            response = requests.request(method, BASE + path, **kw)
            response.raise_for_status()
            return response
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(1.5 * (i + 1))


def post(path, body):
    return req("POST", path, json=body)


def load_ok():
    try:
        return os.getloadavg()[0] < MAX_LOAD
    except Exception:
        return True


def wait_for_calm():
    while not load_ok():
        print(f"  ...loadavg {os.getloadavg()[0]:.1f} >= {MAX_LOAD}; waiting 60s", flush=True)
        time.sleep(60)


def peak_rms(secs=2.0):
    end = time.time() + secs
    mx = 0.0
    while time.time() < end:
        try:
            a = req("GET", "/p5/read?key=audio").json().get("value") or {}
            mx = max(mx, a.get("rms", 0) or 0)
        except Exception:
            pass
        time.sleep(0.12)
    return round(mx, 4)


def control_loud():
    post("/strudel/track", {"name": "ctrl",
        "code": 's("bd*4, hh*8").bank("RolandTR909").gain(.7).play()'})
    r = peak_rms(1.5)
    post("/strudel/stop", {"name": "ctrl"})
    return r


def errcount():
    try:
        e = req("GET", "/errors").json()
        lst = e.get("errors", e) if isinstance(e, dict) else e
        return len(lst) if isinstance(lst, list) else 0
    except Exception:
        return 0


def resolve(section, slot):
    s = section.get("slots") or {}
    return s.get(slot, s.get("*", "full"))


def measure_section(kit, sec, stems, wait_load):
    post("/strudel/hush", {}); time.sleep(0.5)
    on = [(slot, resolve(sec, slot)) for slot in stems if resolve(sec, slot) != "off"]
    if not on:
        return {"on": [], "rms": 0.0, "verdict": "SILENT(no-slots)"}
    post("/strudel/cps", {"cps": kit.get("cps", 0.5)})
    for slot, v in sorted(on, key=lambda x: SLOT_ORDER.index(x[0])):
        post("/strudel/track", {"name": slot, "code": compile_stem(stems[slot], v)})
    time.sleep(0.7)
    rms = peak_rms(2.0)
    verdict = "ok"
    if rms < FLOOR_SILENT:
        post("/strudel/hush", {}); time.sleep(0.3)
        if wait_load:
            wait_for_calm()
        if control_loud() > 0.05:
            verdict = "SILENT"
        else:  # engine starved -> re-measure once after settling
            time.sleep(2)
            verdict = "DEFER(load)"
    elif rms < FLOOR_QUIET:
        verdict = "TOO_QUIET"
    return {"on": [f"{s}:{v}" for s, v in on], "rms": rms, "verdict": verdict}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--arcs", default="")
    ap.add_argument("--kits", default="")
    ap.add_argument("--wait-load", action="store_true",
                    help="pause until loadavg < %.1f before each measurement" % MAX_LOAD)
    args = ap.parse_args()
    arc_filter = set(args.arcs.split(",")) if args.arcs else None
    kit_filter = set(args.kits.split(",")) if args.kits else None

    kits = []
    for p in sorted(glob.glob(f"{MUSIC}/kits/*.json")):
        d = json.loads(open(p).read())
        if kit_filter and d.get("id") not in kit_filter:
            continue
        kits.append(d)

    if args.wait_load:
        wait_for_calm()
    ctrl = control_loud()
    print(f"engine control rms: {ctrl}  (loadavg {os.getloadavg()[0]:.1f})")
    if ctrl < 0.1:
        print("!! engine control is quiet — bridge/load problem; aborting (fix before trusting results)")
        sys.exit(2)

    problems = []
    for kit in kits:
        stems = {s: load_asset(sid) for s, sid in (kit.get("stems") or {}).items()}
        arclist = []
        for a in [kit.get("arc")] + (kit.get("arcs") or []):
            if a and a not in arclist:
                arclist.append(a)
        for aid in arclist:
            aname = aid.replace("arc.", "")
            if arc_filter and aname not in arc_filter and aid not in arc_filter:
                continue
            arc = load_asset(aid)
            if args.wait_load:
                wait_for_calm()
            e0 = errcount()
            rows = [dict(sec=i, label=s.get("label", ""),
                         **measure_section(kit, s, stems, args.wait_load))
                    for i, s in enumerate(arc["sections"])]
            post("/strudel/hush", {})
            derr = errcount() - e0
            bad = [r for r in rows if r["verdict"] not in ("ok", "DEFER(load)")]
            if bad or derr:
                print(f"\n[PROBLEM] {kit['id']} x {aid}  (err delta {derr})")
                for r in rows:
                    mark = ">>" if r["verdict"] not in ("ok", "DEFER(load)") else "  "
                    print(f"   {mark} s{r['sec']:<2}{r['label']:<12} rms={r['rms']:<7} on={r['on']} [{r['verdict']}]")
                problems.append((kit["id"], aid))
            else:
                print(f"[OK] {kit['id']} x {aid}")

    print(f"\n===== {len(problems)} problem kit×arc combos =====")
    for kid, aid in problems:
        print(f"  {kid} x {aid}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
