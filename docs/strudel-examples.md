# Strudel Examples — Organized by Genre & Technique

Curated examples that actually sound good, with explanations of *why* they work.

---

## Runnable Script Boilerplate

Every composition follows this structure. Copy this, then add tracks.

```python
"""My composition — describe the vibe."""

from strudel_server import StrudelController
import time

ctrl = StrudelController()
ctrl.start()
print("Open http://localhost:8766/strudel.html and click 'Start Audio & Connect'")
ctrl.wait_for_browser()

# Optional: load sample packs (wait for them to load)
# ctrl.send("samples('github:yaxu/clean-breaks')")
# time.sleep(3)

# Set tempo
ctrl.set_cps(0.5)
time.sleep(0.3)

# Add tracks one at a time with pauses for musical build-up
ctrl.set_track("drums", '''
s("bd [~ bd] sd [bd ~], hh*8")
  .bank("RolandTR909")
  .gain("1 .6 .8 .6 1 .6 .9 .6")
  .room(.15)
  .play()
''')
print("  + drums")
time.sleep(4)

# ... add more tracks with time.sleep(4) between each ...

# Interactive REPL — lets you modify tracks live
print("\\nTry:")
print('  ctrl.stop_track("drums")   # remove a layer')
print('  ctrl.hush()                # silence everything')

import code
code.interact(local={"ctrl": ctrl, "time": time}, banner="ctrl is ready.")
```

**Key points:**
- `ctrl.wait_for_browser()` blocks until the user clicks "Start Audio & Connect"
- `time.sleep(4)` between tracks gives each layer time to breathe
- Every track code string must end with `.play()`
- The REPL at the end lets you modify tracks interactively
- `ctrl.stop_track(name)` removes layers; `ctrl.hush()` silences everything

---

## Genre Examples (Remote Controller)

Complete Python compositions using `ctrl.set_track()`. Each builds up layers over time.

### House / Techno

**Dub Techno** — Basic Channel / Rhythm & Sound style. The magic is in the dub delay on the rim shot.

```python
ctrl.set_cps(0.5)

# Four-on-the-floor kick
ctrl.set_track("kick", '''
s("bd*4").bank("RolandTR909")
  .shape(.3).gain(.9)
  .play()
''')

# 16th hats with ramping dynamics and gentle pan
ctrl.set_track("hat", '''
s("hh*16").bank("RolandTR909")
  .gain(saw.range(.15, .6))
  .pan(sine.range(.3, .7).fast(3))
  .room(.15)
  .play()
''')

# THE DUB ELEMENT — rim with heavy delay + reverb
ctrl.set_track("rim", '''
s("~ rim ~ [~ rim]").bank("RolandTR707")
  .gain(.5)
  .delay(.7).delaytime(.375).delayfeedback(.55)
  .room(.6).roomsize(4)
  .orbit(2)
  .play()
''')

# Sub bass — sine, barely there
ctrl.set_track("bass", '''
note("<c1 c1 eb1 f1>")
  .s("sine")
  .gain(.7).decay(1.5).sustain(0).lpf(100)
  .play()
''')

# Deep filtered chord pad — slow sweep
ctrl.set_track("chords", '''
note("<[c3,eb3,g3,bb3] [f3,ab3,c4] [eb3,g3,bb3,d4] [f3,ab3,c4,eb4]>/4")
  .s("sawtooth")
  .lpf(sine.range(300, 1200).slow(16))
  .lpq(2).room(.5).roomsize(3)
  .gain(.1).orbit(3)
  .play()
''')
```

**Why it works:** The rim delay creates the "dub" atmosphere. The chord pad's slow filter sweep gives movement without being busy. The sub bass anchors everything without competing for frequency space (lpf at 100 Hz).

---

### Acid House

**303-style acid** — Phuture / DJ Pierre. The filter envelope IS the instrument.

