"""Livecode — start the unified Strudel + p5.js server."""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time

from livecode_server import LivecodeController

parser = argparse.ArgumentParser(description="Livecode unified server")
parser.add_argument("--port", type=int, default=8766, help="HTTP/REST port (WebSocket binds to port - 1)")
parser.add_argument(
    "--catalog",
    action="store_true",
    help="Serve the unified Three.js, p5.js, and Strudel catalog shell. "
    "Catalog mode does not block while waiting for the optional audio engine.",
)
parser.add_argument(
    "--kiosk",
    action="store_true",
    help="After the server is ready, auto-launch the page in a chromeless "
    "Chrome app window (no URL bar, no tabs, no buttons). Still resizable and "
    "movable. Falls back to a fixed 1280x720 frame if --window-size isn't given.",
)
parser.add_argument(
    "--window-size",
    default="1280,720",
    help="Kiosk window size as 'W,H' (default 1280,720). Window stays resizable.",
)
parser.add_argument(
    "--window-position",
    default="0,0",
    help="Kiosk window initial position as 'X,Y' (default 0,0). Still movable.",
)
args = parser.parse_args()


def _find_chrome():
    """Return absolute path to a Chrome/Chromium-family binary, or None."""
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("chrome"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def launch_kiosk(url, size, position):
    chrome = _find_chrome()
    if not chrome:
        print(
            "[--kiosk] No Chrome/Chromium-family browser found — open the URL manually:",
            url,
            file=sys.stderr,
        )
        return None
    # Dedicated profile so we don't collide with the user's normal Chrome session
    # (Chrome refuses --app + existing profile when that profile is already running).
    user_data_dir = tempfile.mkdtemp(prefix="livecode-kiosk-")
    cmd = [
        chrome,
        f"--app={url}",
        f"--window-size={size}",
        f"--window-position={position}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    print(f"[--kiosk] launching: {chrome} --app={url}")
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


ctrl = LivecodeController(ws_port=args.port - 1, http_port=args.port)
ctrl.start()

kiosk_proc = None
if args.kiosk:
    page = "catalog.html" if args.catalog else "livecode.html"
    kiosk_proc = launch_kiosk(
        f"http://localhost:{args.port}/{page}",
        args.window_size,
        args.window_position,
    )

if args.catalog:
    print(f"CATALOG READY: http://localhost:{args.port}/catalog.html")
    print("The audio engine will connect after 'Enable audio' is clicked.")
else:
    print("Waiting for browser connection...")
    ctrl.wait_for_browser(timeout=300)
    print("READY")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ctrl.close()
    if kiosk_proc is not None and kiosk_proc.poll() is None:
        kiosk_proc.terminate()
