"""Hip-hop scenes — TR-808 boom-bap at ~86 BPM (CPS 0.36), half-time feel.

Built around lo-fi jazz hip-hop crossover: vibraphone chords from
jazz.chords_vibraphone() pair well with these tracks.

Vox needs `samples('github:tidalcycles/dirt-samples')` loaded first.
"""

CPS = 0.36


def drums(name: str = "drums") -> dict:
    """808 boom-bap — kick on 1, ghost-kick before snare, snare on 2/4, OH on offbeats."""
    code = '''
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
'''
    return {"name": name, "code": code}


def sub_bass(name: str = "bass") -> dict:
    """Chord roots with slides — 808 sub-bass sustained feel."""
    code = '''
note("<a1 ~ a1 ~ d2 ~ ~ ~ g1 ~ g1 ~ c2 ~ ~ ~ f1 ~ f1 ~ e2 ~ ~ ~ d2 ~ d2 ~ a1 ~ ~ ~>/4")
  .s("sine").shape(.45)
  .lpf(220)
  .attack(.01).decay(.1).sustain(.7).release(.3)
  .gain(.85)
  .room(.2).orbit(3)
  .play()
'''
    return {"name": name, "code": code}


def chords(name: str = "chords") -> dict:
    """Sparse vibraphone chords on the off (e-and pickups)."""
    code = '''
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
'''
    return {"name": name, "code": code}


def lead(name: str = "lead") -> dict:
    """Sparse Rhodes-like phrases with vibrato."""
    code = '''
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
'''
    return {"name": name, "code": code}


def pad(name: str = "pad") -> dict:
    """Quiet pad sitting behind everything."""
    code = '''
note("<[a3,c4,e4] [d4,f#4,a4] [g3,b3,d4] [c4,e4,g4]>/16")
  .s("triangle").add(note("0,0.05"))
  .attack(4).release(6)
  .lpf(sine.range(280, 800).slow(36))
  .gain(.10)
  .room(.7).roomsize(7)
  .orbit(6)
  .play()
'''
    return {"name": name, "code": code}


def vox(name: str = "vox") -> dict:
    """Chopped vox stabs — lands on and-of-3 / and-of-4 (classic chop placement)."""
    code = '''
s("<[~ ~ ~ ~ ~ bev:1 ~ ~] [~ ~ ~ ~ ~ ~ bev:3 bev:0] [~ bev:2 ~ ~ ~ ~ ~ ~] [~ ~ ~ ~ bev:1 ~ bev:3 ~]>/2")
  .speed("<.92 1.05 .98 1.0 1.1 .9>")
  .gain(.5)
  .lpf(2200)
  .pan(sine.range(.3, .7).slow(7))
  .delay(.4).delaytime(.375).delayfeedback(.3)
  .room(.65).roomsize(6)
  .orbit(8)
  .play()
'''
    return {"name": name, "code": code}