```python
ctrl.set_cps(0.55)

ctrl.set_track("kick", '''
s("bd*4").bank("RolandTR909")
  .shape(.4).gain(.95)
  .play()
''')

ctrl.set_track("tops", '''
s("~ cp ~ ~, hh*8").bank("RolandTR909")
  .gain("0.6 0.3 0.5 0.2 0.6 0.3 0.5 0.2")
  .room(.1)
  .play()
''')

# THE ACID — 24dB filter + envelope + resonance sweep
ctrl.set_track("acid", '''
note("[c2 c2 <eb2 c2> c2 [c2 g2] c2 <f2 eb2> c2]*2")
  .s("sawtooth")
  .ftype('24db')
  .lpf(sine.range(200, 1500).slow(8))
  .lpenv(sine.range(1, 8).slow(16))
  .lpd(perlin.range(.05, .2))
  .lpa(.005)
  .lpq(sine.range(4, 14).slow(12))
  .shape(.35).gain(.35)
  .rarely(x => x.add(note(12)))
  .play()
''')
```

# Ride — sparse, rides over the top with occasional double-hits
ctrl.set_track("ride", '''
s("~ ~ rd ~").bank("RolandTR909")
  .gain(.25).room(.2)
  .sometimes(x => x.ply(2))
  .play()
''')

# Stab — occasional chord hit with delay, on its own orbit
ctrl.set_track("stab", '''
note("[c4,eb4,g4](3,8)")
  .s("square").lpf(1500)
  .decay(.15).sustain(0)
  .room(.4).delay(".3:.125:.4")
  .gain(.12).orbit(2)
  .play()
''')
```

**Why it works:** The `.ftype('24db')` gives the steeper Roland-style filter slope. Three different signals (`sine`, `sine`, `perlin`) modulate filter cutoff, envelope depth, and decay independently, creating constantly evolving timbral movement. The `.rarely(x => x.add(note(12)))` adds occasional octave jumps like a real 303. The ride's `.ply(2)` creates occasional double-hits for energy.

---

### Jungle / Breakcore

**Chopped breaks** — mangled Amen-style patterns.

```python
ctrl.send("samples('github:yaxu/clean-breaks')")
time.sleep(3)
ctrl.set_cps(0.55)

# Main break — chopped, with occasional double-time
ctrl.set_track("break1", '''
s("clean:2").loopAt(2)
  .chop(16)
  .every(4, x => x.fast(2))
  .sometimesBy(.15, x => x.speed(-1))
  .shape(.3).gain(.55).room(.15)
  .play()
''')

# Second layer — phased against first for thickness
ctrl.set_track("break2", '''
s("clean:0").loopAt(4)
  .gain(.3)
  .mul(speed("1, 1.003"))
  .shape(.2)
  .play()
''')

# Sub bass
ctrl.set_track("bass", '''
note("<c1 c1 [eb1 ~] [f1 c1]>")
  .s("sine").decay(1.5).sustain(0).gain(.7).shape(.2)
  .play()
''')

# Stab — Euclidean rhythm with delay
ctrl.set_track("stab", '''
note("[c4,eb4,g4,bb4](3,8)")
  .s("sawtooth")
  .lpf(sine.range(600, 2000).slow(8))
  .decay(.2).sustain(0)
  .delay(".5:.167:.5").room(.4)
  .gain(.13).orbit(2)
  .play()
''')

# 808 toms — sparse, masked so they only appear in the second half
ctrl.set_track("perc", '''
s("[~ lt] [~ mt] [~ ht] ~").bank("RolandTR808")
  .gain(.3).room(.25)
  .speed("<1 1.5>")
  .mask("<0 0 1 1>")
  .play()
''')
```

**Why it works:** `.loopAt(2).chop(16)` time-stretches the break to 2 cycles then chops it into 16 granular slices — instant jungle. The second break at `.mul(speed("1, 1.003"))` creates a phasing effect. Euclidean `(3,8)` on the stab gives that classic tresillo rhythm. The `.mask("<0 0 1 1>")` on toms means they only play on cycles 3-4, creating a call-and-response structure.

---

### Jazz

**Jazz combo** — ii-V-I changes, walking bass, voice-led chords.

```python
ctrl.set_cps(0.45)

# Brushes
ctrl.set_track("drums", '''
stack(
  s("~ sd ~ sd").gain(.35).room(.4),
  s("hh*4").gain("<.3 .2 .25 .2>").room(.3)
)
  .play()
''')

# Walking bass follows the chord changes
ctrl.set_track("bass", '''
n("[0 [~ 0] 4 [3 2] [0 ~] [0 ~] <0 2> ~]/2")
  .scale("<D2:dorian G2:mixolydian C2:major C2:major>/2")
  .s("triangle").lpf(400).gain(.6)
  .play()
''')

