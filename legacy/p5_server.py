"""p5.js Remote Controller — send live-coded visuals from Python over WebSocket."""

import asyncio
import http.server
import json
import os
import threading
import time
import uuid
from collections import OrderedDict

import websockets


class P5Controller:
    """Control a p5.js browser tab from Python.

    Usage:
        ctrl = P5Controller()
        ctrl.start()
        ctrl.wait_for_browser()
        ctrl.set_layer("bg", 'background(0);')
        ctrl.set_layer("shape", 'fill(255,0,0); circle(width/2, height/2, 200);')
        ctrl.clear()
        ctrl.close()
    """

    def __init__(self, host="localhost", port=8775, http_port=8776, timeout=5):
        self.host = host
        self.port = port
        self.http_port = http_port
        self.timeout = timeout

        self._connections: set[websockets.WebSocketServerProtocol] = set()
        self._ready = threading.Event()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._server = None
        self._thread: threading.Thread | None = None
        self._pending: dict[str, asyncio.Future] = {}
        self._layers: OrderedDict[str, str] = OrderedDict()
        self._setup_code: str | None = None

    # ── Lifecycle ────────────────────────────────────────────────

    def start(self):
        """Start the WebSocket server and HTTP file server in daemon threads."""
        started = threading.Event()
        self._thread = threading.Thread(target=self._run_loop, args=(started,), daemon=True)
        self._thread.start()
        started.wait()
        self._start_http_server()
        self._cache_bust = int(time.time())
        print(f"p5.js controller listening on ws://{self.host}:{self.port}")
        print(f"Open http://{self.host}:{self.http_port}/p5.html?v={self._cache_bust}")

    def _run_loop(self, started: threading.Event):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._start_server(started))
        self._loop.run_forever()

    async def _start_server(self, started: threading.Event):
        self._server = await websockets.serve(self._handler, self.host, self.port)
        started.set()

    def _start_http_server(self):
        """Start a static HTTP file server for p5.html."""
        root = os.path.dirname(os.path.abspath(__file__))

        class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=root, **kwargs)

            def end_headers(self):
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.send_header("Pragma", "no-cache")
                self.send_header("Expires", "0")
                super().end_headers()

            def log_message(self, format, *args):
                pass  # suppress HTTP request logging

        self._httpd = http.server.HTTPServer((self.host, self.http_port), NoCacheHandler)
        t = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        t.start()

    def wait_for_browser(self, timeout=30):
        """Block until a browser client connects and sends 'ready'."""
        if not self._ready.wait(timeout=timeout):
            raise TimeoutError("No browser connected within timeout")
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
                    # Restore layers if browser reconnects
                    if self._layers:
                        await self._restore_layers(ws)
                elif msg.get("type") == "execute":
                    # Relay: forward execute messages to all OTHER connections
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

    async def _restore_layers(self, ws):
        """Re-send all layers to a newly connected browser."""
        for name, code in self._layers.items():
            mid = f"msg_{uuid.uuid4().hex[:8]}"
            msg = json.dumps({
                "type": "execute", "code": code, "id": mid,
                "mode": "layer", "layer": name,
            })
            await ws.send(msg)

    # ── Sending ──────────────────────────────────────────────────

    def send(self, code: str, mode: str = "eval", **kwargs) -> dict:
        """Send code to the browser and wait for response.

        Modes:
            "eval"  — plain eval() for one-off commands
            "layer" — register a named layer function (requires layer= kwarg)
            "setup" — hard recompile with new setup code

        Returns the response dict. Raises ConnectionError if no browser
        is connected, or TimeoutError if the browser doesn't respond.
        """
        if not self._connections:
            raise ConnectionError("No browser connected")

        mid = f"msg_{uuid.uuid4().hex[:8]}"
        msg = {"type": "execute", "code": code, "id": mid, "mode": mode}
        msg.update(kwargs)
        payload = json.dumps(msg)
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

    # ── Layer management ─────────────────────────────────────────

    def set_layer(self, name: str, code: str):
        """Set or update a named layer. Only the changed layer is sent."""
        self._layers[name] = code
        self.send(code, mode="layer", layer=name)

    def remove_layer(self, name: str):
        """Remove a named layer."""
        self._layers.pop(name, None)
        self.send("", mode="remove", layer=name)

    def clear(self):
        """Remove all layers and clear the canvas (hush equivalent)."""
        self._layers.clear()
        self.send("", mode="clear")

    # ── Setup ────────────────────────────────────────────────────

    def set_setup(self, code: str):
        """Hard recompile — destroys p5 instance and recreates with new setup."""
        self._setup_code = code
        self.send(code, mode="setup")

    def set_canvas(self, width: int, height: int):
        """Resize the canvas."""
        self.send(f"resizeCanvas({width}, {height});", mode="eval")

    # ── State ────────────────────────────────────────────────────

    def set_state(self, key: str, value):
        """Set a key in the persistent window.state object."""
        val_json = json.dumps(value)
        self.send(f"window.state.{key} = {val_json};", mode="eval")

    def init_state(self, **kwargs):
        """Initialize multiple keys in window.state (only sets if not already defined)."""
        for key, value in kwargs.items():
            val_json = json.dumps(value)
            self.send(
                f"if (window.state.{key} === undefined) window.state.{key} = {val_json};",
                mode="eval",
            )

    # ── Convenience ──────────────────────────────────────────────

    def set_fps(self, fps: int):
        """Set the target frame rate."""
        self.send(f"frameRate({fps});", mode="eval")

    def set_background(self, *args):
        """Set a persistent background layer."""
        args_str = ", ".join(str(a) for a in args)
        self.set_layer("__bg", f"background({args_str});")

    @property
    def layers(self) -> dict:
        """Return a copy of the current layer dict."""
        return dict(self._layers)


# ── CLI entry point ──────────────────────────────────────────────

if __name__ == "__main__":
    ctrl = P5Controller()
    ctrl.start()
    print("Open http://localhost:8776/p5.html in Chrome")
    print("Waiting for browser to connect...")
    ctrl.wait_for_browser()
    print("\nReady! Example commands:")
    print("  ctrl.set_layer('bg', 'background(0);')")
    print("  ctrl.set_layer('shape', 'fill(255,0,0); circle(width/2, height/2, 200);')")
    print("  ctrl.clear()")
    print()

    import code
    code.interact(local={"ctrl": ctrl}, banner="p5.js controller ready. Use ctrl.* to send commands.")
