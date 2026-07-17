#!/usr/bin/env python3
"""review.py — keyboard grading interface for the livecode asset catalog.

Usage: python assets/tools/review.py [visual|music] [--port 8766] [--all]

Deploys each asset to the live server (Gene watches the canvas / listens),
one at a time. By default only ungraded assets; --all includes graded ones.

Keys:  1-5 grade & advance · space/right skip · left back
       v cycle variant (music stems) · n type a note · q quit

Grades append to assets/review.jsonl: {"ts","id","grade","note"}.
Requires a fresh index — run assets/tools/build_index.py first.
"""
import argparse
import json
import select
import string
import sys
import termios
import time
import tty
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"
REVIEW = ASSETS / "review.jsonl"

BED_CODE = "background(240,30,12);"
VARIANTS = ["sparse", "full", "peak"]
DEFAULT_SLOT = {"world": "bg", "genart": "bg", "floor": "floor", "set": "setA",
                "subject": "subA", "crowd": "crowd", "fx": "fxA", "post": "post"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Server:
    def __init__(self, port):
        self.base = f"http://localhost:{port}"

    def _call(self, method, route, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + route, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=6) as r:
            return json.loads(r.read().decode() or "{}")

    def get(self, route):
        return self._call("GET", route)

    def post(self, route, **body):
        return self._call("POST", route, body)


def load_grades():
    """id -> latest non-null grade from review.jsonl."""
    grades = {}
    if REVIEW.exists():
        for line in REVIEW.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if isinstance(e, dict) and e.get("id") and e.get("grade") is not None:
                grades[e["id"]] = e["grade"]
    return grades


def append_review(entry):
    with open(REVIEW, "a") as f:
        f.write(json.dumps(entry, separators=(",", ":"), ensure_ascii=False) + "\n")


def load_index(domain):
    p = ASSETS / domain / "index.jsonl"
    if not p.exists():
        sys.exit(f"No index at {p.relative_to(ROOT)} — run: "
                 f"python assets/tools/build_index.py {domain}")
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def load_asset(entry):
    p = ROOT / entry["path"]
    if not p.exists():
        raise RuntimeError(f"file {entry['path']} missing — stale index? re-run build_index.py")
    return json.loads(p.read_text())


class VisualReviewer:
    def __init__(self, srv, index_by_id):
        self.srv = srv
        self.deployed = None
        self.bed = False

    def deploy(self, asset):
        kind = asset.get("kind")
        if kind == "palette":
            return "palette (no deploy): " + json.dumps(asset.get("values", {}))
        code = asset.get("code")
        if not isinstance(code, str):
            raise RuntimeError(f"kind '{kind}' has no deployable code")
        slot = (asset.get("slots") or [DEFAULT_SLOT.get(kind, "setA")])[0]
        if kind in ("world", "genart"):
            self.bed = False  # they claim bg themselves
        elif not self.bed:
            self.srv.post("/p5/layer", name="bg", code=BED_CODE)
            self.bed = True
        self.srv.post("/p5/layer", name=slot, code=code.replace("__SLOT__", slot))
        self.deployed = slot
        return f"deployed -> layer '{slot}'"

    def cleanup(self):
        if self.deployed:
            try:
                self.srv.post("/p5/remove", name=self.deployed)
                self.srv.post("/p5/state", key=self.deployed, value=None)
            except Exception:
                pass
            if self.deployed == "bg":
                self.bed = False
            self.deployed = None

    def shutdown(self):
        self.cleanup()
        if self.bed:
            try:
                self.srv.post("/p5/remove", name="bg")
            except Exception:
                pass
            self.bed = False

    def cycle(self):
        return "variant cycling is music-only"


class MusicReviewer:
    def __init__(self, srv, index_by_id):
        self.srv = srv
        self.index = index_by_id
        self.tracks = []
        self.current = None
        self.variant = "full"
        self.loaded_packs = set()
        try:
            self.packs = json.loads((ASSETS / "music" / "packs.json").read_text())
        except (OSError, ValueError):
            self.packs = {}

    def _load_deps(self, deps):
        todo = [d for d in dict.fromkeys(deps or []) if d not in self.loaded_packs]
        missing = [d for d in todo if d not in self.packs]
        if missing:
            raise RuntimeError(f"unknown pack(s) {missing} — not in assets/music/packs.json")
        for d in todo:
            self.srv.post("/strudel/send", code=self.packs[d])
            self.loaded_packs.add(d)
        if todo:
            time.sleep(2.5)  # let samples() resolve before dependent tracks fire

    @staticmethod
    def compile(stem, variant):
        defaults = {k: v.get("default") for k, v in (stem.get("params") or {}).items()
                    if isinstance(v, dict)}
        return string.Template(stem["code"][variant]).safe_substitute(defaults)

    def _fire(self, slot, stem, variant):
        self.srv.post("/strudel/track", name=slot, code=self.compile(stem, variant))
        if slot not in self.tracks:
            self.tracks.append(slot)

    def deploy(self, asset):
        kind = asset.get("kind")
        self.current, self.variant = asset, "full"
        if kind == "stem":
            self._load_deps(asset.get("deps"))
            cps = (asset.get("cps") or {}).get("written")
            if cps:
                self.srv.post("/strudel/cps", cps=cps)
            self._fire(asset.get("slot") or "lead", asset, "full")
            return f"deployed -> track '{asset.get('slot')}' [full]"
        if kind == "kit":
            return self._deploy_kit(asset)
        if kind == "arc":
            return "arc (no live deploy) — grade from its kit / spec"
        raise RuntimeError(f"can't deploy kind '{kind}'")

    def _deploy_kit(self, kit):
        stems = []
        for slot, sid in (kit.get("stems") or {}).items():
            e = self.index.get(sid)
            if not e:
                raise RuntimeError(f"kit stem '{sid}' not in index (unverified?)")
            stems.append((slot, load_asset(e)))
        deps = [d for _, s in stems for d in (s.get("deps") or [])]
        self._load_deps(deps)                                   # 1. deps
        if kit.get("cps"):
            self.srv.post("/strudel/cps", cps=kit["cps"])       # 2. cps
        stems.sort(key=lambda t: (t[0] != "drums", t[0]))       # 3. drums first
        for slot, s in stems:
            self._fire(slot, s, "full")
        return f"deployed kit -> {len(stems)} tracks ({', '.join(t for t, _ in stems)})"

    def cycle(self):
        if not self.current or self.current.get("kind") != "stem":
            return "v: variant cycling only applies to stems"
        self.variant = VARIANTS[(VARIANTS.index(self.variant) + 1) % len(VARIANTS)]
        slot = self.current.get("slot") or "lead"
        self._fire(slot, self.current, self.variant)
        return f"track '{slot}' [{self.variant}]"

    def cleanup(self):
        for t in self.tracks:
            try:
                self.srv.post("/strudel/stop", name=t)
            except Exception:
                pass
        self.tracks = []
        self.current = None

    shutdown = cleanup


def _pending():
    return bool(select.select([sys.stdin], [], [], 0.05)[0])


def read_key():
    """One keypress in cbreak mode; arrows decoded to 'left'/'right'.

    Unrecognized escape sequences are consumed WHOLE and return "" — a
    stray '5' left over from PgUp (\\x1b[5~) must never register as a grade.
    """
    ch = sys.stdin.read(1)
    if not ch:          # EOF (stdin closed) — treat as quit, never busy-loop
        return "q"
    if ch != "\x1b":
        return ch
    if not _pending():
        return ""       # bare Esc
    if sys.stdin.read(1) != "[":
        return ""       # Alt-<key> etc.
    final = ""
    while _pending():   # CSI: parameter bytes (digits/;) then one final byte
        final = sys.stdin.read(1)
        if not final or not (final.isdigit() or final == ";"):
            break
    return {"C": "right", "D": "left"}.get(final, "")


def print_status(i, n, entry, grades, msg, domain):
    g = grades.get(entry["id"])
    g = "—" if g is None else str(g)
    tags = entry.get("tags", "")
    if len(tags) > 60:
        tags = tags[:57] + "…"
    extra = " (3 variants)" if entry.get("kind") == "stem" else ""
    print(f"\n[{i + 1}/{n}] {entry['id']} — {tags} — grade: {g}{extra}")
    print(f"  {msg}")
    v = "v variant · " if domain == "music" else ""
    print(f"  keys: 1-5 grade · space/→ skip · ← back · {v}n note · q quit")


def main():
    ap = argparse.ArgumentParser(description="Grade catalog assets on the live server.")
    ap.add_argument("domain", choices=["visual", "music"])
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--all", action="store_true", help="include already-graded assets")
    args = ap.parse_args()

    if not sys.stdin.isatty():
        sys.exit("review.py needs an interactive terminal (raw keyboard mode).")

    srv = Server(args.port)
    try:
        status = srv.get("/status")
        if not status.get("ready"):
            raise RuntimeError("no browser connected")
    except Exception as e:
        sys.exit(f"Livecode server not ready on port {args.port} ({e}).\n"
                 "Start it: python livecode.py, open livecode.html, click Start.")

    index = load_index(args.domain)
    grades = load_grades()
    queue = [e for e in index if args.all or e["id"] not in grades]
    if not queue:
        sys.exit("Nothing to review — everything is graded (use --all to regrade).")

    was_recording = bool(status.get("recording"))
    try:
        srv.post("/show/recording", enabled=False)
    except Exception:
        pass

    # v2 engine: the p5 clock is driven by the Strudel transport
    # (owned_transport.js) — with no track playing, the clock freezes and every
    # visual reads as static. Start a near-silent metronome so motion runs while
    # grading visuals. (Music review plays its own audio, so skip it there.)
    xport = args.domain == "visual"
    if xport:
        try:
            srv.post("/strudel/track", name="__reviewclock",
                     code='sound("bd").gain(0.001).play()')
            time.sleep(0.6)
        except Exception:
            pass

    cls = VisualReviewer if args.domain == "visual" else MusicReviewer
    rev = cls(srv, {e["id"]: e for e in index})

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    i, need_deploy = 0, True
    try:
        tty.setcbreak(fd)
        while 0 <= i < len(queue):
            entry = queue[i]
            if need_deploy:
                rev.cleanup()
                try:
                    msg = rev.deploy(load_asset(entry))
                except Exception as e:
                    msg = f"DEPLOY ERROR: {e}"
                print_status(i, len(queue), entry, grades, msg, args.domain)
                need_deploy = False
            k = read_key()
            if k in {"1", "2", "3", "4", "5"}:  # NOT `k in "12345"` — "" is a substring!
                grade = int(k)
                append_review({"ts": now(), "id": entry["id"], "grade": grade, "note": ""})
                grades[entry["id"]] = grade
                print(f"  graded {entry['id']} = {grade}")
                i, need_deploy = i + 1, True
            elif k in (" ", "right"):
                i, need_deploy = i + 1, True
            elif k == "left" and i > 0:
                i, need_deploy = i - 1, True
            elif k == "v":
                try:
                    print("  " + rev.cycle())
                except Exception as e:
                    print(f"  variant error: {e}")
            elif k == "n":
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
                try:
                    note = input("  note> ").strip()
                finally:
                    tty.setcbreak(fd)
                if note:  # attach to latest grade for this id (null if ungraded)
                    append_review({"ts": now(), "id": entry["id"],
                                   "grade": grades.get(entry["id"]), "note": note})
                    print("  noted.")
            elif k in ("q", "\x03", "\x04"):
                break
        if i >= len(queue):
            print("\nQueue done — all assets reviewed.")
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        rev.shutdown()
        if xport:
            try:
                srv.post("/strudel/stop", name="__reviewclock")
            except Exception:
                pass
        try:
            srv.post("/show/recording", enabled=was_recording)
        except Exception:
            pass
    print("Cleaned up — server left idle.")


if __name__ == "__main__":
    main()
