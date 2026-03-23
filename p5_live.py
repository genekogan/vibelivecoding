"""p5.js live controller — HTTP API for Claude to send commands in real-time."""

from p5_server import P5Controller
import http.server
import json
import threading
import time

ctrl = P5Controller()
ctrl.start()

API_PORT = 8777


class P5LiveHandler(http.server.BaseHTTPRequestHandler):
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
                "layers": list(ctrl.layers.keys()),
            })
        else:
            self._reply({"error": "not found"}, 404)

    def do_POST(self):
        try:
            d = self._read_json()
            if self.path == "/layer":
                ctrl.set_layer(d["name"], d["code"])
            elif self.path == "/remove":
                ctrl.remove_layer(d["name"])
            elif self.path == "/clear":
                ctrl.clear()
            elif self.path == "/setup":
                ctrl.set_setup(d["code"])
            elif self.path == "/send":
                r = ctrl.send(d["code"])
                return self._reply({"ok": True, "response": r})
            elif self.path == "/state":
                ctrl.set_state(d["key"], d["value"])
            elif self.path == "/fps":
                ctrl.set_fps(d["fps"])
            else:
                return self._reply({"error": "not found"}, 404)
            self._reply({"ok": True})
        except Exception as e:
            self._reply({"ok": False, "error": str(e)}, 500)

    def log_message(self, *a):
        pass


api = http.server.HTTPServer(("localhost", API_PORT), P5LiveHandler)
threading.Thread(target=api.serve_forever, daemon=True).start()

print(f"p5.js Live API on http://localhost:{API_PORT}")
print(f"Open http://localhost:8776/p5.html in your browser")
print("Waiting for browser connection...")
ctrl.wait_for_browser(timeout=300)
print("READY")

# Keep alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ctrl.close()
