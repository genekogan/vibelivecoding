"""Campfire scene — cartoon riders on EUCs circling the fire (2x scale)."""

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


CAMPFIRE = """
const fx = width * 0.50;
const fy = height * 0.905;

// ── 1. ambient glow on building+ground (additive) ──────────────
push();
blendMode(ADD);
noStroke();
const baseR = min(width, height) * 0.55;
const flick = 1 + noise(frameCount * 0.08) * 0.08;
for (let r = baseR; r > 0; r -= 6) {
  const t = r / baseR;
  const a = pow(1 - t, 2.2) * 22;
  fill(22, 75, 95, a);
  ellipse(fx, fy - 30, r * 2 * flick, r * 1.1);
}
for (let r = baseR * 0.35; r > 0; r -= 4) {
  const t = r / (baseR * 0.35);
  const a = pow(1 - t, 1.6) * 30;
  fill(38, 85, 100, a);
  ellipse(fx, fy - 18, r * 2 * flick, r * 1.4);
}
blendMode(BLEND);
pop();

// ── 2. cartoon rider on an EUC ─────────────────────────────────
function rider(x, y, sc, faceLeft, P) {
  push();
  translate(x, y);
  if (faceLeft) scale(-1, 1);
  noStroke();

  // shadow on ground beneath EUC
  fill(0, 0, 0, 35);
  ellipse(0, 2*sc, 60*sc, 8*sc);

  // ── EUC ──
  // tire
  fill(0, 0, 8);
  ellipse(0, -18*sc, 38*sc, 36*sc);
  // knobby tread (rotates with motion)
  fill(0, 0, 18);
  const wheelSpin = frameCount * 0.20;
  for (let i = 0; i < 14; i++) {
    const a = i * TAU/14 + wheelSpin;
    const r = 16*sc;
    push();
    translate(cos(a)*r, -18*sc + sin(a)*r);
    rotate(a);
    rect(-1.6*sc, -1*sc, 3.2*sc, 3.5*sc);
    pop();
  }
  // hub
  fill(0, 0, 24);
  ellipse(0, -18*sc, 18*sc, 18*sc);
  fill(0, 0, 12);
  ellipse(0, -18*sc, 8*sc, 8*sc);
  // body of EUC (between legs)
  fill(0, 0, 9);
  rect(-12*sc, -42*sc, 24*sc, 24*sc, 2);
  // copper/orange top accent
  fill(16, 75, 82);
  rect(-12*sc, -46*sc, 24*sc, 5*sc, 2);
  // headlight on front
  fill(50, 30, 100);
  ellipse(9*sc, -38*sc, 4*sc, 3*sc);
  // side speaker
  fill(0, 0, 5);
  rect(7*sc, -32*sc, 5*sc, 8*sc, 1);
  // footplates (orange) — extend out from base
  fill(16, 85, 75);
  rect(-23*sc, -3*sc, 14*sc, 3*sc, 1);
  rect( 9*sc,  -3*sc, 14*sc, 3*sc, 1);

  // ── PERSON ──
  // pants
  fill(P.pants);
  rect(-11*sc, -30*sc, 7*sc, 28*sc, 2);
  rect( 4*sc,  -30*sc, 7*sc, 28*sc, 2);
  // shoes (on footplates)
  fill(0, 0, 9);
  rect(-13*sc, -4*sc, 11*sc, 5*sc, 1);
  rect( 2*sc,  -4*sc, 11*sc, 5*sc, 1);

  // torso (shirt)
  fill(P.shirt);
  ellipse(0, -44*sc, 26*sc, 34*sc);
  // collar / neckline
  fill(P.collar);
  arc(0, -58*sc, 13*sc, 7*sc, 0, PI);

  // arms — slight casual riding pose, one bent forward
  fill(P.shirt);
  push(); translate(-13*sc, -52*sc); rotate(-0.35);
  rect(0, 0, 6.5*sc, 22*sc, 2);
  pop();
  push(); translate(13*sc, -52*sc); rotate(0.22);
  rect(-6.5*sc, 0, 6.5*sc, 22*sc, 2);
  pop();
  // hands
  fill(P.skin);
  circle(-18*sc, -30*sc, 7.5*sc);
  circle( 18*sc, -30*sc, 7.5*sc);

  // neck
  fill(P.skin);
  rect(-3*sc, -64*sc, 6*sc, 6*sc);
  // head
  fill(P.skin);
  circle(0, -71*sc, 19*sc);
  // ears
  circle(-9.5*sc, -71*sc, 4*sc);
  circle( 9.5*sc, -71*sc, 4*sc);
  // hair tuft showing under helmet (front)
  fill(P.hair);
  arc(0, -73*sc, 18*sc, 7*sc, PI, TAU);

  // face
  fill(0, 0, 9);
  circle(-3.6*sc, -70*sc, 2.6*sc);
  circle( 3.6*sc, -70*sc, 2.6*sc);
  // mouth (smile)
  noFill();
  stroke(0, 0, 8);
  strokeWeight(1.3*sc);
  arc(0, -65*sc, 7*sc, 5*sc, 0.15, PI - 0.15);
  noStroke();
  // cheek blush (cute)
  fill(0, 35, 100, 35);
  circle(-6*sc, -67*sc, 4*sc);
  circle( 6*sc, -67*sc, 4*sc);

  // helmet — caps the top of the head and curves down sides
  fill(P.helmet);
  arc(0, -73*sc, 24*sc, 25*sc, PI + 0.15, TAU - 0.15, CHORD);
  // visor stripe
  fill(P.visor);
  push(); translate(0, -77*sc);
  rect(-10*sc, 0, 20*sc, 2.5*sc, 1);
  pop();
  // helmet shine
  fill(0, 0, 100, 35);
  ellipse(-5*sc, -82*sc, 8*sc, 3*sc);
  // chin strap
  stroke(0, 0, 14);
  strokeWeight(0.9*sc);
  line(-10*sc, -68*sc, -3.5*sc, -58*sc);
  line( 10*sc, -68*sc,  3.5*sc, -58*sc);
  noStroke();

  pop();
}

// ── 3. fire (drawn at depth=0 between back+front riders) ───────
function drawFire() {
  push();
  translate(fx, fy);
  noStroke();

  // stones ring
  for (let i = 0; i < 8; i++) {
    const a = i / 8 * TAU;
    fill(0, 0, lerp(28, 44, ((i * 13) % 7) / 7));
    ellipse(cos(a) * 50, sin(a) * 14 + 4, 18, 9);
  }
  // logs
  fill(18, 55, 22);
  push(); rotate(-0.25); rect(-34, -3, 70, 7, 1); pop();
  push(); rotate(0.18);  rect(-28,  0, 56, 6, 1); pop();
  // coals
  fill(15, 95, 75, 85);
  ellipse(0, 1, 78, 12);
  fill(45, 95, 100, 60);
  ellipse(0, 1, 60, 8);

  // flame triangles (noise-flickered)
  for (let i = 0; i < 22; i++) {
    const t = frameCount * 0.08 + i * 1.41;
    const nx = noise(i * 0.6, t * 0.07);
    const nh = noise(i + 30, t * 0.10);
    const nw = noise(i + 80, t * 0.09);
    const xJ = (nx - 0.5) * 36;
    const fh = 30 + nh * 100;
    const fw = 12 + nw * 16;
    const hue = lerp(48, 4, nh);
    const alpha = 35 + nw * 50;
    fill(hue, 90, 100, alpha);
    beginShape();
    vertex(xJ - fw/2, 0);
    vertex(xJ + fw/2, 0);
    vertex(xJ + fw * 0.15, -fh);
    endShape(CLOSE);
  }
  // hot core
  for (let i = 0; i < 10; i++) {
    const t = frameCount * 0.11 + i * 2.3;
    const nx = noise(i, t * 0.06);
    const nh = noise(i + 50, t * 0.10);
    const xJ = (nx - 0.5) * 18;
    const fh = 18 + nh * 40;
    fill(54, 60, 100, 75);
    triangle(xJ - 5, 0, xJ + 5, 0, xJ, -fh);
  }
  // sparks
  for (let i = 0; i < 16; i++) {
    const cycle = 240;
    const tt = (frameCount * 1.4 + i * 41) % cycle;
    const sx = (noise(i, frameCount * 0.004) - 0.5) * 80;
    const sy = -tt * 1.3 - noise(i, 99) * 20;
    const a = max(0, 100 - tt * 0.55);
    fill(42, 80, 100, a);
    circle(sx, sy, 1.5 + noise(i, tt * 0.05) * 2);
  }
  pop();
}

// ── 4. compute rider positions, depth-sort, draw with fire ─────
const ride = frameCount * 0.013;   // angular speed
const rx = width * 0.22;
const ry = height * 0.07;

const palettes = [
  { skin:[26,38,90],  hair:[28,75,28],  shirt:[200,80,75], collar:[200,90,55], pants:[220,55,30], helmet:[10,90,80],  visor:[0,0,95]  },
  { skin:[32,52,78],  hair:[42,85,42],  shirt:[55,85,90],  collar:[40,70,70],  pants:[8,30,28],   helmet:[125,70,55], visor:[0,0,95]  },
  { skin:[24,42,86],  hair:[350,55,55], shirt:[285,55,78], collar:[290,70,55], pants:[0,0,15],    helmet:[200,80,72], visor:[40,80,90]},
  { skin:[20,48,72],  hair:[0,0,18],    shirt:[120,55,60], collar:[120,70,40], pants:[28,40,38],  helmet:[42,90,92],  visor:[0,0,95]  },
  { skin:[28,42,82],  hair:[28,80,38],  shirt:[348,75,82], collar:[345,85,55], pants:[218,42,40], helmet:[280,65,75], visor:[0,0,95]  },
];

const placed = palettes.map((p, i) => {
  const angle = ride + i * TAU / palettes.length;
  const x = fx + cos(angle) * rx;
  const y = fy + sin(angle) * ry;
  const depth = sin(angle);                       // -1 back, +1 front
  const sc = lerp(1.55, 2.85, (depth + 1) / 2);   // ~2x of original
  const faceLeft = -sin(angle) < 0;               // direction of motion
  return { x, y, sc, depth, faceLeft, P: p };
});
placed.sort((a, b) => a.depth - b.depth);

// back-half riders
for (const r of placed) if (r.depth < 0) rider(r.x, r.y, r.sc, r.faceLeft, r.P);
// fire
drawFire();
// front-half riders
for (const r of placed) if (r.depth >= 0) rider(r.x, r.y, r.sc, r.faceLeft, r.P);
"""


def main():
    post("/p5/layer", {"name": "campfire", "code": CAMPFIRE})

    if _args.dump_steps:
        json.dump(_collected, sys.stdout)
    else:
        print("Riding.")


if __name__ == "__main__":
    main()
