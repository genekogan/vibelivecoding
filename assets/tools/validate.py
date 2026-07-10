#!/usr/bin/env python3
"""validate.py — mechanical validation gate for the livecode asset catalog.

Deploys each asset against the LIVE livecode server (browser must be connected;
a Playwright host must be writing canvas snapshots) and enforces the gates in
assets/CONTRACT.md: schema, clean deploy, /errors delta, fps, motion/luminance,
param responsiveness (visual); schema, all-variant deploy, audibility via
audio.rms (music stems); stem resolution + combined audibility (kits).

Usage:
    python assets/tools/validate.py [--port 8766] [--snapshots autopilot/snapshots] PATH...
    python assets/tools/validate.py --inbox visual      # everything in assets/visual/inbox/
    python assets/tools/validate.py --inbox music       # everything in assets/music/inbox/

Passing assets get a `verified` stamp written into the JSON and, when sitting
in an inbox/, are moved to their catalog directory. Failing assets get a
`last_fail` field and stay in the inbox. Exit code 1 if any asset FAILs.
"""

import argparse
import json
import re
import string
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"

KIND_SLOTS = {
    "world": ["bg"], "floor": ["floor"], "set": ["setA", "setB"],
    "subject": ["subA", "subB", "subC"], "crowd": ["crowd"],
    "fx": ["fxA", "fxB"], "post": ["post"], "genart": ["bg"], "palette": [],
}
KIND_DIR = {  # kind -> catalog directory under assets/visual/
    "world": "worlds", "floor": "floors", "set": "sets", "subject": "subjects",
    "crowd": "crowds", "fx": "fx", "post": "post", "genart": "genart", "palette": "palettes",
}
SLOT_ORBIT = {"drums": 1, "perc": 2, "bass": 3, "chords": 4,
              "lead": 5, "pad": 6, "texture": 7, "vox": 8}
SLOT_ORDER = list(SLOT_ORBIT)  # drums first — kit firing order
BANNED_STEM = [".cps(", "gm_", "setcps", ".swingBy"]


class Gate(Exception):
    """A named validation gate failed."""
    def __init__(self, gate, detail):
        super().__init__(f"{gate}: {detail}")
        self.gate, self.detail = gate, detail


class Server:
    def __init__(self, port):
        self.base = f"http://localhost:{port}"

    def get(self, path):
        r = requests.get(self.base + path, timeout=10)
        r.raise_for_status()
        return r.json()

    def post(self, path, body=None):
        r = requests.post(self.base + path, json=body or {}, timeout=15)
        r.raise_for_status()
        return r.json() if r.content else {}

    def errors(self):
        return self.get("/errors")["errors"]

    def read(self, key):
        d = self.get(f"/p5/read?key={key}")
        if not d.get("ok"):
            raise Gate("read", f"/p5/read?key={key} failed: {d.get('error')}")
        return d["value"]

    def peak_rms(self, seconds):
        """Poll audio.rms over a window and return the peak (patterns have gaps —
        a single point-sample between notes reads 0 even for audible stems)."""
        peak, deadline = 0.0, time.time() + seconds
        while time.time() < deadline:
            peak = max(peak, self.read("audio").get("rms", 0))
            time.sleep(0.2)
        return peak


# ── snapshot helpers ─────────────────────────────────────────────────────────

def grab(snaps_dir):
    """Load latest.png as a 320px-wide grayscale image (fully decoded copy)."""
    p = Path(snaps_dir) / "latest.png"
    for attempt in range(3):
        try:
            with Image.open(p) as im:
                im = im.convert("L")
                w, h = im.size
                return im.resize((320, max(1, round(h * 320 / w))))
        except Exception:
            if attempt == 2:
                raise Gate("snapshot", f"cannot read {p}")
            time.sleep(1)


def mean_diff(a, b):
    if b.size != a.size:
        b = b.resize(a.size)
    hist = ImageChops.difference(a, b).histogram()
    n = a.size[0] * a.size[1]
    return sum(i * c for i, c in enumerate(hist)) / n / 255.0


def mean_lum(img):
    hist = img.histogram()
    return sum(i * c for i, c in enumerate(hist)) / (img.size[0] * img.size[1]) / 255.0


# ── visual validation ────────────────────────────────────────────────────────

