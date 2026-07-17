"""Draw a stylized version of the pallet-rack + plywood desert building."""

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


SKY = """
noStroke();
const horizon = height * 0.78;
for (let y = 0; y < horizon; y++) {
  const t = y / horizon;
  const h = lerp(208, 35, pow(t, 1.4));
  const s = lerp(40, 14, t);
  const b = lerp(82, 96, t);
  stroke(h, s, b);
  line(0, y, width, y);
}
// wispy clouds drifting slowly
noStroke();
for (let i = 0; i < 7; i++) {
  const baseX = ((i * 311 + frameCount * 0.15) % (width + 400)) - 200;
  const cy = height * (0.06 + i * 0.045);
  for (let j = 0; j < 22; j++) {
    const nx = baseX + j * 11 + sin(j * 0.4 + i) * 6;
    const ny = cy + noise(j * 0.2, i * 1.7) * 10;
    const w = 70 + noise(i, j * 0.1) * 40;
    fill(35, 8, 100, 14);
    ellipse(nx, ny, w, 10);
  }
}
"""

GROUND = """
noStroke();
const horizon = height * 0.78;
// soft horizon line
fill(32, 22, 88);
rect(0, horizon, width, height - horizon);
// dusty gradient toward foreground
for (let y = horizon; y < height; y++) {
  const t = (y - horizon) / (height - horizon);
  const c = lerp(88, 70, t);
  stroke(28, lerp(18, 28, t), c);
  line(0, y, width, y);
}
// playa cracks
stroke(25, 30, 50, 55);
strokeWeight(0.7);
for (let i = 0; i < 140; i++) {
  const seed = i * 0.31;
  const x1 = noise(seed, 0.1) * width;
  const y1 = lerp(horizon + 10, height - 5, noise(seed, 1.7));
  const angle = noise(seed, 2.3) * TAU;
  const len = 25 + noise(seed, 3.1) * 80;
  const x2 = x1 + cos(angle) * len;
  const y2 = y1 + sin(angle) * len * 0.4;
  line(x1, y1, x2, y2);
}
"""

BUILDING = """
push();
noStroke();

// building geometry
const bx = width * 0.06;
const bw = width * 0.88;
const bottomY = height * 0.78;
const topY = height * 0.30;
const peakX = bx + bw * 0.62;
const peakY = height * 0.235;
const rightX = bx + bw;
const rightTopY = height * 0.55;

// roofline polygon helper
function roofY(x) {
  if (x <= peakX) {
    const t = (x - bx) / (peakX - bx);
    return lerp(topY, peakY, t);
  } else {
    const t = (x - peakX) / (rightX - peakX);
    return lerp(peakY, rightTopY, t);
  }
}

// dark structural frame (pallet rack visible through gaps)
fill(22, 18, 20);
beginShape();
for (let x = bx; x <= rightX; x += 6) vertex(x, roofY(x));
vertex(rightX, bottomY);
vertex(bx, bottomY);
endShape(CLOSE);

// palette: tan/brown/red/purple/cream/dark/green
const palette = [
  [30, 32, 56], [25, 22, 70], [35, 14, 82], [40, 28, 88],
  [10, 68, 60], [15, 75, 75], [350, 55, 50], [355, 70, 45],
  [280, 32, 48], [255, 28, 42],
  [0, 0, 92], [42, 32, 92],
  [120, 28, 42], [95, 35, 50],
  [25, 48, 32], [20, 38, 28],
  [0, 0, 28], [35, 18, 24],
];

function hash2(i, j) {
  let h = (i * 374761393 + j * 668265263) | 0;
  h = (h ^ (h >>> 13)) * 1274126177 | 0;
  return (h ^ (h >>> 16)) >>> 0;
}

const cols = 16;
const rows = 6;
const cellW = bw / cols;
const cellH = (bottomY - topY) / rows;

for (let i = 0; i < cols; i++) {
  for (let j = 0; j < rows; j++) {
    const px = bx + i * cellW;
    const py = topY + j * cellH;
    const cx = px + cellW * 0.5;
    const top = roofY(cx);
    if (py + cellH < top) continue;          // panel above roof
    const drawTop = max(py, top);
    const hh = (py + cellH) - drawTop;
    if (hh < 4) continue;

    const hk = hash2(i, j);
    const colorIdx = hk % palette.length;
    const c = palette[colorIdx];

    // small randomized inset so panels don't perfectly tile
    const inset = ((hk >> 4) & 3) * 0.5;
    const ww = cellW - inset * 2;
    fill(c[0], c[1], c[2]);
    rect(px + inset, drawTop, ww, hh - inset);

    // occasional grain lines on plywood-colored panels
    if (c[0] >= 25 && c[0] <= 45 && (hk & 7) < 3) {
      stroke(c[0], c[1] + 10, c[2] - 18, 55);
      strokeWeight(0.5);
      for (let g = 0; g < 3; g++) {
        const gy = drawTop + (g + 1) * (hh / 4);
        line(px + inset + 4, gy, px + ww - 4, gy);
      }
      noStroke();
    }
  }
}

// window cutouts (lower-left section)
fill(40, 50, 70);
const winRow = topY + cellH * 0.55;
for (let k = 0; k < 4; k++) {
  const wx = bx + cellW * (0.4 + k * 1.6);
  rect(wx, winRow, cellW * 0.9, cellH * 0.7);
  // warm interior glow
  fill(38, 65, 88);
  rect(wx + 4, winRow + 4, cellW * 0.9 - 8, cellH * 0.7 - 8);
  fill(40, 50, 70);
}

// pixelated black/white panel (right of center)
const pbx = bx + bw * 0.58;
const pby = topY + cellH * 0.55;
const pbw = cellW * 1.1;
const pbh = cellH * 1.4;
for (let py = 0; py < 8; py++) {
  for (let px2 = 0; px2 < 6; px2++) {
    const v = ((px2 * 13 + py * 7 + (px2 ^ py)) & 1) ? 96 : 6;
    fill(0, 0, v);
    rect(pbx + px2 * pbw / 6, pby + py * pbh / 8, pbw / 6 + 1, pbh / 8 + 1);
  }
}

// yellow door (slightly left of center, upper)
fill(48, 78, 92);
const doorX = bx + bw * 0.51;
const doorY = topY + cellH * 0.55;
rect(doorX, doorY, cellW * 0.6, cellH * 1.4);
fill(45, 90, 70);
rect(doorX + 3, doorY + 3, cellW * 0.6 - 6, cellH * 1.4 - 6);

// mandala / flower mural (middle, on dark panel)
const mx = bx + bw * 0.40;
const my = topY + cellH * 0.55;
const mr = cellH * 0.55;
push();
translate(mx, my);
noFill();
stroke(195, 60, 70);
strokeWeight(1.6);
for (let k = 0; k < 8; k++) {
  push();
  rotate(k * PI / 4);
  ellipse(0, mr * 0.55, mr * 0.45, mr * 0.95);
  pop();
}
noStroke();
fill(48, 75, 90);
circle(0, 0, mr * 0.35);
fill(15, 70, 75);
circle(0, 0, mr * 0.18);
pop();

// red triangle / accent on far-right slope
fill(8, 78, 65);
beginShape();
vertex(bx + bw * 0.78, roofY(bx + bw * 0.78));
vertex(rightX, rightTopY);
vertex(rightX, rightTopY + cellH * 1.2);
vertex(bx + bw * 0.78, roofY(bx + bw * 0.78) + cellH * 1.6);
endShape(CLOSE);

pop();
"""

