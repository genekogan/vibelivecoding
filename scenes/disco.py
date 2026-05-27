"""Disco scenes — CPS 0.52 (~125 BPM).

Each function returns {"name": str, "code": str} ready for /strudel/track
or /p5/layer. Code strings include the trailing .play() for tracks.

p5 layers assume CPS 0.52 → 28.8 frames/beat at 60fps. Adjust the
FRAMES_PER_BEAT constant if you ship the scene at a different tempo.
"""

CPS = 0.52
FRAMES_PER_BEAT = 28.8  # 60 / (CPS * 4) — for use in p5 beat sync


# ── strudel tracks ────────────────────────────────────────────────

def drums(name: str = "drums", gain: float = 0.82) -> dict:
    """Four-on-the-floor 909 kick, clap on 2&4, offbeat open hat, 16th hats, cowbell."""
    code = f'''
stack(
  s("bd bd bd bd").bank("RolandTR909").gain({gain}).shape(.2).lpf(3000),
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
'''
    return {"name": name, "code": code}


def bass(name: str = "bass", progression: str = "c2 c3 c2 c3") -> dict:
    """Pumping root-octave sawtooth, Cm→Fm→Ab→Gm by default."""
    code = f'''
note("<[{progression}] [f2 f3 f2 f3] [ab2 ab3 ab2 ab3] [g2 g3 g2 g3]>")
  .s("sawtooth")
  .lpf(sine.range(400, 1800).slow(8))
  .shape(.35)
  .attack(.005).decay(.12).sustain(.3).release(.1)
  .clip(.8)
  .gain(.72)
  .room(.15).orbit(3)
  .play()
'''
    return {"name": name, "code": code}


def strings(name: str = "strings") -> dict:
    """Lush detuned saw chords with slow attack — Philly strings."""
    code = '''
note("<[c4,eb4,g4,bb4] [f4,ab4,c5,eb5] [ab3,c4,eb4,g4] [g3,bb3,d4,f4]>/4")
  .s("sawtooth").add(note("0,0.08,-0.06"))
  .lpf(sine.range(800, 3500).slow(16))
  .attack(.15).release(1.2)
  .gain(.3)
  .room(.6).roomsize(6)
  .orbit(4)
  .play()
'''
    return {"name": name, "code": code}


def wah(name: str = "wah") -> dict:
    """Square wave with resonant filter sweep — syncopated stabs."""
    code = '''
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
'''
    return {"name": name, "code": code}


def clav(name: str = "clav") -> dict:
    """16th-note funk riff (Stevie Wonder style)."""
    code = '''
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
'''
    return {"name": name, "code": code}


def shimmer(name: str = "shimmer") -> dict:
    """High triangle pad, barely-there, huge reverb."""
    code = '''
note("<[c5,eb5,g5] [f5,ab5,c6] [ab4,c5,eb5] [g4,bb4,d5]>/8")
  .s("triangle").add(note("0,0.05"))
  .attack(2).release(4)
  .lpf(sine.range(1200, 4000).slow(32))
  .gain(.12)
  .room(.85).roomsize(10)
  .orbit(7)
  .play()
'''
    return {"name": name, "code": code}


# ── p5 visual layers ──────────────────────────────────────────────

def bg(name: str = "bg") -> dict:
    return {"name": name, "code": "background(0);"}


def floor(name: str = "floor") -> dict:
    """Beat-pulsing checkerboard disco floor."""
    code = f'''
push();
const beat = frameCount / {FRAMES_PER_BEAT};
const floorY = height * 0.70;
const tileSize = width / 10;
noStroke();
for (let i = 0; i < 10; i++) {{
  for (let j = 0; j < 4; j++) {{
    const x = i * tileSize;
    const y = floorY + j * tileSize;
    const isLight = (i + j) % 2 === 0;
    const tileBeat = beat - (i + j) * 0.15;
    const tilePulse = pow(max(0, sin(tileBeat * TAU)), 6);
    if (isLight) {{
      const h = (i * 36 + j * 90 + frameCount * 2) % 360;
      fill(h, 60 + tilePulse * 30, 30 + tilePulse * 60);
    }} else {{
      fill(0, 0, 8 + tilePulse * 15);
    }}
    rect(x, y, tileSize, tileSize);
  }}
}}
pop();
'''
    return {"name": name, "code": code}


