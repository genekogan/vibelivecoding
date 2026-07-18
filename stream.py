"""Twitch streaming + chat integration for Livecode.

╔══════════════════════════════════════════════════════════════════════════╗
║  DEFUNCT (as of 2026-07-02) — automated headless-browser streaming.       ║
║  Not maintained. For streaming today use manual OBS:                      ║
║      docs/livestreaming-obs.md   (X / Twitch, with sound)                 ║
║  Archival notes + revival guide:                                          ║
║      docs/archive/headless-browser-streaming.md                          ║
║  Kept only for a possible future unattended/scriptable streaming path.    ║
║  Note: this still targets the LEGACY strudel-only page (no p5 visuals)    ║
║  and needs BlackHole 2ch on macOS. Modernize before reviving.             ║
╚══════════════════════════════════════════════════════════════════════════╝

Launches a headed browser via Playwright into a virtual display (Xvfb on Linux,
native window on macOS). FFmpeg captures video/audio natively via x11grab+pulse
(Linux) or avfoundation (macOS) — no Python in the real-time capture path.

Requires: strudel_server.py running separately.

Linux deps: apt-get install -y xvfb pulseaudio ffmpeg
macOS deps: brew install ffmpeg, BlackHole 2ch for audio capture

Usage:
    python stream.py                  # stream + chat
    python stream.py --no-chat        # stream only (skip Twitch chat)
    python stream.py --no-stream      # chat only (skip video/audio streaming)
"""

import asyncio
import json
import os
import platform
import signal
import subprocess
import sys
import websockets
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()


