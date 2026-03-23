"""Unified Livecode Controller — Strudel music + p5.js visuals over a single WebSocket."""

import asyncio
import http.server
import json
import os
import re
import threading
import time
import uuid
from collections import OrderedDict

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

        # p5 state
        self._layers: OrderedDict[str, str] = OrderedDict()
        self._setup_code: str | None = None

    # ── Lifecycle ────────────────────────────────────────────────

    def start(self):
        """Start the WebSocket server and HTTP/REST server in daemon threads."""
        started = threading.Event()
        self._thread = threading.Thread(target=self._run_loop, args=(started,), daemon=True)
        self._thread.start()
        started.wait()
        self._start_http_server()
        self._cache_bust = int(time.time())
        print(f"Livecode controller listening on ws://{self.host}:{self.ws_port}")
        print(f"Open http://{self.host}:{self.http_port}/livecode.html?v={self._cache_bust}")

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
                "GET": {"/status"},
                "POST": {
                    "/strudel/track", "/strudel/stop", "/strudel/hush",
                    "/strudel/cps", "/strudel/send",
                    "/p5/layer", "/p5/remove", "/p5/clear",
                    "/p5/setup", "/p5/send", "/p5/state", "/p5/fps",
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
                    })
                else:
                    # File serving
                    super().do_GET()

            def do_POST(self):
                path = self.path
                try:
                    d = self._read_json()

                    # Strudel routes
                    if path == "/strudel/track":
                        controller.set_track(d["name"], d["code"])
                    elif path == "/strudel/stop":
                        controller.stop_track(d["name"])
                    elif path == "/strudel/hush":
                        controller.hush()
                    elif path == "/strudel/cps":
                        controller.set_cps(d["cps"])
                    elif path == "/strudel/send":
                        r = controller.send_strudel(d["code"], d.get("evaluate", False))
                        return self._reply({"ok": True, "response": r})

                    # p5 routes
                    elif path == "/p5/layer":
                        controller.set_layer(d["name"], d["code"])
                    elif path == "/p5/remove":
                        controller.remove_layer(d["name"])
                    elif path == "/p5/clear":
                        controller.clear()
                    elif path == "/p5/setup":
                        controller.set_setup(d["code"])
                    elif path == "/p5/send":
                        r = controller.send_p5(d["code"])
                        return self._reply({"ok": True, "response": r})
                    elif path == "/p5/state":
                        controller.set_state(d["key"], d["value"])
                    elif path == "/p5/fps":
                        controller.set_fps(d["fps"])
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
        # Clear any leftover Strudel patterns
        self.send_strudel("hush()")
        print("Browser connected and ready")

    def close(self):
        """Shut down the server and background thread."""
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

    EXPECTED_VERSION = 1

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
                    self._ready.set()
                    # Restore state on reconnect
                    await self._restore_all(ws)
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
        except websockets.ConnectionClosed:
            pass
        finally:
            self._connections.discard(ws)
            if not self._connections:
                self._ready.clear()

    async def _restore_all(self, ws):
        """Re-send all tracks and layers to a reconnected browser."""
        # Restore Strudel tracks
        if self._tracks:
            tracks = list(self._tracks.values())
            if len(tracks) == 1:
                code = tracks[0]
            else:
                combined = ",\n".join(tracks)
                code = f"stack(\n{combined}\n)"
            if self._cps is not None:
                code += f".cps({self._cps})"
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

    def _send_and_wait_sync(self, payload: str, mid: str) -> dict:
        """Send payload to all connections and wait for response."""
        if not self._connections:
            raise ConnectionError("No browser connected")
        future = asyncio.run_coroutine_threadsafe(self._send_and_wait(payload, mid), self._loop)
        try:
            result = future.result(timeout=self.timeout)
        except TimeoutError:
            self._pending.pop(mid, None)
            raise TimeoutError(f"Browser did not respond within {self.timeout}s")
        if result.get("type") == "error":
            print(f"Browser error: {result.get('message', '?')}")
        return result

    async def _send_and_wait(self, payload: str, mid: str) -> dict:
        fut = self._loop.create_future()
        self._pending[mid] = fut
        await asyncio.gather(*(ws.send(payload) for ws in self._connections))
        try:
            return await asyncio.wait_for(fut, timeout=self.timeout)
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
        self.send_strudel("hush()")

    def set_cps(self, cps: float):
        """Set cycles per second (tempo)."""
        self._cps = cps
        if self._tracks:
            self._replay_all()

    def _replay_all(self):
        """Replay all active tracks via window.evaluate()."""
        if not self._tracks:
            self.send_strudel("hush()")
            return
        tracks = list(self._tracks.values())
        if len(tracks) == 1:
            code = tracks[0]
        else:
            combined = ",\n".join(tracks)
            code = f"stack(\n{combined}\n)"
        if self._cps is not None:
            code += f".cps({self._cps})"
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
