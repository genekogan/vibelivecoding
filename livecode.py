"""Livecode — start the unified Strudel + p5.js server."""

import argparse
import time

from livecode_server import LivecodeController

parser = argparse.ArgumentParser(description="Livecode unified server")
parser.add_argument("--port", type=int, default=8766, help="HTTP/REST port (WebSocket binds to port - 1)")
args = parser.parse_args()

ctrl = LivecodeController(ws_port=args.port - 1, http_port=args.port)
ctrl.start()

print("Waiting for browser connection...")
ctrl.wait_for_browser(timeout=300)
print("READY")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ctrl.close()
