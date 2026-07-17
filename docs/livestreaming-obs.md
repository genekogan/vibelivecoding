# Livestreaming the vibe-coding session (OBS → X / Twitch)

How to manually stream the livecode session (p5.js visuals + Strudel audio) to
**X/Twitter Live** or **Twitch** using **OBS Studio** on macOS. This is the exact setup
that worked — follow the pre-flight in order and you're live in a couple minutes.

> This is the **current, supported** way to stream. The old automated
> `stream.py` (headless browser + FFmpeg → Twitch) is **defunct** — see
> [archive/headless-browser-streaming.md](archive/headless-browser-streaming.md).

### Which platform (only the ingest URL differs — everything else is identical)
| Platform | OBS → Settings → Stream | Server | Key from |
|----------|-------------------------|--------|----------|
| **X / Twitter** | Service = **Custom** | `rtmps://ca.pscp.tv:443/x` | X's *Create Livestream* dialog (Show RTMP → 👁 reveal key) |
| **Twitch** | Service = **Twitch** → *Connect Account* (easiest), or **Custom** | `rtmp://live.twitch.tv/app` | Twitch → Creator Dashboard → Settings → Stream → primary stream key |

Pick the platform here; the sources, audio routing, and pre-flight below are the same for both.

> **The one rule that saves the stream:** OBS's *Desktop Audio Capture* goes **silent
> when the Mac's output device changes** — and the OBS meter keeps showing green, so
> you won't notice. Whenever you plug/unplug headphones or a Bluetooth device
> connects/drops, you **must** hit *Restart capture* (see step 4). Set your output
> device **first**, then restart capture, then verify.

---

## 0. Get the ingest creds

**X:** in the **Create Livestream** dialog → Source → **Show RTMP**:
- **Server:** `rtmps://ca.pscp.tv:443/x`  (use RTMPS:443, not plain RTMP:80 — many networks block :80)
- **Stream key:** click the 👁 eye icon to reveal, then copy.

`ca.pscp.tv` = Periscope, X's live backend — a standard RTMP ingest.

