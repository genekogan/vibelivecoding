"""Unified Livecode Controller — Strudel music + p5.js visuals over a single WebSocket."""

import asyncio
import http.server
import json
import math
import os
import re
import threading
import time
import uuid
from collections import OrderedDict, deque

import websockets


class LivecodeController:
    """Control Strudel audio and p5.js visuals from a single server.

    Usage:
        ctrl = LivecodeController()
        ctrl.start()
        ctrl.wait_for_browser()
        ctrl.set_track("d1", 'note("c3 e3 g3").s("sawtooth").play()')
        ctrl.set_layer("bg", 'background(0);')
        ctrl.hush()
        ctrl.clear()
        ctrl.close()
    """

    def __init__(self, host="localhost", ws_port=8765, http_port=8766, timeout=5):
        self.host = host
        self.ws_port = ws_port
        self.http_port = http_port
        self.timeout = timeout

        # Shared
        self._connections: set[websockets.WebSocketServerProtocol] = set()
        self._ready = threading.Event()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._server = None
        self._thread: threading.Thread | None = None
        self._pending: dict[str, asyncio.Future] = {}

        # Strudel state
        self._tracks: dict[str, str] = {}
        self._cps: float | None = None
        self._transport_generation: int = 0
        self._reconnect_policy = "declared-hard-reset"

        # p5 state
        self._layers: OrderedDict[str, str] = OrderedDict()
        self._setup_code: str | None = None

        # Autopilot: recent browser-side runtime errors (for the improv loop to self-correct)
        self._errors: deque = deque(maxlen=50)

        # Step timeline (for step-through navigation)
        self._steps: list[dict] = []  # [{route, payload, label?}, ...]
        self._step_index: int = -1  # current position (-1 = before any steps)
        self._recording: bool = True  # auto-record all commands as steps

        # Auto-save session captures to shows/unsorted/
        import datetime
        self._session_id = "jam_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self._autosave_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "shows", "unsorted"
        )
        self._autosave_path = os.path.join(self._autosave_dir, f"{self._session_id}.show.json")
        self._autosave_interval = 60  # seconds
        self._autosave_last_count = 0
        self._autosave_thread: threading.Thread | None = None
        self._autosave_stop = threading.Event()

    # ── Lifecycle ────────────────────────────────────────────────

    def start(self):
        """Start the WebSocket server and HTTP/REST server in daemon threads."""
        started = threading.Event()
        self._thread = threading.Thread(target=self._run_loop, args=(started,), daemon=True)
        self._thread.start()
        started.wait()
        self._start_http_server()
        self._cache_bust = int(time.time())
        # Start background autosave daemon (sequesters captures to shows/unsorted/)
        os.makedirs(self._autosave_dir, exist_ok=True)
        self._autosave_thread = threading.Thread(
            target=self._autosave_loop, daemon=True, name="autosave"
        )
        self._autosave_thread.start()
        print(f"Livecode controller listening on ws://{self.host}:{self.ws_port}")
        print(f"Open http://{self.host}:{self.http_port}/livecode.html?v={self._cache_bust}")
        print(f"Autosaving session to {self._autosave_path}")

    def _run_loop(self, started: threading.Event):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._start_server(started))
        self._loop.run_forever()

    async def _start_server(self, started: threading.Event):
        self._server = await websockets.serve(self._handler, self.host, self.ws_port)
        started.set()

    def _start_http_server(self):
        """Start HTTP server that serves files AND handles REST API."""
        root = os.path.dirname(os.path.abspath(__file__))
        controller = self

        class LivecodeHTTPHandler(http.server.SimpleHTTPRequestHandler):
            # REST API routes
            API_ROUTES = {
                "GET": {"/status", "/state", "/errors", "/transport", "/show/steps", "/show/save"},
                "POST": {
                    "/strudel/track", "/strudel/stop", "/strudel/hush",
                    "/strudel/cps", "/strudel/reset", "/strudel/send",
                    "/p5/layer", "/p5/remove", "/p5/clear",
                    "/p5/setup", "/p5/send", "/p5/state", "/p5/fps",
                    "/show/next", "/show/prev", "/show/goto",
                    "/show/mark", "/show/recording", "/show/load",
                    "/show/load_file", "/show/save_file",
                    "/music/grade",
                },
            }

            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=root, **kwargs)

            def end_headers(self):
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                super().end_headers()

            def _read_json(self):
                n = int(self.headers.get("Content-Length", 0))
                return json.loads(self.rfile.read(n).decode()) if n else {}

            def _reply(self, data, status=200):
                body = json.dumps(data).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path == "/status":
                    self._reply({
                        "ready": controller._ready.is_set(),
                        "tracks": list(controller.tracks.keys()),
                        "layers": list(controller.layers.keys()),
                        "cps": controller._cps,
                        "transportGeneration": controller._transport_generation,
                        "reconnectPolicy": controller._reconnect_policy,
                        "step": controller._step_index,
                        "totalSteps": len(controller._steps),
                        "recording": controller._recording,
                    })
                elif self.path == "/state":
                    # Autopilot: full code dump for self-correction
                    self._reply({
                        "ready": controller._ready.is_set(),
                        "cps": controller._cps,
                        "transportGeneration": controller._transport_generation,
                        "reconnectPolicy": controller._reconnect_policy,
                        "setup": controller._setup_code,
                        "tracks": controller.tracks,
                        "layers": controller.layers,
                    })
                elif self.path == "/errors":
                    # Autopilot: recent browser-side runtime errors
                    self._reply({"errors": list(controller._errors)})
                elif self.path == "/transport":
                    try:
                        self._reply({"ok": True, "transport": controller.transport_snapshot()})
                    except Exception as e:
                        self._reply({"ok": False, "error": str(e)}, 503)
                elif self.path.startswith("/p5/read"):
                    # Read a window.state key from the browser (validation/review tooling)
                    from urllib.parse import urlparse, parse_qs
                    try:
                        q = parse_qs(urlparse(self.path).query)
                        key = q.get("key", [""])[0]
                        value = controller.read_state(key)
                        self._reply({"ok": True, "key": key, "value": value})
                    except Exception as e:
                        self._reply({"ok": False, "error": str(e)}, 500)
                elif self.path == "/show/steps":
                    self._reply({
                        "steps": [
                            {"i": i, "route": s["route"], "label": s.get("label", ""),
                             "payload": {k: v for k, v in s["payload"].items() if k != "code"}}
                            for i, s in enumerate(controller._steps)
                        ],
                        "current": controller._step_index,
                        "total": len(controller._steps),
                    })
                elif self.path == "/show/save":
                    import datetime
                    self._reply({
                        "format": "livecode-show-v1",
                        "name": controller._current_label() or "untitled",
                        "created": datetime.datetime.now().isoformat(),
                        "steps": controller._steps,
                    })
                else:
                    super().do_GET()

            def do_POST(self):
                path = self.path
                try:
                    d = self._read_json()

                    # Strudel routes
                    if path == "/strudel/track":
                        controller.set_track(d["name"], d["code"])
                        controller._record_step(path, d)
                    elif path == "/strudel/stop":
                        controller.stop_track(d["name"])
                        controller._record_step(path, d)
                    elif path == "/strudel/hush":
                        controller.hush()
                        controller._record_step(path, d)
                    elif path == "/strudel/cps":
                        controller.set_cps(d["cps"])
                        controller._record_step(path, d)
                    elif path == "/strudel/reset":
                        result = controller.reset_transport(d.get("quantumCycles", 1))
                        controller._record_step(path, d)
                        return self._reply({"ok": True, "transport": result.get("result")})
                    elif path == "/strudel/send":
                        r = controller.send_strudel(d["code"], d.get("evaluate", False))
                        return self._reply({"ok": True, "response": r})

                    # p5 routes
                    elif path == "/p5/layer":
                        controller.set_layer(d["name"], d["code"])
                        controller._record_step(path, d)
                    elif path == "/p5/remove":
                        controller.remove_layer(d["name"])
                        controller._record_step(path, d)
                    elif path == "/p5/clear":
                        controller.clear()
                        controller._record_step(path, d)
                    elif path == "/p5/setup":
                        controller.set_setup(d["code"])
                        controller._record_step(path, d)
                    elif path == "/p5/send":
                        r = controller.send_p5(d["code"])
                        return self._reply({"ok": True, "response": r})
                    elif path == "/p5/state":
                        controller.set_state(d["key"], d["value"])
                        controller._record_step(path, d)
                    elif path == "/p5/fps":
                        controller.set_fps(d["fps"])
                        controller._record_step(path, d)

                    # Show navigation routes
                    elif path == "/show/next":
                        result = controller.step_next()
                        return self._reply(result)
                    elif path == "/show/prev":
                        result = controller.step_prev()
                        return self._reply(result)
                    elif path == "/show/goto":
                        result = controller.step_goto(d["step"])
                        return self._reply(result)
                    elif path == "/show/mark":
                        controller.step_mark(d.get("label", ""))
                        return self._reply({"ok": True, "step": controller._step_index})
                    elif path == "/show/recording":
                        controller._recording = d.get("enabled", True)
                    elif path == "/show/load":
                        controller.load_steps(d["steps"])
                        return self._reply({"ok": True, "total": len(controller._steps)})
                    elif path == "/show/load_file":
                        result = controller.load_show_from_file(d["path"])
                        return self._reply(result)
                    elif path == "/show/save_file":
                        result = controller.save_show_to_file(d["path"])
                        return self._reply(result)

                    # Music factory: taste grading (bad/ok/good) -> grades.jsonl.
                    # Append-only; the prune tool does any actual deletion later.
                    elif path == "/music/grade":
                        import datetime
                        gid, grade = d.get("id"), d.get("grade")
                        if not gid or grade not in ("bad", "ok", "good"):
                            return self._reply({"ok": False, "error": "need id + grade in {bad,ok,good}"}, 400)
                        rec = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                               "id": gid, "grade": grade}
                        gpath = os.path.join(root, "assets", "music", "grades.jsonl")
                        with open(gpath, "a") as gf:
                            gf.write(json.dumps(rec) + "\n")
                        return self._reply({"ok": True, **rec})
                    else:
                        return self._reply({"error": "not found"}, 404)

                    self._reply({"ok": True})
                except Exception as e:
                    self._reply({"ok": False, "error": str(e)}, 500)

            def log_message(self, format, *args):
                pass  # suppress request logging

        self._httpd = http.server.HTTPServer((self.host, self.http_port), LivecodeHTTPHandler)
        t = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        t.start()

    def wait_for_browser(self, timeout=30):
        """Block until a browser client connects and sends 'ready'."""
        if not self._ready.wait(timeout=timeout):
            raise TimeoutError("No browser connected within timeout")
        print("Browser connected and ready")

    def close(self):
        """Shut down the server and background thread."""
        self._final_autosave()
        if self._server and self._loop:
            asyncio.run_coroutine_threadsafe(self._close_ws_server(), self._loop).result(timeout=3)
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=3)
        if hasattr(self, "_httpd"):
            self._httpd.shutdown()
        self._ready.clear()
        self._connections.clear()

    async def _close_ws_server(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    # ── WebSocket handler ────────────────────────────────────────

    EXPECTED_VERSION = 3

    async def _handler(self, ws):
        self._connections.add(ws)
        try:
            async for raw in ws:
                msg = json.loads(raw)
                if msg.get("type") == "ready":
                    v = msg.get("version", 0)
                    diag = msg.get("diag", {})
                    if v != self.EXPECTED_VERSION:
                        print(f"\n  *** STALE BROWSER: v{v} (need v{self.EXPECTED_VERSION}) — hard-refresh! (Cmd+Shift+R) ***\n")
                        continue
                    print(f"  (browser v{v} OK)")
                    if diag:
                        for dk, dv in diag.items():
                            print(f"    {dk}: {dv}")
                    # Restore state on reconnect
                    await self._restore_all(ws)
                    self._ready.set()
                elif msg.get("type") == "execute":
                    for other in self._connections:
                        if other != ws:
                            await other.send(raw)
                elif msg.get("type") in ("status", "error"):
                    mid = msg.get("id")
                    if mid and mid in self._pending:
                        fut = self._pending[mid]
                        if not fut.done():
                            fut.set_result(msg)
                elif msg.get("type") == "log_error":
                    # Autopilot: browser-side runtime error forwarded for self-correction
                    self._errors.append({
                        "ts": msg.get("ts"),
                        "system": msg.get("system", "?"),
                        "message": msg.get("message", ""),
                    })
        except websockets.ConnectionClosed:
            pass
        finally:
            self._connections.discard(ws)
            if not self._connections:
                self._ready.clear()

    async def _restore_all(self, ws):
        """Re-send all tracks and layers to a reconnected browser."""
        # Every connection is an explicit new transport epoch. Configure the
        # owned scheduler first; websocket ordering guarantees the restored
        # pattern is evaluated after this declared hard reset.
        self._transport_generation += 1
        transport_mid = f"msg_{uuid.uuid4().hex[:8]}"
        await ws.send(json.dumps({
            "type": "execute", "target": "transport", "mode": "configure",
            "id": transport_mid,
            "cps": self._cps if self._cps is not None else 0.5,
            "serverGeneration": self._transport_generation,
            "reconnectPolicy": self._reconnect_policy,
            "reason": "browser-connect-hard-reset",
        }))

        # Restore Strudel tracks
        if self._tracks:
            tracks = list(self._tracks.values())
            if len(tracks) == 1:
                code = tracks[0]
            else:
                combined = ",\n".join(tracks)
                code = f"stack(\n{combined}\n)"
            mid = f"msg_{uuid.uuid4().hex[:8]}"
            msg = json.dumps({
                "type": "execute", "target": "strudel",
                "code": code, "id": mid, "evaluate": True,
            })
            await ws.send(msg)

        # Restore p5 layers
        for name, code in self._layers.items():
            mid = f"msg_{uuid.uuid4().hex[:8]}"
            msg = json.dumps({
                "type": "execute", "target": "p5",
                "code": code, "id": mid,
                "mode": "layer", "layer": name,
            })
            await ws.send(msg)

    # ── Sending (internal) ───────────────────────────────────────

    def _send_and_wait_sync(self, payload: str, mid: str, timeout: float | None = None) -> dict:
        """Send payload to all connections and wait for response."""
        if not self._connections:
            raise ConnectionError("No browser connected")
        wait_timeout = float(timeout if timeout is not None else self.timeout)
        future = asyncio.run_coroutine_threadsafe(
            self._send_and_wait(payload, mid, wait_timeout), self._loop
        )
        try:
            result = future.result(timeout=wait_timeout + 1)
        except TimeoutError:
            self._pending.pop(mid, None)
            raise TimeoutError(f"Browser did not respond within {wait_timeout}s")
        if result.get("type") == "error":
            print(f"Browser error: {result.get('message', '?')}")
        return result

    async def _send_and_wait(self, payload: str, mid: str, timeout: float) -> dict:
        fut = self._loop.create_future()
        self._pending[mid] = fut
        await asyncio.gather(*(ws.send(payload) for ws in self._connections))
        try:
            return await asyncio.wait_for(fut, timeout=timeout)
        finally:
            self._pending.pop(mid, None)

    # ── Strudel sending ──────────────────────────────────────────

    def send_strudel(self, code: str, evaluate: bool = False) -> dict:
        """Send Strudel code to the browser and wait for response."""
        mid = f"msg_{uuid.uuid4().hex[:8]}"
        msg = {"type": "execute", "target": "strudel", "code": code, "id": mid}
        if evaluate:
            msg["evaluate"] = True
        return self._send_and_wait_sync(json.dumps(msg), mid)

    def _send_transport(self, mode: str, timeout: float | None = None, **kwargs) -> dict:
        """Command the one browser-owned Strudel scheduler."""
        mid = f"msg_{uuid.uuid4().hex[:8]}"
        msg = {"type": "execute", "target": "transport", "mode": mode, "id": mid}
        msg.update(kwargs)
        return self._send_and_wait_sync(json.dumps(msg), mid, timeout=timeout)

    def transport_snapshot(self) -> dict | None:
        """Read a fresh transport frame even when p5/rAF is background-throttled."""
        response = self._send_transport("snapshot", reason="server-snapshot")
        return response.get("result")

    # ── p5 sending ───────────────────────────────────────────────

    def send_p5(self, code: str, mode: str = "eval", **kwargs) -> dict:
        """Send p5 code to the browser and wait for response."""
        mid = f"msg_{uuid.uuid4().hex[:8]}"
        msg = {"type": "execute", "target": "p5", "code": code, "id": mid, "mode": mode}
        msg.update(kwargs)
        return self._send_and_wait_sync(json.dumps(msg), mid)

    # ── Strudel track management ─────────────────────────────────

    def set_track(self, name: str, code: str):
        """Set or update a named track, then replay all tracks as a stack."""
        code = self._strip_play(code)
        self._tracks[name] = code
        self._replay_all()

    def stop_track(self, name: str):
        """Remove a named track, then replay remaining tracks."""
        self._tracks.pop(name, None)
        self._replay_all()

    def hush(self):
        """Stop all tracks and clear the track dict."""
        self._tracks.clear()
        self._transport_generation += 1
        return self._send_transport(
            "hush",
            serverGeneration=self._transport_generation,
            reason="server-hush",
        )

    def set_cps(self, cps: float):
        """Change the owned scheduler's CPS without replacing its pattern/phase."""
        value = float(cps)
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"cps must be a finite positive number, got {cps!r}")
        self._cps = value
        return self._send_transport(
            "set_cps",
            cps=value,
            serverGeneration=self._transport_generation,
            reason="server-set-cps",
        )

    def reset_transport(self, quantum_cycles: float = 1):
        """Hard-reset at the next AudioContext-clocked cycle boundary."""
        quantum = float(quantum_cycles)
        if not math.isfinite(quantum) or quantum <= 0 or quantum > 16:
            raise ValueError("quantumCycles must be finite and within (0, 16]")
        cps = self._cps if self._cps is not None else 0.5
        self._transport_generation += 1
        # Worst case is one full quantum away; allow browser scheduling margin.
        timeout = max(float(self.timeout), quantum / cps + 3.0)
        return self._send_transport(
            "reset",
            timeout=timeout,
            quantumCycles=quantum,
            serverGeneration=self._transport_generation,
            reason="server-quantized-reset",
        )

    def _replay_all(self):
        """Replay all active tracks via window.evaluate()."""
        if not self._tracks:
            self.hush()
            return
        tracks = list(self._tracks.values())
        if len(tracks) == 1:
            code = tracks[0]
        else:
            combined = ",\n".join(tracks)
            code = f"stack(\n{combined}\n)"
        self.send_strudel(code, evaluate=True)

    @staticmethod
    def _strip_play(code: str) -> str:
        """Remove trailing .play() from track code."""
        return re.sub(r'\s*\.play\(\)\s*$', '', code.strip())

    # ── p5 layer management ──────────────────────────────────────

    def set_layer(self, name: str, code: str):
        """Set or update a named layer. Only the changed layer is sent."""
        self._layers[name] = code
        self.send_p5(code, mode="layer", layer=name)

    def remove_layer(self, name: str):
        """Remove a named layer."""
        self._layers.pop(name, None)
        self.send_p5("", mode="remove", layer=name)

    def clear(self):
        """Remove all layers and clear the canvas."""
        self._layers.clear()
        self.send_p5("", mode="clear")

    def set_setup(self, code: str):
        """Hard recompile — destroys p5 instance and recreates with new setup."""
        self._setup_code = code
        self.send_p5(code, mode="setup")

    def set_canvas(self, width: int, height: int):
        """Resize the canvas."""
        self.send_p5(f"resizeCanvas({width}, {height});", mode="eval")

    def set_state(self, key: str, value):
        """Set a key in the persistent window.state object."""
        val_json = json.dumps(value)
        self.send_p5(f"window.state.{key} = {val_json};", mode="eval")

    def read_state(self, key: str):
        """Read a (dotted-path) key from window.state in the browser.
        Used by validation/review tooling: /p5/read?key=clk, key=audio, ..."""
        if not re.fullmatch(r"[A-Za-z_$][\w$]*(\.[A-Za-z_$][\w$]*)*", key or ""):
            raise ValueError(f"invalid state key: {key!r}")
        code = (
            f"(function() {{ try {{ return window.state.{key}; }} "
            f"catch (e) {{ return null; }} }})()"
        )
        r = self.send_p5(code, mode="eval")
        return r.get("result")

    def init_state(self, **kwargs):
        """Initialize multiple keys in window.state (only sets if not already defined)."""
        for key, value in kwargs.items():
            val_json = json.dumps(value)
            self.send_p5(
                f"if (window.state.{key} === undefined) window.state.{key} = {val_json};",
                mode="eval",
            )

    def set_fps(self, fps: int):
        """Set the target frame rate."""
        self.send_p5(f"frameRate({fps});", mode="eval")

    # ── Step timeline / navigation ─────────────────────────────

    def _record_step(self, route: str, payload: dict, label: str = ""):
        """Record a command as a step in the timeline."""
        if not self._recording:
            return
        # If we navigated backward and are now making new commands,
        # truncate future steps
        if self._step_index < len(self._steps) - 1:
            self._steps = self._steps[:self._step_index + 1]
        self._steps.append({"route": route, "payload": dict(payload), "label": label})
        self._step_index = len(self._steps) - 1
        self._notify_step()

    def load_steps(self, steps: list):
        """Load a list of steps without executing them. For step-through mode."""
        self._reset_state()
        self._steps = steps
        self._step_index = -1
        self._notify_step()

    # ── Show file I/O ───────────────────────────────────────────

    def show_snapshot(self) -> dict:
        """Return the current timeline as a livecode-show-v1 document."""
        import datetime
        return {
            "format": "livecode-show-v1",
            "name": self._current_label() or self._session_id,
            "created": datetime.datetime.now().isoformat(timespec="seconds"),
            "cps_at_start": self._cps,
            "steps": list(self._steps),
        }

    def save_show_to_file(self, path: str) -> dict:
        """Write current timeline to disk as JSON."""
        path = self._resolve_path(path)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        doc = self.show_snapshot()
        # Use the filename (sans extension) as the saved show name
        base = os.path.splitext(os.path.basename(path))[0]
        if base:
            doc["name"] = base
        with open(path, "w") as f:
            json.dump(doc, f, indent=2)
        return {"ok": True, "path": path, "steps": len(doc["steps"])}

    def load_show_from_file(self, path: str) -> dict:
        """Read a .show.json file and load its steps."""
        path = self._resolve_path(path)
        with open(path) as f:
            doc = json.load(f)
        if doc.get("format") != "livecode-show-v1":
            return {"ok": False, "error": f"unsupported format: {doc.get('format')}"}
        steps = doc.get("steps", [])
        self.load_steps(steps)
        return {"ok": True, "path": path, "name": doc.get("name"),
                "total": len(steps), "default_dwell": doc.get("default_dwell")}

    def _resolve_path(self, path: str) -> str:
        """Resolve path relative to repo root if not absolute."""
        if os.path.isabs(path):
            return path
        root = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(root, path)

    def _autosave_loop(self):
        """Daemon thread that periodically writes the timeline to shows/unsorted/."""
        while not self._autosave_stop.wait(self._autosave_interval):
            try:
                if len(self._steps) > self._autosave_last_count:
                    self.save_show_to_file(self._autosave_path)
                    self._autosave_last_count = len(self._steps)
            except Exception as e:
                print(f"autosave failed: {e}")

    def _final_autosave(self):
        """Write a final autosave snapshot. Called from close()."""
        try:
            if self._steps:
                self.save_show_to_file(self._autosave_path)
        except Exception as e:
            print(f"final autosave failed: {e}")
        self._autosave_stop.set()

    def step_mark(self, label: str):
        """Add a label/marker to the current step position."""
        if self._steps and self._step_index >= 0:
            self._steps[self._step_index]["label"] = label

    def _section_boundaries(self) -> list[int]:
        """Return sorted list of step indices that have labels (section starts)."""
        return [i for i, s in enumerate(self._steps) if s.get("label")]

    def step_next(self) -> dict:
        """Advance to next section (or single step if no labels)."""
        if self._step_index >= len(self._steps) - 1:
            return {"ok": False, "error": "at end", "step": self._step_index, "total": len(self._steps)}
        boundaries = self._section_boundaries()
        if not boundaries:
            # No labels at all — single-step mode
            target = self._step_index + 1
        else:
            # Find next boundary after current position
            next_boundary = None
            for b in boundaries:
                if b > self._step_index:
                    next_boundary = b
                    break
            if next_boundary is None:
                target = len(self._steps) - 1
            else:
                # Find the boundary AFTER next_boundary to know where section ends
                target = len(self._steps) - 1
                for b in boundaries:
                    if b > next_boundary:
                        target = b - 1
                        break
        try:
            was_recording = self._recording
            self._recording = False
            try:
                for i in range(self._step_index + 1, target + 1):
                    self._execute_step(self._steps[i])
            finally:
                self._recording = was_recording
            self._step_index = target
        except Exception as e:
            print(f"step_next error: {e}")
            self._step_index = target
        self._notify_step()
        return {"ok": True, "step": self._step_index, "total": len(self._steps),
                "label": self._current_label()}

    def step_prev(self) -> dict:
        """Go back to previous section (or single step if no labels)."""
        if self._step_index < 0:
            return {"ok": True, "step": -1, "total": len(self._steps)}
        boundaries = self._section_boundaries()
        if not boundaries:
            # No labels — single-step backward
            target = self._step_index - 1
            if target < 0:
                self._step_index = -1
                try:
                    self._reset_state()
                except Exception as e:
                    print(f"step_prev reset error: {e}")
                self._notify_step()
                return {"ok": True, "step": -1, "total": len(self._steps)}
            try:
                self._replay_to(target)
            except Exception as e:
                print(f"step_prev error: {e}")
            self._step_index = target
            self._notify_step()
            return {"ok": True, "step": self._step_index, "total": len(self._steps)}
        # Find which section we're currently in
        current_section_start = 0
        for b in boundaries:
            if b <= self._step_index:
                current_section_start = b
            else:
                break
        # Find the section before that
        prev_section_start = None
        for b in boundaries:
            if b < current_section_start:
                prev_section_start = b
        if prev_section_start is None:
            self._step_index = -1
            try:
                self._reset_state()
            except Exception as e:
                print(f"step_prev reset error: {e}")
            self._notify_step()
            return {"ok": True, "step": -1, "total": len(self._steps)}
        # Replay up to end of previous section
        target = current_section_start - 1
        try:
            self._replay_to(target)
        except Exception as e:
            print(f"step_prev error: {e}")
        self._step_index = target
        self._notify_step()
        return {"ok": True, "step": self._step_index, "total": len(self._steps),
                "label": self._current_label()}

    def step_goto(self, target: int) -> dict:
        """Jump to a specific step index."""
        if target < -1 or target >= len(self._steps):
            return {"ok": False, "error": "out of range", "step": self._step_index, "total": len(self._steps)}
        if target == -1:
            self._step_index = -1
            self._reset_state()
            self._notify_step()
            return {"ok": True, "step": -1, "total": len(self._steps)}
        self._step_index = target
        self._replay_to(target)
        self._notify_step()
        return {"ok": True, "step": self._step_index, "total": len(self._steps)}

    def _reset_state(self):
        """Reset to clean state (no tracks, no layers)."""
        was_recording = self._recording
        self._recording = False
        try:
            self._tracks.clear()
            self._cps = None
            self.hush()
            self._send_transport(
                "set_cps", cps=0.5,
                serverGeneration=self._transport_generation,
                reason="show-reset-default-cps",
            )
            self._layers.clear()
            self.send_p5("", mode="clear")
        finally:
            self._recording = was_recording

    def _replay_step(self, idx: int):
        """Replay a single step."""
        was_recording = self._recording
        self._recording = False
        try:
            step = self._steps[idx]
            self._execute_step(step)
        finally:
            self._recording = was_recording

    def _replay_to(self, target: int):
        """Reset then replay all steps from 0 to target."""
        was_recording = self._recording
        self._recording = False
        try:
            self._tracks.clear()
            self._cps = None
            self.hush()
            self._send_transport(
                "set_cps", cps=0.5,
                serverGeneration=self._transport_generation,
                reason="show-reset-default-cps",
            )
            self._layers.clear()
            self.send_p5("", mode="clear")
            for i in range(target + 1):
                self._execute_step(self._steps[i])
        finally:
            self._recording = was_recording

    def _execute_step(self, step: dict):
        """Execute one recorded step."""
        route = step["route"]
        d = step["payload"]
        if route == "/strudel/track":
            self.set_track(d["name"], d["code"])
        elif route == "/strudel/stop":
            self.stop_track(d["name"])
        elif route == "/strudel/hush":
            self.hush()
        elif route == "/strudel/cps":
            self.set_cps(d["cps"])
        elif route == "/strudel/reset":
            self.reset_transport(d.get("quantumCycles", 1))
        elif route == "/p5/layer":
            self.set_layer(d["name"], d["code"])
        elif route == "/p5/remove":
            self.remove_layer(d["name"])
        elif route == "/p5/clear":
            self.clear()
        elif route == "/p5/setup":
            self.set_setup(d["code"])
        elif route == "/strudel/send":
            evaluate = d.get("evaluate", False)
            self.send_strudel(d["code"], evaluate=evaluate)
        elif route == "/p5/state":
            self.set_state(d["key"], d["value"])
        elif route == "/p5/fps":
            self.set_fps(d["fps"])
        elif route == "/p5/send":
            self.send_p5(d["code"], mode="eval")
        elif route == "/show/mark":
            pass  # no-op — marker steps are just for section boundaries

    def _current_label(self) -> str:
        """Find the label of the current section (most recent labeled step at or before index)."""
        for i in range(self._step_index, -1, -1):
            label = self._steps[i].get("label", "")
            if label:
                return label
        return ""

    def _notify_step(self):
        """Send step position update to all connected browsers."""
        if not self._connections:
            return
        # Count sections for display
        boundaries = self._section_boundaries()
        section_num = 0
        for b in boundaries:
            if b <= self._step_index:
                section_num += 1
        msg = json.dumps({
            "type": "step_update",
            "step": self._step_index,
            "total": len(self._steps),
            "section": section_num,
            "totalSections": len(boundaries),
            "label": self._current_label(),
        })
        asyncio.run_coroutine_threadsafe(self._broadcast(msg), self._loop)

    async def _broadcast(self, msg: str):
        await asyncio.gather(*(ws.send(msg) for ws in self._connections))

    def set_background(self, *args):
        """Set a persistent background layer."""
        args_str = ", ".join(str(a) for a in args)
        self.set_layer("__bg", f"background({args_str});")

    # ── Properties ───────────────────────────────────────────────

    @property
    def tracks(self) -> dict[str, str]:
        """Return a copy of the current track dict."""
        return dict(self._tracks)

    @property
    def layers(self) -> dict:
        """Return a copy of the current layer dict."""
        return dict(self._layers)


# ── CLI entry point ──────────────────────────────────────────────

if __name__ == "__main__":
    ctrl = LivecodeController()
    ctrl.start()
    print("Open http://localhost:8766/livecode.html in Chrome")
    print("Waiting for browser to connect...")
    ctrl.wait_for_browser()
    print("\nReady! Example commands:")
    print('  ctrl.set_track("d1", \'note("c3 e3 g3").s("sawtooth").play()\')')
    print("  ctrl.set_layer('bg', 'background(0);')")
    print("  ctrl.hush()")
    print("  ctrl.clear()")
    print()

    import code
    code.interact(local={"ctrl": ctrl}, banner="Livecode controller ready. Use ctrl.* to send commands.")