# Comping with iReal voicings — sparse, rhythmic
ctrl.set_track("chords", '''
chord("<Dm7 G7 C^7 C^7>")
  .dict('ireal').struct("[~ x]*2").voicing()
  .s("sawtooth").lpf(1500).resonance(2)
  .attack(.01).decay(.3).sustain(.15)
  .gain(.18).room(.3)
  .play()
''')

# Melody with canon effect via .off()
ctrl.set_track("melody", '''
n("<0 [4 3] 2 [~ 1]> <[~ 2] 4 [3 5] [~ 0]>")
  .scale("<D4:dorian G4:mixolydian C4:major C4:major>/2")
  .off(1/8, x => x.add(4).gain(.3))
  .s("sine").release(.5)
  .delay(.3).delaytime(.375).delayfeedback(.2)
  .room(.5).gain(.35).orbit(2)
  .play()
''')
```

**Why it works:** `.dict('ireal').voicing()` automatically voice-leads the chord changes (no manual voicings needed). Scale mode changes per chord: dorian on ii, mixolydian on V, major on I. The `.off(1/8, x => x.add(4))` on the melody creates a canon at the 4th interval — instant bebop complexity.

---

### Ambient

**Slow evolving pads** — Brian Eno / Stars of the Lid.

```python
ctrl.set_cps(0.15)

# Pad 1 — sawtooth, very slow filter
ctrl.set_track("pad1", '''
note("<[c3,eb3,g3,bb3] [ab2,c3,eb3,g3] [f3,ab3,c4] [g3,bb3,d4]>/8")
  .s("sawtooth")
  .attack(2).release(4)
  .lpf(sine.range(200, 900).slow(32))
  .lpq(1).room(.8).roomsize(8)
  .gain(.08).orbit(2)
  .play()
''')

# Pad 2 — triangle, opposite filter phase via cosine
ctrl.set_track("pad2", '''
note("<[g3,bb3,d4] [eb3,g3,bb3] [c4,eb4,g4] [d4,f4,a4]>/8")
  .s("triangle")
  .attack(3).release(5)
  .lpf(cosine.range(300, 1200).slow(32))
  .room(.9).roomsize(10)
  .gain(.06).orbit(3)
  .play()
''')

# Sparse piano — almost accidental
ctrl.set_track("piano", '''
n("<[~ 0] ~ [~ 4] ~ ~ [3 ~] ~ [~ 2]>/2")
  .scale("C4:minor").s("piano")
  .gain(.3).room(.9).roomsize(8)
  .delay(.4).delaytime(.5).delayfeedback(.4)
  .orbit(4).velocity(perlin.range(.3, .7))
  .play()
''')

# High shimmer — barely audible
ctrl.set_track("shimmer", '''
n("<0 2 4 7 9 11 4 2>/4")
  .scale("C6:minor").s("sine")
  .attack(1).release(3).gain(.03)
  .pan(rand).room(1).roomsize(10)
  .orbit(5)
  .play()
''')
```

**Why it works:** CPS at 0.15 means each cycle is ~6.7 seconds. With `/8` patterns, chord changes happen every ~53 seconds. Long attack/release envelopes (2-5 seconds) create glacial crossfades. `sine` vs `cosine` filter LFOs on the two pads create complementary breathing. Piano is mostly rests — the delay fills in the space.

---

### Funk

**Synth funk** — Marc Rebillet / Felix Roos. Works with zero samples.

```python
ctrl.set_cps(0.5)

ctrl.set_track("drums", '''
stack(
  s("bd*2, ~ sd").bank("RolandTR707").room("0 .1"),
  s("hh*4").begin(.2).end(.25).release(.02)
    .gain(.3).bank("RolandTR707").late(.02).room(.5)
).fast(2)
  .play()
''')

ctrl.set_track("bass", '''
note("<[a1 [~ [g2 a2]] [g1 g#1] [a1 [g2 a2]]] [a1 [~ [g2 a2]] [e3 d3] [c3 [g3 a3]]]>")
  .s("sawtooth").lpf(800).resonance(5)
  .decay(.15).sustain(.1).gain(.5)
  .play()
''')

