# Strudel Live Coding — Agent Guide

## What This Is

A Python-to-browser system for AI-driven live-coded music. You write Python scripts that send Strudel pattern code over WebSocket to a browser running the Strudel audio engine. The browser evaluates the code and plays music in real-time.

**Strudel** is a JavaScript live-coding environment inspired by TidalCycles. It uses a cycle-based pattern language with "mini-notation" for expressing rhythms, melodies, and transformations.

## Architecture

```
Python script (your_composition.py)
  └─→ StrudelController (strudel_server.py)
        ├─→ WebSocket server (ws://localhost:8765)
        │     └─→ strudel.html (browser client)
        │           └─→ Strudel @strudel/web@1.0.3 engine
        └─→ HTTP file server (http://localhost:8766)
              └─→ serves strudel.html + static files
```

Optional add-ons:
- `strudel_live.py` — HTTP REST API on port 8767 for external control
- `stream.py` — Twitch streaming + chat integration via FFmpeg + Playwright

## How to Use It

### Quick Start

```python
from strudel_server import StrudelController
import time

ctrl = StrudelController()
ctrl.start()
# User opens http://localhost:8766/strudel.html and clicks "Start Audio & Connect"
ctrl.wait_for_browser()

# Load samples (if needed)
ctrl.send("samples('github:yaxu/clean-breaks')")
time.sleep(2)

# Set tempo
ctrl.set_cps(0.5)  # 0.5 cycles/sec = ~120 BPM

# Add tracks one at a time
ctrl.set_track("drums", '''
s("bd [~ bd] sd [bd ~], hh*8")
  .bank("RolandTR909")
  .gain("1 .6 .8 .6 1 .6 .9 .6")
  .room(.15)
  .play()
''')
time.sleep(4)

ctrl.set_track("bass", '''
note("<c2 c2 eb2 f2>")
  .s("sawtooth").lpf(300).shape(.4)
  .play()
''')

# Remove a layer
ctrl.stop_track("drums")

# Silence everything
ctrl.hush()
```

### Python API Reference

| Method | Description |
|--------|-------------|
| `ctrl.start()` | Start WebSocket + HTTP servers |
| `ctrl.wait_for_browser(timeout=30)` | Block until browser connects |
| `ctrl.send(code, evaluate=False)` | Send raw JS to browser |
| `ctrl.set_track(name, code)` | Set named track (code must end with `.play()`) |
| `ctrl.stop_track(name)` | Remove a track |
| `ctrl.hush()` | Silence everything, clear all tracks |
| `ctrl.set_cps(cps)` | Set tempo in cycles per second |
| `ctrl.tracks` | Dict of current track code |
| `ctrl.close()` | Shut down servers |

### Critical Rules

1. **Each `set_track()` code string must end with `.play()`** — the controller strips it before combining tracks into `stack()`.

2. **One `.play()` per track.** Never put multiple `.play()` calls in one `set_track`. The controller manages multi-track playback via `stack()` internally.

3. **Use `ctrl.send()` for non-pattern code:** sample loading, `hush()`, helper functions. Use `ctrl.set_track()` for musical patterns.

4. **Load samples before using them.** Call `ctrl.send("samples(...)")` and `time.sleep(2-3)` before tracks that use those samples.

5. **Build up layers with `time.sleep()`.** Add tracks one at a time with 3-4 second gaps. Musical tension comes from adding/removing elements.

6. **`evaluate` mode vs `eval` mode:**
   - `ctrl.send(code)` → plain `eval()` — for `hush()`, `samples()`, utility code
   - `ctrl.send(code, evaluate=True)` → Strudel transpiler — for pattern code
   - `ctrl.set_track()` automatically uses evaluate mode internally

### How Multi-Track Works

Strudel's `.play()` replaces the scheduler's single pattern. To play multiple tracks simultaneously, the controller:
1. Strips `.play()` from each track's code
2. Combines all tracks into `stack(track1, track2, ...)`
3. Appends `.cps(N)` if tempo is set
4. Sends via `evaluate` mode (which adds `.play()` internally)

### Tempo Guide

| CPS | BPM (approx) | Style |
|-----|---------------|-------|
| 0.15 | ~36 | Ambient, drone |
| 0.35 | ~84 | Slow downtempo |
| 0.45 | ~108 | Jazz, soul |
| 0.5 | ~120 | House, funk |
| 0.55 | ~132 | Acid, techno |
| 0.65 | ~156 | Drum and bass (half-time) |
| 0.85 | ~200 | Fast DnB, jungle |

Formula: BPM ≈ CPS × 240 (assuming 4 beats per cycle).

---

