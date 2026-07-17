"""Live controller — HTTP API for Claude to send commands in real-time."""

from strudel_server import StrudelController
import http.server
import json
import threading
import time

ctrl = StrudelController()
ctrl.start()

API_PORT = 8767


class LiveHandler(http.server.BaseHTTPRequestHandler):
    def _read_json(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n).decode()) if n else {}

    def _reply(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        if self.path == "/status":
            self._reply({
                "ready": ctrl._ready.is_set(),
                "tracks": list(ctrl.tracks.keys()),
                "cps": ctrl._cps,
            })
        else:
            self._reply({"error": "not found"}, 404)

    def do_POST(self):
        try:
            d = self._read_json()
            if self.path == "/track":
                ctrl.set_track(d["name"], d["code"])
            elif self.path == "/stop":
                ctrl.stop_track(d["name"])
            elif self.path == "/hush":
                ctrl.hush()
            elif self.path == "/cps":
                ctrl.set_cps(d["cps"])
            elif self.path == "/send":
                r = ctrl.send(d["code"], d.get("evaluate", False))
                return self._reply({"ok": True, "response": r})
            else:
                return self._reply({"error": "not found"}, 404)
            self._reply({"ok": True})
        except Exception as e:
            self._reply({"ok": False, "error": str(e)}, 500)

    def log_message(self, *a):
        pass


api = http.server.HTTPServer(("localhost", API_PORT), LiveHandler)
threading.Thread(target=api.serve_forever, daemon=True).start()

print(f"Live API on http://localhost:{API_PORT}")
print(f"Open http://localhost:8766/strudel.html in your browser")
print("Waiting for browser connection...")
ctrl.wait_for_browser(timeout=300)
print("READY")

# Keep alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ctrl.close()
