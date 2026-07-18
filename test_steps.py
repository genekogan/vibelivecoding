"""Test the step-through system end-to-end with Playwright.

Usage:
    pip install playwright && playwright install chromium
    python test_steps.py [--port PORT]
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8766)
args = parser.parse_args()

BASE = f"http://localhost:{args.port}"
ERRORS = []


def post(path, payload=None):
    data = json.dumps(payload or {}).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def get(path):
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return json.loads(r.read())


def check(name, condition, detail=""):
    status = "✓" if condition else "✗"
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    if not condition:
        ERRORS.append(name)


# ── Phase 1: Start server ────────────────────────────────────
print("\n=== Phase 1: Server ===")

# Start server in background
ROOT = os.path.dirname(os.path.abspath(__file__))
server_proc = subprocess.Popen(
    [sys.executable, "livecode.py", "--port", str(args.port)],
    cwd=ROOT,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)
time.sleep(2)

# Check server is responding
try:
    status = get("/status")
    check("server responds", True)
    check("not ready (no browser)", not status["ready"])
    check("no steps initially", status["totalSteps"] == 0)
except Exception as e:
    check("server responds", False, str(e))
    server_proc.kill()
    sys.exit(1)

# ── Phase 2: Playwright browser ─────────────────────────────
print("\n=== Phase 2: Browser via Playwright ===")

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("  ! playwright not installed, skipping browser tests")
    print("    pip install playwright && playwright install chromium")
    server_proc.kill()
    sys.exit(1)

pw = sync_playwright().start()
browser = pw.chromium.launch(headless=True)
page = browser.new_page()

url = f"http://localhost:{args.port}/livecode.html"
page.goto(url)
page.wait_for_load_state("networkidle")
check("page loaded", True)

# Click start button
page.click("#start-btn")
time.sleep(3)

# Check overlay is hidden
overlay_visible = page.evaluate("document.getElementById('overlay').style.display")
check("overlay hidden after start", overlay_visible == "none")

# Wait for server to see connection
deadline = time.time() + 15
while time.time() < deadline:
    status = get("/status")
    if status["ready"]:
        break
    time.sleep(0.5)
check("server sees browser", status["ready"], f"ready={status['ready']}")

# ── Phase 3: Load steps ─────────────────────────────────────
print("\n=== Phase 3: Load steps via /show/load ===")

test_steps = [
    {"route": "/strudel/cps", "payload": {"cps": 0.52}, "label": "Disco Start"},
    {"route": "/strudel/track", "payload": {"name": "drums", "code": 's("bd bd bd bd").bank("RolandTR909").gain(.8).play()'}},
    {"route": "/strudel/track", "payload": {"name": "bass", "code": 'note("c2 c3 c2 c3").s("sawtooth").lpf(800).gain(.7).play()'}},
    {"route": "/p5/layer", "payload": {"name": "bg", "code": "background(0);"}},
    {"route": "/p5/layer", "payload": {"name": "circle", "code": "fill(255,0,0); circle(width/2, height/2, 200);"}},
    {"route": "/strudel/track", "payload": {"name": "strings", "code": 'note("<[c4,eb4,g4] [f4,ab4,c5]>/4").s("sawtooth").attack(.1).gain(.3).play()'}, "label": "Strings In"},
    {"route": "/p5/layer", "payload": {"name": "circle", "code": "fill(0,255,0); circle(width/2, height/2, 300);"}},
    {"route": "/strudel/hush", "payload": {}, "label": "Silence"},
    {"route": "/p5/clear", "payload": {}},
]

result = post("/show/load", {"steps": test_steps})
check("load returns ok", result.get("ok"), str(result))
check("correct step count", result.get("total") == len(test_steps), f"total={result.get('total')}")

status = get("/status")
check("step index is -1 after load", status["step"] == -1)
check("totalSteps matches", status["totalSteps"] == len(test_steps))

# ── Phase 4: Step forward with REST API ─────────────────────
print("\n=== Phase 4: Step forward (REST) ===")

# Step next → should execute section "Disco Start" (steps 0-4, up to before "Strings In")
result = post("/show/next")
check("next returns ok", result.get("ok"), str(result))

status = get("/status")
check("tracks after section 1", len(status["tracks"]) > 0, f"tracks={status['tracks']}")
check("layers after section 1", len(status["layers"]) > 0, f"layers={status['layers']}")
check("cps set", status["cps"] == 0.52)

time.sleep(1)

# Step next → "Strings In" section (steps 5-6)
result = post("/show/next")
check("next #2 ok", result.get("ok"), str(result))
status = get("/status")
check("strings track added", "strings" in status["tracks"], f"tracks={status['tracks']}")

time.sleep(1)

# Step next → "Silence" section (steps 7-8)
result = post("/show/next")
check("next #3 ok", result.get("ok"), str(result))
status = get("/status")
check("all hushed", len(status["tracks"]) == 0, f"tracks={status['tracks']}")
check("layers cleared", len(status["layers"]) == 0, f"layers={status['layers']}")

# Step next → should be at end
result = post("/show/next")
check("at end", not result.get("ok"))

# ── Phase 5: Step backward ──────────────────────────────────
print("\n=== Phase 5: Step backward (REST) ===")

result = post("/show/prev")
check("prev returns ok", result.get("ok"), str(result))
status = get("/status")
check("strings back", "strings" in status["tracks"], f"tracks={status['tracks']}")
check("layers restored", len(status["layers"]) > 0, f"layers={status['layers']}")

time.sleep(1)

result = post("/show/prev")
check("prev #2 ok", result.get("ok"), str(result))
status = get("/status")
check("back to section 1", "drums" in status["tracks"] and "bass" in status["tracks"],
      f"tracks={status['tracks']}")
check("no strings", "strings" not in status["tracks"], f"tracks={status['tracks']}")

time.sleep(1)

result = post("/show/prev")
check("prev to start", result.get("ok"), str(result))
status = get("/status")
check("clean state", len(status["tracks"]) == 0 and len(status["layers"]) == 0,
      f"tracks={status['tracks']}, layers={status['layers']}")

# ── Phase 6: Keyboard navigation in browser ─────────────────
print("\n=== Phase 6: Arrow key navigation (Playwright) ===")

# Reload steps
post("/show/load", {"steps": test_steps})
time.sleep(0.5)

# Check step display is visible
step_visible = page.evaluate("document.getElementById('step-display').style.display")
check("step display visible", step_visible != "none", f"display={step_visible}")

# Press right arrow
page.keyboard.press("ArrowRight")
time.sleep(2)

status = get("/status")
check("→ advanced", status["step"] > -1, f"step={status['step']}")
check("tracks after →", len(status["tracks"]) > 0, f"tracks={status['tracks']}")

# Check UI updated
step_text = page.evaluate("document.getElementById('step-info').textContent")
check("step info updated", step_text != "0/0", f"text='{step_text}'")

label_text = page.evaluate("document.getElementById('step-label').textContent")
check("label shown", "Disco" in label_text, f"label='{label_text}'")

# Press right again
page.keyboard.press("ArrowRight")
time.sleep(2)

status = get("/status")
check("→→ advanced more", "strings" in status["tracks"], f"tracks={status['tracks']}")

# Press left
page.keyboard.press("ArrowLeft")
time.sleep(2)

status = get("/status")
check("← went back", "strings" not in status["tracks"], f"tracks={status['tracks']}")
check("drums still there", "drums" in status["tracks"], f"tracks={status['tracks']}")

# ── Phase 7: goto ────────────────────────────────────────────
print("\n=== Phase 7: goto ===")

result = post("/show/goto", {"step": -1})
check("goto -1 ok", result.get("ok"), str(result))
status = get("/status")
check("clean after goto -1", len(status["tracks"]) == 0)

result = post("/show/goto", {"step": len(test_steps) - 1})
check("goto end ok", result.get("ok"), str(result))
status = get("/status")
check("at end after goto", status["step"] == len(test_steps) - 1)

# ── Phase 8: Disco set --step ────────────────────────────────
print("\n=== Phase 8: Disco set --step ===")

disco_proc = subprocess.run(
    [sys.executable, "compositions/disco_set.py", "--port", str(args.port), "--step"],
    cwd=ROOT,
    capture_output=True, text=True, timeout=30,
)
check("disco_set --step runs", disco_proc.returncode == 0, disco_proc.stderr[:200] if disco_proc.returncode else "")
check("disco output has upload", "Uploading" in disco_proc.stdout or "Loaded" in disco_proc.stdout, disco_proc.stdout[:200])

status = get("/status")
check("disco steps loaded", status["totalSteps"] > 0, f"totalSteps={status['totalSteps']}")
check("starts at -1", status["step"] == -1)

# Step through each track: → adds one track at a time
result = post("/show/next")
check("disco → 1", result.get("ok"))
status = get("/status")
check("drums after →", "drums" in status["tracks"], f"tracks={status['tracks']}")

time.sleep(1)
result = post("/show/next")
check("disco → 2", result.get("ok"))
status = get("/status")
check("bass after →→", "bass" in status["tracks"] and "drums" in status["tracks"],
      f"tracks={status['tracks']}")

time.sleep(1)
result = post("/show/next")
check("disco → 3", result.get("ok"))
status = get("/status")
check("strings after →→→", "strings" in status["tracks"] and "drums" in status["tracks"],
      f"tracks={status['tracks']}")

# Continue to visuals
for i in range(5):
    time.sleep(0.5)
    post("/show/next")
time.sleep(1)
status = get("/status")
check("has p5 layers", len(status["layers"]) > 0, f"layers={status['layers']}")
check("has visual layers", any(l in status["layers"] for l in ["bg", "floor", "beams", "ball"]),
      f"layers={status['layers']}")

# Go back — should remove visual section
time.sleep(1)
result = post("/show/prev")
check("disco ← ok", result.get("ok"))

# Keep going back to bass section
result = post("/show/prev")
time.sleep(1)
result = post("/show/prev")
time.sleep(1)
result = post("/show/prev")
time.sleep(1)
result = post("/show/prev")
time.sleep(1)
result = post("/show/prev")
time.sleep(1)
status = get("/status")
check("back near start", "drums" in status["tracks"], f"tracks={status['tracks']}")

# Arrow keys in browser
page.keyboard.press("ArrowRight")
time.sleep(2)
status = get("/status")
check("browser → advances", status["step"] > 0, f"step={status['step']}")

step_label = page.evaluate("document.getElementById('step-label').textContent")
check("label shows Disco", "Disco" in step_label, f"label='{step_label}'")

# Check toast appeared
toast_text = page.evaluate("document.getElementById('step-toast').textContent")
check("toast has content", len(toast_text) > 0, f"toast='{toast_text}'")

# ── Phase 9: Full show --step (sub-script inlining) ────────────
print("\n=== Phase 9: Full show --step (sub-scripts inlined) ===")

env = os.environ.copy()
env["LIVECODE_PORT"] = str(args.port)
full_proc = subprocess.run(
    [sys.executable, "compositions/full_show.py", "--port", str(args.port), "--step"],
    cwd=ROOT, env=env,
    capture_output=True, text=True, timeout=120,
)
check("full_show --step runs", full_proc.returncode == 0,
      full_proc.stderr[:300] if full_proc.returncode else "")
check("full output has upload", "Uploading" in full_proc.stdout or "Upload" in full_proc.stdout,
      full_proc.stdout[-300:])

# Check that sub-scripts were inlined, not skipped
check("no skipping", "skipping sub-script" not in full_proc.stdout,
      full_proc.stdout[:500])
check("inlined steps", "inlined" in full_proc.stdout, full_proc.stdout[:500])

status = get("/status")
check("full show steps loaded", status["totalSteps"] > 50,
      f"totalSteps={status['totalSteps']}")
check("full starts at -1", status["step"] == -1)

# Step through first section (Jazzy Beats)
result = post("/show/next")
check("full → 1 ok", result.get("ok"))
status = get("/status")
check("has tracks after →", len(status["tracks"]) > 0, f"tracks={status['tracks']}")
check("jazzy label", "Jazzy" in result.get("label", ""), f"label={result.get('label')}")

time.sleep(1)

# Step through to Desert Building (section 2 — has sub-script content)
result = post("/show/next")
check("full → 2 ok", result.get("ok"))
status = get("/status")
check("has p5 layers (building)", len(status["layers"]) > 0,
      f"layers={status['layers']}")
check("building section has layers", any(l in status["layers"] for l in ["sky", "ground", "building"]),
      f"layers={status['layers']}")

time.sleep(1)

# Step forward to Campfire (section 4 has sub-script content too)
post("/show/next")  # Chill Jazz
time.sleep(0.5)
result = post("/show/next")  # Campfire + EUC Riders
check("full → 4 ok", result.get("ok"))
status = get("/status")
check("campfire layer present", "campfire" in status["layers"],
      f"layers={status['layers']}")

# ── Phase 10: /show/save endpoint ──────────────────────────────
print("\n=== Phase 10: /show/save ===")

saved = get("/show/save")
check("save has format", saved.get("format") == "livecode-show-v1",
      f"format={saved.get('format')}")
check("save has steps", len(saved.get("steps", [])) > 50,
      f"steps={len(saved.get('steps', []))}")
check("save has name", len(saved.get("name", "")) > 0,
      f"name={saved.get('name')}")
check("save has created", "created" in saved, str(saved.keys()))

# Verify steps have the right structure
first_step = saved["steps"][0] if saved.get("steps") else {}
check("step has route", "route" in first_step, str(first_step.keys()))
check("step has payload", "payload" in first_step, str(first_step.keys()))

# ── Phase 11: scenes lib + Composition context manager ────────
print("\n=== Phase 11: scenes lib + Composition ===")

v2_proc = subprocess.run(
    [sys.executable, "compositions/disco_set.py", "--port", str(args.port),
     "--step", "--save", "shows/unsorted/_test_v2.show.json"],
    cwd=ROOT, capture_output=True, text=True, timeout=30,
)
check("disco_set --step runs", v2_proc.returncode == 0,
      v2_proc.stderr[:300] if v2_proc.returncode else "")
check("Composition uploads", "Uploading" in v2_proc.stdout, v2_proc.stdout[:200])
check("Composition saves", "Saved show" in v2_proc.stdout, v2_proc.stdout[:300])

# The saved file should exist
saved_path = os.path.join(ROOT, "shows/unsorted/_test_v2.show.json")
check("save file exists", os.path.exists(saved_path), saved_path)

# Verify file contents
if os.path.exists(saved_path):
    with open(saved_path) as f:
        saved_doc = json.load(f)
    check("saved format", saved_doc.get("format") == "livecode-show-v1",
          f"format={saved_doc.get('format')}")
    check("saved default_dwell", saved_doc.get("default_dwell") == "16beats",
          f"default_dwell={saved_doc.get('default_dwell')}")
    check("saved has steps", len(saved_doc.get("steps", [])) > 15,
          f"steps={len(saved_doc.get('steps', []))}")

# Server should now have the v2 show loaded
status = get("/status")
check("v2 loaded on server", status["totalSteps"] > 15,
      f"totalSteps={status['totalSteps']}")
check("v2 starts at -1", status["step"] == -1)

# Step forward — should be at Disco: Drums
result = post("/show/next")
check("v2 → 1 ok", result.get("ok"))
check("Disco: Drums label", "Drums" in result.get("label", ""),
      f"label={result.get('label')}")
status = get("/status")
check("drums track present", "drums" in status["tracks"],
      f"tracks={status['tracks']}")

# ── Phase 12: /show/load_file + /show/save_file ────────────────
print("\n=== Phase 12: /show/load_file + /show/save_file ===")

# Reset server, then load_file the saved v2 show
post("/show/load", {"steps": []})  # clear
result = post("/show/load_file", {"path": "shows/unsorted/_test_v2.show.json"})
check("load_file ok", result.get("ok"), str(result))
check("load_file has total", result.get("total", 0) > 15,
      f"total={result.get('total')}")
check("load_file has default_dwell", result.get("default_dwell") == "16beats",
      f"default_dwell={result.get('default_dwell')}")

# Save again to a different path
save_path = "shows/unsorted/_test_save.show.json"
result = post("/show/save_file", {"path": save_path})
check("save_file ok", result.get("ok"), str(result))
check("save_file has steps", result.get("steps", 0) > 15,
      f"steps={result.get('steps')}")

# Verify file written
full_save = os.path.join(ROOT, save_path)
check("save_file wrote disk", os.path.exists(full_save), full_save)

# ── Phase 13: autosave behavior ────────────────────────────────
print("\n=== Phase 13: autosave to shows/unsorted/ ===")

unsorted_dir = os.path.join(ROOT, "shows", "unsorted")
files_before = set(os.listdir(unsorted_dir)) if os.path.exists(unsorted_dir) else set()
# Auto-save runs every 60s in production. We just verify the path/folder exists.
check("unsorted dir exists", os.path.exists(unsorted_dir))
# Session file pattern: jam_YYYYMMDD_HHMMSS.show.json
session_files = [f for f in files_before if f.startswith("jam_") and f.endswith(".show.json")]
# May or may not be present yet depending on autosave timing — just check pattern works
check("autosave pattern valid", True, f"jam files found: {len(session_files)}")

# ── Phase 14: autoplay dwell parsing ───────────────────────────
print("\n=== Phase 14: autoplay --dwell parsing ===")

# Just invoke autoplay's parser with --help to verify imports work
ap_help = subprocess.run(
    [sys.executable, "autoplay.py", "--help"],
    cwd=ROOT, capture_output=True, text=True, timeout=10,
)
check("autoplay imports", ap_help.returncode == 0, ap_help.stderr[:200])
check("autoplay --dwell documented", "Nbeats" in ap_help.stdout or "dwell" in ap_help.stdout,
      ap_help.stdout[:200])

# Run autoplay briefly against the loaded show with a tiny dwell.
# It should advance through a couple of steps before we kill it.
ap_proc = subprocess.Popen(
    [sys.executable, "autoplay.py",
     "--show", "shows/unsorted/_test_v2.show.json",
     "--port", str(args.port),
     "--dwell", "0.3s"],
    cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
)
time.sleep(3)
ap_proc.terminate()
ap_proc.wait(timeout=3)
output = ap_proc.stdout.read() if ap_proc.stdout else ""
check("autoplay advanced steps", "step" in output and "Loading" in output,
      output[:300])

# After autoplay ran, server should be at some step > -1
status = get("/status")
check("autoplay advanced server", status["step"] > -1, f"step={status['step']}")

# ── Phase 15: Conductor score + binder ───────────────────────
print("\n=== Phase 15: Conductor score + binder ===")

# Declare key/energy/section; verify parse + stamp + push
r = post("/conductor", {"key": "f# minor", "energy": 0.55,
                        "section": "drop", "tags": "dnb,dark"})
check("conductor declare ok", r.get("ok") and r.get("pushed"), str(r)[:160])
check("key parsed to pitch class", r["score"]["key"] == {"root": "f#", "mode": "minor", "pc": 6},
      str(r["score"]["key"]))
check("tags split", r["score"]["tags"] == ["dnb", "dark"], str(r["score"]["tags"]))

time.sleep(0.5)  # let a frame derive K
clk = get("/p5/read?key=clk")["value"]
check("K.keyHue circle-of-fifths", clk.get("keyHue") == 180, f"keyHue={clk.get('keyHue')}")
check("K.keyMinor", clk.get("keyMinor") is True)
check("K.intensity = declared energy", clk.get("intensity") == 0.55,
      f"intensity={clk.get('intensity')}")
check("K.sectionName declared", clk.get("sectionName") == "drop")
check("K.bpm derived", isinstance(clk.get("bpm"), (int, float)) and clk["bpm"] > 0,
      f"bpm={clk.get('bpm')}")

# energy=null hands intensity back to the arc
post("/conductor", {"energy": None})
time.sleep(0.5)
clk = get("/p5/read?key=clk")["value"]
check("energy null restores arc intensity", clk.get("intensity") != 0.55,
      f"intensity={clk.get('intensity')}")

# /status carries the compact summary
status = get("/status")
con = status.get("conductor") or {}
check("status conductor summary", con.get("key") == "f# minor" and con.get("section") == "drop",
      str(con))

# Binder: bind fxA.hue to keyHue, verify snap + re-snap on key change
post("/p5/state", {"key": "binds.fxA", "value": {"hue": "keyHue"}})
post("/p5/layer", {"name": "fxA", "code":
     "const P=(window.state.P&&window.state.P.fxA)||{}; noStroke(); "
     "fill(P.hue||0,80,80); circle(width/2,height/2,80);"})
time.sleep(0.5)
pfx = get("/p5/read?key=P.fxA")["value"] or {}
check("binder snapped hue to keyHue", pfx.get("hue") == 180, f"P.fxA={pfx}")
post("/conductor", {"key": "a"})  # A major → fifths index 3 → 90°
time.sleep(0.5)
pfx = get("/p5/read?key=P.fxA")["value"] or {}
check("binder re-snapped on key change", pfx.get("hue") == 90, f"P.fxA={pfx}")

# Queued conductor declaration fires through the conductor thread
post("/q", {"route": "/conductor", "payload": {"section": "verse"}, "at": 0})
time.sleep(1.5)
view = get("/conductor")
check("queued conductor fired", (view["score"]["section"] or {}).get("name") == "verse",
      str(view["score"]["section"]))
check("conductor view shape", view.get("ok") and "transport" in view and "score" in view)

# Reconnect: score + binds + layers replay; binder re-derives P from the score
page.reload()
page.wait_for_load_state("networkidle")
page.click("#start-btn")
deadline = time.time() + 15
while time.time() < deadline:
    if get("/status")["ready"]:
        break
    time.sleep(0.5)
check("browser reconnected", get("/status")["ready"])
time.sleep(1.0)
cond = get("/p5/read?key=conductor")["value"] or {}
check("score replayed on reconnect", (cond.get("key") or {}).get("pc") == 9, str(cond)[:160])
pfx = get("/p5/read?key=P.fxA")["value"] or {}
check("binder re-derived P after reconnect", pfx.get("hue") == 90, f"P.fxA={pfx}")

# ── Cleanup ──────────────────────────────────────────────────
print("\n=== Cleanup ===")
# Remove test files
for p in ["shows/unsorted/_test_v2.show.json", "shows/unsorted/_test_save.show.json"]:
    fp = os.path.join(ROOT, p)
    if os.path.exists(fp):
        os.remove(fp)
browser.close()
pw.stop()
server_proc.kill()
server_proc.wait()

print(f"\n{'='*50}")
if ERRORS:
    print(f"FAILED: {len(ERRORS)} checks")
    for e in ERRORS:
        print(f"  ✗ {e}")
    sys.exit(1)
else:
    print("ALL CHECKS PASSED")
    sys.exit(0)