**Twitch:** Creator Dashboard → Settings → Stream → copy the **Primary Stream key**
(or just use OBS's *Connect Account* and skip the key entirely).

Either way the key is a **secret** — don't paste it anywhere public or commit it.

---

## 1. One-time OBS setup

### Sources (in your Scene)
| Source | Type / setting | Purpose |
|--------|----------------|---------|
| **macOS Screen Capture** | **Display Capture** → pick the display | the *whole screen* (video) |
| **macOS Audio Capture** | Method = **Desktop Audio Capture** | all system audio (livecode/Strudel) |
| **Mic** *(optional)* | Device = **MacBook Pro Microphone** (a real, **non-Bluetooth** mic) | your voice |

- **Whole screen vs. one window:** if the preview shows only a single app window
  (e.g. the Claude window) instead of the full desktop, your screen source is set to
  *Window/Application* capture. Delete it and add **macOS Screen Capture → Display
  Capture**, or in its Properties switch the method to capture a **Display**, then pick
  the monitor you want.
- **Mic device must be explicit — never "Default".** "Default" can resolve to a
  Bluetooth headset and force it into low-quality *headset mode* (kills playback). Pin
  it to the built-in mic.

### Audio mixer (dedupe!)
- **Mute macOS Screen Capture in the mixer** (click its 🔊 so it shows the red-X 🔇).
  Screen Capture *also* grabs audio, so if you don't mute it you capture the app sound
  **twice** → echo/phasing. Muting in the mixer only kills its audio; the video stays.
- Keep **macOS Audio Capture** unmuted — that's your single app-audio path.
- **Mic:** leave muted for a pure music/visuals stream; unmute (its 🔊) only when you
  want to talk, and pull its fader down so peaks sit around −6 to −12 dB (it clips easily).

### Settings → Audio
- Sample Rate **48 kHz**, Channels **Stereo**.
- **Global Audio Devices → all Disabled.** In particular set **Mic/Auxiliary Audio =
  Disabled** — otherwise it's a *second* mic channel doubling your voice and another
  thing that can grab the Bluetooth headset.

### Advanced Audio Properties (mixer → Options → Advanced Audio Properties)
- Every source: **Monitoring = Monitor Off**, **Track 1** checked.
- Note: **"Monitor Off" does NOT mean muted from the stream** — it means OBS won't echo
  it back to your ears (you already hear it via the system output). Monitor Off = in the
  stream, no self-echo. That's what you want.

### Settings → Stream
Use the platform table at the top of this doc:
- **X:** Service **Custom** → Server `rtmps://ca.pscp.tv:443/x` → paste the revealed X key.
- **Twitch:** Service **Twitch** → *Connect Account* (OAuth), or Custom → `rtmp://live.twitch.tv/app` + your Twitch stream key.

---

## 2. macOS audio routing (monitoring)

You do **not** need BlackHole or a Multi-Output Device — OBS's Desktop Audio Capture taps
the system audio directly. (BlackHole was only ever needed by the defunct `stream.py`
FFmpeg path; it's safe to leave uninstalled. If a virtual device is *selected* as your
output, you hear nothing — that's the "it gets in the way" trap, so keep output on real
headphones.)

- **System OUTPUT → your headphones** (closed-back, so no speaker→mic bleed). This is how
  you monitor — you just hear the system audio normally.
- **System INPUT → a non-Bluetooth mic** (MacBook Pro Mic / Creative Pebble). Keep every
  app's mic off the Bluetooth headset, or macOS drops it into mono "headset (HFP)" mode
  and playback goes silent/garbled.
- Bluetooth headphones work but add latency and, if they disconnect (battery dies), that's
  a device change → silent capture (see the rule up top). **For a real stream, charge them
  or go wired.**

---

## 3. Pre-flight (every time, in this order)

1. Connect/select your **headphones as system output** (menu-bar sound or Audio MIDI Setup).
2. Confirm **system input** is a non-Bluetooth mic.
3. In OBS, open **macOS Audio Capture → Properties → Restart capture** → OK.
   *(Do this AFTER the output device is set — this is the step everyone forgets.)*
4. Play any audio (Spotify / the livecode session) and confirm the **macOS Audio Capture
   meter bounces**.
5. **Verify the audio actually records** (don't trust the meter — see below).
6. Settings → Stream → confirm Custom + `rtmps://ca.pscp.tv:443/x` + key.
7. **Start Streaming**, then confirm **Go Live** in X's dialog.

---

## 4. Verify audio objectively (meter can lie)

The OBS meter can show green while the recording is silent. Prove it before going live:

```bash
# Start Recording in OBS for ~15s while audio plays, then Stop. Recordings land in ~/Movies.
f=$(ls -t ~/Movies/*.mov ~/Movies/*.mkv ~/Movies/*.mp4 2>/dev/null | head -1)
ffmpeg -hide_banner -i "$f" -af volumedetect -f null /dev/null 2>&1 | grep -E "mean_volume|max_volume"
```

- **Silent (broken):** `mean_volume: -91.0 dB` / `max_volume: -91.0 dB` → hit *Restart capture* and re-test.
- **Good:** roughly `mean ≈ -20 dB`, `max < -3 dB`.

No audio source handy? Generate one from the CLI (Desktop Audio Capture grabs all system sound):
```bash
say -r 150 "Testing OBS desktop audio capture. One two three four five."
```

### Optional: test the full RTMP pipe privately (no going public)
```bash
mediamtx                                          # local RTMP server on :1935 (brew install mediamtx)
# OBS → Stream → Custom → rtmp://localhost:1935/live , key: test → Start Streaming
ffplay -fflags nobuffer rtmp://localhost:1935/live/test   # watch + hear what X would receive
```
When it looks/sounds right, swap the server back to `rtmps://ca.pscp.tv:443/x` + real key.

---

## 5. Troubleshooting quick table

| Symptom | Cause → Fix |
|---------|-------------|
| Stream/recording silent, but meter is green | Output device changed → **Restart capture** on macOS Audio Capture |
| Preview shows one app window, not the desktop | Screen source is Window/App capture → use **Display Capture** |
| Echoey / doubled app audio | Both Screen Capture *and* Audio Capture grabbing sound → **mute Screen Capture in the mixer** |
| Headphones go silent when selected | Something opened the BT headset's *mic* → keep all mic inputs on non-Bluetooth devices |
| Voice doubled | Global **Mic/Auxiliary Audio** still enabled → Settings → Audio → set it Disabled |
| Speakers bleed into the mic | Monitor on **closed headphones**, not speakers; or mute the Mic |

---

## Reference: the working configuration

- **Sources:** macOS Screen Capture (Display), macOS Audio Capture (Desktop Audio Capture), Mic (MacBook Pro Microphone)
- **Mixer:** Audio Capture live · Screen Capture audio muted · Mic muted (unmute to talk)
- **Settings → Audio:** 48 kHz stereo · all Global Audio Devices Disabled
- **Advanced Audio:** all sources Monitor Off, Track 1
- **Stream:** Custom · `rtmps://ca.pscp.tv:443/x` · X stream key
- **macOS:** output = headphones · input = non-Bluetooth mic · no BlackHole / Multi-Output Device