def check_visual_schema(a):
    kind = a.get("kind")
    if kind not in KIND_SLOTS:
        raise Gate("schema", f"kind {kind!r} not in {sorted(KIND_SLOTS)}")
    if not re.fullmatch(re.escape(kind) + r"\.[a-z0-9_.]+", a.get("id", "")):
        raise Gate("schema", f"id {a.get('id')!r} must match {kind}.<slug>")
    if kind == "palette":
        if not isinstance(a.get("values"), dict) or not a["values"]:
            raise Gate("schema", "palette asset needs a non-empty 'values' object")
        return
    for f in ("name", "desc", "tags", "code", "slots", "params"):
        if not a.get(f) and a.get(f) != {}:
            raise Gate("schema", f"missing/empty field {f!r}")
    bad = [s for s in a["slots"] if s not in KIND_SLOTS[kind]]
    if bad:
        raise Gate("schema", f"slots {bad} illegal for kind {kind} (legal: {KIND_SLOTS[kind]})")
    for k, v in a.get("params", {}).items():
        if not isinstance(v, dict) or "default" not in v:
            raise Gate("schema", f"param {k!r} has no default")
    code = a["code"]
    if "__SLOT__" not in code or "window.state.clk" not in code:
        raise Gate("schema", "code missing P-block markers (__SLOT__ / window.state.clk)")
    if re.search(r"frameCount\s*/\s*\d", code):
        raise Gate("schema", "frameCount-based beat math is banned — derive rhythm from clk")
    for banned in ("createCanvas", "setcps"):
        if banned in code:
            raise Gate("schema", f"code contains banned call {banned!r}")


def validate_visual(a, srv, snaps):
    check_visual_schema(a)
    if a["kind"] == "palette":
        return {"at": now_iso()}, "palette schema-only"
    slot = a["slots"][0]
    bed = a["kind"] not in ("world", "genart")
    err0 = len(srv.errors())
    try:
        if bed:
            srv.post("/p5/layer", {"name": "bg", "code": "background(240,30,12);"})
        srv.post("/p5/layer", {"name": slot, "code": a["code"].replace("__SLOT__", slot)})
        time.sleep(2)
        delta = srv.errors()[err0:]
        hits = [e for e in delta if f"[{slot}]" in e.get("message", "")
                or f'"{slot}"' in e.get("message", "")]
        if hits:
            raise Gate("errors", hits[0]["message"][:160])
        fps = srv.read("clk").get("fps", 0)
        if fps < 25:
            raise Gate("fps", f"{fps:.1f} < 25")
        img_a = grab(snaps)
        time.sleep(8)
        img_b = grab(snaps)
        motion = mean_diff(img_a, img_b)
        if motion <= 0.004:
            raise Gate("motion", f"static: diff {motion:.4f} <= 0.004")
        if motion >= 0.35:
            raise Gate("motion", f"strobing: diff {motion:.4f} >= 0.35")
        lum = mean_lum(img_b)
        if not (0.02 <= lum <= 0.92):
            raise Gate("luminance", f"{lum:.3f} outside [0.02, 0.92]")
        numeric = [(k, v) for k, v in a["params"].items()
                   if isinstance(v["default"], (int, float))
                   and not isinstance(v["default"], bool)][:2]
        if numeric:
            poke = {k: v.get("max", v["default"] * 2 or 1) for k, v in numeric}
            srv.post("/p5/state", {"key": f"P.{slot}", "value": poke})
            time.sleep(4)
            pdiff = mean_diff(img_b, grab(snaps))
            srv.post("/p5/state", {"key": f"P.{slot}", "value": None})
            if pdiff <= 0.003:
                raise Gate("params", f"poke {list(poke)} changed output by only {pdiff:.4f}")
        return ({"at": now_iso(), "fps": round(fps, 1),
                 "motion": round(motion, 4), "lum": round(lum, 3)},
                f"fps={fps:.1f}, motion={motion:.4f}")
    finally:
        srv.post("/p5/remove", {"name": slot})
        if bed:
            srv.post("/p5/remove", {"name": "bg"})
        srv.post("/p5/state", {"key": slot, "value": None})
        srv.post("/p5/state", {"key": f"P.{slot}", "value": None})


# ── music validation ─────────────────────────────────────────────────────────