## Writing Music That Sounds Amazing

### The Golden Rules

**1. Groove > Grid**
Never write perfectly quantized robot music. Use rests `~`, sub-sequences `[~ bd]`, Euclidean rhythms `(3,8)`, and dynamic `.gain()` patterns. Human feel comes from what you *don't* play.

```
// BAD: mechanical
s("bd sd bd sd, hh hh hh hh")

// GOOD: groove
s("bd [~ bd] sd [bd ~], hh*8")
  .gain("1 .6 .8 .6 1 .6 .9 .6")
```

**2. Use Real Drum Samples**
Never synthesize kicks/snares with `note("c1").s("sine")`. Always use `s("bd sd hh")` with `.bank("RolandTR909")` or similar drum machine.

**3. Effects Create Space**
Dry samples sound like toys. Every track needs some processing:
- `.room(.15-.5)` — subtle reverb on most things
- `.shape(.2-.4)` — warm saturation on bass/drums
- `.lpf()` — filter everything bright (the "club door" metaphor)
- `.delay(".5:.125:.4")` — on sparse melodic parts

**4. Less Is More**
3-5 well-crafted tracks > 10 layers of noise. Standard arrangement:
- **Drums** — kick/snare/hat groove
- **Bass** — filtered saw or sine, root notes
- **Chords/Pad** — filtered, quiet, slow-moving
- **Lead/Melody** — sparse, with delay/reverb
- Optional: percussion, texture, breaks

**5. Repetition with Variation**
Use `.every(N, fn)`, `.sometimes(fn)`, `.chunk(N, fn)`. Brains want predictable patterns with occasional surprises. Don't pile on randomness.

```
s("bd [~ bd] sd [bd ~], hh*8")
  .bank("RolandTR909")
  .every(4, x => x.fast(2))          // double-time every 4th bar
  .firstOf(8, x => x.ply(2))         // fills on bar 1 of 8
```

**6. Stay in Key**
Use `.scale("C:minor")` with `n()` for safety. Common progressions:
- Minor: i - iv - v - i, i - VI - III - VII
- Pentatonic melodies always sound good
- Jazz: ii - V - I (`Dm7 G7 C^7`)

**7. Signals for Smooth Automation**
Use `sine.range(lo,hi).slow(N)` for filter sweeps, not stepped values.

```
.lpf(sine.range(200, 4000).slow(8))   // sweep filter over 8 cycles
.gain(saw.range(.15, .6))             // ramping dynamics
.pan(sine.range(.3, .7).fast(3))      // gentle stereo movement
```

**8. Orbits Separate Effect Buses**
Different tracks sharing the same orbit share reverb/delay settings. Use `.orbit(N)` to give tracks independent effects.

### Arrangement Strategy

When building a composition, layer tracks over time:

```python
ctrl.set_track("drums", drum_code)
time.sleep(4)    # let it breathe
ctrl.set_track("bass", bass_code)
time.sleep(4)    # bass anchors the groove
ctrl.set_track("chords", chord_code)
time.sleep(4)    # harmonic context
ctrl.set_track("lead", melody_code)
```

To create tension: remove elements, not just add them. `ctrl.stop_track("drums")` before a drop creates anticipation.

### Genre Recipes

#### House / Techno
- Tempo: 0.5-0.55 CPS
- Drums: 909, four-on-the-floor kick, offbeat hats
- Bass: sawtooth with 24dB filter
- Chords: slow filter sweep, reverb
- Key: minor keys (Cm, Fm, Gm)

#### Acid House
- Tempo: 0.55 CPS
- Drums: 909 kick + clap + ride
- Bass: sawtooth + `.ftype('24db')` + filter envelope (`.lpenv()`, `.lpd()`, `.lpq()`)
- Stab: short chord hit with delay
- The resonance sweep IS the song

#### Dub Techno
- Tempo: 0.5 CPS
- Drums: 909 kick + 16th hats with dynamics
- Key element: rim shot with heavy delay + reverb (`.delay(.7).delaytime(.375).delayfeedback(.55).room(.6).roomsize(4)`)
- Chords: deep filtered saw, very slow sweep
- Bass: sine sub, almost subliminal

#### Jungle / Breakcore
- Tempo: 0.55-0.85 CPS
- Breaks: `samples('github:yaxu/clean-breaks')` + `.loopAt(2).chop(16)`
- Bass: sine sub with decay
- Stab: minor chord with Euclidean rhythm + delay
- Key: mangle breaks with `.speed(-1)`, `.ply(2)`, `.every(4, fast(2))`

