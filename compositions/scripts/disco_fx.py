"""Disco effects synced to the beat — symmetric, geometric, pulsing."""

import argparse
import json
import sys
import urllib.request

import os
BASE = f"http://localhost:{os.environ.get('LIVECODE_PORT', '8766')}"

_parser = argparse.ArgumentParser()
_parser.add_argument("--dump-steps", action="store_true",
                     help="Print commands as JSON steps to stdout instead of executing")
_args = _parser.parse_args()
_collected: list[dict] = []


def post(path, payload):
    if _args.dump_steps:
        _collected.append({"route": path, "payload": dict(payload)})
        return {"ok": True}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def layer(name, code):
    post("/p5/layer", {"name": name, "code": code})


# CPS 0.52 = 0.52 cycles/sec → 1 cycle ≈ 1.923s ≈ 115 frames at 60fps
# 4 beats per cycle → 1 beat ≈ 28.8 frames
# We'll key everything to: beat = frameCount / 28.8

BG = """
background(0);
"""

DISCO_BALL = """
push();
translate(width/2, height * 0.28);

const beat = frameCount / 28.8;
const pulse = pow(sin(beat * TAU), 4);

// outer glow pulsing on beat
blendMode(ADD);
noStroke();
for (let r = 8; r > 0; r--) {
  fill(0, 0, 100, pulse * 4 + 2);
  circle(0, 0, 140 + r * 20);
}
blendMode(BLEND);

// disco ball sphere — rows of reflective tiles
const ballR = 60 + pulse * 8;
const rows = 10;
for (let j = 0; j < rows; j++) {
  const lat1 = PI * j / rows - HALF_PI;
  const lat2 = PI * (j + 1) / rows - HALF_PI;
  const y1 = sin(lat1) * ballR;
  const y2 = sin(lat2) * ballR;
  const r1 = cos(lat1) * ballR;
  const r2 = cos(lat2) * ballR;
  const cols = max(4, floor(12 * cos((lat1 + lat2) / 2)));

  for (let i = 0; i < cols; i++) {
    const a1 = TAU * i / cols + frameCount * 0.015;
    const a2 = TAU * (i + 1) / cols + frameCount * 0.015;
    const shimmer = noise(i * 0.3, j * 0.3, frameCount * 0.03);
    const b = lerp(35, 100, shimmer);
    const h = (i * 30 + j * 20 + frameCount * 2) % 360;
    fill(h, 25, b);
    stroke(0, 0, 50, 30);
    strokeWeight(0.5);
    beginShape();
    vertex(cos(a1) * r1, y1);
    vertex(cos(a2) * r1, y1);
    vertex(cos(a2) * r2, y2);
    vertex(cos(a1) * r2, y2);
    endShape(CLOSE);
  }
}
noStroke();
pop();
"""

LIGHT_BEAMS = """
push();
const beat = frameCount / 28.8;
const pulse = pow(sin(beat * TAU), 4);

translate(width/2, height * 0.28);
blendMode(ADD);
noFill();

// 8 symmetric beams rotating from disco ball
const numBeams = 8;
const beamLen = max(width, height) * 0.9;
for (let i = 0; i < numBeams; i++) {
  const a = i * TAU / numBeams + frameCount * 0.008;
  const hue = (i * 360 / numBeams + frameCount * 1.5) % 360;

  // beam cone — wider at the end
  const x1 = cos(a) * beamLen;
  const y1 = sin(a) * beamLen;
  const spread = 0.06;
  const x2 = cos(a - spread) * beamLen;
  const y2 = sin(a - spread) * beamLen;
  const x3 = cos(a + spread) * beamLen;
  const y3 = sin(a + spread) * beamLen;

  const alpha = 12 + pulse * 18;
  fill(hue, 70, 100, alpha);
  noStroke();
  triangle(0, 0, x2, y2, x3, y3);
}

blendMode(BLEND);
pop();
"""

FLOOR_TILES = """
push();
const beat = frameCount / 28.8;

// disco floor — bottom 30% of screen
const floorY = height * 0.70;
const tileSize = width / 10;

noStroke();
for (let i = 0; i < 10; i++) {
  for (let j = 0; j < 4; j++) {
    const x = i * tileSize;
    const y = floorY + j * tileSize;

    // checkerboard base with beat-synced color pulses
    const isLight = (i + j) % 2 === 0;
    const tileBeat = beat - (i + j) * 0.15;
    const tilePulse = pow(max(0, sin(tileBeat * TAU)), 6);

    if (isLight) {
      const h = (i * 36 + j * 90 + frameCount * 2) % 360;
      fill(h, 60 + tilePulse * 30, 30 + tilePulse * 60);
    } else {
      fill(0, 0, 8 + tilePulse * 15);
    }
    rect(x, y, tileSize, tileSize);
  }
}
pop();
"""

