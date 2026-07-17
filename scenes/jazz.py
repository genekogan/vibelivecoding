"""Jazz scenes — drums, bass, chords, lead, pad across multiple feels.

Variants (from progressive evolution in the show):
  jazzy   — TR-707, lively (~120 BPM, CPS 0.50)
  chill   — slower, deeper reverb (CPS 0.38)
  complex — longer progressions, more variation (CPS 0.42)
  relaxed — vibraphone-like, minimal (CPS 0.40)
  busy    — full kit with cowbell + vox sample stabs

Standard chord progression: Am9 / D13 / Gmaj7 / Cmaj7
Extended progression:       Am9 D13 Gmaj9 Cmaj7 Fmaj7 Em9 Dm9 Am9
"""

CPS_JAZZY = 0.50
CPS_CHILL = 0.38
CPS_COMPLEX = 0.42
CPS_RELAXED = 0.40


# ── DRUMS ─────────────────────────────────────────────────────────

def drums_jazzy(name: str = "drums") -> dict:
    """TR-707 jazz kit — busy hats, rim accent, ghost notes via gain pattern."""
    code = '''
s("bd ~ [~ bd] ~, ~ sd ~ sd, [hh oh] hh [hh oh] hh, ~ ~ [~ rim] ~")
  .bank("RolandTR707")
  .gain(".9 .4 .6 .3 .8 .5 .7 .4")
  .room(.2)
  .play()
'''
    return {"name": name, "code": code}


def drums_chill(name: str = "drums") -> dict:
    """Softer 707 with dub-delay rim, gentle hat panning."""
    code = '''
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
'''
    return {"name": name, "code": code}


def drums_complex(name: str = "drums") -> dict:
    """Longer pattern with .sometimesBy fills, every-8 claps."""
    code = '''
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
'''
    return {"name": name, "code": code}


def drums_relaxed(name: str = "drums") -> dict:
    """Minimal kit — kick + hat only, easier on the ears."""
    code = '''
stack(
  s("bd ~ ~ [~ bd] ~ ~ bd ~").bank("RolandTR707").gain(.5).lpf(2200),
  s("[hh ~] hh [~ hh] hh").bank("RolandTR707")
    .gain(".4 .2 .25 .15")
    .pan(sine.range(.4, .6).slow(11))
    .lpf(3000).room(.3)
)
  .play()
'''
    return {"name": name, "code": code}


def drums_busy(name: str = "drums") -> dict:
    """Full kit with cowbell, ghost rim, every-16 fill, sparse clap."""
    code = '''
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
'''
    return {"name": name, "code": code}


# ── BASS ──────────────────────────────────────────────────────────

def bass_jazzy(name: str = "bass") -> dict:
    """Triangle dorian bass, sparse 3-against-8."""
    code = '''
note("<a2 e2 g2 d2>(3,8)")
  .scale("A2:dorian")
  .s("triangle")
  .lpf(800).shape(.2)
  .gain(.7)
  .room(.15)
  .play()
'''
    return {"name": name, "code": code}


def bass_chill(name: str = "bass") -> dict:
    """Sine sub with detune chorus, deeper room."""
    code = '''
note("<a2 ~ e2 ~ g2 ~ d2 ~>(3,8)")
  .scale("A2:dorian")
  .s("sine").add(note("0,0.05"))
  .lpf(450).shape(.15)
  .attack(.02).release(.4)
  .gain(.55)
  .room(.45).roomsize(4).orbit(3)
  .play()
'''
    return {"name": name, "code": code}


def bass_complex(name: str = "bass") -> dict:
    """8-bar walking-style line with octave surprises."""
    code = '''
note("<a2 [a2 e3] g2 [d2 a2] f2 [c3 g2] e2 [b2 e2]>")
  .scale("A2:dorian")
  .s("sine").add(note("0,0.05"))
  .lpf(perlin.range(360, 700).slow(12)).shape(.18)
  .attack(.02).release(.45)
  .gain(.55)
  .sometimesBy(.18, x => x.add(12))
  .room(.45).roomsize(4).orbit(3)
  .play()
'''
    return {"name": name, "code": code}


def bass_relaxed(name: str = "bass") -> dict:
    """Steady sine, no surprises, no perlin filter."""
    code = '''
note("<a2 ~ e2 g2 ~ d2 ~ ~>")
  .scale("A2:dorian")
  .s("sine")
  .lpf(420).shape(.12)
  .attack(.02).release(.5)
  .gain(.5)
  .room(.35).roomsize(3).orbit(3)
  .play()
'''
    return {"name": name, "code": code}


def bass_walking(name: str = "bass") -> dict:
    """Proper jazz walking line: 4 quarters per chord, chromatic approach on 4.

    Am → D : A C E Eb     D → G  : D F# A Ab
    G  → C : G B D B      C → F  : C E G E
    F  → E : F A C F      E → D  : E G B Eb
    Dm → A : D F A Bb     Am → A : A C E Bb
    """
    code = '''
note("<[a2 c3 e3 eb3] [d2 f#2 a2 ab2] [g2 b2 d3 b2] [c3 e3 g3 e3] [f2 a2 c3 f2] [e2 g2 b2 eb3] [d2 f2 a2 bb2] [a2 c3 e3 bb2]>/8")
  .s("sawtooth")
  .lpf(720).shape(.28)
  .attack(.005).decay(.18).sustain(.25).release(.15)
  .clip(.88)
  .gain(.6)
  .room(.28).roomsize(3).orbit(3)
  .play()
'''
    return {"name": name, "code": code}


