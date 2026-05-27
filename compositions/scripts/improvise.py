"""Full improvisation — music and visuals evolving together.
Jungle breaks, reese bass, visual chaos, breakdown, drop."""

import argparse
import json
import sys
import time
import urllib.request

import os
BASE = f"http://localhost:{os.environ.get('LIVECODE_PORT', '8766')}"

_parser = argparse.ArgumentParser()
_parser.add_argument("--dump-steps", action="store_true",
                     help="Print commands as JSON steps to stdout instead of executing")
_args = _parser.parse_args()
_collected: list[dict] = []

STEP_ROUTES = {
    "/strudel/track", "/strudel/stop", "/strudel/hush", "/strudel/cps",
    "/p5/layer", "/p5/remove", "/p5/clear", "/p5/setup", "/p5/state", "/p5/fps",
}


def post(path, payload):
    if _args.dump_steps and path in STEP_ROUTES:
        _collected.append({"route": path, "payload": dict(payload)})
        return {"ok": True}
    if _args.dump_steps:
        return {"ok": True}  # skip non-step routes like /strudel/send
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def layer(name, code):
    post("/p5/layer", {"name": name, "code": code})


def track(name, code):
    post("/strudel/track", {"name": name, "code": code})


# ── phase 1: tension rises — chopped breaks, reese bass ────────
if not _args.dump_steps:
    print("Phase 1: jungle tension")

post("/strudel/send", {"code": "samples('github:yaxu/clean-breaks')"})
if not _args.dump_steps: time.sleep(3)

post("/strudel/cps", {"cps": 0.85})

track("drums", '''
stack(
  s("clean:2").loopAt(2).chop(16)
    .every(4, x => x.fast(2))
    .sometimesBy(.12, x => x.speed(-1))
    .shape(.3).room(.12).gain(.75),
  s("~ ~ sd ~ ~ [~ sd] sd ~").bank("RolandTR909")
    .gain(.55).room(.2),
  s("hh*16").bank("RolandTR909")
    .gain(saw.range(.08, .35).fast(4))
    .pan(sine.range(.3, .7).slow(3))
    .lpf(6000).room(.1)
)
  .play()
''')

track("bass", '''
note("<a1 a1 [a1 g1] a1 g1 g1 [g1 a1] g1>/2")
  .s("sawtooth").add(note("0,0.12"))
  .lpf(sine.range(200, 1200).slow(4))
  .shape(.45)
  .gain(.7)
  .room(.15).orbit(3)
  .play()
''')

# visuals: sky starts pulsing, add energy particles
layer("energy", """
push();

// pulsing sky overlay — bass throb
blendMode(ADD);
noStroke();
const pulse = pow(sin(frameCount * 0.12), 8) * 45;
fill(280, 50, 90, pulse);
rect(0, 0, width, height * 0.78);
blendMode(BLEND);

// rising energy particles from ground
if (!window.state._ep) window.state._ep = [];
const ep = window.state._ep;
if (frameCount % 2 === 0) {
  ep.push({
    x: random(width), y: height,
    vx: random(-1, 1), vy: random(-4, -1.5),
    hue: random(360), life: 255
  });
}
if (ep.length > 300) ep.splice(0, ep.length - 300);
noStroke();
for (let i = ep.length - 1; i >= 0; i--) {
  const p = ep[i];
  p.x += p.vx; p.y += p.vy; p.life -= 1.8;
  if (p.life <= 0) { ep.splice(i, 1); continue; }
  fill(p.hue, 80, 100, p.life / 255 * 80);
  circle(p.x, p.y, map(p.life, 0, 255, 1, 5));
}
pop();
""")

if not _args.dump_steps: time.sleep(10)

# ── phase 2: darker, add amen-style fills, strobe ──────────────
if not _args.dump_steps: print("Phase 2: amen fills, strobe")

