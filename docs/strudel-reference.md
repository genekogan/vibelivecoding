# Strudel API Reference

Complete reference for writing Strudel code via the remote controller.
For the full interactive docs see https://strudel.cc/workshop/getting-started

---

## Core Concepts

### Cycles
Time is **cycle-based**: one cycle is ~2 seconds at default tempo. More events in a pattern = each event gets shorter. Patterns **tile infinitely** — no start/stop, just loops.

### Everything Is a Pattern
Notes, effects, speeds, gains, samples — all are patterns. They can be modulated, combined, and transformed with the same tools.

### Parallel Tracks
In our remote controller, each `.play()` call replaces the scheduler's single pattern. Multi-track playback is handled by the controller combining tracks into `stack()`.

---

## Mini-Notation

The core pattern language. Strings in quotes are parsed by the transpiler.

### Sequence & Structure

| Syntax | Name | Description | Example |
|--------|------|-------------|---------|
| `a b c` | Sequence | Events fill one cycle evenly | `"bd sd hh oh"` |
| `[a b]` | Group | Sub-sequence squeezed into parent slot | `"bd [hh hh] sd hh"` |
| `[[a b]]` | Nested group | Further subdivision | `"bd [[jazz sd]]"` |
| `<a b c>` | Alternate | One element per cycle, rotating | `"<bd cp>"` |
| `a,b` | Layer | Parallel patterns (polyphony) | `"bd*4, hh*8, ~ sd"` |

### Repetition & Speed

| Syntax | Name | Description | Example |
|--------|------|-------------|---------|
| `a*N` | Multiply | Repeat/speed up N times | `"hh*8"` |
| `[a b]/N` | Divide | Slow down over N cycles | `"[c e g b]/4"` |
| `a!N` | Replicate | Repeat N times, same duration each | `"c!3 eb"` |
| `a@N` | Elongate | Hold for N time units | `"c@3 eb"` (c is 3× longer) |

### Rests & Randomness

| Syntax | Name | Description | Example |
|--------|------|-------------|---------|
| `~` or `-` | Rest | Silence | `"bd ~ sd ~"` |
| `a?` | Degrade | 50% chance of silence | `"hh*8?"` |
| `a\|b` | Random choice | Pick one each cycle | `"bd \| cp"` |

### Sample & Rhythm

| Syntax | Name | Description | Example |
|--------|------|-------------|---------|
| `a:N` | Sample select | Choose sample number | `"hh:0 hh:1 hh:2"` |
| `a(k,n)` | Euclidean | Distribute k hits in n steps | `"bd(3,8)"` = tresillo |
| `a(k,n,r)` | Euclidean rotated | With rotation offset | `"cp(5,8,2)"` |
| `{a b c}%N` | Polymeter | Fit steps into N positions | `"{0 1 2 3 4}%8"` |

### Drum Sound Abbreviations

| Abbrev | Sound | Abbrev | Sound |
|--------|-------|--------|-------|
| `bd` | bass drum | `oh` | open hi-hat |
| `sd` | snare drum | `lt` | low tom |
| `rim` | rimshot | `mt` | middle tom |
| `hh` | closed hi-hat | `ht` | high tom |
| `cp` | clap | `rd` | ride cymbal |
| `cr` | crash cymbal | `cb` | cowbell |
| `sh` | shaker | `tb` | tambourine |

---

## Sound Selection

| Function | Description | Example |
|----------|-------------|---------|
| `s("x")` / `sound("x")` | Play sample or synth | `s("bd sd hh")` |
| `n("0 1 2")` | Select sample number or scale degree | `n("0 1 4 2").s("jazz")` |
| `note("x")` | Play pitched note (letter or MIDI) | `note("c3 e3 g3")` |
| `freq(hz)` | Set frequency directly | `freq(440)` |
| `bank("name")` | Switch drum machine bank | `s("bd sd").bank("RolandTR909")` |
| `samples(url)` | Load sample pack | `samples('github:yaxu/clean-breaks')` |
| `stack(a, b)` | Play patterns simultaneously | `stack(s("bd*4"), s("hh*8"))` |

### Note Names

