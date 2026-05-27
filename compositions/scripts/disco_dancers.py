"""Disco dancers — choreographed moves cycling every 2 beats, synced to BPM."""

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


DANCERS = """
push();
const beat = frameCount / 28.8;
const kick = pow(sin(beat * TAU), 4);
const floorY = height * 0.74;

// Backup dancers — uniform white outfits, smaller, flanking
const backups = [
  { xFrac:0.10, sc:1.2, skin:[25,40,85],  shirt:[0,0,95],  pants:[0,0,95],  hair:[0,0,12],   belt:[0,0,70],  wave:0.4, solo:false },
  { xFrac:0.90, sc:1.2, skin:[25,40,85],  shirt:[0,0,95],  pants:[0,0,95],  hair:[0,0,12],   belt:[0,0,70],  wave:0.4, solo:false },
  { xFrac:0.22, sc:1.4, skin:[30,55,75],  shirt:[0,0,92],  pants:[0,0,92],  hair:[30,70,25], belt:[0,0,70],  wave:0.3, solo:false },
  { xFrac:0.78, sc:1.4, skin:[30,55,75],  shirt:[0,0,92],  pants:[0,0,92],  hair:[30,70,25], belt:[0,0,70],  wave:0.3, solo:false },
  { xFrac:0.34, sc:1.6, skin:[22,42,90],  shirt:[0,0,90],  pants:[0,0,90],  hair:[350,55,50],belt:[0,0,70],  wave:0.2, solo:false },
  { xFrac:0.66, sc:1.6, skin:[22,42,90],  shirt:[0,0,90],  pants:[0,0,90],  hair:[350,55,50],belt:[0,0,70],  wave:0.2, solo:false },
];

// SOLOIST — front and center, biggest, white suit with gold accents
const soloist = { xFrac:0.50, sc:2.2, skin:[20,45,78], shirt:[0,0,100], pants:[0,0,100], hair:[0,0,8], belt:[45,95,100], wave:0.0, solo:true };

const dancers = [...backups, soloist];  // soloist drawn last = on top

// ── STAYING ALIVE CHOREOGRAPHY ──────────────────────────────
// 16-beat phrase (4 bars), each move = 1 beat, snaps on beat boundaries
// Sequence: point-R, point-L, point-R, point-L, strut-R, strut-L, strut-R, strut-L,
//           cross-point-R, cross-point-L, hip-walk-R, hip-walk-L, arm-sweep, arm-sweep, hold-pose, hold-pose
function getMove(beatInPhrase, subBeat, mirror) {
  const m = mirror;
  // subBeat: 0→1 within the beat, snapped timing
  const pop = subBeat < 0.15 ? 1 : 0;  // accent on downbeat
  const bounce = abs(sin(subBeat * PI)) * 6;  // one bounce per beat
  const snap = subBeat < 0.3 ? subBeat / 0.3 : 1;  // quick snap to position

  const b = beatInPhrase % 16;

  if (b < 4) {
    // TRAVOLTA DIAGONAL POINT — alternating R/L every beat
    const isRight = (b % 2 === 0);
    const side = isRight ? 1 : -1;
    return {
      dy: bounce,
      tilt: side * 0.06 * m * snap,
      hipX: side * 5 * m * snap,
      lArm: isRight ? -0.3 : lerp(0.3, -2.6, snap),
      rArm: isRight ? lerp(0.3, -2.6, snap) : -0.3,
      lLeg: side * 0.15 * snap,
      rLeg: -side * 0.1 * snap,
      spin: 0,
      crouch: 0,
      point: snap,
      pointHand: isRight ? 'r' : 'l',
    };
  }
  if (b < 8) {
    // STRUT — hip-walk with attitude, alternating weight shift
    const step = (b % 2 === 0) ? 1 : -1;
    const strut = sin(subBeat * PI);
    return {
      dy: strut * 4,
      tilt: step * 0.1 * m * strut,
      hipX: step * 7 * m * strut,
      lArm: -0.6 + step * 0.3 * strut,
      rArm: -0.6 - step * 0.3 * strut,
      lLeg: step * 0.2 * strut,
      rLeg: -step * 0.2 * strut,
      spin: 0,
      crouch: -strut * 3,
      point: 0,
    };
  }
  if (b < 12) {
    // CROSS-BODY POINT — point across body, lean into it
    const isRight = (b % 2 === 0);
    const side = isRight ? 1 : -1;
    return {
      dy: bounce,
      tilt: -side * 0.12 * m * snap,
      hipX: -side * 6 * m * snap,
      lArm: isRight ? -0.4 : lerp(0.2, -2.2, snap),
      rArm: isRight ? lerp(0.2, -2.2, snap) : -0.4,
      lLeg: -side * 0.12 * snap,
      rLeg: side * 0.08 * snap,
      spin: 0,
      crouch: snap * -4,
      point: snap,
      pointHand: isRight ? 'r' : 'l',
    };
  }
  if (b < 14) {
    // ARM SWEEP — both arms sweep from low to high in 2 beats
    const sweepT = ((b - 12) + subBeat) / 2;
    const armAngle = lerp(0.5, -2.8, sweepT);
    return {
      dy: bounce,
      tilt: sin(sweepT * PI) * 0.05 * m,
      hipX: sin(sweepT * PI) * 4 * m,
      lArm: armAngle,
      rArm: armAngle,
      lLeg: sin(sweepT * PI) * 0.1,
      rLeg: -sin(sweepT * PI) * 0.1,
      spin: 0,
      crouch: 0,
      point: sweepT > 0.8 ? 1 : 0,
      pointHand: 'both',
    };
  }
  // HOLD POSE — freeze at top of point, subtle bounce
  return {
    dy: bounce * 0.5,
    tilt: 0.04 * m,
    hipX: 3 * m,
    lArm: -2.6,
    rArm: -2.6,
    lLeg: 0.05,
    rLeg: -0.05,
    spin: 0,
    crouch: 0,
    point: 1,
    pointHand: 'both',
  };
}

// ── SOLOIST CHOREOGRAPHY — flashier, more varied, showstopper ──
function getSoloMove(beatInPhrase, subBeat) {
  const bounce = abs(sin(subBeat * PI)) * 8;
  const snap = subBeat < 0.2 ? subBeat / 0.2 : 1;
  const ease = subBeat < 0.5 ? 2*subBeat*subBeat : 1-pow(-2*subBeat+2,2)/2;
  const b = beatInPhrase % 32;  // 32-beat solo phrase (8 bars)

  if (b < 4) {
    // ICONIC STRUT FORWARD — hip sway, arms swinging opposite
    const side = (b % 2 === 0) ? 1 : -1;
    const stride = sin(subBeat * PI);
    return {
      dy: stride * 5,
      tilt: side * 0.14 * stride,
      hipX: side * 10 * stride,
      lArm: 0.4 - side * 0.6 * stride,
      rArm: 0.4 + side * 0.6 * stride,
      lLeg: side * 0.3 * stride,
      rLeg: -side * 0.25 * stride,
      spin: 0,
      crouch: -stride * 4,
      point: 0,
    };
  }
  if (b < 8) {
    // DIAGONAL POINT SEQUENCE — R up, L down, R across, L up (sharp snaps)
    const poses = [
      { lArm: -0.3, rArm: -2.8, tilt: 0.08, hipX: 6 },
      { lArm: 0.8, rArm: -0.3, tilt: -0.1, hipX: -5 },
      { lArm: -0.3, rArm: -1.8, tilt: -0.06, hipX: -4 },
      { lArm: -2.8, rArm: -0.3, tilt: 0.1, hipX: 5 },
    ];
    const pose = poses[(b - 4) % 4];
    return {
      dy: bounce,
      tilt: pose.tilt * snap,
      hipX: pose.hipX * snap,
      lArm: pose.lArm * snap + (1 - snap) * (-0.3),
      rArm: pose.rArm * snap + (1 - snap) * (-0.3),
      lLeg: 0.1 * snap,
      rLeg: -0.1 * snap,
      spin: 0,
      crouch: 0,
      point: snap,
      pointHand: (b % 2 === 0) ? 'r' : 'l',
    };
  }
  if (b < 12) {
    // SPIN + POINT — 2 beats spin, land into held point
    if (b < 10) {
      const spinT = ((b - 8) + subBeat) / 2;
      return {
        dy: 4,
        tilt: 0,
        hipX: 0,
        lArm: -1.8,
        rArm: -1.8,
        lLeg: 0,
        rLeg: 0,
        spin: spinT * TAU,
        crouch: 0,
        point: 0,
      };
    }
    // land into power point
    return {
      dy: bounce * 0.4,
      tilt: 0.1 * snap,
      hipX: 6 * snap,
      lArm: -0.4,
      rArm: -2.8 * snap,
      lLeg: 0.15 * snap,
      rLeg: -0.08,
      spin: 0,
      crouch: 0,
      point: snap,
      pointHand: 'r',
    };
  }
  if (b < 16) {
    // KNEE DIP + RISE — drop low beat 12-13, explode up 14-15
    const phase = b - 12;
    if (phase < 2) {
      const dropT = ((phase) + subBeat) / 2;
      const dip = pow(dropT, 1.5);
      return {
        dy: 0,
        tilt: 0,
        hipX: 0,
        lArm: lerp(-0.3, 0.6, dip),
        rArm: lerp(-0.3, 0.6, dip),
        lLeg: lerp(0.05, 0.5, dip),
        rLeg: lerp(-0.05, -0.5, dip),
        spin: 0,
        crouch: dip * 35,
        point: 0,
      };
    }
    const riseT = ((phase - 2) + subBeat) / 2;
    const rise = pow(riseT, 0.5);
    return {
      dy: -rise * 10,
      tilt: 0,
      hipX: 0,
      lArm: lerp(0.6, -2.6, rise),
      rArm: lerp(0.6, -2.6, rise),
      lLeg: lerp(0.5, 0, rise),
      rLeg: lerp(-0.5, 0, rise),
      spin: 0,
      crouch: lerp(35, 0, rise),
      point: rise > 0.7 ? 1 : 0,
      pointHand: 'both',
    };
  }
  if (b < 20) {
    // BODY ROLL — wave from knees up
    const rollT = subBeat;
    const side = (b % 2 === 0) ? 1 : -1;
    return {
      dy: sin(rollT * PI) * 6,
      tilt: side * sin(rollT * PI) * 0.12,
      hipX: side * sin(rollT * PI * 2) * 8,
      lArm: -1.0 + sin(rollT * PI) * 0.4,
      rArm: -1.0 - sin(rollT * PI) * 0.4,
      lLeg: sin(rollT * PI) * 0.08,
      rLeg: -sin(rollT * PI) * 0.08,
      spin: 0,
      crouch: sin(rollT * PI * 2) * 8,
      point: 0,
    };
  }
  if (b < 24) {
    // TRAVOLTA WALK — the classic sidewalk strut with alternating points
    const isRight = (b % 2 === 0);
    const side = isRight ? 1 : -1;
    const step = sin(subBeat * PI);
    return {
      dy: step * 7,
      tilt: side * 0.1 * step,
      hipX: side * 9 * step,
      lArm: isRight ? (-0.5 + step * 0.2) : lerp(0.3, -2.5, snap),
      rArm: isRight ? lerp(0.3, -2.5, snap) : (-0.5 + step * 0.2),
      lLeg: side * 0.25 * step,
      rLeg: -side * 0.2 * step,
      spin: 0,
      crouch: -step * 5,
      point: snap * 0.8,
      pointHand: isRight ? 'r' : 'l',
    };
  }
  if (b < 28) {
    // DOUBLE-TIME BOUNCE — fast alternating arm pumps
    const fast = sin(subBeat * TAU * 2);
    const side = fast > 0 ? 1 : -1;
    return {
      dy: abs(fast) * 8,
      tilt: fast * 0.05,
      hipX: fast * 4,
      lArm: -1.2 + fast * 0.6,
      rArm: -1.2 - fast * 0.6,
      lLeg: fast * 0.15,
      rLeg: -fast * 0.15,
      spin: 0,
      crouch: 0,
      point: 0,
    };
  }
  // FINALE HOLD — dramatic wide stance, both arms up
  return {
    dy: bounce * 0.3,
    tilt: sin(subBeat * PI) * 0.03,
    hipX: 0,
    lArm: -2.4,
    rArm: -2.4,
    lLeg: 0.2,
    rLeg: -0.2,
    spin: 0,
    crouch: 0,
    point: 1,
    pointHand: 'both',
  };
}

for (const d of dancers) {
  push();
  const x = width * d.xFrac;
  const baseY = floorY + (1 - d.sc / 2.2) * height * 0.08;
  const sc = d.sc;
  const mirror = d.xFrac > 0.5 ? -1 : 1;

  // cascading wave: front pair leads, back follows slightly after
  const db = beat - d.wave;
  let mv;
  if (d.solo) {
    const beatInPhrase = floor(db * 4) % 32;
    const subBeat = (db * 4) % 1;
    mv = getSoloMove(beatInPhrase, subBeat);
  } else {
    const beatInPhrase = floor(db * 4) % 16;
    const subBeat = (db * 4) % 1;
    mv = getMove(beatInPhrase, subBeat, mirror);
  }

  translate(x + mv.hipX * sc, baseY + mv.dy * sc + (mv.crouch || 0) * sc);
  rotate(mv.spin || 0);
  rotate(mv.tilt || 0);
  noStroke();

  // spotlight for soloist
  if (d.solo) {
    push(); blendMode(ADD);
    for (let r = 5; r > 0; r--) {
      fill(45, 30, 100, 6 + kick * 8);
      ellipse(0, -30*sc, (60 + r*18)*sc, (90 + r*20)*sc);
    }
    blendMode(BLEND); pop();
  }

  // shadow (stretches when crouching)
  const crouchAmt = (mv.crouch || 0) / 35;
  fill(0, 0, 0, d.solo ? 60 : 45);
  ellipse(0, 4*sc, (36 + crouchAmt*20)*sc, 8*sc);

  // floor glow
  push(); blendMode(ADD);
  fill(d.shirt[0], 45, 55, 14);
  ellipse(0, 3*sc, 50*sc, 10*sc);
  blendMode(BLEND); pop();

  // ── ROLLER SKATES ──
  // boot
  fill(0, 0, 95);
  rect(-13*sc, -6*sc, 11*sc, 8*sc, 2);
  rect(2*sc,   -6*sc, 11*sc, 8*sc, 2);
  // sole/plate
  fill(0, 0, 40);
  rect(-14*sc, 2*sc, 13*sc, 3*sc, 1);
  rect(1*sc,   2*sc, 13*sc, 3*sc, 1);
  // wheels (4 per skate)
  fill(d.solo ? 45 : 0, d.solo ? 80 : 0, d.solo ? 100 : 25);
  const wheelY = 5.5*sc;
  circle(-12*sc, wheelY, 3.5*sc);
  circle(-8*sc, wheelY, 3.5*sc);
  circle(-4*sc, wheelY, 3.5*sc);
  circle(-0.5*sc, wheelY, 3.5*sc);
  circle(3.5*sc, wheelY, 3.5*sc);
  circle(7.5*sc, wheelY, 3.5*sc);
  circle(11.5*sc, wheelY, 3.5*sc);
  circle(15*sc, wheelY, 3.5*sc);
  // wheel shine
  fill(0, 0, 100, 40);
  circle(-12*sc, wheelY - 0.8*sc, 1.5*sc);
  circle(-4*sc, wheelY - 0.8*sc, 1.5*sc);
  circle(3.5*sc, wheelY - 0.8*sc, 1.5*sc);
  circle(11.5*sc, wheelY - 0.8*sc, 1.5*sc);

  // ── BELL-BOTTOM LEGS ──
  push();
  rotate(mv.lLeg);
  fill(d.pants[0], d.pants[1], d.pants[2]);
  beginShape();
  vertex(-10*sc,-3*sc); vertex(-2*sc,-3*sc);
  vertex(-3*sc,-26*sc); vertex(-9*sc,-26*sc);
  endShape(CLOSE);
  beginShape();
  vertex(-14*sc,-3*sc); vertex(2*sc,-3*sc);
  vertex(-2*sc,-8*sc); vertex(-10*sc,-8*sc);
  endShape(CLOSE);
  pop();
  push();
  rotate(mv.rLeg);
  fill(d.pants[0], d.pants[1], d.pants[2]);
  beginShape();
  vertex(2*sc,-3*sc); vertex(10*sc,-3*sc);
  vertex(9*sc,-26*sc); vertex(3*sc,-26*sc);
  endShape(CLOSE);
  beginShape();
  vertex(-2*sc,-3*sc); vertex(14*sc,-3*sc);
  vertex(10*sc,-8*sc); vertex(2*sc,-8*sc);
  endShape(CLOSE);
  pop();

  // ── BELT ──
  fill(d.belt[0], d.belt[1], d.belt[2]);
  rect(-10*sc, -29*sc, 20*sc, 4*sc, 1);
  fill(45, 30, 100, 60+kick*40);
  rect(-3*sc, -29*sc, 6*sc, 4*sc, 1);

  // ── TORSO ──
  fill(d.shirt[0], d.shirt[1], d.shirt[2]);
  beginShape();
  vertex(-12*sc,-28*sc); vertex(12*sc,-28*sc);
  vertex(13*sc,-52*sc); vertex(-13*sc,-52*sc);
  endShape(CLOSE);

  // V-neck + chain
  fill(d.skin[0], d.skin[1], d.skin[2]);
  triangle(-8*sc,-52*sc, 8*sc,-52*sc, 0,-38*sc);
  fill(45, 80, 95, 50+kick*40);
  circle(0, -42*sc, 4*sc);

  // collar flaps
  fill(d.shirt[0], d.shirt[1]-15, d.shirt[2]+8);
  beginShape();
  vertex(-13*sc,-52*sc); vertex(-8*sc,-52*sc);
  vertex(-4*sc,-44*sc); vertex(-18*sc,-52*sc);
  endShape(CLOSE);
  beginShape();
  vertex(13*sc,-52*sc); vertex(8*sc,-52*sc);
  vertex(4*sc,-44*sc); vertex(18*sc,-52*sc);
  endShape(CLOSE);

  // shirt sparkle
  push(); blendMode(ADD);
  fill(d.shirt[0], 30, 100, kick*45);
  ellipse(0, -40*sc, 20*sc, 28*sc);
  blendMode(BLEND); pop();

  // ── LEFT ARM ──
  push();
  translate(-13*sc, -48*sc);
  rotate(mv.lArm);
  fill(d.shirt[0], d.shirt[1], d.shirt[2]);
  rect(0, 0, 7*sc, 24*sc, 2);
  fill(d.skin[0], d.skin[1], d.skin[2]);
  circle(3.5*sc, 24*sc, 8*sc);
  // point finger
  if (mv.point > 0.2 && (mv.pointHand === 'l' || mv.pointHand === 'both')) {
    stroke(d.skin[0], d.skin[1], d.skin[2]);
    strokeWeight(2.5*sc); line(3.5*sc,24*sc,3.5*sc,32*sc); noStroke();
    push(); blendMode(ADD);
    fill(45,70,100,mv.point*80);
    circle(3.5*sc,33*sc,5*sc);
    blendMode(BLEND); pop();
  }
  pop();

  // ── RIGHT ARM ──
  push();
  translate(13*sc, -48*sc);
  let rArmAngle = mv.rArm;
  // disco circle: offset the hand position in a circle
  if (mv.circleArm) {
    rArmAngle = -2.0;
  }
  rotate(rArmAngle);
  fill(d.shirt[0], d.shirt[1], d.shirt[2]);
  rect(-7*sc, 0, 7*sc, 24*sc, 2);
  fill(d.skin[0], d.skin[1], d.skin[2]);
  circle(-3.5*sc, 24*sc, 8*sc);
  if (mv.point > 0.2 && (mv.pointHand === 'r' || mv.pointHand === 'both')) {
    stroke(d.skin[0], d.skin[1], d.skin[2]);
    strokeWeight(2.5*sc); line(-3.5*sc,24*sc,-3.5*sc,32*sc); noStroke();
    push(); blendMode(ADD);
    fill(45,70,100,mv.point*80);
    circle(-3.5*sc,33*sc,5*sc);
    blendMode(BLEND); pop();
  }
  // overhead circle trail for disco circles move
  if (mv.circleArm) {
    push(); blendMode(ADD);
    const cp = mv.circlePhase;
    for (let i = 0; i < 6; i++) {
      const ca = cp - i * 0.3;
      fill((d.shirt[0]+i*20)%360, 60, 100, 40-i*6);
      circle(-3.5*sc + cos(ca)*8*sc, 24*sc + sin(ca)*8*sc - 6*sc, 4*sc);
    }
    blendMode(BLEND); pop();
  }
  pop();

  // ── NECK ──
  fill(d.skin[0], d.skin[1], d.skin[2]);
  rect(-3*sc, -58*sc, 6*sc, 7*sc);

  // ── HEAD ──
  fill(d.skin[0], d.skin[1], d.skin[2]);
  // head bob on beat
  const headBob = sin(db * TAU * 2) * 2 * sc;
  push();
  translate(0, headBob);

  circle(0, -66*sc, 20*sc);

  // afro
  fill(d.hair[0], d.hair[1], d.hair[2]);
  arc(0, -68*sc, 26*sc, 28*sc, PI+0.15, TAU-0.15, CHORD);
  ellipse(-11*sc, -66*sc, 7*sc, 14*sc);
  ellipse(11*sc, -66*sc, 7*sc, 14*sc);

  // sunglasses
  fill(0, 0, 6);
  rect(-8*sc,-68*sc,6*sc,4*sc,1);
  rect(2*sc,-68*sc,6*sc,4*sc,1);
  stroke(0,0,20); strokeWeight(1*sc);
  line(-2*sc,-66*sc,2*sc,-66*sc);
  line(-8*sc,-66.5*sc,-12*sc,-67*sc);
  line(8*sc,-66.5*sc,12*sc,-67*sc);
  noStroke();
  fill(d.shirt[0],60,40,60);
  rect(-7.5*sc,-67.5*sc,5*sc,3*sc,0.5);
  rect(2.5*sc,-67.5*sc,5*sc,3*sc,0.5);
  fill(0,0,100,25+kick*55);
  circle(-5*sc,-67.5*sc,1.8*sc);
  circle(5*sc,-67.5*sc,1.8*sc);

  // smile + teeth
  noFill(); stroke(0,0,8); strokeWeight(1.2*sc);
  arc(0,-61.5*sc,8*sc,5*sc,0.15,PI-0.15);
  noStroke();
  fill(0,0,98);
  rect(-3*sc,-61.5*sc,6*sc,2*sc,1);

  // mustache (back two pairs)
  if (d.wave > 0.15) {
    fill(d.hair[0],d.hair[1],max(d.hair[2]-5,5));
    arc(0,-62.5*sc,8*sc,3*sc,0,PI);
  }

  pop(); // head bob

  pop(); // dancer
}

pop();
"""

post("/p5/layer", {"name": "dancers", "code": DANCERS})

if _args.dump_steps:
    json.dump(_collected, sys.stdout)
else:
    print("Choreographed.")
