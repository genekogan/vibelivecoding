# [ARCHIVED / DEFUNCT] Automated headless-browser streaming (`stream.py`)

**Status: DEFUNCT as of 2026-07-02.** Not maintained, not the supported path. Preserved
here in case the automated/unattended streaming approach is revived later. For streaming
today, use manual OBS: **[../livestreaming-obs.md](../livestreaming-obs.md)**.

---

## What it was

`stream.py` (repo root) — a fully automated, no-GUI streamer:

- **Playwright** launched a browser (headed on macOS, Xvfb virtual display on Linux),
  navigated to the Strudel page, and auto-clicked *Start Audio & Connect*.
- **FFmpeg** captured that browser's video + audio **natively** (no Python in the
  realtime path) and pushed RTMP to **Twitch**, with auto-restart on crash.
- **Twitch chat** was read via `twitchAPI` (optional, `--no-chat`).

```bash
python stream.py              # stream + chat
python stream.py --no-chat    # stream only
python stream.py --no-stream  # chat only
```

### How capture worked
| OS | Video | Audio |
|----|-------|-------|
| **macOS** | avfoundation screen device | avfoundation audio device = **BlackHole 2ch** (the *only* reason BlackHole was installed) |
| **Linux** | `x11grab` on Xvfb `:99` | PulseAudio `module-null-sink` monitor |

### What it depended on
- `legacy/strudel.html` + `legacy/strudel_server.py` — the **pre-unification, Strudel-only**
  page (no p5.js visuals in the stream).
- `.env`: `TWITCH_STREAM_KEY`, `TWITCH_APP_ID`, `TWITCH_APP_SECRET`, `TWITCH_CHANNEL`,
  `CAPTURE_SCREEN_DEVICE`, `CAPTURE_AUDIO_DEVICE` (avfoundation indices — brittle, change per machine).
- **BlackHole 2ch** on macOS for the audio tap.

## Why it was deprecated

- The streamed page was **legacy Strudel-only** — no visuals. Superseded by the unified
  `livecode.py` / `livecode.html` (p5 + Strudel in one page).
- Manual **OBS** is far more robust: captures desktop audio via macOS ScreenCaptureKit
  (**no BlackHole**), handles device changes, and streams to **X or Twitch** the same way.
- avfoundation device-index config was fragile (indices differ per machine, silently wrong).

## The one thing OBS-manual does NOT replace

Hands-off, **scriptable/unattended** streaming (e.g. a bot or cron-driven stream with no
human at the keyboard). That's the reason to keep this around.

## If you revive it — modernize first
1. Reinstall BlackHole: `brew install --cask blackhole-2ch`.
2. Point `STRUDEL_URL` at the **unified** `http://localhost:8766/livecode.html` (not legacy
   strudel.html) so visuals are included; update the start-button selector if needed.
3. Swap the hardcoded Twitch target `rtmp://live.twitch.tv/app/<key>` for X if desired:
   `rtmps://ca.pscp.tv:443/x/<key>`.
4. Re-derive avfoundation indices: `ffmpeg -f avfoundation -list_devices true -i ""`.
5. Verify audio objectively (see the volumedetect check in the OBS runbook).

## Files
- `stream.py` (repo root) — the streamer (carries a deprecation banner pointing here).
- `legacy/` — the standalone pre-unification servers it drove.