Standard letter names with optional sharps/flats and octave:
- `c d e f g a b` — natural notes (default octave 3)
- `db eb gb ab bb` — flats
- `c# d# f# g# a#` — sharps
- `c2 e3 g4 b5` — with octave number

---

## Scales & Chords

| Function | Description | Example |
|----------|-------------|---------|
| `.scale("C:minor")` | Interpret `n()` as scale degrees | `n("0 2 4 6").scale("C:minor")` |
| `chord("Cm7")` | Chord symbol | `chord("<Cm7 Fm7 Gm7>")` |
| `.voicing()` | Auto voice-lead chords | `chord("Cm7").voicing()` |
| `.dict('ireal')` | Voicing dictionary | `chord("C^7").dict('ireal').voicing()` |
| `.mode("root:g2")` | Set voicing root | Used for basslines |
| `.transpose(n)` | Shift semitones | `.transpose("<0 5 -2>")` |
| `.scaleTranspose(n)` | Shift scale degrees | `.scaleTranspose(2)` |
| `.add(note(n))` | Add to note values | `.add(note(12))` = octave up |

### Common Scales

`major`, `minor`, `dorian`, `mixolydian`, `lydian`, `phrygian`, `minor:pentatonic`, `major:pentatonic`, `bebop`, `whole tone`, `melodic:minor`, `harmonic:minor`

### Chord Symbols

Standard jazz notation: `C^7` (major 7), `Cm7` (minor 7), `C7` (dominant 7), `Cm7b5` (half-dim), `Cdim7`, `C7b9`, `C7#9`, `C13`, `Csus4`

---

## Tempo

| Function | Description |
|----------|-------------|
| `.cps(n)` | Cycles per second (pattern method — **use this**) |
| `setcpm(n)` | Cycles per minute (global, works in REPL) |

**Note:** `setcps()` as a global is NOT available in our CDN bundle. Use `ctrl.set_cps()` from Python or `.cps()` as a pattern method.

---

## Audio Effects

### Filters

| Effect | Description | Range |
|--------|-------------|-------|
| `.lpf(freq)` / `.cutoff(freq)` | Low-pass filter cutoff | 20-20000 Hz |
| `.lpq(q)` / `.resonance(q)` | Low-pass resonance | 0-50 |
| `.hpf(freq)` | High-pass filter cutoff | 20-20000 Hz |
| `.bpf(freq)` | Band-pass filter | 20-20000 Hz |
| `.vowel("a e i o")` | Vowel formant filter | a, e, i, o, u |
| `.ftype("24db")` | Steeper filter slope | `"12db"` or `"24db"` |

### Filter Envelopes

| Effect | Description |
|--------|-------------|
| `.lpenv(depth)` | Filter envelope depth (positive = up, negative = down) |
| `.lpa(t)` / `.lpattack(t)` | Filter envelope attack time |
| `.lpd(t)` / `.lpdecay(t)` | Filter envelope decay time |
| `.lps(level)` / `.lpsustain(l)` | Filter envelope sustain level |
| `.lpr(t)` / `.lprelease(t)` | Filter envelope release time |

Same pattern for `hp*` (high-pass) and `bp*` (band-pass) filter envelopes.

### Dynamics & Amplitude Envelope

| Effect | Description | Range |
|--------|-------------|-------|
| `.gain(n)` | Volume (exponential) | 0-1+ |
| `.velocity(n)` | MIDI-style velocity (multiplied with gain) | 0-1 |
| `.attack(t)` | Fade-in time (seconds) | 0+ |
| `.decay(t)` | Fade to sustain time | 0+ |
| `.sustain(level)` | Hold level | 0-1 |
| `.release(t)` | Fade-out time | 0+ |
| `.adsr("a:d:s:r")` | Shorthand ADSR | `".01:.1:.5:.2"` |
| `.clip(n)` / `.legato(n)` | Note duration multiplier | 0-1+ |
| `.postgain(n)` | Gain after effects chain | 0+ |

### Space & Time

