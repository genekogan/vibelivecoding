"""Drum & bass scenes — for both the transition arc (0.42 → 0.85 CPS)
and full DnB at 0.85 CPS (~204 BPM).

Transition stages (each progressively faster):
  Stage 1 → drop vox, cps 0.42 (no new tracks, transition prep only)
  Stage 2 → cps 0.50, drums_twostep
  Stage 3 → cps 0.60, drums_twostep + sub_drone
  Stage 4 → cps 0.72, drums_breakbeat + sparse chords
  Stage 5 → cps 0.85, drums_full + bass_chopped + lead + dark pad

scenes.dnb.drums_full() etc. are the final-stage versions.
"""

CPS_STAGE_1 = 0.42
CPS_STAGE_2 = 0.50
CPS_STAGE_3 = 0.60
CPS_STAGE_4 = 0.72
CPS_FULL = 0.85


def drums_twostep(name: str = "drums") -> dict:
    """909 two-step pattern — bd/sd on quarters, fast hats."""
    code = '''
stack(
  s("bd ~ ~ ~ ~ ~ bd ~, ~ ~ sd ~ ~ ~ ~ sd").bank("RolandTR909").gain(.75)
    .shape(.2).room(.25),
  s("hh*16").bank("RolandTR909")
    .gain(saw.range(.15, .45).fast(4))
    .pan(sine.range(.35, .65).slow(7))
    .lpf(4500).room(.2)
)
  .play()
'''
    return {"name": name, "code": code}


def drums_breakbeat(name: str = "drums") -> dict:
    """Breakbeat snare pattern with every-8 doubles, OH on 4."""
    code = '''
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
'''
    return {"name": name, "code": code}


def drums_full(name: str = "drums") -> dict:
    """Full DnB kit — broken kick, double-snare, ride accents, every-16 ply doubles."""
    code = '''
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
'''
    return {"name": name, "code": code}


def sub_drone(name: str = "bass") -> dict:
    """Slow sustained sub-bass walking down: a → g → f → e."""
    code = '''
note("<a1 ~ ~ ~ ~ ~ ~ ~ g1 ~ ~ ~ ~ ~ ~ ~ f1 ~ ~ ~ ~ ~ ~ ~ e1 ~ ~ ~ ~ ~ ~ ~>/4")
  .s("sine").shape(.5)
  .lpf(180)
  .attack(.01).decay(.15).sustain(.6).release(.25)
  .gain(.85)
  .room(.15).orbit(3)
  .play()
'''
    return {"name": name, "code": code}


def bass_chopped(name: str = "bass") -> dict:
    """Chopped sub-bass for full DnB feel — rhythmic doubles per chord."""
    code = '''
note("<[a1 ~ a1 ~] [~ ~ ~ ~] [g1 ~ g1 ~] [~ ~ ~ ~] [f1 ~ f1 ~] [~ ~ ~ ~] [e1 ~ ~ e1] [~ ~ ~ ~]>/4")
  .s("sine").shape(.55)
  .lpf(160)
  .attack(.005).decay(.1).sustain(.5).release(.2)
  .gain(.9)
  .room(.12).orbit(3)
  .play()
'''
    return {"name": name, "code": code}


def chords_sparse(name: str = "chords") -> dict:
    """Thinned chords for transition — one stab per 8 steps."""
    code = '''
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
'''
    return {"name": name, "code": code}


def lead(name: str = "lead") -> dict:
    """Triangle pentatonic with quarter-note delay."""
    code = '''
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
'''
    return {"name": name, "code": code}


def pad_dark(name: str = "pad") -> dict:
    """Darker pad for full DnB — descending minor."""
    code = '''
note("<[a3,c4,e4] [g3,bb3,d4] [f3,a3,c4] [e3,g3,b3]>/16")
  .s("sawtooth").add(note("0,0.06"))
  .attack(3).release(5)
  .lpf(sine.range(250, 700).slow(32))
  .gain(.12)
  .room(.75).roomsize(8)
  .orbit(6)
  .play()
'''
    return {"name": name, "code": code}