#### Jazz
- Tempo: 0.45 CPS
- Drums: brushes (simple `s("~ sd ~ sd")` + soft hats)
- Bass: walking line using `.scale("D2:dorian")` etc.
- Chords: `chord("Dm7").dict('ireal').voicing()` for auto voice-leading
- Melody: pentatonic with `.off()` for canon effect

#### Ambient
- Tempo: 0.15 CPS (very slow)
- No drums
- Pads: long attack/release (`.attack(2).release(4)`), heavy reverb
- Piano: sparse notes with reverb + delay
- Texture: high sine tones, barely audible
- Use opposite filter phases on layers: `sine` vs `cosine`

#### Funk
- Tempo: 0.5 CPS
- Drums: 707 or 808, syncopated
- Bass: sawtooth with filter, syncopated ghost notes
- Keys: staccato chord stabs
- Clav: square wave, short decay

#### DnB / Liquid
- Tempo: 0.85 CPS
- Walking bass, piano samples, warm pads
- Use `.clip(1)` on piano to control note length
- Detuned pad: `.mul(note("0, 0.08"))` for chorus thickness
- Lots of delay (`.delaytime(.25).delayfeedback(.45)`)
- Use `.orbit()` extensively — many layers need separate reverb

#### Jazzy Beats
- Tempo: 0.5 CPS
- Drums: 707, syncopated ghost notes via gain patterns (`".9 .5 .6 .4"`)
- Mix `hh` and `oh` (open hi-hat) for timbral variety
- Guitar: `minor:pentatonic` scale, triangle oscillator
- Octave-up echo layer for depth
- Key: per-step gain variation creates the "human" feel

#### Jazz Fusion
- Tempo: 0.45 CPS
- Drums: 909 kick/snare + hats with stereo pan movement
- Chords: `chord("Dm9").dict('ireal').voicing()` with `.struct()` for rhythm
- Pad: `supersaw` + `.detune(sine.range(3,8).slow(16))` for big 80s sound
- Scale modes follow chord changes: dorian→mixolydian→major
- 6-8 layers, each on its own `.orbit()`

### Sample Loading

```python
# GitHub sample packs (expects strudel.json at repo root)
ctrl.send("samples('github:yaxu/clean-breaks')")
ctrl.send("samples('github:tidalcycles/dirt-samples')")

# CDN-hosted sample packs (reliable, fast)
ctrl.send("samples('https://strudel.b-cdn.net/tidal-drum-machines.json', 'https://strudel.b-cdn.net/tidal-drum-machines/machines/')")
ctrl.send("samples('https://strudel.b-cdn.net/piano.json', 'https://strudel.b-cdn.net/piano/')")
ctrl.send("samples('https://strudel.b-cdn.net/vcsl.json', 'https://strudel.b-cdn.net/VCSL/')")

# Inline samples from URLs
ctrl.send("""samples({
  bass: 'https://cdn.freesound.org/previews/614/614637_2434927-hq.mp3',
  bell: { c6: 'https://cdn.freesound.org/previews/411/411089_5121236-lq.mp3' }
})""")
```

**Samples are cached** in the browser after first load. After `ctrl.send("samples(...)")`, wait 2-3 seconds before using them.

### Drum Machines

| Bank | Style | Best For |
|------|-------|----------|
| `RolandTR808` | Deep, boomy | Hip-hop, trap, electro |
| `RolandTR909` | Punchy, bright | House, techno |
| `RolandTR707` | Crisp, clean | Pop, new wave, funk |
| `RolandTR505` | Lo-fi, thin | Lo-fi, indie |
| `AkaiLinn` | Tight, funky | Prince, electrofunk |
| `CasioRZ1` | Digital, snappy | 80s digital |

### Built-in Oscillators (Always Work, No Samples Needed)

| Waveform | Character | Use For |
|----------|-----------|---------|
| `sawtooth` | Bright, buzzy | Bass, pads, leads |
| `square` | Hollow, woody | Stabs, clav, retro leads |
| `triangle` | Soft, muted | Default for `note()`, gentle leads |
| `sine` | Pure tone | Sub bass, gentle textures |
| `supersaw` | Big, detuned | Epic pads |

### Useful Techniques Often Missed

**Ghost notes via gain patterns:** Per-step gain variation makes drums feel human.
```
s("bd [~ bd] sd [bd ~]").gain(".9 .5 .6 .4 .3 .7 .5 .3")
```

**Open hi-hat (`oh`):** Mix with closed `hh` for realism.
```
s("[hh hh [hh oh] hh] [hh [~ hh] hh hh]").bank("RolandTR707")
```

**`.clip(n)` / `.legato(n)`:** Controls note duration. `.clip(1)` = notes fill their time slot exactly. Essential for piano samples.
```
note("[c3,eb3,g3]").s("piano").clip(1)
```