ctrl.set_track("keys", '''
note("<[[a2,g3,[b3 c4],e4] ~ [g3,c4,e4](3,8)@4 ~@2]!3 [[e2,e3,a3,b3,e4]@3 [e2,e3,ab3,b3,e4]@5]>")
  .s("sawtooth").lpf(2000).resonance(2)
  .attack(.01).decay(.2).sustain(.3)
  .gain(.2).room(.3)
  .play()
''')
```

**Why it works:** The bass pattern uses chromatic passing tones (g1 g#1) and syncopated ghost notes. The keys use `@` elongation for held notes and Euclidean `(3,8)` for rhythmic density. The `.late(.02)` on hats creates a lazy, behind-the-beat feel.

---

### Drum & Bass / Liquid

**Lush melodic session** — no drums, walking bass, real piano + pads. ~190 BPM.

```python
# Load real instrument samples
ctrl.send("samples('https://strudel.b-cdn.net/piano.json', 'https://strudel.b-cdn.net/piano/')")
ctrl.send("samples('https://strudel.b-cdn.net/vcsl.json', 'https://strudel.b-cdn.net/VCSL/')")
time.sleep(3)

ctrl.set_cps(0.85)  # ~200 BPM

# Walking bass — chromatic passing tones
ctrl.set_track("bass", '''
note("<c2 d2 eb2 f2 ab2 g2 f2 eb2 bb1 c2 d2 eb2 f2 ab2 bb2 c3>/4")
  .s("sawtooth").lpf(500).lpq(2)
  .shape(.3).gain(.45)
  .decay(.4).sustain(.3).release(.1)
  .play()
''')

# Piano — real samples, jazz voicings, .clip(1) to control note length
ctrl.set_track("piano", '''
note("<[c3,eb3,g3,bb3] [ab2,c3,eb3,g3] [bb2,d3,f3,ab3] [g2,bb2,d3,f3]>/2")
  .s("piano").clip(1)
  .room(.5).roomsize(3).lpf(3500)
  .gain(.4).orbit(2)
  .play()
''')

# Piano melody — arpeggiated top line
ctrl.set_track("piano_mel", '''
note("<g4 bb4 c5 eb5 [d5 c5] bb4 g4 [ab4 bb4]>/2")
  .s("piano").clip(1)
  .room(.6).roomsize(4)
  .delay(.4).delaytime(.25).delayfeedback(.4)
  .gain(.3).orbit(3)
  .play()
''')

# Warm pad — detuned saws, slow attack
ctrl.set_track("pad", '''
note("<[c4,eb4,g4,bb4] [ab3,c4,eb4,g4] [bb3,d4,f4,ab4] [g3,bb3,d4,f4]>/4")
  .s("sawtooth")
  .mul(note("0, 0.08"))
  .attack(.5).decay(2).sustain(.7).release(1)
  .lpf(sine.range(600, 2000).slow(16)).lpq(1)
  .room(.8).roomsize(6)
  .gain(.15).orbit(4)
  .play()
''')

# Vibraphone — shimmering arpeggios with dotted delay
ctrl.set_track("vibes", '''
note("<eb5 g5 bb5 c6 [bb5 g5] eb5 d5 [c5 bb4]>/2")
  .s("triangle")
  .attack(.005).decay(.4).sustain(.05).release(.3)
  .lpf(4000)
  .delay(.5).delaytime(.167).delayfeedback(.5)
  .room(.6).roomsize(4)
  .pan(sine.range(.2, .8).slow(4))
  .gain(.18).orbit(5)
  .play()
''')

# Synth lead — sparse, singing saw
ctrl.set_track("lead", '''
note("<~ ~ [eb5 d5] [c5 ~] ~ [bb4 c5] [d5 ~] ~>/2")
  .s("sawtooth")
  .attack(.05).decay(.3).sustain(.4).release(.5)
  .lpf(sine.range(1000, 3000).slow(8))
  .delay(.5).delaytime(.25).delayfeedback(.45)
  .room(.7).roomsize(5)
  .gain(.15).orbit(7)
  .play()
''')
```

**Why it works:** At 0.85 CPS (~200 BPM), the walking bass drives forward motion without drums. `.clip(1)` on piano controls note length so chords don't bleed together. The detuned pad (`.mul(note("0, 0.08"))`) adds warmth. Every melodic layer uses a different `.orbit()` so reverb/delay settings don't clash. The dotted delay on vibes (`.delaytime(.167)` = dotted 8th) creates cross-rhythms against the straight bass.

---

### Jazzy Beats

**Syncopated drums + pentatonic guitar** — hip-hop jazz, ghost notes.

```python
# Load drum machines
ctrl.send("samples('https://strudel.b-cdn.net/tidal-drum-machines.json', 'https://strudel.b-cdn.net/tidal-drum-machines/machines/')")
time.sleep(2)

