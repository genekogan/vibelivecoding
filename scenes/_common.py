"""Composition runtime — Composition context manager and CLI helper.

Usage in compositions/*.py:

    from scenes import disco
    from scenes._common import Composition

    with Composition("disco_set") as show:
        show.mark("Drums")
        show.track(**disco.drums())
        show.cps(0.52)

        show.mark("Visuals")
        show.layer(**disco.floor())
        show.layer(**disco.ball())

Run with --step to collect steps and upload to server (no auto-play).
Run plain to perform live (each post goes to the server immediately).
Pass --save PATH to also save the show file when done.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int,
                   default=int(os.environ.get("LIVECODE_PORT", 8766)))
    p.add_argument("--step", action="store_true",
                   help="Collect steps and upload to server; do not auto-play")
    p.add_argument("--save", type=str, default=None,
                   help="Save show to this path after building")
    p.add_argument("--dump-steps", action="store_true",
                   help="Print steps as JSON to stdout instead of executing")
    return p.parse_known_args()


STEP_ROUTES = {
    "/strudel/track", "/strudel/stop", "/strudel/hush", "/strudel/cps",
    "/strudel/send",
    "/p5/layer", "/p5/remove", "/p5/clear",
    "/p5/setup", "/p5/state", "/p5/fps", "/p5/send",
}


def _post_raw(base: str, path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload or {}).encode()
    req = urllib.request.Request(
        f"{base}{path}", data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def _get_raw(base: str, path: str) -> dict:
    with urllib.request.urlopen(f"{base}{path}") as r:
        return json.loads(r.read())


class Composition:
    """Context manager for building shows.

    In --step or --dump-steps mode: collects commands into a list.
    In default mode: posts each command to the server immediately.
    On exit: in --step mode, uploads via /show/load. In --dump-steps,
    prints JSON to stdout. Optionally saves to --save path.
    """

    def __init__(self, name: str, *, default_dwell: str | None = None,
                 args=None, wait: bool = True):
        if args is None:
            args, _ = parse_args()
        self.name = name
        self.default_dwell = default_dwell
        self.args = args
        self.base = f"http://localhost:{args.port}"
        self.steps: list[dict] = []
        self._wait = wait
        self.collect = bool(args.step or args.dump_steps)

    # ── lifecycle ────────────────────────────────────────────────

    def __enter__(self):
        if not self.collect and self._wait:
            self._wait_ready()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.args.dump_steps:
            json.dump(self._snapshot(), sys.stdout)
            return False
        if self.args.step:
            if self._wait:
                self._wait_ready()
            print(f"\nUploading {len(self.steps)} steps to server…")
            _post_raw(self.base, "/show/load", {"steps": self.steps})
            print(f"Loaded! Use ← → in browser, or run autoplay.py.")
        if self.args.save:
            self._save(self.args.save)
        return False

    def _wait_ready(self, timeout: float = 300):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if _get_raw(self.base, "/status")["ready"]:
                    return
            except Exception:
                pass
            time.sleep(0.5)
        raise TimeoutError("browser never connected")

    def _snapshot(self) -> dict:
        import datetime
        return {
            "format": "livecode-show-v1",
            "name": self.name,
            "created": datetime.datetime.now().isoformat(timespec="seconds"),
            "default_dwell": self.default_dwell,
            "steps": list(self.steps),
        }

    def _save(self, path: str):
        if not os.path.isabs(path):
            root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(root, path)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(self._snapshot(), f, indent=2)
        print(f"Saved show to {path} ({len(self.steps)} steps)")

    # ── primitive: post-or-collect ───────────────────────────────

    def post(self, route: str, payload: dict | None = None, *, label: str = "") -> dict:
        if self.collect and route in STEP_ROUTES:
            step = {"route": route, "payload": dict(payload or {})}
            if label:
                step["label"] = label
            self.steps.append(step)
            return {"ok": True}
        if self.collect:
            # non-step route (e.g. /show/mark in collect mode): treat as label-only marker
            return {"ok": True}
        return _post_raw(self.base, route, payload)

    # ── helpers ──────────────────────────────────────────────────

    def mark(self, label: str):
        """Insert a section boundary marker labeled `label`."""
        if self.collect:
            self.steps.append({"route": "/show/mark", "payload": {}, "label": label})
        else:
            _post_raw(self.base, "/show/mark", {"label": label})
        return self

    def track(self, name: str, code: str):
        return self.post("/strudel/track", {"name": name, "code": code})

    def stop(self, name: str):
        return self.post("/strudel/stop", {"name": name})

    def hush(self):
        return self.post("/strudel/hush", {})

    def cps(self, cps: float):
        return self.post("/strudel/cps", {"cps": cps})

    def send_strudel(self, code: str, evaluate: bool = False):
        return self.post("/strudel/send", {"code": code, "evaluate": evaluate})

    def layer(self, name: str, code: str):
        return self.post("/p5/layer", {"name": name, "code": code})

    def remove(self, name: str):
        return self.post("/p5/remove", {"name": name})

    def clear(self):
        return self.post("/p5/clear", {})

    def pause(self, seconds: float):
        """Sleep in live mode; no-op in collect mode."""
        if not self.collect:
            time.sleep(seconds)