class LivecodeStream:
    """Orchestrates Twitch streaming and chat for the livecode setup."""

    def __init__(self, config=None):
        self.config = config or self._load_config()
        self.browser = None
        self.page = None
        self.ffmpeg_proc = None
        self.chat_bot = None
        self._pw = None
        self._running = False
        self._stopping = False
        self._stop_event = asyncio.Event()
        self._xvfb = None
        self._is_linux = platform.system() == "Linux"
        self._is_mac = platform.system() == "Darwin"
        self._chat_callback = self._default_chat_callback

    @staticmethod
    def _load_config():
        return {
            "twitch_app_id": os.getenv("TWITCH_APP_ID", ""),
            "twitch_app_secret": os.getenv("TWITCH_APP_SECRET", ""),
            "twitch_stream_key": os.getenv("TWITCH_STREAM_KEY", ""),
            "twitch_channel": os.getenv("TWITCH_CHANNEL", ""),
            "strudel_url": os.getenv("STRUDEL_URL", "http://localhost:8766/strudel.html"),
            "ws_url": os.getenv("WS_URL", "ws://localhost:8765"),
            "width": int(os.getenv("STREAM_WIDTH", "1920")),
            "height": int(os.getenv("STREAM_HEIGHT", "1080")),
            "fps": int(os.getenv("STREAM_FPS", "30")),
            "video_bitrate": os.getenv("STREAM_VIDEO_BITRATE", "3500k"),
            "audio_bitrate": os.getenv("STREAM_AUDIO_BITRATE", "160k"),
            # Linux: virtual display number (default :99)
            "display": os.getenv("DISPLAY", ":99"),
            "pulse_sink": os.getenv("PULSE_SINK", "virtual_sink"),
            # macOS: avfoundation device indices (find with: ffmpeg -f avfoundation -list_devices true -i "")
            "capture_screen_device": os.getenv("CAPTURE_SCREEN_DEVICE", "1"),
            "capture_audio_device": os.getenv("CAPTURE_AUDIO_DEVICE", "0"),
        }

    # ── Main entry point ──────────────────────────────────────

    async def start(self, stream=True, chat=True):
        """Launch browser, start streaming and/or chat, then drop into REPL."""
        self._running = True

        # Set up virtual display/audio on Linux
        if self._is_linux:
            self._setup_virtual_display()
            self._setup_virtual_audio()

        # Launch Playwright browser (headed — renders to Xvfb on Linux)
        await self._launch_browser()

        # Navigate and auto-click start
        await self._connect_strudel()

        if stream:
            self._start_ffmpeg()
            self._monitor_task = asyncio.create_task(self._monitor_ffmpeg())
            print("Streaming to Twitch (native capture)")

        if chat:
            asyncio.create_task(self._start_chat())

        print("\nReady! Press Ctrl+C to stop.\n")

        # Wait until signaled to stop
        await self._stop_event.wait()
        await self.stop()

    # ── Virtual display/audio (Linux) ─────────────────────────

    def _setup_virtual_display(self):
        """Start Xvfb virtual display (Linux only)."""
        display = self.config["display"]
        w, h = self.config["width"], self.config["height"]
        print(f"Starting Xvfb on {display} ({w}x{h})...")
        self._xvfb = subprocess.Popen(
            ["Xvfb", display, "-screen", "0", f"{w}x{h}x24", "-ac"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        os.environ["DISPLAY"] = display
        # Give Xvfb a moment to start
        import time
        time.sleep(1)
        print(f"  Xvfb started (PID {self._xvfb.pid})")

    def _setup_virtual_audio(self):
        """Start PulseAudio with a virtual sink (Linux only)."""
        sink = self.config["pulse_sink"]
        print("Setting up PulseAudio virtual sink...")
        subprocess.run(["pulseaudio", "--start"], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([
            "pactl", "load-module", "module-null-sink",
            f"sink_name={sink}",
            f"sink_properties=device.description=VirtualSink",
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["pactl", "set-default-sink", sink], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"  PulseAudio virtual sink '{sink}' ready")

    # ── Browser ───────────────────────────────────────────────

    async def _launch_browser(self):
        """Launch headed Chromium via Playwright (renders to Xvfb on Linux)."""
        print("Launching browser (headed)...")
        self._pw = await async_playwright().start()
        self.browser = await self._pw.chromium.launch(
            headless=False,
            args=[
                "--autoplay-policy=no-user-gesture-required",
                "--disable-features=AudioServiceOutOfProcess",
                f"--window-size={self.config['width']},{self.config['height']}",
                "--window-position=0,0",
                *(["--no-sandbox"] if self._is_linux else []),
            ],
        )
        context = await self.browser.new_context(
            viewport={"width": self.config["width"], "height": self.config["height"]},
            ignore_https_errors=True,
            no_viewport=True,
        )
        self.page = await context.new_page()

    async def _connect_strudel(self):
        """Navigate to strudel.html and click the start button."""
        url = self.config["strudel_url"]
        print(f"Navigating to {url}")
        await self.page.goto(url, wait_until="networkidle")

        # Click "Start Audio & Connect"
        btn = self.page.locator("#start-btn")
        await btn.click()
        print("Clicked 'Start Audio & Connect'")

        # Wait for WebSocket connection (the overlay hides on connect)
        await self.page.wait_for_selector("#overlay", state="hidden", timeout=15000)
        print("Browser connected to server")

    # ── FFmpeg ────────────────────────────────────────────────

    def _build_ffmpeg_cmd(self):
        """Build platform-specific FFmpeg command for native capture."""
        stream_key = self.config["twitch_stream_key"]
        w, h = self.config["width"], self.config["height"]
        fps = self.config["fps"]

        if self._is_mac:
            screen_dev = self.config["capture_screen_device"]
            audio_dev = self.config["capture_audio_device"]
            input_args = [
                "-f", "avfoundation",
                "-framerate", str(fps),
                "-video_size", f"{w}x{h}",
                "-capture_cursor", "0",
                "-i", f"{screen_dev}:{audio_dev}",
            ]
        else:
            # Linux: x11grab for video, pulse for audio
            display = self.config["display"]
            sink = self.config["pulse_sink"]
            input_args = [
                "-f", "x11grab",
                "-framerate", str(fps),
                "-video_size", f"{w}x{h}",
                "-i", f"{display}.0",
                "-f", "pulse",
                "-i", f"{sink}.monitor",
            ]

        encode_args = [
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-profile:v", "high",
            "-maxrate", self.config["video_bitrate"],
            "-bufsize", "7000k",
            "-pix_fmt", "yuv420p",
            "-g", str(fps * 2),
            "-r", str(fps),
            "-c:a", "aac",
            "-ac", "2",
            "-b:a", self.config["audio_bitrate"],
            "-ar", "44100",
            "-f", "flv",
            f"rtmp://live.twitch.tv/app/{stream_key}",
        ]

        return ["ffmpeg", "-y", *input_args, *encode_args]

    def _start_ffmpeg(self):
        """Start FFmpeg subprocess for native capture RTMP streaming."""
        stream_key = self.config["twitch_stream_key"]
        if not stream_key:
            print("WARNING: No TWITCH_STREAM_KEY set — FFmpeg will not start")
            return

        cmd = self._build_ffmpeg_cmd()
        self.ffmpeg_proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        print(f"FFmpeg started (PID {self.ffmpeg_proc.pid})")

    # ── FFmpeg monitor ───────────────────────────────────────

    async def _monitor_ffmpeg(self):
        """Monitor FFmpeg stderr and auto-restart on crash."""
        loop = asyncio.get_event_loop()
        restart_count = 0
        max_restarts = 10

        while self._running:
            if not self.ffmpeg_proc:
                await asyncio.sleep(1)
                continue

            # Read stderr in a thread to avoid blocking
            def _read_stderr():
                try:
                    for line in self.ffmpeg_proc.stderr:
                        text = line.decode("utf-8", errors="replace").strip()
                        if text:
                            print(f"  [ffmpeg] {text}")
                except (ValueError, OSError):
                    pass  # pipe closed

            reader = loop.run_in_executor(None, _read_stderr)

            # Wait for FFmpeg to exit
            while self._running and self.ffmpeg_proc.poll() is None:
                await asyncio.sleep(2)

            if not self._running:
                break

            retcode = self.ffmpeg_proc.returncode
            print(f"FFmpeg exited with code {retcode}")

            # Auto-restart
            restart_count += 1
            if restart_count > max_restarts:
                print(f"FFmpeg crashed {restart_count} times — giving up")
                break

            print(f"Restarting FFmpeg (attempt {restart_count}/{max_restarts})...")
            await asyncio.sleep(3)
            self._start_ffmpeg()

    # ── Twitch Chat ───────────────────────────────────────────

    async def _start_chat(self):
        """Connect to Twitch chat using twitchAPI."""
        app_id = self.config["twitch_app_id"]
        app_secret = self.config["twitch_app_secret"]
        channel = self.config["twitch_channel"]

        if not all([app_id, app_secret, channel]):
            print("WARNING: Twitch credentials not fully configured — chat disabled")
            return

        try:
            from twitchAPI.twitch import Twitch
            from twitchAPI.oauth import UserAuthenticationStorageHelper
            from twitchAPI.type import AuthScope
            from twitchAPI.chat import Chat, EventData, ChatMessage
        except ImportError:
            print("WARNING: twitchAPI not installed — chat disabled")
            print("  pip install twitchAPI")
            return

        print("Connecting to Twitch chat...")

        twitch = await Twitch(app_id, app_secret)
        helper = UserAuthenticationStorageHelper(twitch, [AuthScope.CHAT_READ])
        await helper.bind()

        chat = await Chat(twitch)

        async def on_ready(event: EventData):
            print(f"Twitch chat connected — joining #{channel}")
            await event.chat.join_room(channel)

        async def on_message(msg: ChatMessage):
            await self._on_chat_message(msg.user.name, msg.text)

        chat.register_event("ready", on_ready)
        chat.register_event("message", on_message)

        chat.start()
        self.chat_bot = chat
        self._twitch = twitch

    async def _on_chat_message(self, username: str, text: str):
        """Handle incoming chat message. Override for custom behavior."""
        await self._chat_callback(username, text)

    @staticmethod
    async def _default_chat_callback(username: str, text: str):
        """Default chat handler — just print to console."""
        print(f"[chat] {username}: {text}")

    def on_chat(self, callback):
        """Set a custom async callback for chat messages.

        callback signature: async def handler(username: str, text: str)
        """
        self._chat_callback = callback

    # ── Strudel commands ──────────────────────────────────────

    async def send_strudel(self, code: str, evaluate: bool = False):
        """Send Strudel code to strudel_server.py via WebSocket."""
        uri = self.config["ws_url"]
        async with websockets.connect(uri) as ws:
            msg = {"type": "execute", "code": code}
            if evaluate:
                msg["evaluate"] = True
            await ws.send(json.dumps(msg))

    # ── Shutdown ──────────────────────────────────────────────

    def request_stop(self):
        """Signal the main loop to initiate shutdown."""
        self._stop_event.set()

    async def stop(self):
        """Clean shutdown of all components. Safe to call multiple times."""
        if self._stopping:
            return
        self._stopping = True
        self._running = False
        print("\nShutting down...")

        # Stop FFmpeg monitor
        if hasattr(self, '_monitor_task') and not self._monitor_task.done():
            self._monitor_task.cancel()

        # Stop FFmpeg
        if self.ffmpeg_proc and self.ffmpeg_proc.poll() is None:
            self.ffmpeg_proc.terminate()
            try:
                self.ffmpeg_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ffmpeg_proc.kill()
            print("  FFmpeg stopped")

        # Stop chat
        if self.chat_bot:
            try:
                self.chat_bot.stop()
                await self._twitch.close()
            except Exception:
                pass
            print("  Twitch chat stopped")

        # Close browser
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
            print("  Browser closed")

        if self._pw:
            try:
                await self._pw.stop()
            except Exception:
                pass

        # Stop Xvfb (Linux)
        if self._xvfb and self._xvfb.poll() is None:
            self._xvfb.terminate()
            self._xvfb.wait(timeout=5)
            print("  Xvfb stopped")

        # Stop PulseAudio (Linux)
        if self._is_linux:
            subprocess.run(["pulseaudio", "--kill"], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("  PulseAudio stopped")

        print("Done.")


# ── CLI entry point ──────────────────────────────────────────

async def main():
    stream_flag = "--no-stream" not in sys.argv
    chat_flag = "--no-chat" not in sys.argv

    s = LivecodeStream()

    # Ctrl+C / SIGTERM just sets the stop event — start() handles shutdown
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, s.request_stop)

    await s.start(stream=stream_flag, chat=chat_flag)


if __name__ == "__main__":
    asyncio.run(main())