ctrl.set_cps(0.5)

# Syncopated kick — ghost notes and offbeats
ctrl.set_track("kick", '''
s("[bd ~ [~ bd] ~] [~ bd ~ ~]")
  .bank("RolandTR707")
  .gain(".9 .5 .6 .4 .3 .7 .5 .3")
  .shape(.2).room(.15)
  .play()
''')

# Snare — rim clicks and ghost hits
ctrl.set_track("snare", '''
s("[~ ~ sd ~] [~ sd [~ sd] ~]")
  .bank("RolandTR707")
  .gain(".3 .2 .7 .3 .2 .8 .4 .3")
  .room(.25)
  .play()
''')

# Hats — swung 16ths mixing closed and open hi-hats
ctrl.set_track("hats", '''
s("[hh hh [hh oh] hh] [hh [~ hh] hh hh]")
  .bank("RolandTR707")
  .gain("[.5 .25 .4 .6] [.3 .2 .5 .35]")
  .pan(sine.range(.35,.65).slow(4))
  .room(.1).orbit(1)
  .play()
''')

# Guitar melody — minor pentatonic, sparse with reverb
ctrl.set_track("guitar", '''
n("[~ 4] [2 ~] [~ [3 5]] [0 ~]")
  .scale("Eb5:minor:pentatonic")
  .s("triangle")
  .attack(.005).decay(.18).sustain(.08).release(.6)
  .lpf(3500).resonance(3)
  .gain(.22)
  .room(.65).roomsize(4)
  .delay(".3:.166:.35")
  .orbit(2)
  .play()
''')

# Guitar echo — octave-up layer, very quiet, more reverb
ctrl.set_track("guitar_echo", '''
n("<[~ 4] ~ [2 ~] ~> <~ [3 ~] ~ [5 0]>")
  .scale("Eb6:minor:pentatonic")
  .s("triangle")
  .attack(.01).decay(.12).sustain(.05).release(.8)
  .lpf(4500).resonance(2)
  .gain(.1)
  .room(.8).roomsize(5)
  .delay(".4:.25:.45")
  .orbit(3)
  .play()
''')
```

**Why it works:** The gain patterns (`".9 .5 .6 .4 .3 .7 .5 .3"`) on the kick create ghost notes — softer hits between the main beats give a human, hip-hop feel. The `oh` (open hi-hat) mixed with `hh` (closed) adds timbral variety. Using `minor:pentatonic` scale means the melody notes always sound consonant. The octave-up guitar echo layer with more reverb creates depth without cluttering the mix.

---

### Jazz Fusion with Synth Pads

**Drums + jazz guitar + Vince DiCola supersaw pads** — 80s fusion energy.

```python
ctrl.set_cps(0.45)

# Kick/snare — 909, syncopated
ctrl.set_track("kick_snare", '''
s("bd [~ bd] sd [bd ~]")
  .bank("RolandTR909")
  .gain("1 .7 .9 .6").shape(.3).room(.15)
  .play()
''')

# Hats — 8ths with panned movement
ctrl.set_track("hats", '''
s("hh*8").bank("RolandTR909")
  .gain(".8 .3 .5 .2 .7 .3 .6 .2")
  .pan(sine.range(.3,.7).fast(3))
  .room(.1)
  .play()
''')

# Perc — clap with delay + occasional crush
ctrl.set_track("perc", '''
s("~ cp:3 ~ [~ cp:1]").bank("RolandTR909")
  .gain(.4).room(.4)
  .delay(".3:.125:.3").pan(.7)
  .sometimes(x => x.crush(8))
  .play()
''')

# Jazz guitar comping — iReal voicings, sparse rhythmic hits
ctrl.set_track("guitar_comp", '''
chord("<Dm9 G13 C^9 A7b9>/2")
  .dict('ireal').voicing()
  .struct("[~ x] [x ~] [~ x] [~ [x ~]]")
  .s("square").lpf(1200)
  .attack(.005).decay(.2).sustain(.08).release(.15)
  .gain(.16).room(.35).pan(.4).orbit(2)
  .play()
''')