| Effect | Description | Range |
|--------|-------------|-------|
| `.room(n)` | Reverb send amount | 0-1+ |
| `.roomsize(n)` | Reverb room size | 0-10+ |
| `.roomfade(t)` | Reverb fade time | seconds |
| `.roomlp(freq)` | Reverb low-pass frequency | Hz |
| `.roomdim(freq)` | Reverb damping frequency | Hz |
| `.delay(n)` | Delay send amount | 0-1 |
| `.delaytime(t)` | Delay time | seconds or cycle fraction |
| `.delayfeedback(n)` | Delay feedback | 0-1 |
| `.delay("a:b:c")` | Shorthand: amount:time:feedback | `".5:.125:.6"` |
| `.pan(n)` | Stereo position | 0=left, 0.5=center, 1=right |
| `.orbit(n)` | Route to effects bus | integer (default: 1) |

**Important:** `room` and `delay` are **global per orbit**. Tracks on the same orbit share reverb/delay settings. Use different `.orbit(N)` values to separate.

### Distortion & Lo-Fi

| Effect | Description | Range |
|--------|-------------|-------|
| `.shape(n)` | Warm waveshape distortion | 0-1 |
| `.distort(n)` | Hard distortion | 0+ |
| `.crush(n)` | Bitcrusher | 1-16 (lower = harsher) |
| `.coarse(n)` | Sample rate reduction | 1+ (higher = more lo-fi) |

### Pitch

| Effect | Description |
|--------|-------------|
| `.speed(n)` | Playback speed (negative = reverse) |
| `.penv(n)` | Pitch envelope depth (semitones) |
| `.pdec(t)` | Pitch envelope decay |
| `.pcurve(n)` | Pitch envelope curve |
| `.detune(n)` | Detune in cents |

### Vibrato

| Effect | Description |
|--------|-------------|
| `.vib(freq)` / `.vibrato(freq)` | Vibrato frequency (Hz) |
| `.vibmod(depth)` / `.vmod(depth)` | Vibrato depth (semitones) |
| `.vib("freq:depth")` | Shorthand |

### FM Synthesis

| Effect | Description |
|--------|-------------|
| `.fm(depth)` | FM modulation depth (index) |
| `.fmh(ratio)` | FM harmonicity ratio |
| `.fmattack(t)` | FM envelope attack |
| `.fmdecay(t)` | FM envelope decay |
| `.fmsustain(level)` | FM envelope sustain |
| `.fmenv("lin"\|"exp")` | FM envelope type |

### Tremolo

| Effect | Description |
|--------|-------------|
| `.tremolosync(speed)` / `.tremsync(speed)` | Tremolo speed (cycle-synced) |
| `.tremolodepth(n)` | Tremolo intensity (0-1) |
| `.tremoloskew(n)` | Waveform skew (0-1) |
| `.tremolophase(n)` | Phase offset |
| `.tremoloshape(type)` | Waveform: sine, tri, square, saw, ramp |

### Phaser

| Effect | Description |
|--------|-------------|
| `.phaser(speed)` / `.ph(speed)` | Phaser speed |
| `.phaserdepth(n)` / `.phd(n)` | Phaser intensity (0-1) |
| `.phasercenter(freq)` / `.phc(freq)` | Center frequency (Hz) |
| `.phasersweep(range)` / `.phs(range)` | LFO sweep range |

### Sidechain / Ducking

| Effect | Description |
|--------|-------------|
| `.duckorbit(n)` / `.duck(n)` | Target orbit for ducking |
| `.duckattack(t)` / `.duckatt(t)` | Recovery time (seconds) |
| `.duckdepth(n)` | Modulation depth (0-1) |

### Other

| Effect | Description |
|--------|-------------|
| `.noise(n)` | Add noise to oscillator (0-1) |
| `.compressor("t:r:k:a:r")` | Dynamic compression |

---

## Pattern Modifiers

### Time

