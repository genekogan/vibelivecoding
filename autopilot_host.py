"""Autopilot browser host + snapshot sampler.

Opens livecode.html in a *visible* Chromium window (this same window is what you
project / put on the public display), clicks "Start" so no human is needed, keeps
the browser alive, and on a slow heartbeat saves a screenshot to
autopilot/snapshots/ so the autopilot loop can *see* what it is making.

This is feedback-only sampling — NOT every frame, and unrelated to any future
archival / Twitch recording (that stays a separate process, e.g. stream.py
attaching FFmpeg to a launch like this one).

Requires: livecode.py (the server) running separately, and Playwright
            (pip install playwright && playwright install chromium).

Usage:
    python autopilot_host.py
    python autopilot_host.py --interval 20 --fullscreen
"""

import argparse
import asyncio
import os
import platform
import signal

from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))


def _parse_args():
    p = argparse.ArgumentParser(description="Autopilot browser host + snapshot sampler")
    p.add_argument("--url", default="http://localhost:8766/livecode.html",
                   help="livecode.html URL")
    p.add_argument("--interval", type=float, default=6.0,
                   help="seconds between snapshots (heartbeat for the autopilot loop)")
    p.add_argument("--snapshots-dir", default=os.path.join(ROOT, "autopilot", "snapshots"),
                   help="where to write latest.png + rolling prev*.png")
    p.add_argument("--keep", type=int, default=3,
                   help="number of previous snapshots to retain alongside latest.png")
    # INITIAL window size. The window is freely resizable live — the p5 canvas
    # tracks it via createCanvas(windowWidth, windowHeight) + windowResized,
    # and page.screenshot() captures at the current size. So just drag the
    # window to half-screen and visuals + snapshots follow.
    p.add_argument("--width", type=int, default=1280,
                   help="initial window width (resizable live)")
    p.add_argument("--height", type=int, default=720,
                   help="initial window height (resizable live)")
    p.add_argument("--fullscreen", action="store_true",
                   help="launch the window fullscreen (for the projector)")
    p.add_argument("--kiosk", action="store_true",
                   help="open the window in Chrome 'app mode' — no URL bar, no "
                   "tabs, no automation infobar. Still resizable and movable.")
    # Cap saved snapshot size so the autopilot agent can always Read it
    # (large windows would otherwise produce PNGs the LLM API rejects).
    p.add_argument("--max-shot-width", type=int, default=1280,
                   help="downscale screenshots whose width exceeds this (px)")
    return p.parse_args()