def compile_stem(a, variant):
    defaults = {k: v.get("default") for k, v in a.get("params", {}).items()}
    return string.Template(a["code"][variant]).safe_substitute(defaults)


def check_stem_schema(a):
    slot = a.get("slot")
    if slot not in SLOT_ORBIT:
        raise Gate("schema", f"slot {slot!r} not in {SLOT_ORDER}")
    if a.get("orbit") != SLOT_ORBIT[slot]:
        raise Gate("schema", f"orbit {a.get('orbit')} != {SLOT_ORBIT[slot]} for slot {slot}")
    cps = a.get("cps") or {}
    if not all(k in cps for k in ("written", "min", "max")):
        raise Gate("schema", "cps must declare written/min/max")
    code = a.get("code") or {}
    for variant in ("sparse", "full", "peak"):
        if variant not in code:
            raise Gate("schema", f"missing code variant {variant!r}")
        compiled = compile_stem(a, variant)
        if not compiled.rstrip().endswith(".play()"):
            raise Gate("schema", f"{variant} does not end with .play()")
        if f".orbit({a['orbit']})" not in compiled:
            raise Gate("schema", f"{variant} missing .orbit({a['orbit']})")
        for banned in BANNED_STEM:
            if banned in compiled:
                raise Gate("schema", f"{variant} contains banned {banned!r}")


def load_deps(srv, deps):
    if not deps:
        return
    packs_file = ASSETS / "music" / "packs.json"
    if not packs_file.exists():
        raise Gate("deps", f"deps {deps} declared but {packs_file} does not exist")
    packs = json.loads(packs_file.read_text())
    for dep in deps:
        if dep not in packs:
            raise Gate("deps", f"pack {dep!r} not in packs.json")
        srv.post("/strudel/send", {"code": packs[dep]})
    time.sleep(2.5)


def validate_stem(a, srv):
    check_stem_schema(a)
    slot = a["slot"]
    err0 = len(srv.errors())
    cps0 = srv.get("/status")["cps"]
    rms_by_variant = {}
    try:
        load_deps(srv, a.get("deps") or [])
        srv.post("/strudel/cps", {"cps": a["cps"]["written"]})
        for variant in ("full", "peak", "sparse"):
            srv.post("/strudel/track", {"name": slot, "code": compile_stem(a, variant)})
            rms = srv.peak_rms(2.5)
            if slot not in srv.get("/status")["tracks"]:
                raise Gate("deploy", f"{variant}: track {slot!r} not in /status tracks")
            strudel_errs = [e for e in srv.errors()[err0:] if e.get("system") == "strudel"]
            if strudel_errs:
                raise Gate("errors", f"{variant}: {strudel_errs[0]['message'][:160]}")
            rms_by_variant[variant] = round(rms, 4)
            floor = 0.003 if variant == "sparse" else 0.01
            if rms <= floor:
                raise Gate("audible", f"{variant}: rms {rms:.4f} <= {floor}")
        return ({"at": now_iso(), "rms": rms_by_variant},
                f"rms full={rms_by_variant['full']}, sparse={rms_by_variant['sparse']}")
    finally:
        srv.post("/strudel/stop", {"name": slot})
        srv.post("/strudel/cps", {"cps": cps0})


def resolve_stem(stem_id):
    for p in (ASSETS / "music" / "stems").glob("*/*.json"):
        d = json.loads(p.read_text())
        if d.get("id") == stem_id:
            return d
    return None