def beams(name: str = "beams") -> dict:
    """8 symmetric rotating light beams from the ceiling."""
    code = f'''
push();
const beat = frameCount / {FRAMES_PER_BEAT};
const pulse = pow(sin(beat * TAU), 4);
translate(width/2, height * 0.28);
blendMode(ADD);
noFill();
const numBeams = 8;
const beamLen = max(width, height) * 0.9;
for (let i = 0; i < numBeams; i++) {{
  const a = i * TAU / numBeams + frameCount * 0.008;
  const hue = (i * 360 / numBeams + frameCount * 1.5) % 360;
  const x2 = cos(a - 0.06) * beamLen;
  const y2 = sin(a - 0.06) * beamLen;
  const x3 = cos(a + 0.06) * beamLen;
  const y3 = sin(a + 0.06) * beamLen;
  fill(hue, 70, 100, 12 + pulse * 18);
  noStroke();
  triangle(0, 0, x2, y2, x3, y3);
}}
blendMode(BLEND);
pop();
'''
    return {"name": name, "code": code}


def ball(name: str = "ball") -> dict:
    """Disco ball with reflective rotating tiles."""
    code = f'''
push();
translate(width/2, height * 0.28);
const beat = frameCount / {FRAMES_PER_BEAT};
const pulse = pow(sin(beat * TAU), 4);
blendMode(ADD);
noStroke();
for (let r = 8; r > 0; r--) {{
  fill(0, 0, 100, pulse * 4 + 2);
  circle(0, 0, 140 + r * 20);
}}
blendMode(BLEND);
const ballR = 60 + pulse * 8;
const rows = 10;
for (let j = 0; j < rows; j++) {{
  const lat1 = PI * j / rows - HALF_PI;
  const lat2 = PI * (j + 1) / rows - HALF_PI;
  const y1 = sin(lat1) * ballR;
  const y2 = sin(lat2) * ballR;
  const r1 = cos(lat1) * ballR;
  const r2 = cos(lat2) * ballR;
  const cols = max(4, floor(12 * cos((lat1 + lat2) / 2)));
  for (let i = 0; i < cols; i++) {{
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
  }}
}}
noStroke();
pop();
'''
    return {"name": name, "code": code}


def sparkles(name: str = "sparkles") -> dict:
    """4-way mirrored particle bursts on each kick."""
    code = f'''
push();
const beat = frameCount / {FRAMES_PER_BEAT};
if (!window.state._dsp) window.state._dsp = [];
const sp = window.state._dsp;
const kick = pow(sin(beat * TAU), 8);
if (kick > 0.5 && sp.length < 400) {{
  for (let k = 0; k < 6; k++) {{
    const a = random(TAU);
    const spd = random(1, 5);
    sp.push({{x: cos(a)*20, y: sin(a)*20, vx: cos(a)*spd, vy: sin(a)*spd,
             hue: (beat*90+random(60))%360, life: 120+random(80)}});
  }}
}}
noStroke();
blendMode(ADD);
const cx = width/2, cy = height * 0.50;
for (let i = sp.length-1; i >= 0; i--) {{
  const p = sp[i];
  p.x += p.vx; p.y += p.vy; p.vy += 0.02; p.life -= 1.5;
  if (p.life <= 0) {{ sp.splice(i, 1); continue; }}
  const alpha = p.life / 200 * 80;
  const sz = map(p.life, 0, 200, 1, 5);
  fill(p.hue, 80, 100, alpha);
  circle(cx+p.x, cy+p.y, sz);
  circle(cx-p.x, cy+p.y, sz);
  circle(cx+p.x, cy-p.y, sz);
  circle(cx-p.x, cy-p.y, sz);
}}
blendMode(BLEND);
pop();
'''
    return {"name": name, "code": code}