track("drums", '''
stack(
  s("clean:2").loopAt(2).chop(16)
    .every(4, x => x.fast(2))
    .every(7, x => x.chop(32).rev())
    .sometimesBy(.18, x => x.speed(-1))
    .sometimesBy(.1, x => x.ply(2))
    .shape(.35).room(.1).gain(.78),
  s("~ ~ sd ~ ~ [~ sd] sd ~").bank("RolandTR909")
    .gain(.58).room(.18)
    .sometimesBy(.15, x => x.speed(1.5)),
  s("hh*16").bank("RolandTR909")
    .gain("[.35 .12 .25 .08]*4")
    .lpf(sine.range(3000, 7000).slow(2))
    .pan(rand).room(.08)
)
  .play()
''')

track("chords", '''
chord("<Am7 Gm7 Fm7 Em7>/2")
  .dict("ireal").voicing()
  .struct("[x ~ ~ ~] [~ ~ x ~]")
  .s("sawtooth").add(note("0,0.08,-0.06"))
  .lpf(sine.range(400, 1800).slow(8))
  .attack(.01).release(.8)
  .gain(.25)
  .room(.55).roomsize(5)
  .orbit(4)
  .play()
''')

track("lead", '''
n("<[0 7 4 ~] [~ 5 ~ 9] [7 ~ 4 2] [~ 0 ~ ~]>")
  .scale("A4:minor:pentatonic")
  .s("square")
  .lpf(2000)
  .attack(.003).decay(.2).sustain(0).release(.15)
  .gain(.35)
  .delay(.5).delaytime(.125).delayfeedback(.45)
  .room(.5).roomsize(4)
  .pan(rand)
  .orbit(5)
  .play()
''')

# visuals: strobe flash on beats, trails on the riders
layer("energy", """
push();
blendMode(ADD);
noStroke();

// strobe on every few frames (synced to tempo feel)
const strobe = (frameCount % 12 < 2) ? 30 : 0;
fill(0, 0, 100, strobe);
rect(0, 0, width, height);

// bass throb
const pulse = pow(sin(frameCount * 0.15), 6) * 50;
fill(320, 55, 95, pulse);
rect(0, 0, width, height * 0.78);

blendMode(BLEND);

// more intense particles — faster, denser
if (!window.state._ep) window.state._ep = [];
const ep = window.state._ep;
for (let k = 0; k < 3; k++) {
  ep.push({
    x: random(width), y: height,
    vx: random(-2, 2), vy: random(-6, -2),
    hue: (frameCount * 3 + random(60)) % 360, life: 255
  });
}
if (ep.length > 500) ep.splice(0, ep.length - 500);
noStroke();
for (let i = ep.length - 1; i >= 0; i--) {
  const p = ep[i];
  p.x += p.vx + sin(frameCount * 0.05 + i) * 0.5;
  p.y += p.vy;
  p.life -= 2;
  if (p.life <= 0) { ep.splice(i, 1); continue; }
  fill(p.hue, 85, 100, p.life / 255 * 90);
  circle(p.x, p.y, map(p.life, 0, 255, 1, 6));
}
pop();
""")

if not _args.dump_steps: time.sleep(12)

# ── phase 3: BREAKDOWN — pull everything out ───────────────────
if not _args.dump_steps: print("Phase 3: breakdown")

post("/strudel/stop", {"name": "drums"})
post("/strudel/stop", {"name": "lead"})
post("/strudel/cps", {"cps": 0.42})

track("bass", '''
note("<a1 ~ ~ ~ ~ ~ ~ ~>/2")
  .s("sawtooth").add(note("0,0.15"))
  .lpf(sine.range(120, 800).slow(8))
  .shape(.5)
  .gain(.65)
  .room(.6).roomsize(8).orbit(3)
  .play()
''')

track("chords", '''
chord("<Am9 ~ ~ ~ ~ ~ ~ ~>/4")
  .dict("ireal").voicing()
  .s("triangle")
  .attack(2).release(4)
  .lpf(900)
  .gain(.25)
  .room(.85).roomsize(10)
  .orbit(4)
  .play()
''')

track("pad", '''
note("[a3,c4,e4,g4]")
  .s("sawtooth").add(note("0,0.08,-0.06,0.14"))
  .attack(4).release(8)
  .lpf(sine.range(200, 600).slow(16))
  .gain(.18)
  .room(.95).roomsize(12)
  .orbit(6)
  .play()
''')