# Jazz guitar lead — scale modes follow chord changes
ctrl.set_track("guitar_lead", '''
n("<[0 ~ 4 3] [2 ~ ~ 1]> <[~ 2] [4 ~ 3 5] [~ 0 ~ 2] [4 3 ~ ~]>")
  .scale("<D4:dorian G4:mixolydian C4:major A4:phrygian>/2")
  .s("triangle").lpf(2200)
  .attack(.008).decay(.25).sustain(.05).release(.3)
  .gain(.28).room(.4)
  .delay(".25:.375:.2").orbit(3).pan(.6)
  .sometimes(x => x.add(note(12)).gain(.15))
  .play()
''')

# Walking bass — scale-based
ctrl.set_track("bass", '''
n("[0 [~ 0] 4 [3 2]] [0 [~ 3] 4 [5 ~]] [0 [2 ~] 4 [3 2]] [0 [~ 4] 3 [2 0]]/2")
  .scale("<D2:dorian G2:mixolydian C2:major A2:phrygian>/2")
  .s("sawtooth").lpf(380).shape(.4)
  .gain(.55).room(.15).orbit(4)
  .play()
''')

# Supersaw pad — big detuned pad with slow filter sweep
ctrl.set_track("dicola_pad", '''
note("<[d3,f3,a3,c4] [g3,b3,d4,f4] [c3,e3,g3,b3] [a2,c3,e3,g3]>/2")
  .s("supersaw")
  .detune(sine.range(3,8).slow(16))
  .lpf(sine.range(600,2800).slow(12)).lpq(2)
  .attack(.4).decay(.6).sustain(.7).release(.8)
  .gain(.13).room(.6).roomsize(4)
  .pan(.45).orbit(5)
  .play()
''')

# Soaring synth lead — filter envelope + delay
ctrl.set_track("dicola_lead", '''
n("<[~ 4] [5 ~ 7 4]> <[2 ~ ~ 0] [~ 4 5 ~]>")
  .scale("<D5:dorian G5:mixolydian C5:major A5:phrygian>/2")
  .s("sawtooth")
  .lpf(sine.range(1500,5000).slow(8)).lpq(3)
  .attack(.02).decay(.15).sustain(.6).release(.4)
  .gain(.2).room(.5).roomsize(3)
  .delay(".35:.25:.3").orbit(6).pan(.6)
  .every(4, x => x.add(note(12)).gain(.12))
  .play()
''')
```

**Why it works:** 8 layers but each has its own `.orbit()` so effects don't collide. The `supersaw` oscillator with `.detune(sine.range(3,8).slow(16))` creates the huge 80s pad sound — the detune amount itself is modulated. Scale modes change per chord (dorian→mixolydian→major→phrygian) so the lead and bass follow the harmony automatically. The `.sometimes(x => x.add(note(12)).gain(.15))` on the guitar occasionally leaps an octave for energy.

---

### Synth-Only (Zero Dependencies)

**Guaranteed to work** — uses only built-in oscillators, no samples needed.

```python
ctrl.set_cps(0.5)

# Kick — sine with fast decay
ctrl.set_track("kick", '''
note("c1 c1 c1 [c1 c1]")
  .s("sine").decay(.15).sustain(0).gain(.8)
  .play()
''')

# Bass — filtered sawtooth
ctrl.set_track("bass", '''
note("<c2 [~ c2] eb2 [f2 c2]>")
  .s("sawtooth").lpf(500).decay(.25).sustain(0).gain(.45)
  .play()
''')

# Chords — triangle, Euclidean
ctrl.set_track("chords", '''
note("[c3,eb3,g3](3,8)")
  .s("triangle").lpf(1500).gain(.2).room(.3)
  .play()
''')

# Lead — square with filter sweep
ctrl.set_track("lead", '''
note("<[~ c4] [eb4 g4] bb3 [c4 ~]>")
  .s("square").lpf(sine.range(400, 2000).slow(4))
  .gain(.12).room(.4)
  .play()
''')
```

**Why it works:** Pure oscillators always work — no sample loading needed. Sine for sub-bass kick, sawtooth for bass warmth, triangle for mellow chords, square for cutting lead. The filter sweep on the lead is the main movement.

---

## Technique Examples (Standalone Strudel Code)

These are pure Strudel patterns showing specific techniques. Use with `ctrl.send(code, evaluate=True)` or as track code.

### The `.off()` Canon Technique

Creates instant richness by layering copies at different time offsets and intervals.

```js
n("0 [4 3] 2 [~ 1]").scale("C5:minor:pentatonic")
  .off(1/8, x=>x.add(4).gain(.5))   // 4th above, 1/8 cycle later
  .off(1/4, x=>x.add(7).gain(.3))   // 5th above, 1/4 cycle later
  .s("triangle").room(.4).delay(.25)
