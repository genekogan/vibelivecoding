"""Strudel Remote Controller — send live-coded music from Python over WebSocket."""

import asyncio
import http.server
import json
import os
import re
import threading
import time
import uuid

import websockets


class StrudelController:
    """Control a Strudel browser tab from Python.

    Usage:
        ctrl = StrudelController()
        ctrl.start()
        ctrl.wait_for_browser()
        ctrl.set_track("d1", 'note("c3 e3 g3").s("sawtooth").lpf(800).gain(0.5).play()')
        ctrl.hush()
        ctrl.close()
    """

    def __init__(self, host="localhost", port=8765, http_port=8766, timeout=5):
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
        self._tracks: dict[str, str] = {}
        self._cps: float | None = None

    # ── Lifecycle ────────────────────────────────────────────────

    def start(self):
        """Start the WebSocket server and HTTP file server in daemon threads."""
        started = threading.Event()
        self._thread = threading.Thread(target=self._run_loop, args=(started,), daemon=True)
        self._thread.start()
        started.wait()
        self._start_http_server()
        self._cache_bust = int(time.time())
        print(f"Strudel controller listening on ws://{self.host}:{self.port}")
        print(f"Open http://{self.host}:{self.http_port}/strudel.html?v={self._cache_bust}")

    def _run_loop(self, started: threading.Event):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._start_server(started))
        self._loop.run_forever()

    async def _start_server(self, started: threading.Event):
        self._server = await websockets.serve(self._handler, self.host, self.port)
        started.set()

    def _start_http_server(self):
        """Start a static HTTP file server for strudel.html (and cached samples)."""
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
        # Clear any leftover patterns from a previous session
        self.send("hush()")
        print("Browser connected and ready")

    def close(self):
        """Shut down the server and background thread."""
        # Close WebSocket server
        if self._server and self._loop:
            asyncio.run_coroutine_threadsafe(self._close_ws_server(), self._loop).result(timeout=3)
        # Stop event loop
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=3)
        # Stop HTTP server
        if hasattr(self, "_httpd"):
            self._httpd.shutdown()
        self._ready.clear()
        self._connections.clear()

    async def _close_ws_server(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    # ── WebSocket handler ────────────────────────────────────────

    EXPECTED_VERSION = 9

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
                        # Don't set _ready — reject stale browsers
                        continue
                    print(f"  (browser v{v} OK)")
                    if diag:
                        for dk, dv in diag.items():
                            print(f"    {dk}: {dv}")
                    self._ready.set()
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

    # ── Sending ──────────────────────────────────────────────────

    def send(self, code: str, evaluate: bool = False) -> dict:
        """Send Strudel code to the browser and wait for response.

        When evaluate=True, the browser uses window.evaluate() which runs
        through Strudel's transpiler and calls setPattern() directly.
        When evaluate=False (default), the browser uses plain eval().

        Returns the response dict. Raises ConnectionError if no browser
        is connected, or TimeoutError if the browser doesn't respond.
        """
        if not self._connections:
            raise ConnectionError("No browser connected")

        mid = f"msg_{uuid.uuid4().hex[:8]}"
        msg = {"type": "execute", "code": code, "id": mid}
        if evaluate:
            msg["evaluate"] = True
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

    # ── Track management ─────────────────────────────────────────
    #
    # Strudel's .play() calls repl.setPattern(pattern, true) which
    # REPLACES the scheduler's single pattern — each .play() overwrites
    # the previous one.  To run multiple tracks simultaneously we must
    # combine them into a single stack(...).play() call.

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
        self.send("hush()")

    def set_cps(self, cps: float):
        """Set cycles per second (tempo).

        CPS is applied as a .cps() control on the pattern (not via the
        global setcps function, which is only available inside repl.evaluate
        and not from plain eval in the v1.0.3 CDN bundle).
        """
        self._cps = cps
        if self._tracks:
            self._replay_all()

    def _replay_all(self):
        """Replay all active tracks via window.evaluate().

        Must use evaluate mode because the Strudel transpiler converts
        mini-notation strings ("bd*4" → m("bd*4")) — without it,
        reify() treats strings as literal values producing silence.

        The standalone evaluate calls .play() internally, so we do NOT
        append .play() here.  CPS is set via .cps() pattern control.
        """
        if not self._tracks:
            self.send("hush()")
            return
        tracks = list(self._tracks.values())
        if len(tracks) == 1:
            code = tracks[0]
        else:
            combined = ",\n".join(tracks)
            code = f"stack(\n{combined}\n)"
        if self._cps is not None:
            code += f".cps({self._cps})"
        self.send(code, evaluate=True)

    @staticmethod
    def _strip_play(code: str) -> str:
        """Remove trailing .play() from track code."""
        return re.sub(r'\s*\.play\(\)\s*$', '', code.strip())

    # ── Convenience ──────────────────────────────────────────────

    @property
    def tracks(self) -> dict[str, str]:
        """Return a copy of the current track dict."""
        return dict(self._tracks)


# ── CLI entry point ──────────────────────────────────────────────

if __name__ == "__main__":
    ctrl = StrudelController()
    ctrl.start()
    print("Open http://localhost:8766/strudel.html in Chrome")
    print("Waiting for browser to connect...")
    ctrl.wait_for_browser()
    print("\nReady! Example commands:")
    print('  ctrl.send(\'note("c3 e3 g3").s("sawtooth").lpf(800).gain(0.5).play()\')')
    print('  ctrl.set_track("d1", \'note("c3 e3 g3").s("sawtooth").play()\')')
    print('  ctrl.hush()')
    print()

    # Drop into interactive mode so users can call ctrl.*
    import code
    code.interact(local={"ctrl": ctrl}, banner="Strudel controller ready. Use ctrl.* to send commands.")