def validate_kit(a, srv):
    stems = {}
    for slot, stem_id in (a.get("stems") or {}).items():
        stem = resolve_stem(stem_id)
        if stem is None:
            raise Gate("stems", f"stem {stem_id!r} not found under assets/music/stems/")
        if not stem.get("verified"):
            raise Gate("stems", f"stem {stem_id!r} is not verified")
        w = stem["cps"]
        if not (w["min"] <= a["cps"] <= w["max"]):
            raise Gate("cps", f"kit cps {a['cps']} outside {stem_id} window [{w['min']}, {w['max']}]")
        stems[slot] = stem
    if not stems:
        raise Gate("schema", "kit declares no stems")
    kit_key = a.get("key") or {}
    for slot, stem in stems.items():
        sk = stem.get("key") or {}
        if kit_key and sk and sk.get("mode") != kit_key.get("mode"):
            print(f"  warn: {stem['id']} mode {sk.get('mode')} != kit mode {kit_key.get('mode')}")
    err0 = len(srv.errors())
    cps0 = srv.get("/status")["cps"]
    fired = []
    try:
        deps = sorted({d for s in stems.values() for d in (s.get("deps") or [])})
        load_deps(srv, deps)
        srv.post("/strudel/cps", {"cps": a["cps"]})
        for slot in sorted(stems, key=SLOT_ORDER.index):
            srv.post("/strudel/track", {"name": slot, "code": compile_stem(stems[slot], "full")})
            fired.append(slot)
        rms = srv.peak_rms(3)
        strudel_errs = [e for e in srv.errors()[err0:] if e.get("system") == "strudel"]
        if strudel_errs:
            raise Gate("errors", strudel_errs[0]["message"][:160])
        if rms <= 0.02:
            raise Gate("audible", f"combined rms {rms:.4f} <= 0.02")
        return {"at": now_iso(), "rms": round(rms, 4)}, f"rms={rms:.4f}"
    finally:
        for slot in fired:
            srv.post("/strudel/stop", {"name": slot})
        srv.post("/strudel/cps", {"cps": cps0})


# ── plumbing ─────────────────────────────────────────────────────────────────

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def dest_for(path, a):
    fmt = a["format"]
    if fmt == "livecode-visual-v1":
        return ASSETS / "visual" / KIND_DIR[a["kind"]] / f"{a['id']}.json"
    if fmt == "livecode-stem-v1":
        return ASSETS / "music" / "stems" / a["slot"] / f"{a['id']}.json"
    return ASSETS / "music" / "kits" / path.name


def write_asset(path, a):
    path.write_text(json.dumps(a, indent=2) + "\n")


def validate_file(path, srv, snaps):
    """Returns True on pass. Prints the result line; stamps/moves the file."""
    try:
        a = json.loads(path.read_text())
    except Exception as e:
        print(f"FAIL {path.name}: parse: {e}")
        return False
    aid = a.get("id", path.stem)
    try:
        fmt = a.get("format")
        if fmt == "livecode-visual-v1":
            verified, detail = validate_visual(a, srv, snaps)
        elif fmt == "livecode-stem-v1":
            verified, detail = validate_stem(a, srv)
        elif fmt == "livecode-kit-v1":
            verified, detail = validate_kit(a, srv)
        else:
            raise Gate("schema", f"unknown format {fmt!r}")
    except Gate as g:
        print(f"FAIL {aid}: {g.gate}: {g.detail}")
        a["last_fail"] = {"at": now_iso(), "gate": g.gate, "detail": str(g.detail)}
        write_asset(path, a)
        return False
    a["verified"] = verified
    a.pop("last_fail", None)
    write_asset(path, a)
    if "inbox" in path.parts:
        dest = dest_for(path, a)
        dest.parent.mkdir(parents=True, exist_ok=True)
        path.rename(dest)
    print(f"PASS {aid} ({detail})")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", type=Path, help="asset JSON file(s)")
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--snapshots", default=str(ROOT / "autopilot" / "snapshots"))
    ap.add_argument("--inbox", choices=["visual", "music"],
                    help="validate everything in assets/<domain>/inbox/")
    args = ap.parse_args()

    paths = list(args.paths)
    if args.inbox:
        paths += sorted((ASSETS / args.inbox / "inbox").glob("*.json"))
    if not paths:
        ap.error("no asset files given (pass PATHs or --inbox)")
    snaps = Path(args.snapshots)
    if not snaps.is_absolute() and not snaps.exists():
        snaps = ROOT / args.snapshots

    srv = Server(args.port)
    try:
        status = srv.get("/status")
    except Exception as e:
        sys.exit(f"error: livecode server unreachable on port {args.port}: {e}")
    if not status.get("ready"):
        sys.exit("error: server up but no browser connected (/status ready=false) — "
                 "open livecode.html or start autopilot_host.py")
    srv.post("/show/recording", {"enabled": False})

    failed = 0
    for p in paths:
        if not p.exists():
            print(f"FAIL {p}: missing: file not found")
            failed += 1
            continue
        if not validate_file(p, srv, snaps):
            failed += 1
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