```

**Why:** Three staggered copies of the melody at musically consonant intervals (unison, 4th, 5th) create a Bach-like counterpoint effect automatically.

### Euclidean Rhythms

Distribute k hits across n steps — generates musical rhythms from around the world.

```js
// Tresillo (3,8) — Cuban/Afro
s("bd(3,8)")

// Cinquillo (5,8) — Reggaeton
s("hh(5,8)")

// West African bell (7,12)
s("cp(7,12)")

// Combined
stack(
  s("bd(3,8)").bank("RolandTR909").gain(.9),
  s("sd(5,8,2)").bank("RolandTR909").gain(.5),
  s("hh(7,8)").bank("RolandTR909").gain(.4)
)
```

### Detuned Thickness

Add a slightly detuned copy for chorus/unison effect.

```js
// Method 1: .mul() with tiny offset
note("<c2 eb2 f2 ab2>")
  .s("sawtooth")
  .mul(note("0, 0.08"))   // second voice 8 cents sharp
  .lpf(500)

// Method 2: .superimpose() with pitch offset
note("c2 d2 eb2 f2")
  .superimpose(x=>x.add(.05))
  .s("sawtooth").lpf(400)
```

### Filter Envelope Design

The filter envelope is the key to acid, bass, and lead sounds.

```js
// Classic acid squelch
note("c2(5,8)")
  .s("sawtooth").ftype('24db')
  .lpf(400)          // base cutoff
  .lpenv(8)          // envelope opens 8x above base
  .lpa(.005)         // instant attack
  .lpd(.15)          // fast decay
  .lpq(12)           // high resonance = squelch
  .shape(.3)

// Slow pad filter bloom
note("[c3,eb3,g3,bb3]")
  .s("sawtooth")
  .lpf(sine.range(300, 2000).slow(16))  // 16-cycle sweep
  .lpq(2)                                 // gentle resonance
  .attack(.5).release(1)
```

### Breakbeat Manipulation

```js
// Basic chop
s("clean:2").loopAt(2).chop(8)

// With slice rearrangement
s("clean:2").loopAt(2)
  .splice(8, "0 1 2 3 4 5 6 7")
  .sometimes(x => x.ply(2))          // double hits
  .sometimesBy(.1, x => x.speed(-1)) // rare reverse
  .room(.2).shape(.3)

// Polyrhythmic break layering
stack(
  s("clean:2").loopAt(2).chop(16).gain(.5),
  s("clean:0").loopAt(4).gain(.3)
    .mul(speed("1, 1.003"))           // phasing
)
```

### Dynamic Patterns with `.every()` and `.chunk()`

```js
// Drum fill every 4th bar
s("bd [~ bd] sd [bd ~], hh*8")
  .bank("RolandTR909")
  .every(4, x => x.fast(2))

// Progressive transformation
n("0 2 4 6").scale("C:minor")
  .chunk(4, x => x.add(note(7)))     // rotate which quarter is transposed
  .s("triangle").room(.3)

// Conditional variation
s("bd*4, [~ sd]*2, hh*8")
  .bank("RolandTR909")
  .firstOf(8, x => x.ply(2))         // fill on bar 1
  .lastOf(4, x => x.fast(1.5))       // push on last bar
  .sometimes(x => x.room(.3))        // random reverb splashes
```

---

## Complete Compositions (Strudel Native)

### Caverave (Felix Roos)

Demonstrates: `layer()`, `mask()`, scale changes, interleaved arpeggios.

```js
const keys = x => x.s('sawtooth').cutoff(1200).gain(.5)
  .attack(0).decay(.16).sustain(.3).release(.1);

const drums = stack(
  s("bd*2").mask("<x@7 ~>/8").gain(.8),
  s("~ <sd!7 [sd@3 ~]>").mask("<x@7 ~>/4").gain(.5),
  s("[~ hh]*2").delay(.3).delayfeedback(.5).delaytime(.125).gain(.4)
);