RINGS = """
push();
translate(width/2, height * 0.50);

const beat = frameCount / 28.8;

// concentric rings pulsing outward on each beat
noFill();
for (let i = 0; i < 6; i++) {
  const ringBeat = beat - i * 0.5;
  const expand = (ringBeat % 4) / 4;
  const r = expand * min(width, height) * 0.55;
  const alpha = (1 - expand) * 80;
  if (alpha < 2) continue;

  const hue = (i * 60 + frameCount * 2) % 360;
  stroke(hue, 75, 100, alpha);
  strokeWeight(2.5 - expand * 1.5);
  circle(0, 0, r * 2);
}
noStroke();
pop();
"""

STARBURST = """
push();
translate(width/2, height * 0.50);

const beat = frameCount / 28.8;
const kick = pow(sin(beat * TAU), 8);

// starburst lines — symmetric, pulsing on kick
stroke(0, 0, 100, kick * 60 + 8);
strokeWeight(1);
const rays = 24;
for (let i = 0; i < rays; i++) {
  const a = i * TAU / rays;
  const len = 80 + kick * 200 + sin(frameCount * 0.03 + i * 0.5) * 40;
  const x = cos(a) * len;
  const y = sin(a) * len;
  line(0, 0, x, y);
}

// inner rotating star
noFill();
stroke(45, 80, 100, 50);
strokeWeight(1.5);
push();
rotate(frameCount * 0.01);
beginShape();
for (let i = 0; i < 12; i++) {
  const a = i * TAU / 12;
  const r = (i % 2 === 0) ? 50 + kick * 30 : 25 + kick * 15;
  vertex(cos(a) * r, sin(a) * r);
}
endShape(CLOSE);
pop();

// counter-rotating star
stroke(280, 70, 100, 40);
push();
rotate(-frameCount * 0.008);
beginShape();
for (let i = 0; i < 16; i++) {
  const a = i * TAU / 16;
  const r = (i % 2 === 0) ? 90 + kick * 40 : 55 + kick * 20;
  vertex(cos(a) * r, sin(a) * r);
}
endShape(CLOSE);
pop();

noStroke();
pop();
"""

SPARKLES = """
push();
const beat = frameCount / 28.8;

// symmetric sparkle particles — mirrored on both sides
if (!window.state._dsp) window.state._dsp = [];
const sp = window.state._dsp;

const kick = pow(sin(beat * TAU), 8);
// emit on beat
if (kick > 0.5 && sp.length < 400) {
  for (let k = 0; k < 6; k++) {
    const a = random(TAU);
    const spd = random(1, 5);
    sp.push({
      x: cos(a) * 20, y: sin(a) * 20,
      vx: cos(a) * spd, vy: sin(a) * spd,
      hue: (beat * 90 + random(60)) % 360,
      life: 120 + random(80)
    });
  }
}

noStroke();
blendMode(ADD);
// draw mirrored from center
const cx = width / 2, cy = height * 0.50;
for (let i = sp.length - 1; i >= 0; i--) {
  const p = sp[i];
  p.x += p.vx; p.y += p.vy;
  p.vy += 0.02;
  p.life -= 1.5;
  if (p.life <= 0) { sp.splice(i, 1); continue; }
  const alpha = p.life / 200 * 80;
  const sz = map(p.life, 0, 200, 1, 5);
  fill(p.hue, 80, 100, alpha);
  // mirror 4 ways for symmetry
  circle(cx + p.x, cy + p.y, sz);
  circle(cx - p.x, cy + p.y, sz);
  circle(cx + p.x, cy - p.y, sz);
  circle(cx - p.x, cy - p.y, sz);
}
blendMode(BLEND);
pop();
"""

layer("bg", BG)
layer("floor", FLOOR_TILES)
layer("beams", LIGHT_BEAMS)
layer("rings", RINGS)
layer("starburst", STARBURST)
layer("ball", DISCO_BALL)
layer("sparkles", SPARKLES)

if _args.dump_steps:
    json.dump(_collected, sys.stdout)
else:
    print("Disco visuals.")
