"""Unified Livecode Controller — Strudel music + p5.js visuals over a single WebSocket."""

import asyncio
import http.server
import json
import math
import os
import re
import sys
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
        # One reentrant lock guards track-stack + timeline mutations. HTTP
        # requests are handled on concurrent threads (ThreadingHTTPServer);
        # a single lock avoids any ordering deadlock between the two.
        self._lock = threading.RLock()

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

        # Conductor: quantized command queue. Commands submitted with a bar
        # quantum are held and fired ON the next matching bar line, decoupling
        # the client's think-time from musical timing (no mid-bar seams).
        self._queue: list[dict] = []
        self._queue_history: deque = deque(maxlen=30)
        self._queue_seq = 0
        self._queue_cv = threading.Condition()
        self._conductor_stop = threading.Event()
        self._conductor_thread: threading.Thread | None = None

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
        self._conductor_thread = threading.Thread(
            target=self._conductor_loop, daemon=True, name="conductor"
        )
        self._conductor_thread.start()
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
            # HTTP/1.1 keep-alive: module-graph pages (threejs browser = 500+ ES
            # modules) fetch in parallel bursts; per-request connections under
            # HTTP/1.0 overflow the accept backlog and fail the whole import.
            protocol_version = "HTTP/1.1"
            # REST API routes
            API_ROUTES = {
                "GET": {"/status", "/state", "/errors", "/transport", "/q",
                        "/show/steps", "/show/save"},
                "POST": {
                    "/strudel/track", "/strudel/stop", "/strudel/hush",
                    "/strudel/cps", "/strudel/reset", "/strudel/send",
                    "/p5/layer", "/p5/remove", "/p5/clear",
                    "/p5/setup", "/p5/send", "/p5/state", "/p5/fps",
                    "/q", "/q/cancel",
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
                        "queued": len(controller._queue),
                        "lastError": controller._errors[-1] if controller._errors else None,
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
                elif self.path == "/q":
                    self._reply(controller.queue_status())
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
                    self._reply(controller.show_snapshot())
                else:
                    super().do_GET()

            def do_POST(self):
                path = self.path
                t0 = time.perf_counter()
                d = {}
                err = None
                try:
                    d = self._read_json()
                    resp, status = self._dispatch_post(path, d)
                    if status >= 400:
                        err = resp.get("error", f"HTTP {status}")
                    self._reply(resp, status)
                except Exception as e:
                    err = str(e)
                    self._reply({"ok": False, "error": err}, 500)
                controller._log_command(path, d, (time.perf_counter() - t0) * 1000, err)

            def _dispatch_post(self, path, d):
                """Handle one POST route; return (response_dict, status)."""
                # Strudel routes
                if path == "/strudel/track":
                    if not isinstance(d.get("name"), str) or not d["name"].strip():
                        return {"ok": False, "error": "strudel track requires a non-empty name"}, 400
                    if not isinstance(d.get("code"), str) or not d["code"].strip():
                        return {"ok": False, "error": "strudel track requires non-empty code"}, 400
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
                    return {"ok": True, "transport": result.get("result")}, 200
                elif path == "/strudel/send":
                    r = controller.send_strudel(d["code"], d.get("evaluate", False))
                    return {"ok": True, "response": r}, 200

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
                    return {"ok": True, "response": r}, 200
                elif path == "/p5/state":
                    controller.set_state(d["key"], d["value"])
                    controller._record_step(path, d)
                elif path == "/p5/fps":
                    controller.set_fps(d["fps"])
                    controller._record_step(path, d)

                # Conductor queue routes
                elif path == "/q":
                    if "items" in d:
                        queued = controller.queue_batch(d["items"])
                    else:
                        queued = [controller.queue_command(
                            d["route"], d.get("payload") or {},
                            d.get("at", 4), d.get("offset", 0))]
                    return {"ok": True, "queued": queued}, 200
                elif path == "/q/cancel":
                    r = controller.queue_cancel(d.get("id"), bool(d.get("all")))
                    return r, (200 if r.get("ok") else 404)

                # Show navigation routes
                elif path == "/show/next":
                    return controller.step_next(), 200
                elif path == "/show/prev":
                    return controller.step_prev(), 200
                elif path == "/show/goto":
                    return controller.step_goto(d["step"]), 200
                elif path == "/show/mark":
                    controller.step_mark(d.get("label", ""))
                    return {"ok": True, "step": controller._step_index}, 200
                elif path == "/show/recording":
                    controller._recording = bool(d.get("enabled", True))
                elif path == "/show/load":
                    controller.load_steps(d["steps"])
                    return {"ok": True, "total": len(controller._steps)}, 200
                elif path == "/show/load_file":
                    return controller.load_show_from_file(d["path"]), 200
                elif path == "/show/save_file":
                    return controller.save_show_to_file(d["path"]), 200

                # Music factory: taste grading (bad/ok/good) -> grades.jsonl.
                # Append-only; the prune tool does any actual deletion later.
                elif path == "/music/grade":
                    import datetime
                    gid, grade = d.get("id"), d.get("grade")
                    if not gid or grade not in ("bad", "ok", "good"):
                        return {"ok": False, "error": "need id + grade in {bad,ok,good}"}, 400
                    rec = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                           "id": gid, "grade": grade}
                    gpath = os.path.join(root, "assets", "music", "grades.jsonl")
                    with open(gpath, "a") as gf:
                        gf.write(json.dumps(rec) + "\n")
                    return {"ok": True, **rec}, 200
                else:
                    return {"error": "not found"}, 404

                return {"ok": True}, 200

            def log_message(self, format, *args):
                pass  # suppress static-file noise; API commands log via _log_command

        # Threaded: a slow browser round-trip on one command must not block
        # /status polls, file serving, or other commands behind it.
        class LivecodeHTTPServer(http.server.ThreadingHTTPServer):
            daemon_threads = True
            request_queue_size = 128   # default 5 drops connections under module-fetch bursts

        self._httpd = LivecodeHTTPServer((self.host, self.http_port), LivecodeHTTPHandler)
        t = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        t.start()

    def wait_for_browser(self, timeout=30):
        """Block until a browser client connects and sends 'ready'."""
        if not self._ready.wait(timeout=timeout):
            raise TimeoutError("No browser connected within timeout")
        print("Browser connected and ready")

    def close(self):
        """Shut down the server and background thread."""
        self._conductor_stop.set()
        with self._queue_cv:
            self._queue_cv.notify_all()
        self._final_autosave()
        if self._autosave_thread:
            self._autosave_thread.join(timeout=2)
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

    # ── Console logging ──────────────────────────────────────────

    _GLYPHS = {"strudel": "♪", "p5": "▦", "show": "⏭", "music": "★"}

    @staticmethod
    def _tint(code: str, s: str) -> str:
        """ANSI-color s when stdout is a terminal."""
        return f"\033[{code}m{s}\033[0m" if sys.stdout.isatty() else s

    def _log_command(self, route: str, payload: dict, ms: float, error: str | None = None):
        """One-line performance log per API command: what landed and how fast."""
        ts = self._tint("2", time.strftime("%H:%M:%S"))
        head, _, verb = route.strip("/").partition("/")
        bits = []
        name = payload.get("name") or payload.get("label")
        if name:
            bits.append(str(name))
        if isinstance(payload.get("code"), str):
            bits.append(f"{len(payload['code'])}ch")
        if head == "show":
            bits.append(f"{self._step_index + 1}/{len(self._steps)}")
        detail = "  ".join(bits)
        # flush: under nohup/pipes stdout is block-buffered and lines would
        # otherwise sit invisible for minutes
        if error:
            print(f"{ts}  {self._tint('31', '✗')} {route}  {detail}  "
                  f"{self._tint('31', error)}  ({ms:.0f}ms)", flush=True)
        else:
            glyph = self._GLYPHS.get(head, "·")
            print(f"{ts}  {glyph} {verb or head:<9} {detail:<28} {ms:>5.0f}ms", flush=True)

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
                        print(f"\n  *** STALE BROWSER: v{v} (need v{self.EXPECTED_VERSION}) — hard-refresh! (Cmd+Shift+R) ***\n", flush=True)
                        # Disconnect so a stale tab can't receive commands or
                        # answer _send_and_wait ahead of the current browser.
                        await ws.close(code=4000, reason=f"stale client v{v}, need v{self.EXPECTED_VERSION}")
                        continue
                    print(f"  (browser v{v} OK)", flush=True)
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
                    # Browser-side runtime error: keep for /errors polling AND
                    # surface immediately — a broken layer/pattern must not
                    # fail silently while the terminal shows nothing.
                    entry = {
                        "ts": msg.get("ts"),
                        "system": msg.get("system", "?"),
                        "message": msg.get("message", ""),
                    }
                    self._errors.append(entry)
                    print(self._tint("31", f"  [browser:{entry['system']}] {entry['message']}"),
                          flush=True)
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

    @staticmethod
    def _raise_for_browser_error(result: dict) -> None:
        """Turn browser-side execution failures into REST-visible failures."""
        if result.get("type") == "error" or result.get("success") is False:
            message = result.get("message") or result.get("error") or "unknown browser error"
            raise RuntimeError(f"Browser rejected command: {message}")

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
        try:
            self._raise_for_browser_error(result)
        except RuntimeError as error:
            print(error)
            raise
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
        if not isinstance(name, str) or not name.strip():
            raise ValueError("track name must be a non-empty string")
        if not isinstance(code, str) or not code.strip():
            raise ValueError("track code must be a non-empty string")
        code = self._strip_play(code)
        with self._lock:
            missing = object()
            previous = self._tracks.get(name, missing)
            self._tracks[name] = code
            try:
                return self._replay_all()
            except Exception:
                if previous is missing:
                    self._tracks.pop(name, None)
                else:
                    self._tracks[name] = previous
                try:
                    self._replay_all()
                except Exception as rollback_error:
                    print(f"Track rollback failed for {name!r}: {rollback_error}")
                raise

    def stop_track(self, name: str):
        """Remove a named track, then replay remaining tracks."""
        with self._lock:
            self._tracks.pop(name, None)
            self._replay_all()

    def hush(self):
        """Stop all tracks and clear the track dict."""
        with self._lock:
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

    @staticmethod
    def _validate_state_key(key: str):
        """Require a plain dotted identifier path — anything else becomes a confusing JS error."""
        if not re.fullmatch(r"[A-Za-z_$][\w$]*(\.[A-Za-z_$][\w$]*)*", key or ""):
            raise ValueError(f"invalid state key: {key!r}")

    def set_state(self, key: str, value):
        """Set a key in the persistent window.state object."""
        self._validate_state_key(key)
        val_json = json.dumps(value)
        self.send_p5(f"window.state.{key} = {val_json};", mode="eval")

    def read_state(self, key: str):
        """Read a (dotted-path) key from window.state in the browser.
        Used by validation/review tooling: /p5/read?key=clk, key=audio, ..."""
        self._validate_state_key(key)
        code = (
            f"(function() {{ try {{ return window.state.{key}; }} "
            f"catch (e) {{ return null; }} }})()"
        )
        r = self.send_p5(code, mode="eval")
        return r.get("result")

    def init_state(self, **kwargs):
        """Initialize multiple keys in window.state (only sets if not already defined)."""
        for key, value in kwargs.items():
            self._validate_state_key(key)
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
        with self._lock:
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
        with self._lock:
            self._reset_state()
            self._steps = steps
            self._step_index = -1
            self._notify_step()

    # ── Show file I/O ───────────────────────────────────────────

    def show_snapshot(self) -> dict:
        """Return the current timeline as a livecode-show-v1 document."""
        import datetime
        with self._lock:
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
        self._autosave_stop.set()
        try:
            if self._steps:
                self.save_show_to_file(self._autosave_path)
        except Exception as e:
            print(f"final autosave failed: {e}")

    def step_mark(self, label: str):
        """Add a label/marker to the current step position."""
        with self._lock:
            if self._steps and self._step_index >= 0:
                self._steps[self._step_index]["label"] = label

    def _section_boundaries(self) -> list[int]:
        """Return sorted list of step indices that have labels (section starts)."""
        return [i for i, s in enumerate(self._steps) if s.get("label")]

    def step_next(self) -> dict:
        """Advance to next section (or single step if no labels)."""
        with self._lock:
            return self._step_next_locked()

    def _step_next_locked(self) -> dict:
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
        with self._lock:
            return self._step_prev_locked()

    def _step_prev_locked(self) -> dict:
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
        with self._lock:
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
            self._reset_state()
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

    # ── Conductor: quantized command queue ───────────────────────
    #
    # queue_command("/strudel/track", {...}, at=8, offset=2) holds the command
    # and fires it 2 bars after the next 8-bar line (cycle == bar). Targets are
    # cycle numbers, so cps changes mid-wait shift the ETA but never the grid.

    QUEUEABLE_ROUTES = {
        "/strudel/track", "/strudel/stop", "/strudel/hush", "/strudel/cps",
        "/p5/layer", "/p5/remove", "/p5/fps", "/p5/state",
    }
    _QUEUE_LEAD = 0.08  # fire this many seconds before the downbeat (like boundary.py)

    def queue_command(self, route: str, payload: dict, at: float = 4, offset: float = 0) -> dict:
        """Enqueue a command to fire on the next `at`-bar line (+ offset bars).

        at=0 fires immediately. While the transport is stopped, grid-quantized
        items hold (there is no grid yet) — visible via GET /q.
        """
        if route not in self.QUEUEABLE_ROUTES:
            raise ValueError(f"route not queueable: {route}")
        at, offset = float(at), float(offset)
        if not math.isfinite(at) or at < 0 or not math.isfinite(offset) or offset < 0:
            raise ValueError("at/offset must be finite and >= 0")
        if route in ("/strudel/track", "/p5/layer"):
            if not isinstance(payload.get("name"), str) or not payload["name"].strip():
                raise ValueError(f"{route} requires a non-empty name")
            if not isinstance(payload.get("code"), str) or not payload["code"].strip():
                raise ValueError(f"{route} requires non-empty code")
        with self._queue_cv:
            self._queue_seq += 1
            item = {
                "id": f"q{self._queue_seq}", "seq": self._queue_seq,
                "route": route, "payload": dict(payload),
                "at": at, "offset": offset, "target": None,
                "queued_ts": time.time(), "status": "pending",
            }
            self._queue.append(item)
            self._queue_cv.notify_all()
        when = "now" if at <= 0 else f"next {at:g}-bar line" + (f" +{offset:g}" if offset else "")
        print(f"{self._tint('2', time.strftime('%H:%M:%S'))}  ⏱ queued {item['id']} "
              f"{route}  {payload.get('name', '')}  → {when}", flush=True)
        return self._queue_item_summary(item)

    def queue_batch(self, items: list) -> list[dict]:
        """Enqueue several commands (e.g. a staggered phase-in) in one call."""
        return [
            self.queue_command(i["route"], i.get("payload") or {},
                               i.get("at", 4), i.get("offset", 0))
            for i in items
        ]

    def queue_cancel(self, qid: str | None = None, cancel_all: bool = False) -> dict:
        with self._queue_cv:
            if cancel_all:
                n = len(self._queue)
                for item in self._queue:
                    item["status"] = "cancelled"
                    self._queue_history.append(item)
                self._queue.clear()
                return {"ok": True, "cancelled": n}
            for item in self._queue:
                if item["id"] == qid:
                    item["status"] = "cancelled"
                    self._queue.remove(item)
                    self._queue_history.append(item)
                    return {"ok": True, "cancelled": 1, "id": qid}
        return {"ok": False, "error": f"no pending item {qid!r}"}

    def _queue_item_summary(self, item: dict, cycle: float | None = None,
                            cps: float | None = None) -> dict:
        code = item["payload"].get("code")
        out = {
            "id": item["id"], "route": item["route"],
            "name": item["payload"].get("name"),
            "at": item["at"], "offset": item["offset"],
            "target": item["target"], "status": item["status"],
        }
        if isinstance(code, str):
            out["codeChars"] = len(code)
        if item.get("error"):
            out["error"] = item["error"]
        if item.get("fired_cycle") is not None:
            out["firedCycle"] = round(item["fired_cycle"], 3)
        if cycle is not None and cps and item["status"] == "pending" and item["at"] > 0:
            target = item["target"]
            if target is None:
                target = (math.floor(cycle / item["at"]) + 1) * item["at"] + item["offset"]
            out["etaSeconds"] = round(max(0.0, (target - cycle) / cps), 2)
        return out

    def queue_status(self) -> dict:
        """Transport position, upcoming boundaries, pending + recent items."""
        snap = {}
        try:
            snap = self.transport_snapshot() or {}
        except Exception:
            pass
        playing = bool(snap.get("playing"))
        cycle = float(snap.get("cycle") or 0.0)
        cps = float(snap.get("cps") or self._cps or 0.5)
        with self._queue_cv:
            pending = [self._queue_item_summary(i, cycle if playing else None, cps)
                       for i in self._queue]
            history = [self._queue_item_summary(i) for i in list(self._queue_history)[-10:]]
        boundaries = {}
        if playing:
            boundaries = {
                str(n): round(((math.floor(cycle / n) + 1) * n - cycle) / cps, 2)
                for n in (1, 2, 4, 8, 16, 32)
            }
        return {"ok": True, "playing": playing, "cycle": round(cycle, 3), "cps": cps,
                "nextBoundarySeconds": boundaries, "pending": pending, "history": history}

    def _conductor_loop(self):
        """Daemon: watch the transport, fire queued items on their bar lines."""
        while not self._conductor_stop.is_set():
            with self._queue_cv:
                if not self._queue:
                    self._queue_cv.wait(timeout=1.0)
                    continue
            snap = None
            try:
                snap = self.transport_snapshot() or {}
            except Exception:
                pass
            playing = bool(snap and snap.get("playing"))
            cycle = float(snap.get("cycle") or 0.0) if snap else 0.0
            cps = float((snap.get("cps") if snap else None) or self._cps or 0.5)

            to_fire, sleep_for = [], 1.0
            with self._queue_cv:
                for item in list(self._queue):
                    if item["at"] <= 0:
                        to_fire.append(item)
                        continue
                    if not playing:
                        continue  # no grid yet — hold until the transport runs
                    # A hard reset rewinds the cycle counter; a stale target
                    # would then sit unreachably far in the future — recompute.
                    if item["target"] is not None and \
                            item["target"] - cycle > item["at"] + item["offset"] + 0.01:
                        item["target"] = None
                    if item["target"] is None:
                        item["target"] = (math.floor(cycle / item["at"]) + 1) * item["at"] \
                            + item["offset"]
                    dt = (item["target"] - cycle) / cps
                    if dt <= self._QUEUE_LEAD:
                        to_fire.append(item)
                    else:
                        sleep_for = min(sleep_for, dt - self._QUEUE_LEAD)
                for item in to_fire:
                    self._queue.remove(item)
            for item in sorted(to_fire, key=lambda i: (i["target"] or 0, i["seq"])):
                self._fire_queued(item, cycle if playing else None)
            if to_fire:
                continue  # more items may share the boundary we just crossed
            with self._queue_cv:
                self._queue_cv.wait(timeout=max(0.02, min(sleep_for, 1.0)))

    def _fire_queued(self, item: dict, cycle: float | None):
        t0 = time.perf_counter()
        try:
            self._execute_step({"route": item["route"], "payload": item["payload"]})
            self._record_step(item["route"], item["payload"])
            item["status"] = "fired"
        except Exception as e:
            item["status"] = "failed"
            item["error"] = str(e)
        item["fired_ts"] = time.time()
        item["fired_cycle"] = cycle
        self._queue_history.append(item)
        ms = (time.perf_counter() - t0) * 1000
        ts = self._tint("2", time.strftime("%H:%M:%S"))
        name = item["payload"].get("name", "")
        tgt = f"@bar {item['target']:g}" if item.get("target") is not None else "now"
        verb = item["route"].rsplit("/", 1)[-1]
        if item["status"] == "fired":
            print(f"{ts}  ⏱ fired {verb} {name}  {tgt}  {ms:.0f}ms", flush=True)
        else:
            print(f"{ts}  {self._tint('31', '✗')} queue {item['id']} {item['route']} {name}  "
                  f"{self._tint('31', item['error'])}", flush=True)
        if self._connections:
            asyncio.run_coroutine_threadsafe(
                self._broadcast(json.dumps({
                    "type": "queue_update",
                    "pending": len(self._queue),
                    "fired": {"route": item["route"], "name": name, "status": item["status"]},
                })), self._loop)

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