class AutopilotHost:
    def __init__(self, args):
        self.args = args
        self._pw = None
        self.browser = None
        self.page = None
        self._is_linux = platform.system() == "Linux"
        self._stop = asyncio.Event()

    # ── Browser ───────────────────────────────────────────────

    async def _launch(self):
        print("Launching browser (headed)...")
        self._pw = await async_playwright().start()

        if self.args.kiosk:
            # Kiosk mode: launch the Playwright-bundled Chrome ourselves via
            # subprocess in --app=URL mode (chromeless OS window), then attach
            # Playwright over CDP. This is the only reliable way to get an
            # app-mode window that Playwright can actually drive — both
            # chromium.launch and launch_persistent_context insist on opening
            # their own about:blank tab.
            import shutil
            import subprocess
            import tempfile

            # Prefer the user's real Chrome over Playwright's bundled
            # "Chrome for Testing" — the latter shows an unkillable warning
            # bar at the top of every window. Fall back to bundled if no
            # system Chrome is installed.
            system_chrome_candidates = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
                "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
                shutil.which("google-chrome"),
                shutil.which("chromium"),
                shutil.which("chromium-browser"),
            ]
            exe = next(
                (p for p in system_chrome_candidates if p and os.path.exists(p)),
                self._pw.chromium.executable_path,
            )
            print(f"Kiosk Chrome binary: {exe}")
            user_data_dir = tempfile.mkdtemp(prefix="livecode-kiosk-")
            self._kiosk_user_data_dir = user_data_dir
            chrome_cmd = [
                exe,
                f"--app={self.args.url}",
                f"--window-size={self.args.width},{self.args.height}",
                "--window-position=0,0",
                f"--user-data-dir={user_data_dir}",
                "--remote-debugging-port=9222",
                "--autoplay-policy=no-user-gesture-required",
                "--no-first-run",
                "--no-default-browser-check",
                *(["--no-sandbox"] if self._is_linux else []),
            ]
            print(f"Launching Chrome in --app= mode: {' '.join(chrome_cmd[:4])}...")
            self._kiosk_proc = subprocess.Popen(
                chrome_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Wait for the CDP endpoint to come up.
            import urllib.request
            for _ in range(50):
                try:
                    urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=0.5).read()
                    break
                except Exception:
                    await asyncio.sleep(0.2)
            else:
                raise RuntimeError("Chrome --app= mode never opened its CDP endpoint")

            self.browser = await self._pw.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = self.browser.contexts[0]
            # Find the page that opened to our URL (skip any about:blank).
            for _ in range(30):
                pages = context.pages
                target = next((p for p in pages if "livecode" in p.url or p.url.startswith("http")), None)
                if target:
                    self.page = target
                    break
                await asyncio.sleep(0.2)
            else:
                self.page = context.pages[0] if context.pages else await context.new_page()
        else:
            launch_args = [
                "--autoplay-policy=no-user-gesture-required",
                "--disable-features=AudioServiceOutOfProcess",
                f"--window-size={self.args.width},{self.args.height}",
                "--window-position=0,0",
                *(["--start-fullscreen"] if self.args.fullscreen else []),
                *(["--no-sandbox"] if self._is_linux else []),
            ]
            self.browser = await self._pw.chromium.launch(headless=False, args=launch_args)
            # no_viewport=True: the page viewport follows the OS window, so live
            # window-resize propagates to canvas + screenshots.
            context = await self.browser.new_context(
                ignore_https_errors=True,
                no_viewport=True,
            )
            self.page = await context.new_page()

    async def _connect(self):
        """Navigate to livecode.html and click Start; wait until connected."""
        print(f"Navigating to {self.args.url}")
        await self.page.goto(self.args.url, wait_until="networkidle")
        await self.page.locator("#start-btn").click()
        print("Clicked 'Start Audio & Visuals'")
        # The Start handler hides #overlay once the WebSocket connects.
        await self.page.wait_for_selector("#overlay", state="hidden", timeout=15000)
        print("Browser connected to server")

    async def _ensure_connected(self):
        """Recover if the page reloaded / lost the connection."""
        try:
            if self.page.is_closed():
                raise RuntimeError("page closed")
            # #overlay reappears when disconnected (it re-shows on a reload).
            if await self.page.is_visible("#overlay"):
                print("Overlay visible again — reconnecting...")
                await self._connect()
        except Exception as e:  # page/browser died — relaunch from scratch
            print(f"Recovering browser ({e})...")
            await self._teardown_browser()
            await self._launch()
            await self._connect()

    # ── Snapshot sampling ─────────────────────────────────────

    def _rotate(self, d):
        """Shift latest.png -> prev1 -> prev2 ... so the agent has simple semantics."""
        keep = max(0, self.args.keep)
        oldest = os.path.join(d, f"prev{keep}.png")
        if os.path.exists(oldest):
            os.remove(oldest)
        for i in range(keep, 1, -1):
            src = os.path.join(d, f"prev{i - 1}.png")
            if os.path.exists(src):
                os.replace(src, os.path.join(d, f"prev{i}.png"))
        latest = os.path.join(d, "latest.png")
        if keep >= 1 and os.path.exists(latest):
            os.replace(latest, os.path.join(d, "prev1.png"))

    async def _snapshot(self):
        d = self.args.snapshots_dir
        os.makedirs(d, exist_ok=True)
        tmp = os.path.join(d, ".latest.tmp.png")
        await self.page.screenshot(path=tmp)
        # Downscale if wider than cap (PIL); keeps agent reads within LLM image limits
        # regardless of how big the user's browser window is.
        try:
            from PIL import Image
            im = Image.open(tmp)
            if im.width > self.args.max_shot_width:
                ratio = self.args.max_shot_width / im.width
                new_size = (self.args.max_shot_width, int(im.height * ratio))
                im.resize(new_size, Image.LANCZOS).save(tmp, optimize=True)
            im.close()
        except Exception as e:
            print(f"shot resize skipped: {e}")
        self._rotate(d)
        os.replace(tmp, os.path.join(d, "latest.png"))  # atomic publish

    async def _canvas_snapshot(self):
        """Capture the p5 canvas pixels via toDataURL → snapshots/canvas.png.

        Uses toDataURL (not an element screenshot) so the canvas is captured even
        when the opaque fullscreen video overlays it — lets the agent verify the
        next livecode set it's building 'behind the curtain' during video playback.
        """
        d = self.args.snapshots_dir
        data = await self.page.evaluate(
            "() => { const c = document.querySelector('canvas');"
            " return c ? c.toDataURL('image/png') : null; }"
        )
        if not data or "," not in data:
            return
        import base64
        raw = base64.b64decode(data.split(",", 1)[1])
        tmp = os.path.join(d, ".canvas.tmp.png")
        with open(tmp, "wb") as f:
            f.write(raw)
        try:
            from PIL import Image
            im = Image.open(tmp)
            if im.width > self.args.max_shot_width:
                ratio = self.args.max_shot_width / im.width
                im = im.resize((self.args.max_shot_width, int(im.height * ratio)), Image.LANCZOS)
                im.save(tmp, optimize=True)
            im.close()
        except Exception as e:
            print(f"canvas shot resize skipped: {e}")
        os.replace(tmp, os.path.join(d, "canvas.png"))  # atomic publish

    # ── Lifecycle ─────────────────────────────────────────────

    async def run(self):
        await self._launch()
        await self._connect()
        os.makedirs(self.args.snapshots_dir, exist_ok=True)
        print(f"Sampling every {self.args.interval}s -> {self.args.snapshots_dir}/latest.png")
        print("Ctrl+C to stop.")
        while not self._stop.is_set():
            try:
                await self._ensure_connected()
                await self._snapshot()
                await self._canvas_snapshot()
            except Exception as e:
                print(f"snapshot tick failed: {e}")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self.args.interval)
            except asyncio.TimeoutError:
                pass

    async def _teardown_browser(self):
        try:
            if self.browser:
                await self.browser.close()
        except Exception:
            pass

    async def shutdown(self):
        self._stop.set()
        await self._teardown_browser()
        try:
            if self._pw:
                await self._pw.stop()
        except Exception:
            pass


async def _main():
    args = _parse_args()
    host = AutopilotHost(args)
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, host._stop.set)
        except NotImplementedError:
            pass
    try:
        await host.run()
    finally:
        await host.shutdown()
        print("Autopilot host stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        pass