| Modifier | Description | Example |
|----------|-------------|---------|
| `.fast(n)` | Speed up pattern | `.fast(2)` |
| `.slow(n)` | Slow down pattern | `.slow(4)` |
| `.early(n)` | Shift earlier in cycle | `.early(0.25)` |
| `.late(n)` | Shift later in cycle | `.late(0.125)` |
| `.rev()` | Reverse event order | |
| `.palindrome()` | Play forward then backward | |
| `.iter(n)` | Rotate pattern each cycle | `.iter(4)` |
| `.ply(n)` | Repeat each event n times | `.ply("<1 2 3>")` |
| `.swing(amount)` | Swing feel | `.swing(0.1)` |
| `.hurry(n)` | Speed up sample AND pattern | `.hurry(2)` |

### Conditional & Random

| Modifier | Description | Example |
|----------|-------------|---------|
| `.every(n, fn)` | Apply fn every nth cycle | `.every(4, x=>x.fast(2))` |
| `.firstOf(n, fn)` | Apply fn on first of n cycles | `.firstOf(4, rev)` |
| `.lastOf(n, fn)` | Apply fn on last of n cycles | |
| `.sometimes(fn)` | 50% chance per event | `.sometimes(x=>x.crush(4))` |
| `.sometimesBy(p, fn)` | p probability per event | `.sometimesBy(.3, fn)` |
| `.often(fn)` | 75% chance | |
| `.rarely(fn)` | 25% chance | |
| `.degradeBy(p)` | Remove p fraction of events | `.degradeBy(.3)` |
| `.when(pat, fn)` | Apply fn where pattern is 1 | `.when("<0 1>", fast(2))` |
| `.chunk(n, fn)` | Apply fn to 1/n, rotating | `.chunk(4, fast(2))` |
| `.mask(pat)` | Mute where pattern is 0 | `.mask("<0 1 1 1>")` |

### Layering & Accumulation

| Modifier | Description | Example |
|----------|-------------|---------|
| `.superimpose(fn)` | Stack original + modified | `.superimpose(x=>x.add(note(12)))` |
| `.off(time, fn)` | Superimpose with time offset | `.off(1/8, x=>x.add(note(7)))` |
| `.jux(fn)` | Split L/R, apply fn to right | `.jux(rev)` |
| `.juxBy(n, fn)` | jux with partial spread | `.juxBy(.5, rev)` |
| `.layer(fn1, fn2)` | Stack transformations | `.layer(x=>x.s("piano"), x=>x.s("bass"))` |
| `.add(pat)` | Add values (notes, numbers) | `.add(note("<0 7 12>"))` |
| `.struct(pat)` | Impose rhythmic structure | `.struct("x(3,8)")` |
| `.echo(n, time, fb)` | Pattern-level echo | `.echo(3, 1/8, .5)` |
| `.reset(pat)` | Reset pattern phase | `.reset("<x@7 x(5,8,-1)>")` |

### Sample Manipulation

| Modifier | Description | Example |
|----------|-------------|---------|
| `.chop(n)` | Chop sample into n pieces | `.chop(8)` |
| `.splice(n, pat)` | Chop + rearrange with pattern | `.splice(8, "0 1 2 3 4 5 6 7")` |
| `.slice(n, pat)` | Slice into n, select by pattern | `.slice(8, "0 3 5 7")` |
| `.striate(n)` | Progressive slice playback | `.striate(6)` |
| `.loopAt(n)` | Time-stretch to n cycles | `.loopAt(4)` |
| `.fit()` | Fit sample to event duration | |
| `.begin(n)` | Start point (0-1) | `.begin(.25)` |
| `.end(n)` | End point (0-1) | `.end(.75)` |
| `.cut(n)` | Choke group (new cuts old) | `.cut(1)` |
| `.scrub(pos)` | Tape-loop scrubbing | `.scrub("{0 .25 .5 .75}%8")` |

---

## Signals (Continuous Values)

Use as arguments to any effect for smooth automation.

| Signal | Shape | Range |
|--------|-------|-------|
| `sine` | Smooth wave | 0 to 1 |
| `cosine` | Cosine wave | 0 to 1 |
| `saw` | Ramp up | 0 to 1 |
| `tri` | Triangle | 0 to 1 |
| `square` | On/off | 0 or 1 |
| `rand` | Random per event | 0 to 1 |
| `perlin` | Smooth random (noise) | 0 to 1 |
| `irand(n)` | Random integer | 0 to n-1 |

### Signal Modifiers

