"""Livecode — start the unified Strudel + p5.js server."""

from livecode_server import LivecodeController
import time

ctrl = LivecodeController()
ctrl.start()

print("Waiting for browser connection...")
ctrl.wait_for_browser(timeout=300)
print("READY")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ctrl.close()