# visuals: calm down, particles fade, sky darkens
layer("energy", """
push();
// slow fade of remaining particles
if (!window.state._ep) window.state._ep = [];
const ep = window.state._ep;
noStroke();
for (let i = ep.length - 1; i >= 0; i--) {
  const p = ep[i];
  p.x += p.vx * 0.3;
  p.y += p.vy * 0.3;
  p.life -= 4;
  if (p.life <= 0) { ep.splice(i, 1); continue; }
  fill(p.hue, 60, 100, p.life / 255 * 50);
  circle(p.x, p.y, map(p.life, 0, 255, 0.5, 3));
}

// dark wash creeping in
blendMode(MULTIPLY);
fill(0, 0, 40, 25);
rect(0, 0, width, height * 0.78);
blendMode(BLEND);

pop();
""")

if not _args.dump_steps: time.sleep(10)

# ── phase 4: tension build — snare roll, rising filter ─────────
if not _args.dump_steps: print("Phase 4: tension build")

post("/strudel/cps", {"cps": 0.55})

track("drums", '''
s("sd*8").bank("RolandTR909")
  .gain(saw.range(.15, .75).slow(2))
  .lpf(saw.range(1000, 8000).slow(4))
  .room(.3).orbit(2)
  .play()
''')

track("bass", '''
note("a1")
  .s("sawtooth").add(note("0,0.2,-0.15"))
  .lpf(saw.range(80, 2000).slow(4))
  .shape(.55)
  .gain(saw.range(.3, .9).slow(4))
  .room(.3).orbit(3)
  .play()
''')

# visuals: screen shake, intensifying
layer("energy", """
push();
// screen shake
const shk = sin(frameCount * 0.5) * 3;
translate(shk, cos(frameCount * 0.7) * 2);

blendMode(ADD);
noStroke();
// rapid color pulses building
const intensity = (frameCount % 3 === 0) ? 35 : 5;
fill((frameCount * 15) % 360, 70, 100, intensity);
rect(0, 0, width, height);
blendMode(BLEND);

// particles exploding from center
if (!window.state._ep) window.state._ep = [];
const ep = window.state._ep;
for (let k = 0; k < 5; k++) {
  const a = random(TAU);
  ep.push({
    x: width/2, y: height*0.5,
    vx: cos(a) * random(2, 8), vy: sin(a) * random(2, 8),
    hue: (frameCount * 8 + random(90)) % 360, life: 200
  });
}
if (ep.length > 600) ep.splice(0, ep.length - 600);
noStroke();
for (let i = ep.length - 1; i >= 0; i--) {
  const p = ep[i];
  p.x += p.vx; p.y += p.vy; p.vy += 0.05;
  p.life -= 3;
  if (p.life <= 0) { ep.splice(i, 1); continue; }
  fill(p.hue, 90, 100, p.life / 200 * 100);
  circle(p.x, p.y, map(p.life, 0, 200, 1, 7));
}
pop();
""")

if not _args.dump_steps: time.sleep(8)

# ── phase 5: THE DROP — full jungle, visual explosion ──────────
if not _args.dump_steps: print("Phase 5: DROP")

post("/strudel/cps", {"cps": 0.85})

track("drums", '''
stack(
  s("clean:2").loopAt(2).chop(16)
    .every(4, x => x.fast(2))
    .every(7, x => x.chop(32).rev())
    .every(11, x => x.ply(2))
    .sometimesBy(.2, x => x.speed(-1))
    .shape(.4).room(.1).gain(.85),
  s("bd ~ [~ bd] ~ ~ bd ~ [bd ~]").bank("RolandTR909")
    .gain(.8).shape(.3),
  s("hh*16").bank("RolandTR909")
    .gain("[.4 .1 .25 .08]*4")
    .pan(rand).lpf(7000).room(.08),
  s("~ ~ ~ oh ~ ~ ~ ~, ~ ~ ~ ~ ~ ~ ~ ride").bank("RolandTR909")
    .gain(.35).room(.3).orbit(2)
)
  .play()
''')