const synths = stack(
  "<eb4 d4 c4 b3>/2"
  .scale("<C:minor!3 C:melodic:minor>/2")
  .struct("[~ x]*2")
  .layer(
    x=>x.scaleTranspose(0).early(0),
    x=>x.scaleTranspose(2).early(1/8),
    x=>x.scaleTranspose(7).early(1/4),
    x=>x.scaleTranspose(8).early(3/8)
  ).note().apply(keys).mask("<~ x>/16"),
  note("<C2 Bb1 Ab1 [G1 [G2 G1]]>/2")
  .struct("[x [~ x] <[~ [~ x]]!3 [x x]>@2]/2".fast(2))
  .s('sawtooth').attack(0.001).decay(0.2).sustain(1).cutoff(500),
  chord("<Cm7 Bb7 Fm7 G7b13>/2")
  .struct("~ [x@0.2 ~]".fast(2))
  .dict('lefthand').voicing().every(2, early(1/8))
  .apply(keys).sustain(0)
  .delay(.4).delaytime(.12)
  .mask("<x@7 ~>/8".early(1/4))
).add(note("<-1 0>/8"))

stack(drums.fast(2), synths).slow(2)
```

### Melting Submarine (Felix Roos)

Demonstrates: detuning, perlin noise modulation, `echoWith()`, `degradeBy()`.

```js
samples('github:tidalcycles/dirt-samples')

stack(
  // drums
  s("bd:5,[~ <sd:1!3 sd:1(3,4,3)>],hh27(3,4,1)")
  .speed(perlin.range(.7,.9)),

  // bass — detuned + perlin pitch
  "<a1 b1*2 a1(3,8) e2>"
  .off(1/8,x=>x.add(12).degradeBy(.5))
  .add(perlin.range(0,.5))
  .superimpose(add(.05))
  .note().decay(.15).sustain(0)
  .s('sawtooth').gain(.4)
  .cutoff(sine.slow(7).range(300,5000))
  .lpa(.1).lpenv(-2),

  // chords — detuned saw pad
  chord("<Am7!3 <Em7 E7b13 Em7 Ebm7b5>>")
  .dict('lefthand').voicing()
  .add(note("0,.04"))
  .add(note(perlin.range(0,.5)))
  .s('sawtooth').gain(.16).cutoff(500).attack(1),

  // melody — triangle, degraded + echo
  "a4 c5 <e6 a6>".struct("x(5,8,-1)")
  .superimpose(x=>x.add(.04))
  .add(perlin.range(0,.5)).note()
  .decay(.1).sustain(0).s('triangle')
  .degradeBy(perlin.range(0,.5))
  .echoWith(4,.125,(x,n)=>x.gain(.15*1/(n+1)))
).slow(3/2)
```

### Giant Steps (John Coltrane)

Demonstrates: complex jazz harmony, voice-led chords with `.anchor()`, bass line.

```js
let melody = seq(
  "[F#5 D5] [B4 G4] Bb4 [B4 A4]",
  "[D5 Bb4] [G4 Eb4] F#4 [G4 F4]",
  "Bb4 [B4 A4] D5 [D#5 C#5]",
  "F#5 [G5 F5] Bb5 [F#5 F#5]",
).note()

stack(
  melody,
  seq(
    "[B^7 D7] [G^7 Bb7] Eb^7 [Am7 D7]",
    "[G^7 Bb7] [Eb^7 F#7] B^7 [Fm7 Bb7]",
    "Eb^7 [Am7 D7] G^7 [C#m7 F#7]",
    "B^7 [Fm7 Bb7] Eb^7 [C#m7 F#7]"
  ).chord().dict('lefthand').anchor(melody).mode('duck').voicing(),
  seq(
    "[B2 D2] [G2 Bb2] [Eb2 Bb3] [A2 D2]",
    "[G2 Bb2] [Eb2 F#2] [B2 F#2] [F2 Bb2]",
    "[Eb2 Bb2] [A2 D2] [G2 D2] [C#2 F#2]",
    "[B2 F#2] [F2 Bb2] [Eb2 Bb3] [C#2 F#2]"
  ).note()
).slow(20)
```

---

## Raw Example Sources

For additional examples from the Strudel community, see:
- `docs/strudel-examples-raw.md` — 15+ examples from tunes.mjs (CC BY-NC-SA 4.0)
- `docs/strudel-reference-raw.md` — Full reference compiled from strudel.cc docs