STAIRS = """
push();
// orange scaffolding stairs going up to the door
const sxBot = width * 0.62;
const syBot = height * 0.78;
const sxTop = width * 0.555;
const syTop = height * 0.46;

// landing platform under door
fill(18, 75, 70);
noStroke();
rect(sxTop - 20, syTop - 6, width * 0.10, 14);

// stair stringers (diagonals)
stroke(15, 85, 78);
strokeWeight(5);
line(sxBot,           syBot, sxTop,        syTop);
line(sxBot + 60,      syBot, sxTop + 60,   syTop);

// handrails (parallel, higher)
stroke(15, 85, 78);
strokeWeight(3);
line(sxBot,      syBot - 70, sxTop,      syTop - 70);
line(sxBot + 60, syBot - 70, sxTop + 60, syTop - 70);
// vertical posts on rails
for (let i = 0; i <= 6; i++) {
  const t = i / 6;
  const x = lerp(sxBot, sxTop, t);
  const y = lerp(syBot, syTop, t);
  line(x,      y - 70, x,      y);
  line(x + 60, y - 70, x + 60, y);
}

// stair steps (white-ish treads with orange edge)
strokeWeight(1);
for (let i = 0; i < 14; i++) {
  const t = i / 13;
  const x = lerp(sxBot, sxTop, t);
  const y = lerp(syBot, syTop, t);
  noStroke();
  fill(0, 0, 88);
  rect(x, y - 6, 60, 8);
  stroke(15, 85, 78);
  strokeWeight(2);
  noFill();
  rect(x, y - 6, 60, 8);
}
pop();
"""

DEBRIS = """
push();
noStroke();
// scattered lumber pile in front of building
for (let i = 0; i < 22; i++) {
  push();
  const baseX = width * 0.43 + (i * 13) % 90;
  const baseY = height * 0.79 + ((i * 7) % 6);
  translate(baseX, baseY);
  rotate(((i * 1.731) % 1) * 0.6 - 0.3);
  const hue = 28 + ((i * 5) % 15);
  const sat = 28 + ((i * 11) % 30);
  const bri = 50 + ((i * 17) % 35);
  fill(hue, sat, bri);
  rect(0, 0, 60 + ((i * 9) % 30), 5);
  pop();
}

// IBC tote (white square container)
fill(0, 0, 86);
rect(width * 0.36, height * 0.71, width * 0.04, height * 0.075);
stroke(0, 0, 60);
strokeWeight(0.7);
noFill();
for (let g = 1; g < 5; g++) {
  const gy = height * 0.71 + g * (height * 0.075 / 5);
  line(width * 0.36, gy, width * 0.40, gy);
}

// small ATV/utility vehicle blob far-left
noStroke();
fill(35, 25, 30);
rect(width * 0.13, height * 0.715, width * 0.06, height * 0.06);
fill(0, 0, 12);
circle(width * 0.145, height * 0.78, 16);
circle(width * 0.18, height * 0.78, 16);

pop();
"""


def main():
    if not _args.dump_steps:
        # poll for browser readiness; controller is shared with strudel
        deadline = time.time() + 60
        while time.time() < deadline:
            with urllib.request.urlopen(f"{BASE}/status") as r:
                if json.loads(r.read())["ready"]:
                    break
            time.sleep(0.4)

    layer("sky", SKY)
    layer("ground", GROUND)
    layer("building", BUILDING)
    layer("stairs", STAIRS)
    layer("debris", DEBRIS)

    if _args.dump_steps:
        json.dump(_collected, sys.stdout)
    else:
        print("Drawn.")


if __name__ == "__main__":
    main()