| Modifier | Description | Example |
|----------|-------------|---------|
| `.range(lo, hi)` | Set output range | `sine.range(200, 4000)` |
| `.slow(n)` | Slow the signal down | `sine.range(200, 4000).slow(8)` |
| `.fast(n)` | Speed the signal up | `sine.fast(3)` |
| `.segment(n)` | Sample-and-hold at n steps | `sine.segment(8)` |
| `.mul(n)` | Multiply signal | `sine.mul(4)` |
| `.add(n)` | Add to signal | `sine.add(0.5)` |

### Common Signal Patterns

```js
// Filter sweep over 8 cycles
.lpf(sine.range(200, 4000).slow(8))

// Ramping dynamics on hats
.gain(saw.range(.15, .6))

// Gentle stereo movement
.pan(sine.range(.3, .7).fast(3))

// Smooth random filter
.cutoff(perlin.range(300, 3000).slow(8))

// Random pitch variation
.add(perlin.range(0, .5))
```

---

## Synth Waveforms

Set via `.s()` or `.sound()`:

| Waveform | Character |
|----------|-----------|
| `sawtooth` | Bright, buzzy (classic synth bass/lead) |
| `square` | Hollow, woody |
| `triangle` | Soft, muted (default for `note()`) |
| `sine` | Pure tone |
| `supersaw` | Detuned sawtooth (big pad sound) |
| `white` | White noise |
| `pink` | Pink noise |
| `brown` | Brown noise |
| `crackle` | Subtle crackling |

### Additive Synthesis

| Function | Description |
|----------|-------------|
| `.partials([1, 1, 0.5])` | Harmonic magnitudes |
| `.phases(randL(200))` | Harmonic phase offsets |

### Wavetable Synthesis

Use `wt_*` prefix for AKWF wavetables (1000+ available). Auto-loop enabled. Scan via `.loopBegin()` / `.loopEnd()`.

---

## Drum Machines

Use with `.bank()`:

| Bank | Style |
|------|-------|
| `RolandTR808` | Hip-hop, trap, electro |
| `RolandTR909` | House, techno |
| `RolandTR707` | Pop, new wave |
| `RolandTR505` | Lo-fi, indie |
| `AkaiLinn` | Prince, electrofunk |
| `RhythmAce` | Vintage analog |
| `ViscoSpaceDrum` | Spacey electronic |
| `RolandCompurhythm1000` | Early digital |
| `CasioRZ1` | 80s digital |

---

## Sample Loading

### GitHub Shortcut
```js
samples('github:user/repo')           // main branch, strudel.json at root
samples('github:user/repo/branch')    // specific branch
```

### CDN URLs
```js
samples('https://strudel.b-cdn.net/tidal-drum-machines.json',
        'https://strudel.b-cdn.net/tidal-drum-machines/machines/')
samples('https://strudel.b-cdn.net/piano.json',
        'https://strudel.b-cdn.net/piano/')
samples('https://strudel.b-cdn.net/vcsl.json',
        'https://strudel.b-cdn.net/VCSL/')
```

### Inline Definition
```js
samples({
  bass: 'https://cdn.freesound.org/previews/614/614637_2434927-hq.mp3',
  bell: { c6: 'https://cdn.freesound.org/previews/411/411089_5121236-lq.mp3' }
})
```

### Known Packs
- `github:yaxu/clean-breaks` — breakbeat loops
- `github:tidalcycles/dirt-samples` — classic Dirt samples
- `github:felixroos/samples` — Felix Roos collection

---

## Audio Signal Flow

1. Sound generation (oscillator or sample)
2. Sound shaping (filter, envelope)
3. Effects (distortion, phaser, tremolo)
4. Output split → dry + delay bus + reverb bus
5. Orbit mixing (shared delay/reverb per orbit)
6. Final output

**Constraint:** You cannot chain the same effect type twice. The second call overrides the first: `.lpf(100).lpf(800)` → only 800 Hz applies.

---

## Multi-Pattern Syntax (REPL only)

```js
$: pattern1      // active pattern
_$: pattern2     // muted pattern
```

In the remote controller, use `ctrl.set_track()` instead.