track("bass", '''
note("<[a1 ~ a1 g1] [~ g1 ~ a1] [g1 ~ f1 ~] [~ e1 ~ a1]>")
  .s("sawtooth").add(note("0,0.15,-0.12"))
  .lpf(sine.range(200, 1600).fast(2))
  .shape(.55)
  .gain(.75)
  .room(.12).orbit(3)
  .play()
''')

track("chords", '''
chord("<Am7 Gm7 Fm7 Em7>/2")
  .dict("ireal").voicing()
  .struct("[x ~ x ~] [~ x ~ x]")
  .s("sawtooth").add(note("0,0.06"))
  .lpf(sine.range(600, 2200).slow(4))
  .attack(.005).release(.4)
  .gain(.3)
  .room(.45).roomsize(4)
  .orbit(4)
  .play()
''')

track("lead", '''
n("<[0 4 7 4] [9 7 ~ 5] [4 ~ 2 0] [~ 7 9 12]>")
  .scale("A4:minor:pentatonic")
  .s("square")
  .lpf(sine.range(1500, 4000).fast(1))
  .attack(.003).decay(.15).sustain(0).release(.1)
  .gain(.4)
  .delay(.4).delaytime(.125).delayfeedback(.5)
  .room(.4).roomsize(3)
  .pan(rand)
  .orbit(5)
  .play()
''')

track("pad", '''
note("<[a3,c4,e4] [g3,bb3,d4] [f3,ab3,c4] [e3,g3,b3]>/8")
  .s("sawtooth").add(note("0,0.08,-0.06"))
  .attack(2).release(4)
  .lpf(sine.range(300, 900).slow(16))
  .gain(.15)
  .room(.8).roomsize(8)
  .orbit(6)
  .play()
''')

# visuals: full chaos — color explosions, light beams, everything pulsing
layer("energy", """
push();

// color-cycling sky pulse
blendMode(ADD);
noStroke();
const beat = pow(sin(frameCount * 0.18), 4);
fill((frameCount * 4) % 360, 60, 95, beat * 40);
rect(0, 0, width, height * 0.78);

// fast strobes
if (frameCount % 8 < 1) {
  fill(0, 0, 100, 25);
  rect(0, 0, width, height);
}
blendMode(BLEND);

// massive particle system — sparks flying everywhere
if (!window.state._ep) window.state._ep = [];
const ep = window.state._ep;
// emit from fire area + random spots
for (let k = 0; k < 4; k++) {
  const src = (k < 2) ? {x: width*0.5, y: height*0.91} : {x: random(width), y: random(height*0.5, height)};
  const a = random(TAU);
  const spd = random(2, 10);
  ep.push({
    x: src.x, y: src.y,
    vx: cos(a) * spd, vy: sin(a) * spd - 3,
    hue: (frameCount * 5 + k * 90 + random(45)) % 360,
    life: 180 + random(80)
  });
}
if (ep.length > 800) ep.splice(0, ep.length - 800);
noStroke();
for (let i = ep.length - 1; i >= 0; i--) {
  const p = ep[i];
  p.x += p.vx; p.y += p.vy; p.vy += 0.04;
  p.vx *= 0.995;
  p.life -= 2;
  if (p.life <= 0 || p.x < -20 || p.x > width+20) { ep.splice(i, 1); continue; }
  const a = p.life / 260 * 100;
  fill(p.hue, 85, 100, a);
  const sz = map(p.life, 0, 260, 1, 8);
  circle(p.x, p.y, sz);
}

// light beams sweeping from the projection screen area
push();
blendMode(ADD);
const beamAngle = frameCount * 0.03;
for (let b = 0; b < 3; b++) {
  const ba = beamAngle + b * TAU / 3;
  const bx1 = width * 0.30;
  const by1 = height * 0.45;
  const bx2 = bx1 + cos(ba) * width * 0.6;
  const by2 = by1 + sin(ba) * height * 0.4;
  stroke((b * 120 + frameCount * 2) % 360, 60, 100, 15);
  strokeWeight(30);
  line(bx1, by1, bx2, by2);
}
blendMode(BLEND);
pop();

pop();
""")

if _args.dump_steps:
    json.dump(_collected, sys.stdout)
else:
    print("Full send.")