**`.begin(n)` / `.end(n)`:** Trim sample playback (0-1 range). Useful for extracting just the transient of a hat.
```
s("hh*4").begin(.2).end(.25)   // just the first click of the hi-hat
```

**`.mask(pat)`:** Gates a pattern — 0 = silence, 1 = play. Great for introducing layers.
```
s("[~ lt] [~ mt] [~ ht] ~").mask("<0 0 1 1>")  // only plays on cycles 3-4
```

**`.late(n)` / `.early(n)`:** Micro-timing offset. `.late(.02)` creates a lazy, behind-the-beat feel.

**`.ply(n)`:** Doubles/triples each hit. Great for fills: `.sometimes(x => x.ply(2))`.

**`.detune(n)`:** Detune oscillator in cents. Modulate for evolving pads:
```
.s("supersaw").detune(sine.range(3,8).slow(16))
```

**`pan(rand)`:** Random stereo placement per event — great for shimmer/texture layers.

**Pentatonic scales:** `"C5:minor:pentatonic"` — always sounds consonant, impossible to play a "wrong" note.

**`@` elongation in mini-notation:** `"c@3 eb"` = c is 3× as long as eb. Essential for shuffle grooves: `"[4@2 4]"`.

**`!` replication:** `"c!3 eb"` = c c c eb (each same length). Shorthand for repetition without `*`.

### Things That Don't Work

- `gm_*` instruments (e.g. `gm_acoustic_bass`) require `@strudel/soundfonts` — **NOT in the CDN bundle**
- `github:tidalcycles/strudel-samples` — **404, don't use it**
- `setcps()` as a global function — use `.cps()` pattern method or `ctrl.set_cps()`
- `.piano()` / `.pianoroll()` — visualization methods, not sounds. Use `.s("piano")` with loaded piano samples.
- Calling `.play()` twice in one track — creates duplicate scheduler entries

### Pattern Cookbook

**Instant complexity with `.off()`:**
```
n("0 [4 3] 2 [~ 1]").scale("C5:minor:pentatonic")
  .off(1/8, x=>x.add(4).gain(.4))   // canon at 4th, offset 1/8
  .off(1/4, x=>x.add(7).gain(.3))   // canon at 5th, offset 1/4
  .s("triangle").room(.4).delay(.25)
```

**Acid bassline with filter envelope:**
```
note("[c2 c2 <eb2 c2> c2 [c2 g2] c2 <f2 eb2> c2]*2")
  .s("sawtooth").ftype('24db')
  .lpf(sine.range(200, 1500).slow(8))
  .lpenv(sine.range(1, 8).slow(16))
  .lpd(perlin.range(.05, .2))
  .lpa(.005)
  .lpq(sine.range(4, 14).slow(12))
  .shape(.35).gain(.35)
```

**Dub delay on percussion:**
```
s("~ rim ~ [~ rim]").bank("RolandTR707")
  .delay(.7).delaytime(.375).delayfeedback(.55)
  .room(.6).roomsize(4)
  .orbit(2)
```

**Layered hats with dynamics:**
```
s("hh*16").bank("RolandTR909")
  .gain(saw.range(.2,.8))
  .pan(sine.range(.3,.7).fast(3))
  .room(.1)
```

**Chopped breakbeat:**
```
s("clean:2").loopAt(2).chop(16)
  .every(4, x => x.fast(2))
  .sometimesBy(.15, x => x.speed(-1))
  .shape(.3).room(.15)
```

**Jazz voicings with auto voice-leading:**
```
chord("<Dm9 G13 C^9 A7b9>/2")
  .dict('ireal').voicing()
  .struct("[~ x] [x ~] [~ x] [~ [x ~]]")
  .s("square")
  .lpf(1200)
  .attack(.005).decay(.2).sustain(.08)
```

**Ambient pad with slow evolution:**
```
note("<[c3,eb3,g3,bb3] [ab2,c3,eb3,g3] [f3,ab3,c4] [g3,bb3,d4]>/8")
  .s("sawtooth")
  .attack(2).release(4)
  .lpf(sine.range(200, 900).slow(32))
  .room(.8).roomsize(8)
  .gain(.08)
```

**Superimpose for detuned thickness:**
```
note("c2 d2 eb2 f2")
  .s("sawtooth")
  .mul(note("0, 0.08"))    // slight detune for chorus
  .lpf(500).shape(.3)
```

### Full API Reference

See `docs/strudel-reference.md` for the complete function reference.
See `docs/strudel-examples.md` for genre-organized examples with explanations.