# ── CHORDS ────────────────────────────────────────────────────────

def chords_jazzy(name: str = "chords") -> dict:
    """Square wave chord stabs with rhythmic struct."""
    code = '''
chord("<Am9 D13 Gmaj7 Cmaj7>/2")
  .dict("ireal").voicing()
  .struct("[~ x] [x ~] [~ x] [~ [x ~]]")
  .s("square")
  .lpf(1400)
  .attack(.005).decay(.3).sustain(.1)
  .gain(.45)
  .room(.35)
  .play()
'''
    return {"name": name, "code": code}


def chords_chill(name: str = "chords") -> dict:
    """Triangle chord pads, longer attack, big delay."""
    code = '''
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
'''
    return {"name": name, "code": code}


def chords_complex(name: str = "chords") -> dict:
    """Extended 8-chord ii-V-I cycle with modulation tones."""
    code = '''
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
'''
    return {"name": name, "code": code}


def chords_vibraphone(name: str = "chords") -> dict:
    """Vibraphone-like — sine with mallet attack, gentle tremolo."""
    code = '''
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
'''
    return {"name": name, "code": code}


def chords_walking(name: str = "chords") -> dict:
    """Stretched chords (one per cycle) to support walking bass."""
    code = '''
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
'''
    return {"name": name, "code": code}


# ── LEAD ──────────────────────────────────────────────────────────

def lead_jazzy(name: str = "lead") -> dict:
    """Triangle pentatonic with echo offset."""
    code = '''
n("<0 2 4 5 [4 2] 0 ~ ~>*2")
  .scale("A4:minor:pentatonic")
  .s("triangle")
  .gain(.45)
  .delay(".5:.375:.4")
  .room(.4)
  .off(1/8, x => x.add(7).gain(.25))
  .play()
'''
    return {"name": name, "code": code}


def lead_chill(name: str = "lead") -> dict:
    """Sparser pentatonic, big delay + slow LFO filter."""
    code = '''
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
'''
    return {"name": name, "code": code}


def lead_complex(name: str = "lead") -> dict:
    """8-bar phrase that follows extended chord changes."""
    code = '''
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
'''
    return {"name": name, "code": code}


def lead_vibraphone(name: str = "lead") -> dict:
    """Vibraphone melody — sine, tremolo, sparse."""
    code = '''
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
'''
    return {"name": name, "code": code}


# ── PAD ───────────────────────────────────────────────────────────

def pad(name: str = "pad") -> dict:
    """Slow ambient sawtooth pad, very long attack/release."""
    code = '''
note("<[a3,c4,e4] [d4,f4,a4] [g3,b3,d4] [c4,e4,g4]>/8")
  .s("sawtooth").add(note("0,0.1,-0.08"))
  .attack(3).release(5)
  .lpf(sine.range(300, 1100).slow(32))
  .gain(.18)
  .room(.9).roomsize(10)
  .orbit(6)
  .play()
'''
    return {"name": name, "code": code}


def pad_modal(name: str = "pad") -> dict:
    """Slow pad shifting through modal centers (matches chords_complex)."""
    code = '''
note("<[a3,c4,e4,g4] [d4,f#4,a4,c5] [g3,b3,d4,f#4] [c4,e4,g4,b4] [f#3,a3,c4,e4] [b3,d#4,f#4,a4] [e3,g3,b3,d4] [a3,c#4,e4,g4]>/16")
  .s("sawtooth").add(note("0,0.1,-0.08,0.06"))
  .attack(4).release(6)
  .lpf(sine.range(280, 1100).slow(40))
  .gain(perlin.range(.12, .22).slow(20))
  .room(.92).roomsize(10)
  .orbit(6)
  .play()
'''
    return {"name": name, "code": code}


def pad_minimal(name: str = "pad") -> dict:
    """Triangle pad, simpler, lower gain."""
    code = '''
note("<[a3,c4,e4] [d4,f#4,a4] [g3,b3,d4] [c4,e4,g4]>/16")
  .s("triangle").add(note("0,0.05"))
  .attack(4).release(6)
  .lpf(sine.range(320, 900).slow(36))
  .gain(.13)
  .room(.7).roomsize(7)
  .orbit(6)
  .play()
'''
    return {"name": name, "code": code}


def sparkle(name: str = "sparkle") -> dict:
    """Bell/marimba sparkle on every 4th cycle, random pan, big delay."""
    code = '''
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
'''
    return {"name": name, "code": code}


# ── VOX (vocal accents — needs samples('github:tidalcycles/dirt-samples')) ──

def vox_jazz(name: str = "vox") -> dict:
    """Sparse vocal stabs drifting in stereo."""
    code = '''
s("<[~ ~ bev:1 ~] [~ ~ ~ ~] [~ bev:3 ~ ~] [~ ~ ~ ~] [~ ~ bev:0 ~] [~ ~ ~ ~] [bev:2 ~ ~ ~] [~ ~ ~ ~]>")
  .speed("<.92 1.0 1.08 .96>")
  .gain(.42)
  .lpf(1800)
  .pan(sine.range(.25, .75).slow(7))
  .delay(.55).delaytime(.5).delayfeedback(.35)
  .room(.78).roomsize(7)
  .orbit(8)
  .play()
'''
    return {"name": name, "code": code}


def breath_fx(name: str = "breathfx") -> dict:
    """Reversed breath texture for transitions."""
    code = '''
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
'''
    return {"name": name, "code": code}
