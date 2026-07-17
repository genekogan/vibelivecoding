"""Full show — complete performance arc, perfectly reproducible.

Usage:
  python livecode.py --port 8776
  # open http://localhost:8776/livecode.html, click Start
  python compositions/full_show.py [--port PORT] [--section N]

Sections (in order):
  1. Jazzy Beats — 707 drums, walking bass, jazz chord stabs, pentatonic lead
  2. Desert Building — pallet rack structure, plywood panels, stairs, debris
  3. Chill Jazz — vibraphone, slower, deeper reverb, ambient pad
  4. Campfire + EUC Riders — cartoon riders circling fire on electric unicycles
  5. Mix it Up — extended jazz, more complex patterns
  6. Vibe Down — relaxed, stripped back
  7. Walking Bass — upright-style walking line
  8. Vox + Drums — vocal samples, cowbell, more fills
  9. Projection Mural — generative art on building (recursive scene + voronoi)
  10. Hip Hop — 808 boom-bap, sub bass, half-time
  11. DnB Transition — tempo steps 0.42→0.50→0.60→0.72→0.85
  12. Jungle Improvise — chopped breaks, reese bass, visual chaos, breakdown, drop
  13. Disco — full 6-track arrangement (Cm→Fm→Ab→Gm)
  14. Disco Visuals — ball, floor, beams, starburst, rings, sparkles
  15. Disco Dancers — roller-skating soloist + backup dancers, Staying Alive choreo
  16. Breakdown — strip to sparse kick, rebuild through 5 stages
  17. Crescendo — push 125→134→144→156 BPM, max everything
  18. Decrescendo — peel layers off one by one
  19. Finale — soloist alone, strings swell, one hit, white flash, fade to black

Each section file is self-contained. This script runs them in sequence.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8776)
parser.add_argument("--section", type=int, default=0, help="Start from section (0=beginning)")
parser.add_argument("--step", action="store_true", help="Step-through mode: pause between sections, advance with arrow keys in browser")
args = parser.parse_args()

BASE = f"http://localhost:{args.port}"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


_pending_steps = []  # collected in --step mode


STEP_ROUTES = {
    "/strudel/track", "/strudel/stop", "/strudel/hush", "/strudel/cps",
    "/strudel/send",
    "/p5/layer", "/p5/remove", "/p5/clear", "/p5/setup", "/p5/state", "/p5/fps",
}


def _post_raw(path, payload=None):
    """Always send to server (used for /show/* and /strudel/send)."""
    data = json.dumps(payload or {}).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def post(path, payload=None):
    if args.step and path in STEP_ROUTES:
        _pending_steps.append({"route": path, "payload": dict(payload or {})})
        return {"ok": True}
    return _post_raw(path, payload)


def wait_ready(timeout=300):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{BASE}/status") as r:
                if json.loads(r.read())["ready"]:
                    return
        except Exception:
            pass
        time.sleep(0.5)
    raise TimeoutError("browser never connected")


def track(name, code):
    post("/strudel/track", {"name": name, "code": code})


def layer(name, code):
    post("/p5/layer", {"name": name, "code": code})


def stop(name):
    try:
        post("/strudel/stop", {"name": name})
    except Exception:
        pass


def remove(name):
    try:
        post("/p5/remove", {"name": name})
    except Exception:
        pass


def mark(label):
    """Insert a section boundary marker (visible in browser footer)."""
    if args.step:
        # Insert a no-op marker that labels this section boundary
        _pending_steps.append({"route": "/show/mark", "payload": {}, "label": label})
    else:
        _post_raw("/show/mark", {"label": label})


def pause(seconds):
    """Sleep in auto mode, no-op in step mode."""
    if not args.step:
        time.sleep(seconds)


SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")


def run_script(filename):
    """Run a sibling script in compositions/scripts/, passing port via LIVECODE_PORT."""
    path = os.path.join(SCRIPTS_DIR, filename)
    env = os.environ.copy()
    env["LIVECODE_PORT"] = str(args.port)
    if args.step:
        # Run sub-script with --dump-steps and capture its JSON output
        result = subprocess.run(
            [sys.executable, path, "--dump-steps"],
            cwd=ROOT, env=env,
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            print(f"  [step mode] ERROR running {filename}: {result.stderr[:200]}")
            return
        try:
            steps = json.loads(result.stdout)
            _pending_steps.extend(steps)
            print(f"  [step mode] inlined {len(steps)} steps from {filename}")
        except json.JSONDecodeError:
            print(f"  [step mode] ERROR: bad JSON from {filename}: {result.stdout[:200]}")
        return
    subprocess.run([sys.executable, path], cwd=ROOT, env=env)


print("Waiting for browser…")
wait_ready()
print("Connected. Starting show.\n")

# In step mode, skip all time.sleep calls — we're just collecting commands
if args.step:
    time.sleep = lambda _: None

# Load samples
post("/strudel/send", {"code": "samples('https://strudel.b-cdn.net/tidal-drum-machines.json', 'https://strudel.b-cdn.net/tidal-drum-machines/machines/')"})
time.sleep(1)

# ═══════════════════════════════════════════════════════════════
# SECTION 1: JAZZY BEATS
# ═══════════════════════════════════════════════════════════════
if args.section <= 1:
    print("═══ 1. Jazzy Beats ═══")

    mark("Jazzy Beats")
    post("/strudel/hush")
    post("/p5/clear")
    time.sleep(0.5)
    post("/strudel/cps", {"cps": 0.5})

    track("drums", '''
s("bd ~ [~ bd] ~, ~ sd ~ sd, [hh oh] hh [hh oh] hh, ~ ~ [~ rim] ~")
  .bank("RolandTR707")
  .gain(".9 .4 .6 .3 .8 .5 .7 .4")
  .room(.2)
  .play()
''')
    time.sleep(2)

    track("bass", '''
note("<a2 e2 g2 d2>(3,8)")
  .scale("A2:dorian")
  .s("triangle")
  .lpf(800).shape(.2)
  .gain(.7)
  .room(.15)
  .play()
''')
    time.sleep(2)

    track("chords", '''
chord("<Am9 D13 Gmaj7 Cmaj7>/2")
  .dict("ireal").voicing()
  .struct("[~ x] [x ~] [~ x] [~ [x ~]]")
  .s("square")
  .lpf(1400)
  .attack(.005).decay(.3).sustain(.1)
  .gain(.45)
  .room(.35)
  .play()
''')
    time.sleep(2)

    track("lead", '''
n("<0 2 4 5 [4 2] 0 ~ ~>*2")
  .scale("A4:minor:pentatonic")
  .s("triangle")
  .gain(.45)
  .delay(".5:.375:.4")
  .room(.4)
  .off(1/8, x => x.add(7).gain(.25))
  .play()
''')
    time.sleep(10)

# ═══════════════════════════════════════════════════════════════
# SECTION 2: DESERT BUILDING VISUAL
# ═══════════════════════════════════════════════════════════════
if args.section <= 2:
    print("═══ 2. Desert Building ═══")

    mark("Desert Building")
    run_script("draw_desert_building.py")
    time.sleep(8)

# ═══════════════════════════════════════════════════════════════
# SECTION 3: CHILL JAZZ
# ═══════════════════════════════════════════════════════════════
if args.section <= 3:
    print("═══ 3. Chill Jazz ═══")

    mark("Chill Jazz")
    post("/strudel/cps", {"cps": 0.38})

    track("drums", '''
stack(
  s("bd ~ ~ [~ bd]").bank("RolandTR707").gain(.55).lpf(2400),
  s("~ rim ~ rim").bank("RolandTR707").gain(.4)
    .delay(.5).delaytime(.375).delayfeedback(.55)
    .room(.7).roomsize(5).orbit(2),
  s("[hh oh] hh [hh ~] hh").bank("RolandTR707")
    .gain(".5 .25 .35 .2 .45 .25 .3 .2")
    .pan(sine.range(.35, .65).slow(7))
    .lpf(3500).room(.45)
)
  .play()
''')

    track("bass", '''
note("<a2 ~ e2 ~ g2 ~ d2 ~>(3,8)")
  .scale("A2:dorian")
  .s("sine").add(note("0,0.05"))
  .lpf(450).shape(.15)
  .attack(.02).release(.4)
  .gain(.55)
  .room(.45).roomsize(4).orbit(3)
  .play()
''')

    track("chords", '''
chord("<Am9 D13 Gmaj7 Cmaj7>/4")
  .dict("ireal").voicing()
  .struct("[~ ~ x ~] [~ x ~ ~]")
  .s("triangle").add(note("0,0.07"))
  .lpf(900).attack(.4).release(1.2)
  .gain(.32)
  .room(.75).roomsize(6)
  .delay(.25).delaytime(.5).delayfeedback(.35)
  .orbit(4)
  .play()
''')

    track("lead", '''
n("<0 ~ 2 ~ ~ 4 ~ 2 ~ 0 ~ ~>")
  .scale("A4:minor:pentatonic")
  .s("triangle")
  .gain(.35)
  .attack(.05).release(.6)
  .delay(.65).delaytime(.5).delayfeedback(.55)
  .room(.85).roomsize(8)
  .lpf(sine.range(1200, 2800).slow(24))
  .pan(sine.range(.3, .7).slow(13))
  .off(1/4, x => x.add(7).gain(.18))
  .orbit(5)
  .play()
''')

    track("pad", '''
note("<[a3,c4,e4] [d4,f4,a4] [g3,b3,d4] [c4,e4,g4]>/8")
  .s("sawtooth").add(note("0,0.1,-0.08"))
  .attack(3).release(5)
  .lpf(sine.range(300, 1100).slow(32))
  .gain(.18)
  .room(.9).roomsize(10)
  .orbit(6)
  .play()
''')
    time.sleep(12)

# ═══════════════════════════════════════════════════════════════
# SECTION 4: CAMPFIRE + EUC RIDERS
# ═══════════════════════════════════════════════════════════════
if args.section <= 4:
    print("═══ 4. Campfire + EUC Riders ═══")

    mark("Campfire + EUC Riders")
    run_script("draw_campfire.py")
    time.sleep(12)

# ═══════════════════════════════════════════════════════════════
# SECTION 5: MIX IT UP
# ═══════════════════════════════════════════════════════════════
if args.section <= 5:
    print("═══ 5. Mix It Up ═══")

    mark("Mix It Up")
    post("/strudel/cps", {"cps": 0.42})

    track("drums", '''
stack(
  s("bd ~ ~ [~ bd] ~ ~ bd ~").bank("RolandTR707").gain(.55).lpf(2400)
    .sometimesBy(.12, x => x.fast(2)),
  s("~ ~ rim ~ ~ rim ~ [~ rim]").bank("RolandTR707").gain(.42)
    .delay(.6).delaytime(.375).delayfeedback(.55)
    .room(.7).roomsize(5).orbit(2),
  s("[hh oh] hh [hh ~] [hh oh] [hh ~] [oh hh] [hh ~] hh").bank("RolandTR707")
    .gain("[.5 .25 .35 .2] [.45 .3 .25 .15] [.45 .25 .4 .2] [.5 .35 .25 .3]")
    .pan(sine.range(.3, .7).slow(11))
    .lpf(3500).room(.45),
  s("~ ~ ~ ~ ~ ~ ~ cp").bank("RolandTR707")
    .every(8, x => x.fast(2))
    .gain(.35).room(.55).delay(.3).delaytime(.25).orbit(7)
)
  .play()
''')

    track("bass", '''
note("<a2 [a2 e3] g2 [d2 a2] f2 [c3 g2] e2 [b2 e2]>")
  .scale("A2:dorian")
  .s("sine").add(note("0,0.05"))
  .lpf(perlin.range(360, 700).slow(12)).shape(.18)
  .attack(.02).release(.45)
  .gain(.55)
  .sometimesBy(.18, x => x.add(12))
  .room(.45).roomsize(4).orbit(3)
  .play()
''')

    track("chords", '''
chord("<Am9 D13 Gmaj9 Cmaj7 F#m7b5 B7b9 Em9 A13>/4")
  .dict("ireal").voicing()
  .struct("[~ ~ x ~] [~ x ~ x] [~ ~ x ~] [x ~ x ~]")
  .s("triangle").add(note("0,0.07,-0.05"))
  .lpf(sine.range(700, 1400).slow(20))
  .attack(.4).release(1.4)
  .gain(.32)
  .room(.78).roomsize(7)
  .delay(.3).delaytime(.5).delayfeedback(.42)
  .orbit(4)
  .play()
''')

    track("lead", '''
n("<[0 ~ 2 ~] [4 ~ ~ 5] [~ 7 ~ 4] [2 ~ 0 ~] [~ 5 7 ~] [9 ~ 7 5] [4 ~ 2 ~] [0 ~ ~ ~]>")
  .scale("<A4:minor:pentatonic A4:minor:pentatonic G4:major:pentatonic G4:major:pentatonic F#4:locrian B3:phrygian E4:dorian A4:minor:pentatonic>/4")
  .s("triangle")
  .gain(.36)
  .attack(.04).release(.7)
  .delay(.7).delaytime(.5).delayfeedback(.55)
  .room(.85).roomsize(8)
  .lpf(sine.range(1200, 3000).slow(24))
  .pan(sine.range(.25, .75).slow(9))
  .off(1/4, x => x.add(7).gain(.2))
  .sometimesBy(.18, x => x.add(12))
  .every(8, x => x.echo(3, 1/8, .55))
  .orbit(5)
  .play()
''')

    track("pad", '''
note("<[a3,c4,e4,g4] [d4,f#4,a4,c5] [g3,b3,d4,f#4] [c4,e4,g4,b4] [f#3,a3,c4,e4] [b3,d#4,f#4,a4] [e3,g3,b3,d4] [a3,c#4,e4,g4]>/16")
  .s("sawtooth").add(note("0,0.1,-0.08,0.06"))
  .attack(4).release(6)
  .lpf(sine.range(280, 1100).slow(40))
  .gain(perlin.range(.12, .22).slow(20))
  .room(.92).roomsize(10)
  .orbit(6)
  .play()
''')

    track("sparkle", '''
n("<~ ~ [12 ~ 7 ~] ~>")
  .scale("A5:minor:pentatonic")
  .s("sine")
  .attack(.005).decay(.4).sustain(0).release(.3)
  .gain(.32)
  .pan(rand)
  .delay(.7).delaytime(.375).delayfeedback(.6)
  .room(.85).roomsize(9)
  .lpf(4500)
  .every(3, x => x.add(7))
  .orbit(7)
  .play()
''')
    time.sleep(12)

# ═══════════════════════════════════════════════════════════════
# SECTION 6: VIBE DOWN
# ═══════════════════════════════════════════════════════════════
if args.section <= 6:
    print("═══ 6. Vibe Down ═══")

    mark("Vibe Down")
    post("/strudel/cps", {"cps": 0.40})
    stop("sparkle")

    track("drums", '''
stack(
  s("bd ~ ~ [~ bd] ~ ~ bd ~").bank("RolandTR707").gain(.5).lpf(2200),
  s("[hh ~] hh [~ hh] hh").bank("RolandTR707")
    .gain(".4 .2 .25 .15")
    .pan(sine.range(.4, .6).slow(11))
    .lpf(3000).room(.3)
)
  .play()
''')

    track("bass", '''
note("<a2 ~ e2 g2 ~ d2 ~ ~>")
  .scale("A2:dorian")
  .s("sine")
  .lpf(420).shape(.12)
  .attack(.02).release(.5)
  .gain(.5)
  .room(.35).roomsize(3).orbit(3)
  .play()
''')

    track("chords", '''
chord("<Am9 D13 Gmaj9 Cmaj7 Fmaj7 Em9 Dm9 Am9>/4")
  .dict("ireal").voicing()
  .struct("[~ x ~ ~] [~ ~ x ~]")
  .s("sine")
  .attack(.003).decay(.7).sustain(0).release(.6)
  .gain(.42)
  .vib(5).vibmod(.15)
  .lpf(3500)
  .room(.55).roomsize(5)
  .delay(.18).delaytime(.375).delayfeedback(.18)
  .orbit(4)
  .play()
''')

    track("lead", '''
n("<[0 ~ 2 ~] [~ 4 ~ ~] [5 ~ 4 2] [~ ~ 0 ~] [~ 2 4 ~] [7 ~ 5 ~] [4 ~ 2 ~] [0 ~ ~ ~]>")
  .scale("A4:minor:pentatonic")
  .s("sine")
  .attack(.003).decay(.6).sustain(0).release(.5)
  .gain(.42)
  .vib(5.5).vibmod(.18)
  .lpf(4500)
  .pan(sine.range(.35, .65).slow(13))
  .delay(.22).delaytime(.5).delayfeedback(.20)
  .room(.6).roomsize(5)
  .orbit(5)
  .play()
''')

    track("pad", '''
note("<[a3,c4,e4] [d4,f#4,a4] [g3,b3,d4] [c4,e4,g4]>/16")
  .s("triangle").add(note("0,0.05"))
  .attack(4).release(6)
  .lpf(sine.range(320, 900).slow(36))
  .gain(.13)
  .room(.7).roomsize(7)
  .orbit(6)
  .play()
''')
    time.sleep(10)

# ═══════════════════════════════════════════════════════════════
# SECTION 7: WALKING BASS
# ═══════════════════════════════════════════════════════════════
if args.section <= 7:
    print("═══ 7. Walking Bass ═══")

    mark("Walking Bass")

    track("chords", '''
chord("<Am9 D13 Gmaj9 Cmaj7 Fmaj7 Em9 Dm9 Am9>/8")
  .dict("ireal").voicing()
  .struct("[~ x ~ ~] [~ ~ x ~]")
  .s("sine")
  .attack(.003).decay(.7).sustain(0).release(.6)
  .gain(.4)
  .vib(5).vibmod(.15)
  .lpf(3500)
  .room(.55).roomsize(5)
  .delay(.18).delaytime(.375).delayfeedback(.18)
  .orbit(4)
  .play()
''')

    track("bass", '''
note("<[a2 c3 e3 eb3] [d2 f#2 a2 ab2] [g2 b2 d3 b2] [c3 e3 g3 e3] [f2 a2 c3 f2] [e2 g2 b2 eb3] [d2 f2 a2 bb2] [a2 c3 e3 bb2]>/8")
  .s("sawtooth")
  .lpf(720).shape(.28)
  .attack(.005).decay(.18).sustain(.25).release(.15)
  .clip(.88)
  .gain(.6)
  .room(.28).roomsize(3).orbit(3)
  .play()
''')
    time.sleep(10)

# ═══════════════════════════════════════════════════════════════
# SECTION 8: VOX + DRUMS
# ═══════════════════════════════════════════════════════════════
if args.section <= 8:
    print("═══ 8. Vox + Drums ═══")

    mark("Vox + Drums")
    post("/strudel/send", {"code": "samples('github:tidalcycles/dirt-samples')"})
    time.sleep(2)

    track("drums", '''
stack(
  s("bd ~ [~ bd] ~ ~ bd [~ bd] ~").bank("RolandTR707")
    .gain(.5).lpf(2200)
    .every(16, x => x.struct("bd bd [bd bd] bd")),
  s("[hh ~] [hh hh] [oh hh] [hh ~] [hh hh] [~ hh] [oh hh] [hh ~]").bank("RolandTR707")
    .gain(saw.range(.18, .5).fast(2))
    .pan(sine.range(.3, .7).slow(13))
    .lpf(3000).room(.3),
  s("~ ~ rim ~ ~ ~ ~ [~ rim]").bank("RolandTR707").gain(.36)
    .delay(.32).delaytime(.5).delayfeedback(.22)
    .room(.55).orbit(2),
  s("<~ ~ ~ ~ ~ cb ~ ~>").bank("RolandTR707")
    .gain(.30).pan(.72)
    .delay(.25).delaytime(.375).delayfeedback(.2)
    .room(.5).orbit(2),
  s("~ ~ ~ ~ ~ ~ ~ cp").bank("RolandTR707")
    .every(8, x => x.fast(2)).gain(.32)
    .delay(.35).room(.55).orbit(2)
)
  .play()
''')

    track("vox", '''
s("<[~ ~ bev:1 ~] [~ ~ ~ ~] [~ bev:3 ~ ~] [~ ~ ~ ~] [~ ~ bev:0 ~] [~ ~ ~ ~] [bev:2 ~ ~ ~] [~ ~ ~ ~]>")
  .speed("<.92 1.0 1.08 .96>")
  .gain(.42)
  .lpf(1800)
  .pan(sine.range(.25, .75).slow(7))
  .delay(.55).delaytime(.5).delayfeedback(.35)
  .room(.78).roomsize(7)
  .orbit(8)
  .play()
''')

    track("breathfx", '''
s("<~ ~ ~ ~ ~ ~ ~ breath:0>/2")
  .rev()
  .gain(.32)
  .speed(.85)
  .lpf(2000)
  .pan(rand)
  .delay(.4).delaytime(.5).delayfeedback(.25)
  .room(.85).roomsize(8)
  .orbit(8)
  .play()
''')
    time.sleep(10)

# ═══════════════════════════════════════════════════════════════
# SECTION 9: PROJECTION MURAL (recursive scene + voronoi)
# ═══════════════════════════════════════════════════════════════
if args.section <= 9:
    print("═══ 9. Projection Mural ═══")

    mark("Projection Mural")
    run_script("projection_mural.py")
    time.sleep(10)

# ═══════════════════════════════════════════════════════════════
# SECTION 10: HIP HOP
# ═══════════════════════════════════════════════════════════════
if args.section <= 10:
    print("═══ 10. Hip Hop ═══")

    mark("Hip Hop")
    post("/strudel/cps", {"cps": 0.36})
    stop("breathfx")

    track("drums", '''
stack(
  s("bd ~ ~ [~ bd] ~ bd ~ ~").bank("RolandTR808").gain(.85).shape(.25)
    .sometimesBy(.18, x => x.struct("bd ~ ~ bd")),
  s("~ ~ sd ~ ~ ~ sd [~ sd]").bank("RolandTR808").gain(.7)
    .room(.45).delay(.18).delaytime(.25).delayfeedback(.2),
  s("hh*8").bank("RolandTR808")
    .gain("[.45 .25 .35 .2 .4 .25 .35 .2]*1")
    .pan(sine.range(.4, .6).slow(11))
    .lpf(4500)
    .every(8, x => x.fast(2))
    .sometimesBy(.08, x => x.ply(3)),
  s("~ ~ ~ oh ~ ~ ~ ~").bank("RolandTR808").gain(.45).pan(.62).lpf(4000),
  s("~ ~ ~ ~ ~ ~ ~ cp").bank("RolandTR707")
    .every(16, x => x.struct("cp ~ cp ~"))
    .gain(.4).room(.55).delay(.3).delaytime(.5).delayfeedback(.25).orbit(2)
)
  .play()
''')

    track("bass", '''
note("<a1 ~ a1 ~ d2 ~ ~ ~ g1 ~ g1 ~ c2 ~ ~ ~ f1 ~ f1 ~ e2 ~ ~ ~ d2 ~ d2 ~ a1 ~ ~ ~>/4")
  .s("sine").shape(.45)
  .lpf(220)
  .attack(.01).decay(.1).sustain(.7).release(.3)
  .gain(.85)
  .room(.2).orbit(3)
  .play()
''')

    track("chords", '''
chord("<Am9 D13 Gmaj9 Cmaj7 Fmaj7 Em9 Dm9 Am9>/8")
  .dict("ireal").voicing()
  .struct("[~ ~ x ~ ~ ~ ~ ~] [~ ~ ~ ~ ~ x ~ x]")
  .s("sine")
  .attack(.003).decay(.7).sustain(0).release(.5)
  .gain(.4)
  .vib(5).vibmod(.15)
  .lpf(3500)
  .room(.55).roomsize(5)
  .delay(.18).delaytime(.5).delayfeedback(.18)
  .orbit(4)
  .play()
''')

    track("lead", '''
n("<[~ ~ 0 ~ 2 ~ ~ ~] [~ ~ ~ ~ ~ 4 ~ 2] [~ 5 ~ 4 ~ 2 ~ ~] [~ ~ ~ ~ ~ ~ ~ ~]>/2")
  .scale("A4:minor:pentatonic")
  .s("sine")
  .attack(.003).decay(.5).sustain(0).release(.4)
  .gain(.38)
  .vib(5).vibmod(.18)
  .lpf(4200)
  .pan(sine.range(.3, .7).slow(11))
  .delay(.3).delaytime(.5).delayfeedback(.25)
  .room(.6).roomsize(5)
  .orbit(5)
  .play()
''')

    track("pad", '''
note("<[a3,c4,e4] [d4,f#4,a4] [g3,b3,d4] [c4,e4,g4]>/16")
  .s("triangle").add(note("0,0.05"))
  .attack(4).release(6)
  .lpf(sine.range(280, 800).slow(36))
  .gain(.10)
  .room(.7).roomsize(7)
  .orbit(6)
  .play()
''')

    track("vox", '''
s("<[~ ~ ~ ~ ~ bev:1 ~ ~] [~ ~ ~ ~ ~ ~ bev:3 bev:0] [~ bev:2 ~ ~ ~ ~ ~ ~] [~ ~ ~ ~ bev:1 ~ bev:3 ~]>/2")
  .speed("<.92 1.05 .98 1.0 1.1 .9>")
  .gain(.5)
  .lpf(2200)
  .pan(sine.range(.3, .7).slow(7))
  .delay(.4).delaytime(.375).delayfeedback(.3)
  .room(.65).roomsize(6)
  .orbit(8)
  .play()
''')
    time.sleep(12)

# ═══════════════════════════════════════════════════════════════
# SECTION 11: DnB TRANSITION
# ═══════════════════════════════════════════════════════════════
if args.section <= 11:
    print("═══ 11. DnB Transition ═══")

    mark("DnB Transition")
    stop("vox")
    stop("breathfx")

    # Stage 1: 0.42 → 0.50
    post("/strudel/cps", {"cps": 0.50})
    track("drums", '''
stack(
  s("bd ~ ~ ~ ~ ~ bd ~, ~ ~ sd ~ ~ ~ ~ sd").bank("RolandTR909").gain(.75)
    .shape(.2).room(.25),
  s("hh*16").bank("RolandTR909")
    .gain(saw.range(.15, .45).fast(4))
    .pan(sine.range(.35, .65).slow(7))
    .lpf(4500).room(.2)
)
  .play()
''')
    time.sleep(6)

    # Stage 2: 0.60
    post("/strudel/cps", {"cps": 0.60})
    track("bass", '''
note("<a1 ~ ~ ~ ~ ~ ~ ~ g1 ~ ~ ~ ~ ~ ~ ~ f1 ~ ~ ~ ~ ~ ~ ~ e1 ~ ~ ~ ~ ~ ~ ~>/4")
  .s("sine").shape(.5)
  .lpf(180)
  .attack(.01).decay(.15).sustain(.6).release(.25)
  .gain(.85)
  .room(.15).orbit(3)
  .play()
''')
    time.sleep(6)

    # Stage 3: 0.72
    post("/strudel/cps", {"cps": 0.72})
    track("drums", '''
stack(
  s("bd ~ [~ bd] ~ ~ bd ~ ~, ~ ~ sd ~ ~ [~ sd] sd ~").bank("RolandTR909")
    .gain(.78).shape(.25)
    .every(8, x => x.fast(2))
    .room(.2),
  s("hh*16").bank("RolandTR909")
    .gain(saw.range(.12, .42).fast(4))
    .pan(sine.range(.3, .7).slow(5))
    .lpf(5000).room(.15),
  s("~ ~ ~ oh ~ ~ ~ ~").bank("RolandTR909")
    .gain(.4).pan(.6).lpf(4200)
)
  .play()
''')

    track("chords", '''
chord("<Am9 Em9 Fmaj7 Dm9>/4")
  .dict("ireal").voicing()
  .struct("[~ ~ x ~ ~ ~ ~ ~]")
  .s("sine")
  .attack(.003).decay(.8).sustain(0).release(.5)
  .gain(.32)
  .vib(5).vibmod(.12)
  .lpf(2800)
  .room(.6).roomsize(6)
  .delay(.2).delaytime(.25).delayfeedback(.2)
  .orbit(4)
  .play()
''')
    time.sleep(6)

    # Stage 4: 0.85
    post("/strudel/cps", {"cps": 0.85})
    track("drums", '''
stack(
  s("bd ~ [~ bd] ~ ~ [~ bd] ~ ~, ~ ~ sd ~ ~ [~ sd] [sd ~] ~").bank("RolandTR909")
    .gain(.8).shape(.28)
    .every(16, x => x.ply(2))
    .sometimesBy(.08, x => x.speed(1.5))
    .room(.18),
  s("hh*16").bank("RolandTR909")
    .gain("[.42 .18 .30 .12]*4")
    .pan(sine.range(.3, .7).slow(3))
    .lpf(5500).room(.12),
  s("~ ~ ~ oh ~ ~ ~ ~ ~ ~ ~ oh ~ ~ ~ ~").bank("RolandTR909")
    .gain(.35).pan(.62).lpf(4500),
  s("~ ~ ~ ~ ~ ~ ~ ride").bank("RolandTR909")
    .every(4, x => x.struct("[~ ride ~ ~]"))
    .gain(.3).room(.35).orbit(2)
)
  .play()
''')

    track("bass", '''
note("<[a1 ~ a1 ~] [~ ~ ~ ~] [g1 ~ g1 ~] [~ ~ ~ ~] [f1 ~ f1 ~] [~ ~ ~ ~] [e1 ~ ~ e1] [~ ~ ~ ~]>/4")
  .s("sine").shape(.55)
  .lpf(160)
  .attack(.005).decay(.1).sustain(.5).release(.2)
  .gain(.9)
  .room(.12).orbit(3)
  .play()
''')

    track("lead", '''
n("<[0 ~ ~ 2] [~ ~ ~ ~] [4 ~ 5 ~] [~ 2 ~ ~]>/2")
  .scale("A4:minor:pentatonic")
  .s("triangle")
  .attack(.003).decay(.4).sustain(0).release(.3)
  .gain(.35)
  .delay(.45).delaytime(.25).delayfeedback(.35)
  .room(.65).roomsize(6)
  .pan(sine.range(.3, .7).slow(5))
  .orbit(5)
  .play()
''')

    track("pad", '''
note("<[a3,c4,e4] [g3,bb3,d4] [f3,a3,c4] [e3,g3,b3]>/16")
  .s("sawtooth").add(note("0,0.06"))
  .attack(3).release(5)
  .lpf(sine.range(250, 700).slow(32))
  .gain(.12)
  .room(.75).roomsize(8)
  .orbit(6)
  .play()
''')
    time.sleep(8)

# ═══════════════════════════════════════════════════════════════
# SECTION 12: JUNGLE IMPROVISE (full chaos arc)
# ═══════════════════════════════════════════════════════════════
if args.section <= 12:
    print("═══ 12. Jungle Improvise ═══")

    mark("Jungle Improvise")
    run_script("improvise.py")
    time.sleep(5)

# ═══════════════════════════════════════════════════════════════
# SECTION 13: DISCO MUSIC
# ═══════════════════════════════════════════════════════════════
if args.section <= 13:
    print("═══ 13. Disco ═══")

    mark("Disco")
    post("/strudel/hush")
    time.sleep(0.5)
    post("/strudel/cps", {"cps": 0.52})

    # Kill any leftover tracks
    for name in ["drums", "bass", "chords", "lead", "pad", "sparkle", "vox", "breathfx"]:
        stop(name)

    track("drums", '''
stack(
  s("bd bd bd bd").bank("RolandTR909").gain(.82).shape(.2).lpf(3000),
  s("~ cp ~ cp").bank("RolandTR909").gain(.55).room(.35).delay(.12).delaytime(.25).delayfeedback(.15),
  s("~ oh ~ oh ~ oh ~ oh").bank("RolandTR909").gain(.42).pan(.55).lpf(5000),
  s("hh*16").bank("RolandTR909")
    .gain("[.45 .15 .30 .12]*4")
    .pan(sine.range(.4, .6).slow(7))
    .lpf(6000).room(.1),
  s("~ ~ ~ ~ ~ ~ ~ cb").bank("RolandTR707")
    .every(4, x => x.struct("~ cb ~ cb"))
    .gain(.3).pan(.7)
)
  .play()
''')
    time.sleep(3)

    track("bass", '''
note("<[c2 c3 c2 c3] [f2 f3 f2 f3] [ab2 ab3 ab2 ab3] [g2 g3 g2 g3]>")
  .s("sawtooth")
  .lpf(sine.range(400, 1800).slow(8))
  .shape(.35)
  .attack(.005).decay(.12).sustain(.3).release(.1)
  .clip(.8)
  .gain(.72)
  .room(.15).orbit(3)
  .play()
''')
    time.sleep(3)

    track("strings", '''
note("<[c4,eb4,g4,bb4] [f4,ab4,c5,eb5] [ab3,c4,eb4,g4] [g3,bb3,d4,f4]>/4")
  .s("sawtooth").add(note("0,0.08,-0.06"))
  .lpf(sine.range(800, 3500).slow(16))
  .attack(.15).release(1.2)
  .gain(.3)
  .room(.6).roomsize(6)
  .orbit(4)
  .play()
''')
    time.sleep(3)

    track("wah", '''
note("<[c4 ~ eb4 ~] [~ f4 ~ ab4] [~ g4 eb4 ~] [g4 ~ f4 ~]>")
  .s("square")
  .lpf(sine.range(600, 4000).fast(2))
  .lpq(sine.range(3, 12).slow(4))
  .attack(.003).decay(.25).sustain(.08).release(.15)
  .gain(.38)
  .pan(sine.range(.3, .7).slow(5))
  .delay(.2).delaytime(.25).delayfeedback(.2)
  .room(.4).roomsize(3)
  .orbit(5)
  .play()
''')
    time.sleep(3)

    track("clav", '''
note("<[c5 ~ c5 eb5 ~ c5 ~ ~] [f5 ~ f5 ab5 ~ f5 ~ ~] [ab4 ~ ab4 c5 ~ ab4 ~ ~] [g4 ~ bb4 d5 ~ g4 ~ ~]>")
  .s("square")
  .lpf(2800)
  .attack(.001).decay(.08).sustain(0).release(.05)
  .gain(.32)
  .pan(sine.range(.35, .65).fast(3))
  .delay(.15).delaytime(.125).delayfeedback(.25)
  .room(.3)
  .orbit(6)
  .play()
''')
    time.sleep(3)

    track("shimmer", '''
note("<[c5,eb5,g5] [f5,ab5,c6] [ab4,c5,eb5] [g4,bb4,d5]>/8")
  .s("triangle").add(note("0,0.05"))
  .attack(2).release(4)
  .lpf(sine.range(1200, 4000).slow(32))
  .gain(.12)
  .room(.85).roomsize(10)
  .orbit(7)
  .play()
''')
    time.sleep(5)

# ═══════════════════════════════════════════════════════════════
# SECTION 14: DISCO VISUALS
# ═══════════════════════════════════════════════════════════════
if args.section <= 14:
    print("═══ 14. Disco Visuals ═══")

    mark("Disco Visuals")
    post("/p5/clear")
    time.sleep(0.3)
    remove("energy")
    run_script("disco_fx.py")
    time.sleep(8)

# ═══════════════════════════════════════════════════════════════
# SECTION 15: DISCO DANCERS
# ═══════════════════════════════════════════════════════════════
if args.section <= 15:
    print("═══ 15. Disco Dancers ═══")

    mark("Disco Dancers")
    run_script("disco_dancers.py")
    time.sleep(12)

# ═══════════════════════════════════════════════════════════════
# SECTION 16: BREAKDOWN — strip to sparse kick, rebuild
# ═══════════════════════════════════════════════════════════════
if args.section <= 16:
    print("═══ 16. Breakdown ═══")

    mark("Breakdown")
    post("/strudel/hush")
    time.sleep(0.3)

    for lyr in ["beams", "rings", "starburst", "ball", "sparkles", "dancers"]:
        remove(lyr)

    layer("floor", '''
push();
const beat = frameCount / 28.8;
const floorY = height * 0.70;
const tileSize = width / 10;
noStroke();
for (let i = 0; i < 10; i++) {
  for (let j = 0; j < 4; j++) {
    const x = i * tileSize;
    const y = floorY + j * tileSize;
    fill(0, 0, 4 + ((i+j)%2) * 3);
    rect(x, y, tileSize, tileSize);
  }
}
pop();
''')

    time.sleep(0.5)
    post("/strudel/cps", {"cps": 0.52})
    track("drums", 's("bd ~ ~ ~ bd ~ ~ ~").bank("RolandTR909").gain(.4).lpf(800).shape(.1).play()')
    time.sleep(4)

    # Build 1: hats
    track("drums", '''
stack(
  s("bd ~ ~ ~ bd ~ ~ ~").bank("RolandTR909").gain(.5).lpf(1200).shape(.15),
  s("hh*8").bank("RolandTR909").gain(.15).lpf(3000)
).play()
''')
    layer("floor", '''
push();
const beat = frameCount / 28.8;
const floorY = height * 0.70;
const tileSize = width / 10;
noStroke();
for (let i = 0; i < 10; i++) {
  for (let j = 0; j < 4; j++) {
    const x = i * tileSize; const y = floorY + j * tileSize;
    const tilePulse = pow(max(0, sin((beat-(i+j)*0.2)*TAU)), 8);
    if ((i+j)%2===0) fill(0,0,6+tilePulse*15); else fill(0,0,3+tilePulse*5);
    rect(x, y, tileSize, tileSize);
  }
}
pop();
''')
    time.sleep(4)

    # Build 2: bass + more kick
    track("bass", '''
note("<[c2 c3 c2 c3] [f2 f3 f2 f3] [ab2 ab3 ab2 ab3] [g2 g3 g2 g3]>")
  .s("sawtooth").lpf(400).shape(.3)
  .attack(.005).decay(.12).sustain(.3).release(.1)
  .gain(.35).play()
''')
    track("drums", '''
stack(
  s("bd ~ bd ~ bd ~ bd ~").bank("RolandTR909").gain(.55).lpf(1500).shape(.15),
  s("hh*8").bank("RolandTR909").gain(.2).lpf(4000)
).play()
''')
    layer("beams", '''
push();
translate(width/2, height*0.28);
blendMode(ADD);
const beat = frameCount / 28.8;
const a = beat * 0.3;
const hue = (frameCount * 1.5) % 360;
fill(hue, 70, 100, 8); noStroke();
triangle(0, 0, cos(a-0.05)*width, sin(a-0.05)*height, cos(a+0.05)*width, sin(a+0.05)*height);
blendMode(BLEND);
pop();
''')
    time.sleep(4)

    # Build 3: four on floor + clap
    track("drums", '''
stack(
  s("bd bd bd bd").bank("RolandTR909").gain(.65).lpf(2500).shape(.2),
  s("~ cp ~ cp").bank("RolandTR909").gain(.35).room(.2),
  s("hh*8").bank("RolandTR909").gain(.28).lpf(5000)
).play()
''')
    track("bass", '''
note("<[c2 c3 c2 c3] [f2 f3 f2 f3] [ab2 ab3 ab2 ab3] [g2 g3 g2 g3]>")
  .s("sawtooth").lpf(900).shape(.35)
  .attack(.005).decay(.12).sustain(.3).release(.1)
  .gain(.55).play()
''')
    layer("beams", '''
push();
translate(width/2, height*0.28);
blendMode(ADD);
const beat = frameCount / 28.8;
const pulse = pow(sin(beat * TAU), 4);
noStroke();
for (let i = 0; i < 4; i++) {
  const a = i * TAU/4 + frameCount * 0.006;
  const hue = (i * 90 + frameCount * 1.5) % 360;
  fill(hue, 70, 100, 8 + pulse * 10);
  const len = max(width,height)*0.8;
  triangle(0,0, cos(a-0.04)*len, sin(a-0.04)*len, cos(a+0.04)*len, sin(a+0.04)*len);
}
blendMode(BLEND); pop();
''')
    layer("floor", '''
push();
const beat = frameCount / 28.8;
const floorY = height * 0.70;
const tileSize = width / 10;
noStroke();
for (let i = 0; i < 10; i++) {
  for (let j = 0; j < 4; j++) {
    const x = i * tileSize; const y = floorY + j * tileSize;
    const tilePulse = pow(max(0, sin((beat-(i+j)*0.15)*TAU)), 6);
    if ((i+j)%2===0) { const h=(i*36+frameCount*1.5)%360; fill(h, 40+tilePulse*30, 12+tilePulse*30); }
    else fill(0,0, 5+tilePulse*8);
    rect(x, y, tileSize, tileSize);
  }
}
pop();
''')
    time.sleep(4)

    # Build 4: strings + wah + ball
    track("strings", '''
note("<[c4,eb4,g4,bb4] [f4,ab4,c5,eb5] [ab3,c4,eb4,g4] [g3,bb3,d4,f4]>/4")
  .s("sawtooth").add(note("0,0.08,-0.06"))
  .lpf(1800).attack(.15).release(1.2)
  .gain(.2).room(.4).roomsize(4).orbit(4).play()
''')
    track("wah", '''
note("<[c4 ~ eb4 ~] [~ f4 ~ ab4] [~ g4 eb4 ~] [g4 ~ f4 ~]>")
  .s("square").lpf(sine.range(600,2500).fast(2)).lpq(6)
  .attack(.003).decay(.25).sustain(.08).release(.15)
  .gain(.2).delay(.15).delaytime(.25).delayfeedback(.15).orbit(5).play()
''')
    time.sleep(4)

    # Build 5: full arrangement + all visuals + dancers
    track("drums", '''
stack(
  s("bd bd bd bd").bank("RolandTR909").gain(.82).shape(.2).lpf(3000),
  s("~ cp ~ cp").bank("RolandTR909").gain(.55).room(.35).delay(.12).delaytime(.25).delayfeedback(.15),
  s("~ oh ~ oh ~ oh ~ oh").bank("RolandTR909").gain(.42).pan(.55).lpf(5000),
  s("hh*16").bank("RolandTR909").gain("[.45 .15 .30 .12]*4").pan(sine.range(.4,.6).slow(7)).lpf(6000).room(.1),
  s("~ ~ ~ ~ ~ ~ ~ cb").bank("RolandTR707").every(4, x => x.struct("~ cb ~ cb")).gain(.3).pan(.7)
).play()
''')
    track("bass", '''
note("<[c2 c3 c2 c3] [f2 f3 f2 f3] [ab2 ab3 ab2 ab3] [g2 g3 g2 g3]>")
  .s("sawtooth").lpf(sine.range(400,1800).slow(8)).shape(.35)
  .attack(.005).decay(.12).sustain(.3).release(.1).clip(.8)
  .gain(.72).room(.15).orbit(3).play()
''')
    track("strings", '''
note("<[c4,eb4,g4,bb4] [f4,ab4,c5,eb5] [ab3,c4,eb4,g4] [g3,bb3,d4,f4]>/4")
  .s("sawtooth").add(note("0,0.08,-0.06"))
  .lpf(sine.range(800,3500).slow(16)).attack(.15).release(1.2)
  .gain(.3).room(.6).roomsize(6).orbit(4).play()
''')
    track("wah", '''
note("<[c4 ~ eb4 ~] [~ f4 ~ ab4] [~ g4 eb4 ~] [g4 ~ f4 ~]>")
  .s("square").lpf(sine.range(600,4000).fast(2)).lpq(sine.range(3,12).slow(4))
  .attack(.003).decay(.25).sustain(.08).release(.15)
  .gain(.38).pan(sine.range(.3,.7).slow(5))
  .delay(.2).delaytime(.25).delayfeedback(.2).room(.4).roomsize(3).orbit(5).play()
''')
    track("clav", '''
note("<[c5 ~ c5 eb5 ~ c5 ~ ~] [f5 ~ f5 ab5 ~ f5 ~ ~] [ab4 ~ ab4 c5 ~ ab4 ~ ~] [g4 ~ bb4 d5 ~ g4 ~ ~]>")
  .s("square").lpf(2800).attack(.001).decay(.08).sustain(0).release(.05)
  .gain(.32).pan(sine.range(.35,.65).fast(3))
  .delay(.15).delaytime(.125).delayfeedback(.25).room(.3).orbit(6).play()
''')
    track("shimmer", '''
note("<[c5,eb5,g5] [f5,ab5,c6] [ab4,c5,eb5] [g4,bb4,d5]>/8")
  .s("triangle").add(note("0,0.05"))
  .attack(2).release(4).lpf(sine.range(1200,4000).slow(32))
  .gain(.12).room(.85).roomsize(10).orbit(7).play()
''')

    run_script("disco_fx.py")
    run_script("disco_dancers.py")
    time.sleep(10)

# ═══════════════════════════════════════════════════════════════
# SECTION 17: CRESCENDO — 134 → 144 → 156 BPM
# ═══════════════════════════════════════════════════════════════
if args.section <= 17:
    print("═══ 17. Crescendo ═══")

    mark("Crescendo")

    # Stage 1: 134 BPM
    post("/strudel/cps", {"cps": 0.56})
    track("drums", '''
stack(
  s("bd bd bd bd").bank("RolandTR909").gain(.88).shape(.25).lpf(4000),
  s("~ cp ~ cp").bank("RolandTR909").gain(.62).room(.4).delay(.1).delaytime(.2).delayfeedback(.18),
  s("~ oh ~ oh ~ oh ~ oh").bank("RolandTR909").gain(.5).pan(.55).lpf(6000),
  s("hh*16").bank("RolandTR909").gain("[.55 .2 .40 .18]*4").pan(sine.range(.3,.7).slow(5)).lpf(8000).room(.12),
  s("~ ~ ~ ~ ~ ~ ~ cb").bank("RolandTR707").every(2, x => x.struct("~ cb ~ cb ~ cb ~ cb")).gain(.38).pan(.6)
).play()
''')
    track("bass", '''
note("<[c2 c3 c2 c3] [f2 f3 f2 f3] [ab2 ab3 ab2 ab3] [g2 g3 g2 g3]>")
  .s("sawtooth").lpf(sine.range(600,2800).slow(4)).shape(.4)
  .attack(.003).decay(.1).sustain(.4).release(.08).clip(.85)
  .gain(.78).room(.2).orbit(3).play()
''')
    track("strings", '''
note("<[c4,eb4,g4,bb4] [f4,ab4,c5,eb5] [ab3,c4,eb4,g4] [g3,bb3,d4,f4]>/4")
  .s("sawtooth").add(note("0,0.1,-0.08,0.15"))
  .lpf(sine.range(1200,5000).slow(8)).attack(.1).release(1.5)
  .gain(.38).room(.7).roomsize(8).orbit(4).play()
''')
    time.sleep(5)

    # Stage 2: 144 BPM
    post("/strudel/cps", {"cps": 0.6})
    track("bass", '''
note("<[c2 c3 c2 c3 c2 c3 c2 c3] [f2 f3 f2 f3 f2 f3 f2 f3] [ab2 ab3 ab2 ab3 ab2 ab3 ab2 ab3] [g2 g3 g2 g3 g2 g3 g2 g3]>")
  .s("sawtooth").lpf(sine.range(800,3500).slow(3)).shape(.45)
  .attack(.002).decay(.08).sustain(.5).release(.06).clip(.9)
  .gain(.82).room(.2).orbit(3).play()
''')
    track("clav", '''
note("<[c5 ~ c5 eb5 ~ c5 eb5 ~] [f5 ~ f5 ab5 ~ f5 ab5 ~] [ab4 ~ ab4 c5 ~ ab4 c5 ~] [g4 ~ bb4 d5 ~ g4 bb4 ~]>")
  .s("square").lpf(4500).attack(.001).decay(.06).sustain(0).release(.04)
  .gain(.4).pan(sine.range(.25,.75).fast(4))
  .delay(.12).delaytime(.1).delayfeedback(.3).room(.35).orbit(6).play()
''')
    track("wah", '''
note("<[c4 eb4 c4 eb4] [f4 ab4 f4 ab4] [g4 eb4 g4 eb4] [g4 f4 g4 f4]>")
  .s("square").lpf(sine.range(800,6000).fast(3)).lpq(sine.range(5,15).slow(2))
  .attack(.002).decay(.2).sustain(.1).release(.12)
  .gain(.42).pan(sine.range(.2,.8).slow(3))
  .delay(.18).delaytime(.2).delayfeedback(.22).room(.5).roomsize(4).orbit(5).play()
''')
    track("shimmer", '''
note("<[c5,eb5,g5,bb5] [f5,ab5,c6,eb6] [ab4,c5,eb5,g5] [g4,bb4,d5,f5,a5]>/4")
  .s("triangle").add(note("0,0.06,12"))
  .attack(1).release(3).lpf(sine.range(2000,7000).slow(16))
  .gain(.2).room(.9).roomsize(12).orbit(7).play()
''')
    time.sleep(5)

    # Stage 3: 156 BPM — PEAK
    post("/strudel/cps", {"cps": 0.65})
    track("drums", '''
stack(
  s("bd bd bd bd").bank("RolandTR909").gain(.92).shape(.3).lpf(5000),
  s("~ cp ~ cp").bank("RolandTR909").gain(.7).room(.45).delay(.08).delaytime(.15).delayfeedback(.2),
  s("oh*8").bank("RolandTR909").gain(.35).pan(sine.range(.3,.7).fast(2)).lpf(7000),
  s("hh*16").bank("RolandTR909").gain("[.6 .25 .5 .2]*4").pan(sine.range(.2,.8).slow(3)).lpf(10000).room(.15),
  s("cb*4").bank("RolandTR707").gain(.35).pan(.65),
  s("~ ~ ~ ~ ride ~ ~ ~").bank("RolandTR909").gain(.3).pan(.4)
).play()
''')
    track("bass", '''
note("<[c2 c3]*4 [f2 f3]*4 [ab2 ab3]*4 [g2 g3]*4>")
  .s("sawtooth").add(note("0,0.04"))
  .lpf(sine.range(1000,5000).slow(2)).shape(.5)
  .attack(.001).decay(.06).sustain(.6).release(.04).clip(.95)
  .gain(.88).room(.2).orbit(3).play()
''')
    track("strings", '''
note("<[c4,eb4,g4,bb4,c5] [f4,ab4,c5,eb5,f5] [ab3,c4,eb4,g4,ab4] [g3,bb3,d4,f4,g4]>/4")
  .s("sawtooth").add(note("0,0.12,-0.1,0.18,-0.14"))
  .lpf(sine.range(2000,8000).slow(4)).attack(.08).release(2)
  .gain(.42).room(.8).roomsize(10).orbit(4).play()
''')
    track("riser", '''
note("c4 d4 eb4 f4 g4 ab4 bb4 c5 d5 eb5 f5 g5 ab5 bb5 c6 d6".slow(8))
  .s("sawtooth").lpf(sine.range(1500,9000).slow(8))
  .attack(.01).decay(.3).sustain(.2).release(.2)
  .gain(.25).delay(.2).delaytime(.15).delayfeedback(.35)
  .room(.7).roomsize(8).orbit(2).play()
''')

    # Cranked visuals
    layer("beams", '''
push();
const beat = frameCount / 23.1;
const pulse = pow(sin(beat * TAU), 3);
translate(width/2, height * 0.28);
blendMode(ADD);
for (let i = 0; i < 12; i++) {
  const a = i * TAU/12 + frameCount * 0.015;
  const hue = (i * 30 + frameCount * 3) % 360;
  fill(hue, 80, 100, 18 + pulse * 25); noStroke();
  const spread = 0.07; const beamLen = max(width,height)*1.1;
  triangle(0,0, cos(a-spread)*beamLen, sin(a-spread)*beamLen, cos(a+spread)*beamLen, sin(a+spread)*beamLen);
}
blendMode(BLEND); pop();
''')
    layer("floor", '''
push();
const beat = frameCount / 23.1;
const floorY = height * 0.70;
const tileSize = width / 10;
noStroke();
for (let i = 0; i < 10; i++) {
  for (let j = 0; j < 4; j++) {
    const x = i * tileSize; const y = floorY + j * tileSize;
    const tilePulse = pow(max(0, sin((beat-(i+j)*0.1)*TAU)), 4);
    if ((i+j)%2===0) { const h=(i*36+j*90+frameCount*4)%360; fill(h, 80+tilePulse*20, 45+tilePulse*55); }
    else fill(0, 0, 10+tilePulse*25);
    rect(x, y, tileSize, tileSize);
  }
}
pop();
''')
    layer("sparkles", '''
push();
const beat = frameCount / 23.1;
if (!window.state._dsp) window.state._dsp = [];
const sp = window.state._dsp;
const kick = pow(sin(beat * TAU), 6);
if (kick > 0.3 && sp.length < 800) { for(let k=0;k<16;k++){const a=random(TAU);const spd=random(3,9);sp.push({x:cos(a)*25,y:sin(a)*25,vx:cos(a)*spd,vy:sin(a)*spd,hue:(beat*120+random(90))%360,life:160+random(100)});} }
noStroke(); blendMode(ADD);
const cx=width/2, cy=height*0.50;
for(let i=sp.length-1;i>=0;i--){const p=sp[i];p.x+=p.vx;p.y+=p.vy;p.vy+=0.015;p.life-=1.2;if(p.life<=0){sp.splice(i,1);continue;}const alpha=p.life/260*100;const sz=map(p.life,0,260,1,7);fill(p.hue,85,100,alpha);circle(cx+p.x,cy+p.y,sz);circle(cx-p.x,cy+p.y,sz);circle(cx+p.x,cy-p.y,sz);circle(cx-p.x,cy-p.y,sz);}
blendMode(BLEND); pop();
''')
    time.sleep(10)

# ═══════════════════════════════════════════════════════════════
# SECTION 18: DECRESCENDO
# ═══════════════════════════════════════════════════════════════
if args.section <= 18:
    print("═══ 18. Decrescendo ═══")

    mark("Decrescendo")

    # Peel 1: riser + clav gone
    stop("riser")
    stop("clav")
    track("wah", '''
note("<[c4 ~ ~ ~] [~ f4 ~ ~] [~ ~ eb4 ~] [g4 ~ ~ ~]>")
  .s("square").lpf(1200).lpq(4)
  .attack(.003).decay(.3).sustain(.05).release(.2)
  .gain(.2).room(.5).orbit(5).play()
''')
    remove("starburst")
    time.sleep(5)

    # Peel 2: drums stripped
    post("/strudel/cps", {"cps": 0.56})
    track("drums", '''
stack(
  s("bd bd bd bd").bank("RolandTR909").gain(.75).shape(.2).lpf(2500),
  s("~ cp ~ cp").bank("RolandTR909").gain(.45).room(.5)
).play()
''')
    stop("wah")
    remove("sparkles")
    remove("rings")
    layer("beams", '''
push();
const beat = frameCount / 26.8;
const pulse = pow(sin(beat * TAU), 4);
translate(width/2, height * 0.28);
blendMode(ADD);
for (let i = 0; i < 4; i++) {
  const a = i * TAU/4 + frameCount * 0.004;
  const hue = (i * 90 + frameCount) % 360;
  fill(hue, 50, 100, 6 + pulse*8); noStroke();
  const len = max(width,height)*0.7;
  triangle(0,0, cos(a-0.04)*len, sin(a-0.04)*len, cos(a+0.04)*len, sin(a+0.04)*len);
}
blendMode(BLEND); pop();
''')
    time.sleep(5)

    # Peel 3: minimal, dancers gone
    post("/strudel/cps", {"cps": 0.52})
    stop("shimmer")
    track("bass", 'note("<c2 ~ ~ ~ f2 ~ ~ ~ ab2 ~ ~ ~ g2 ~ ~ ~>").s("sawtooth").lpf(600).shape(.2).gain(.45).play()')
    track("strings", '''
note("<[c4,eb4,g4] [f4,ab4,c5] [ab3,c4,eb4] [g3,bb3,d4]>/8")
  .s("sawtooth").add(note("0,0.08"))
  .lpf(1200).attack(.3).release(2)
  .gain(.15).room(.8).roomsize(10).orbit(4).play()
''')
    layer("floor", '''
push();
const beat = frameCount / 28.8;
const floorY = height * 0.70;
const tileSize = width / 10;
noStroke();
for (let i = 0; i < 10; i++) {
  for (let j = 0; j < 4; j++) {
    const x = i * tileSize; const y = floorY + j * tileSize;
    const tilePulse = pow(max(0, sin((beat-(i+j)*0.2)*TAU)), 10);
    fill(0, 0, 3 + tilePulse * 8);
    rect(x, y, tileSize, tileSize);
  }
}
pop();
''')
    remove("dancers")
    time.sleep(5)

    # Peel 4: soloist alone in spotlight
    stop("bass")
    track("drums", 's("bd ~ ~ ~ bd ~ ~ ~").bank("RolandTR909").gain(.5).lpf(1500).shape(.1).play()')
    remove("beams")

    layer("dancers", '''
push();
const beat = frameCount / 28.8;
const kick = pow(sin(beat * TAU), 4);
const floorY = height * 0.76;
push(); blendMode(ADD); noStroke();
const spotPulse = 0.5 + kick * 0.5;
for (let r = 6; r > 0; r--) {
  fill(45, 20, 100, spotPulse * 5);
  beginShape(); vertex(width/2-5,0); vertex(width/2+5,0);
  vertex(width/2+60+r*10, floorY+20); vertex(width/2-60-r*10, floorY+20);
  endShape(CLOSE);
}
blendMode(BLEND); pop();
const sc = 2.2;
const t = (beat * 2) % 1;
const phase = floor(beat * 2) % 4;
let armL, armR, tilt, hipX, dy;
if (phase===0) { armL=-0.4; armR=lerp(0.3,-2.8,pow(t,0.5)); tilt=t*0.08; hipX=t*5; dy=sin(t*PI)*3; }
else if (phase===1) { armL=lerp(0.3,-2.8,pow(t,0.5)); armR=-0.4; tilt=-t*0.08; hipX=-t*5; dy=sin(t*PI)*3; }
else if (phase===2) { const rise=pow(t,0.7); armL=lerp(0.3,-2.6,rise); armR=lerp(0.3,-2.6,rise); tilt=0; hipX=0; dy=-rise*8; }
else { armL=-2.6; armR=-2.6; tilt=sin(t*PI)*0.02; hipX=0; dy=-8+sin(t*PI)*2; }
translate(width/2+hipX*sc, floorY+dy*sc); rotate(tilt); noStroke();
fill(0,0,0,50); ellipse(0,4*sc,40*sc,8*sc);
fill(0,0,95); rect(-13*sc,-6*sc,11*sc,8*sc,2); rect(2*sc,-6*sc,11*sc,8*sc,2);
fill(45,80,100); for(let w=0;w<4;w++){circle((-12+4*w)*sc,5.5*sc,3.5*sc);circle((3.5+4*w)*sc,5.5*sc,3.5*sc);}
fill(0,0,100);
beginShape();vertex(-10*sc,-3*sc);vertex(-2*sc,-3*sc);vertex(-3*sc,-26*sc);vertex(-9*sc,-26*sc);endShape(CLOSE);
beginShape();vertex(2*sc,-3*sc);vertex(10*sc,-3*sc);vertex(9*sc,-26*sc);vertex(3*sc,-26*sc);endShape(CLOSE);
fill(45,95,100); rect(-10*sc,-29*sc,20*sc,4*sc,1);
fill(0,0,100); beginShape();vertex(-12*sc,-28*sc);vertex(12*sc,-28*sc);vertex(13*sc,-52*sc);vertex(-13*sc,-52*sc);endShape(CLOSE);
fill(20,45,78); triangle(-8*sc,-52*sc,8*sc,-52*sc,0,-38*sc);
fill(45,80,95,60+kick*40); circle(0,-42*sc,5*sc);
push();translate(-13*sc,-48*sc);rotate(armL);fill(0,0,100);rect(0,0,7*sc,24*sc,2);fill(20,45,78);circle(3.5*sc,24*sc,8*sc);
if(armL<-2){stroke(20,45,78);strokeWeight(2.5*sc);line(3.5*sc,24*sc,3.5*sc,33*sc);noStroke();push();blendMode(ADD);fill(45,70,100,80);circle(3.5*sc,34*sc,6*sc);blendMode(BLEND);pop();}pop();
push();translate(13*sc,-48*sc);rotate(armR);fill(0,0,100);rect(-7*sc,0,7*sc,24*sc,2);fill(20,45,78);circle(-3.5*sc,24*sc,8*sc);
if(armR<-2){stroke(20,45,78);strokeWeight(2.5*sc);line(-3.5*sc,24*sc,-3.5*sc,33*sc);noStroke();push();blendMode(ADD);fill(45,70,100,80);circle(-3.5*sc,34*sc,6*sc);blendMode(BLEND);pop();}pop();
fill(20,45,78);rect(-3*sc,-58*sc,6*sc,7*sc);circle(0,-66*sc,20*sc);
fill(0,0,8);arc(0,-68*sc,26*sc,28*sc,PI+0.15,TAU-0.15,CHORD);
fill(0,0,6);rect(-8*sc,-68*sc,6*sc,4*sc,1);rect(2*sc,-68*sc,6*sc,4*sc,1);
pop();
''')
    time.sleep(6)

    # Peel 5: just strings swelling
    stop("drums")
    track("strings", '''
note("[c3,eb3,g3,bb3,c4,eb4,g4,bb4,c5]/8")
  .s("sawtooth").add(note("0,0.06,-0.04,0.1,-0.08,0.12"))
  .lpf(sine.range(400,6000).slow(8))
  .attack(.5).release(6)
  .gain(.35).room(.95).roomsize(14).orbit(4).play()
''')
    time.sleep(6)

# ═══════════════════════════════════════════════════════════════
# SECTION 19: FINALE
# ═══════════════════════════════════════════════════════════════
if args.section <= 19:
    print("═══ 19. Finale ═══")

    mark("Finale")
    stop("strings")
    time.sleep(1.5)

    # THE FINAL HIT
    track("finale", '''
stack(
  s("bd").bank("RolandTR909").gain(1).shape(.4).lpf(5000),
  s("cp").bank("RolandTR909").gain(.8).room(.8).roomsize(12),
  note("c2,c3,g3,c4,eb4,g4,bb4,c5,eb5,g5")
    .s("sawtooth").lpf(4000).shape(.3)
    .attack(.001).release(8)
    .gain(.5).room(.95).roomsize(14)
).play()
''')

    # White flash → fade to black
    layer("flash", '''
push();
if (!window.state._flash) window.state._flash = 100;
const f = window.state._flash;
if (f > 0) { background(0, 0, f); window.state._flash -= 1.2; }
else { background(0); }
pop();
''')

    # Soloist frozen — both arms up
    layer("dancers", '''
push();
const floorY = height * 0.76;
const sc = 2.2;
const fade = window.state._flash !== undefined ? max(0, window.state._flash) : 100;
const alpha = fade > 50 ? 100 : fade * 2;
if (alpha < 2) { pop(); return; }
translate(width/2, floorY - 8*sc); noStroke();
fill(0,0,0,alpha*0.5); ellipse(0,4*sc+8*sc,40*sc,8*sc);
fill(0,0,95,alpha); rect(-13*sc,-6*sc+8*sc,11*sc,8*sc,2); rect(2*sc,-6*sc+8*sc,11*sc,8*sc,2);
fill(45,80,100,alpha); for(let w=0;w<4;w++){circle((-12+4*w)*sc,5.5*sc+8*sc,3.5*sc);circle((3.5+4*w)*sc,5.5*sc+8*sc,3.5*sc);}
fill(0,0,100,alpha);
beginShape();vertex(-12*sc,-3*sc+8*sc);vertex(-4*sc,-3*sc+8*sc);vertex(-5*sc,-26*sc);vertex(-11*sc,-26*sc);endShape(CLOSE);
beginShape();vertex(4*sc,-3*sc+8*sc);vertex(12*sc,-3*sc+8*sc);vertex(11*sc,-26*sc);vertex(5*sc,-26*sc);endShape(CLOSE);
fill(45,95,100,alpha); rect(-10*sc,-29*sc,20*sc,4*sc,1);
fill(0,0,100,alpha); beginShape();vertex(-12*sc,-28*sc);vertex(12*sc,-28*sc);vertex(13*sc,-52*sc);vertex(-13*sc,-52*sc);endShape(CLOSE);
fill(20,45,78,alpha); triangle(-8*sc,-52*sc,8*sc,-52*sc,0,-38*sc);
fill(45,80,95,alpha); circle(0,-42*sc,5*sc);
push();translate(-13*sc,-48*sc);rotate(-2.6);fill(0,0,100,alpha);rect(0,0,7*sc,24*sc,2);fill(20,45,78,alpha);circle(3.5*sc,24*sc,8*sc);
stroke(20,45,78);strokeWeight(2.5*sc);line(3.5*sc,24*sc,3.5*sc,33*sc);noStroke();push();blendMode(ADD);fill(45,70,100,alpha*0.8);circle(3.5*sc,34*sc,7*sc);blendMode(BLEND);pop();pop();
push();translate(13*sc,-48*sc);rotate(-2.6);fill(0,0,100,alpha);rect(-7*sc,0,7*sc,24*sc,2);fill(20,45,78,alpha);circle(-3.5*sc,24*sc,8*sc);
stroke(20,45,78);strokeWeight(2.5*sc);line(-3.5*sc,24*sc,-3.5*sc,33*sc);noStroke();push();blendMode(ADD);fill(45,70,100,alpha*0.8);circle(-3.5*sc,34*sc,7*sc);blendMode(BLEND);pop();pop();
fill(20,45,78,alpha);rect(-3*sc,-58*sc,6*sc,7*sc);circle(0,-66*sc,20*sc);
fill(0,0,8,alpha);arc(0,-68*sc,26*sc,28*sc,PI+0.15,TAU-0.15,CHORD);
fill(0,0,6,alpha);rect(-8*sc,-68*sc,6*sc,4*sc,1);rect(2*sc,-68*sc,6*sc,4*sc,1);
pop();
''')

    remove("floor")
    remove("beams")
    remove("ball")

    time.sleep(10)

    # Silence + black
    post("/strudel/hush")
    remove("dancers")
    remove("flash")
    remove("starburst")
    remove("sparkles")
    remove("rings")
    layer("bg", "background(0);")

    print("\n═══ BLACK. SILENCE. END. ═══")

# ── Step mode: upload all collected steps to server ──────────
if args.step and _pending_steps:
    print(f"\nUploading {len(_pending_steps)} steps to server…")
    _post_raw("/show/load", {"steps": _pending_steps})
    print(f"Done! Use ← → arrow keys in the browser to step through the show.")
    print(f"Step 0 = clean slate. Press → to advance.")
