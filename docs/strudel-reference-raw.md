# Strudel Live-Coding Complete Reference

Compiled from official Strudel documentation (strudel.cc).
Sources: workshop/first-sounds, workshop/first-notes, workshop/first-effects, workshop/pattern-effects, learn/samples, learn/synths, learn/effects.

---

## Table of Contents

1. [First Sounds](#1-first-sounds)
2. [First Notes](#2-first-notes)
3. [First Effects](#3-first-effects)
4. [Pattern Effects](#4-pattern-effects)
5. [Samples](#5-samples)
6. [Synths](#6-synths)
7. [Effects Reference](#7-effects-reference)

---

## 1. First Sounds

Source: https://strudel.cc/workshop/first-sounds

### sound() / s()

Plays sounds by name. `s()` is a shorthand alias for `sound()`.

```js
sound("casio")
```

```js
sound("casio:1")
```

```js
sound("bd hh sd oh")
```

```js
sound("bd hh - rim - bd hh rim")
```

```js
sound("bd [hh hh] sd [hh bd] bd - [hh sd] cp")
```

```js
sound("hh hh hh, bd casio")
```

```js
sound(`bd*2, - cp,
- - - oh, hh*4,
[- casio]*2`)
```

```js
s(`jazz*2,
insect [crow metal] - -,
- space:4 - space:1,
- wind`)
```

### bank()

Changes the drum machine / sound bank used for playback.

```js
sound("bd hh sd oh").bank("RolandTR909")
```

Available banks include: AkaiLinn, RhythmAce, RolandTR808, RolandTR707, RolandTR909, RolandTR505, ViscoSpaceDrum, CasioRZ1.

### setcpm()

Sets tempo in cycles per minute. Default cycle duration is 2 seconds.

```js
setcpm(90/4)
```

```js
setcpm(100/4)
```

```js
setcpm(45)
```

### n()

Selects sample numbers (zero-based indexing).

```js
n("0 1 [4 2] 3*2").sound("jazz")
```

### Mini-Notation Syntax

| Concept | Syntax | Example |
|---------|--------|---------|
| Sequence | space | `sound("bd bd sd hh")` |
| Sample Number | :x | `sound("hh:0 hh:1")` |
| Rests | - or ~ | `sound("metal - jazz")` |
| Alternate | <> | `sound("<bd hh rim oh>")` |
| Sub-Sequences | [] | `sound("bd [metal jazz]")` |
| Sub-Sub-Sequences | [[]] | `sound("bd [[jazz sd]]")` |
| Speed up (repeat) | * | `sound("bd sd*2 cp*3")` |
| Parallel (layers) | , | `sound("bd*2, hh*2")` |

### Drum Sound Abbreviations

| Abbreviation | Meaning |
|---|---|
| bd | bass drum |
| sd | snare drum |
| rim | rimshot |
| hh | hi-hat (closed) |
| oh | open hi-hat |
| cp | clap |
| lt | low tom |
| mt | middle tom |
| ht | high tom |
| rd | ride cymbal |
| cr | crash cymbal |

### Key Concepts

**Cycles**: The default duration is 2 seconds. One cycle squishes all sequence content into that duration, regardless of how many events are in it.

**Angle brackets `<...>`**: Plays one element per cycle, cycling through the list.

```js
sound("<bd bd hh bd rim bd hh bd>*8")
```

```js
sound("bd hh*2 rim hh*3")
```

```js
sound("bd [hh rim]*2")
```

```js
sound("hh hh hh*16")
```

**Multi-line sequences** use backticks (template literals) for readability.

### Example Patterns

Rock beat:
```js
setcpm(100/4)
sound("[bd sd]*2, hh*8").bank("RolandTR505")
```

House pattern:
```js
sound("bd*4, [- cp]*2, [- hh]*4").bank("RolandTR909")
```

---

## 2. First Notes

Source: https://strudel.cc/workshop/first-notes

### note()

Sets pitch using MIDI numbers or letter names.

**With MIDI numbers:**
```js
note("48 52 55 59").sound("piano")
```

**With letter names:**
```js
note("c e g b").sound("piano")
```

**Flats and sharps:**
```js
note("db eb gb ab bb").sound("piano")
```

```js
note("c# d# f# g# a#").sound("piano")
```

**Octave specification:**
```js
note("c2 e3 g4 b5").sound("piano")
```

### Changing the Sound

```js
note("36 43, 52 59 62 64").sound("piano")
```

Available sounds include: gm_electric_guitar_muted, gm_acoustic_bass, gm_voice_oohs, gm_blown_bottle, sawtooth, square, triangle, bd, sd, hh.

**Switch between sounds (alternating per event):**
```js
note("48 67 63 [62, 58]")
.sound("piano gm_electric_guitar_muted")
```

**Stack multiple sounds (layered):**
```js
note("48 67 63 [62, 58]")
.sound("piano, gm_electric_guitar_muted")
```

### Longer Sequences

**Slow down with `/`:**
```js
note("[36 34 41 39]/4").sound("gm_acoustic_bass")
```

The `/4` plays the sequence in brackets over 4 cycles (= 8 seconds at default tempo).

**Play one per cycle with angle brackets:**
```js
note("<36 34 41 39>").sound("gm_acoustic_bass")
```

Angle brackets are a shortcut: `<a b c>` is equivalent to `[a b c]/3`.

**Play one sequence per cycle:**
```js
note("<[36 48]*4 [34 46]*4 [41 53]*4 [39 51]*4>")
.sound("gm_acoustic_bass")
```

**Alternate between multiple things:**
```js
note("60 <63 62 65 63>")
.sound("gm_xylophone")
```

```js
sound("bd*4, [~ <sd cp>]*2, [~ hh]*4")
.bank("RolandTR909")
```

### scale()

Interprets `n()` values as scale degrees rather than raw MIDI numbers.

```js
setcpm(60)
n("0 2 4 <[6,8] [7,9]>")
.scale("C:minor").sound("piano")
```

Available scales: C:major, A2:minor, D:dorian, G:mixolydian, A2:minor:pentatonic, F:major:pentatonic, and many more.

**Automate scale changes:**
```js
setcpm(60)
n("<0 -3>, 2 4 <[6,8] [7,9]>")
.scale("<C:major D:mixolydian>/4")
.sound("piano")
```

### Elongate with `@`

```js
note("c@3 eb").sound("gm_acoustic_bass")
```

Not using `@` is like using `@1`. In the above example, c is 3 units long and eb is 1 unit long.

```js
setcpm(60)
n("<[4@2 4] [5@2 5] [6@2 6] [5@2 5]>*2")
.scale("<C2:mixolydian F2:mixolydian>/4")
.sound("gm_acoustic_bass")
```

This groove is called a "shuffle". Each beat has two notes, where the first is twice as long as the second.

### Replicate with `!`

```js
setcpm(60)
note("c!2 [eb,<g a bb a>]").sound("piano")
```

### Mini-Notation Recap (Notes additions)

| Concept | Syntax | Example |
|---------|--------|---------|
| Slow down | / | `note("[c a f e]/2")` |
| Alternate | <> | `note("c a f <e g>")` |
| Elongate | @ | `note("c@3 e")` |
| Replicate | ! | `note("c!3 e")` |

### Complete Song Example

**Classy Bassline:**
```js
note("<[c2 c3]*4 [bb1 bb2]*4 [f2 f3]*4 [eb2 eb3]*4>")
.sound("gm_synth_bass_1")
.lpf(800)
```

**Classy Melody:**
```js
n(`<
[~ 0] 2 [0 2] [~ 2]
[~ 0] 1 [0 1] [~ 1]
[~ 0] 3 [0 3] [~ 3]
[~ 0] 2 [0 2] [~ 2]
>*4`).scale("C4:minor")
.sound("gm_synth_strings_1")
```

**Classy Drums:**
```js
sound("bd*4, [~ <sd cp>]*2, [~ hh]*4")
.bank("RolandTR909")
```

### Playing Multiple Patterns with `$:`

```js
$: note("<[c2 c3]*4 [bb1 bb2]*4 [f2 f3]*4 [eb2 eb3]*4>")
.sound("gm_synth_bass_1").lpf(800)

$: n(`<
[~ 0] 2 [0 2] [~ 2]
[~ 0] 1 [0 1] [~ 1]
[~ 0] 3 [0 3] [~ 3]
[~ 0] 2 [0 2] [~ 2]
>*4`).scale("C4:minor")
.sound("gm_synth_strings_1")

$: sound("bd*4, [~ <sd cp>]*2, [~ hh]*4")
.bank("RolandTR909")
```

Tip: Try changing `$` to `_$` to mute a part!

---

## 3. First Effects

Source: https://strudel.cc/workshop/first-effects

### lpf() - Low Pass Filter

"lpf = **l**ow **p**ass **f**ilter" -- removes frequencies above the cutoff.

- Lower values = muffled sound
- Higher values = brighter sound

```js
.lpf(800)
```

```js
.lpf(200)
```

```js
.lpf(5000)
```

```js
.lpf("200 1000 200 1000")
```

### vowel()

Filters the sound with vowel-like formant qualities.

```js
.vowel("<a e i o>")
```

### gain()

Controls volume/dynamics.

```js
.gain(".25 1")
```

"Rhythm is all about dynamics!"

### ADSR Envelope

Controls the amplitude shape of each sound event.

- **attack** -- time to reach full volume
- **decay** -- time to fall from peak to sustain level
- **sustain** -- held volume level (0-1)
- **release** -- time to fade out after note ends

```js
.attack(.1).decay(.1).sustain(.25).release(.2)
```

Short notation:
```js
.adsr(".1:.1:.5:.2")
```

### delay()

Adds echo/delay effect.

```js
.delay(.5)
```

```js
.delay(".8:.125")
```

```js
.delay(".8:.06:.8")
```

The parameters in colon-separated format are: send level, delay time, feedback.

### room()

Adds reverb (spatial room simulation).

```js
.room(2)
```

Accepts numeric values for different reverb sizes.

### pan()

Stereo positioning. 0 = left, 1 = right, 0.5 = center.

```js
.pan("0 0.3 .6 1")
```

### speed()

Changes sample playback speed (cheap pitch shifting). Negative values reverse playback.

```js
.speed("<1 2 -1 -2>")
```

### Continuous Modulation with Signals

Available signal waveforms: `sine`, `saw`, `square`, `tri`, `rand`, `perlin`.

**Setting range:**
```js
.lpf(saw.range(500, 2000))
```

**Controlling signal speed:**
```js
.slow(4)
```

```js
.fast()
```

### Tempo Modifiers

```js
.slow(2)    // halves pattern speed
.fast(2)    // doubles pattern speed
```

In mini-notation: `*` speeds up, `/` slows down.

---

## 4. Pattern Effects

Source: https://strudel.cc/workshop/pattern-effects

### rev() - Reverse

Reverses the order of events in the pattern.

```js
n("0 1 [4 3] 2 0 2 [~ 3] 4").sound("jazz").rev()
```

### jux() - Juxtapose

Splits the pattern into left and right stereo channels. The original plays on the left, and a modified version plays on the right.

```js
n("0 1 [4 3] 2 0 2 [~ 3] 4").sound("jazz").jux(rev)
```

This is equivalent to:
```js
$: n("0 1 [4 3] 2 0 2 [~ 3] 4").sound("jazz").pan(0)
$: n("0 1 [4 3] 2 0 2 [~ 3] 4").sound("jazz").pan(1).rev()
```

### slow() with Multiple Speeds

Creates polyrhythmic effects by applying different playback speeds simultaneously.

```js
note("c2, eb3 g3 [bb3 c4]").sound("piano").slow("0.5,1,1.5")
```

### add()

Adds numbers to note values (transposition).

```js
note("c2 [eb3,g3]".add("<0 <1 -1>>"))
```

Can chain multiple additions:
```js
note("c2 [eb3,g3]".add("<0 <1 -1>>").add("0,7"))
```

### ply()

Multiplies/repeats each event n times within its time slot.

```js
sound("hh hh, bd rim [~ cp] rim").bank("RolandTR707").ply(2)
```

Equivalent to:
```js
sound("hh*2 hh*2, bd*2 rim*2 [~ cp*2] rim*2")
```

### off()

Copies the pattern, offsets it in time, and applies a transformation to the copy. Creates canons, echoes, and layered textures.

Parameters: time offset (fraction of cycle), transformation function.

```js
n("0 [4 <3 2>] <2 3> [~ 1]".off(1/16, x=>x.add(4)))
```

Nested off example:
```js
s("bd sd [rim bd] sd,[~ hh]*4").bank("CasioRZ1")
.off(2/16, x=>x.speed(1.5).gain(.25)
.off(3/16, y=>y.vowel("<a e i o>*8")))
```

### Pattern Effects Reference Table

| Name | Description | Example |
|------|-------------|---------|
| rev | reverse | `n("0 2 4 6 ~ 7 9 5").scale("C:minor").rev()` |
| jux | split left/right, modify right | `n("0 2 4 6 ~ 7 9 5").scale("C:minor").jux(rev)` |
| add | add numbers/notes | `n("0 2 4 6 ~ 7 9 5".add("<0 1 2 1>")).scale("C:minor")` |
| ply | speed up each event n times | `s("bd sd [~ bd] sd").ply("<1 2 3>")` |
| off | copy, shift time & modify | `s("bd sd [~ bd] sd, hh*8").off(1/16, x=>x.speed(2))` |

---

## 5. Samples

Source: https://strudel.cc/learn/samples

### Default Samples

Strudel includes built-in drum machines via the tidal-drum-machines library.

**Drum sounds:**

| Abbreviation | Sound |
|---|---|
| bd | bass/kick drum |
| sd | snare drum |
| rim | rimshot |
| cp | clap |
| hh | closed hi-hat |
| oh | open hi-hat |
| cr | crash |
| rd | ride |
| ht | high tom |
| mt | medium tom |
| lt | low tom |

**Percussion:**

| Abbreviation | Sound |
|---|---|
| sh | shakers/maracas/cabasas |
| cb | cowbell |
| tb | tambourine |
| perc | other percussion |
| misc | miscellaneous samples |
| fx | effects |

Instrument samples from VCSL also load by default. View available samples in the REPL "sounds" tab.

### Sound Aliases

Create custom short names for sounds:

```js
soundAlias('RolandTR808_bd', 'kick')
```

### Sound Banks with bank()

Shortens lengthy drum machine prefixes:

```js
// Without bank:
s("RolandTR808_bd RolandTR808_sd,RolandTR808_hh*16")

// With bank:
s("bd sd,hh*16").bank("RolandTR808")
```

The bank function prepends the bank name with an underscore to the sample name.

**Pattern banks dynamically:**
```js
s("bd sd,hh*16").bank("<RolandTR808 RolandTR909>")
```

### Selecting Sounds with n()

Zero-based indexing to choose specific samples:

```js
s("hh*8").bank("RolandTR909").n("0 1 2 3")
```

Colon syntax in mini-notation:

```js
s("bd*4,hh:0 hh:1 hh:2 hh:3 hh:4 hh:5 hh:6 hh:7")
.bank("RolandTR909")
```

Numbers exceeding available samples wrap around.

### Loading Custom Samples

#### From File URLs

```js
samples({
  bassdrum: 'bd/BT0AADA.wav',
  hihat: 'hh27/000_hh27closedhh.wav',
  snaredrum: ['sd/rytm-01-classic.wav', 'sd/rytm-00-hard.wav'],
}, 'https://raw.githubusercontent.com/tidalcycles/Dirt-Samples/master/');

s("bassdrum snaredrum:0 bassdrum snaredrum:1, hihat*16")
```

Support both single files and arrays of files.

#### From strudel.json

```js
samples('https://raw.githubusercontent.com/tidalcycles/Dirt-Samples/master/strudel.json')
s("bd sd bd sd,hh*16")
```

JSON format with optional `_base` key:

```json
{
  "_base": "https://raw.githubusercontent.com/tidalcycles/Dirt-Samples/master/",
  "bassdrum": "bd/BT0AADA.wav",
  "snaredrum": "sd/rytm-01-classic.wav",
  "hihat": "hh27/000_hh27closedhh.wav"
}
```

**Caching tip:** Browsers cache aggressively. Force refresh by appending version parameters: `?version=2`

#### Generate strudel.json

```bash
npx --yes @strudel/sampler --json > strudel.json
```

#### GitHub Shortcut

```js
samples('github:tidalcycles/dirt-samples')
s("bd sd bd sd,hh*16")
```

Format: `samples('github:<user>/<repo>/<branch>')`. Defaults to `main` branch and assumes `strudel.json` at repository root.

#### Local Disk - Import Folder

Access "import sounds folder" button in REPL sounds tab. Select folder structure (subfolders supported). Example structure:

```
samples
+-- swoop
|   +-- swoopshort.wav
|   +-- swooplong.wav
|   +-- swooptight.wav
+-- smash
    +-- smashhigh.wav
    +-- smashlow.wav
    +-- smashmiddle.wav
```

Available as: `swoop` (3 samples) and `smash` (3 samples) with zero-based alphabetical indexing.

#### Local Disk - @strudel/sampler Server

```bash
cd samples
npx @strudel/sampler
```

Load via:
```js
samples('http://localhost:5432/')
```

Auto-generates `strudel.json` based on folder structure. Requires NodeJS.

#### Specifying Pitch for Samples

Single pitch:
```js
samples({
  'gtr': 'gtr/0001_cleanC.wav',
  'moog': { 'g3': 'moog/005_Mighty%20Moog%20G3.wav' },
}, 'github:tidalcycles/dirt-samples');

note("g3 [bb3 c4] <g4 f4 eb4 f3>@2").s("gtr,moog").clip(1).gain(.5)
```

Multiple pitch regions (multi-sampled instrument):
```js
setcpm(60)
samples({
  'moog': {
    'g2': 'moog/004_Mighty%20Moog%20G2.wav',
    'g3': 'moog/005_Mighty%20Moog%20G3.wav',
    'g4': 'moog/006_Mighty%20Moog%20G4.wav',
  }
}, 'github:tidalcycles/dirt-samples')

note("g2!2 <bb2 c3>!2, <c4@3 [<eb4 bb3> g4 f4]>")
.s('moog').clip(1).gain(.5)
```

The sampler picks the closest matching sample for the current note.

#### Shabda Tool

```js
samples('shabda:bass:4,hihat:4,rimshot:2')

$: n("0 1 2 3 0 1 2 3").s('bass')
$: n("0 1*2 2 3*2").s('hihat').clip(1)
$: n("~ 0 ~ 1 ~ 0 0 1").s('rimshot')
```

Generate voice/speech samples:
```js
samples('shabda/speech:the_drum,forever')
samples('shabda/speech/fr-FR/m:magnifique')

$: s("the_drum*2").chop(16).speed(rand.range(0.85,1.1))
$: s("forever magnifique").slow(4).late(0.125)
```

### Sampler Effects (Sample Playback Control)

#### begin

Skips the beginning of a sample. Range: 0-1.

```js
samples({ rave: 'rave/AREUREADY.wav' }, 'github:tidalcycles/dirt-samples')
s("rave").begin("<0 .25 .5 .75>").fast(2)
```

#### end

Cuts the sample at a given point. Range: 0-1.

```js
s("bd*2,oh*4").end("<.1 .2 .5 1>").fast(2)
```

#### loop

Loops the sample (not synced to cycle tempo). Parameter: on/off (1 = loop).

```js
s("casio").loop(1)
```

#### loopBegin / loopb

Sets the loop start point between begin and end. Range: 0-1. Note: `wt_` samples auto-loop.

```js
s("space").loop(1)
.loopBegin("<0 .125 .25>")._scope()
```

#### loopEnd / loope

Sets the loop end point between begin and end, after loopBegin. Range: 0-1.

```js
s("space").loop(1)
.loopEnd("<1 .75 .5 .25>")._scope()
```

#### cut

Drum-machine style choke groups: stops a playing sample when another with the same cut group number plays.

```js
s("[oh hh]*4").cut(1)
```

#### clip / legato

Multiplies event duration; cuts samples exceeding that duration. Parameter: factor (>= 0).

```js
note("c a f e").s("piano").clip("<.5 1 2>")
```

#### loopAt

Fits sample to given number of cycles by adjusting speed.

```js
samples({ rhodes: 'https://cdn.freesound.org/previews/132/132051_316502-lq.mp3' })
s("rhodes").loopAt(2)
```

#### fit

Fits sample to event duration. Good for rhythmical loops.

```js
samples({ rhodes: 'https://cdn.freesound.org/previews/132/132051_316502-lq.mp3' })
s("rhodes/2").fit()
```

#### chop

Cuts sample into n parts for granular-style playback.

```js
samples({ rhodes: 'https://cdn.freesound.org/previews/132/132051_316502-lq.mp3' })
s("rhodes")
 .chop(4)
 .rev()
 .loopAt(2)
```

#### striate

Cuts sample into n parts, triggering progressive portions per loop.

```js
s("numbers:0 numbers:1 numbers:2").striate(6).slow(3)
```

#### slice

Chops samples into numbered slices, triggered by a pattern of slice indices.

```js
samples('github:tidalcycles/dirt-samples')
s("breaks165").slice(8, "0 1 <2 2*2> 3 [4 0] 5 6 7".every(3, rev)).slow(0.75)
```

With fractional slice points:
```js
samples('github:tidalcycles/dirt-samples')
s("breaks125").fit().slice([0,.25,.5,.75], "0 1 1 <2 3>")
```

#### splice

Like slice but adjusts playback speed per slice to match step duration.

```js
samples('github:tidalcycles/dirt-samples')
s("breaks165")
.splice(8, "0 1 [2 3 0]@2 3 0@2 7")
```

#### scrub

Scrubs audio file like a tape loop. Position syntax: "position:speed".

```js
samples('github:switchangel/pad')
s("swpad:0").scrub("{0.1!2 .25@3 0.7!2 <0.8:1.5>}%8")
```

```js
samples('github:yaxu/clean-breaks/main');
s("amen/4").fit().scrub("{0@3 0@2 4@3}%8".div(16))
```

#### speed

Changes sample playback speed. Negative values reverse playback.

```js
s("bd*6").speed("1 2 4 1 -2 -4")
```

```js
speed("1 1.5*2 [2 1.1]").s("piano").clip(1)
```

### Important Notes on Samples

- **Lazy loading**: Sample maps load initially, but audio files load only when played. The first trigger may have latency.
- **Caching**: Browsers cache strudel.json on first load.
- **Sample ordering**: Within folders, samples use zero-based alphabetical indexing.
- **Bank prepending**: The bank function adds an underscore: `bankname_samplename`.
- **Default override**: Custom samples can override default sounds.

---

## 6. Synths

Source: https://strudel.cc/learn/synths

### Basic Waveforms

Four fundamental oscillator types, selectable via `sound()` or `s()`:

- `sine` -- pure sine wave
- `sawtooth` -- sawtooth wave (harmonically rich)
- `square` -- square wave (hollow/woody)
- `triangle` -- triangle wave (softer than sawtooth)

The default waveform for note patterns (when no sound is specified) is `triangle`.

### Noise Types

Three noise varieties (ordered from harsh to soft):

- `white` -- white noise
- `pink` -- pink noise
- `brown` -- brown noise

Additionally:
- `crackle` -- subtle crackling noise, with density control via the `density` parameter

The `noise` parameter adds noise to any oscillator:
```js
.noise(0.1)
.noise(0.25)
.noise(0.5)
```

### Additive Synthesis

#### partials

Controls harmonic magnitudes relative to the fundamental frequency. Accepts arrays.

```js
.partials([1, 1, "<1 0>", "<1 0>"])
```

Can be generated algorithmically. Compatible with pattern functions like `randL`, `binaryL`, and lists of patterns.

#### phases

Determines where in each cycle harmonic sine waves start.

```js
.phases(randL(200))
```

### Vibrato

#### vib / vibrato / v

Vibrato frequency in hertz.

```js
.vib("<.5 1 2 4 8 16>")
```

Can specify modulation depth with colon syntax:
```js
.vib("<.5 1 2 4 8 16>:12")
```

#### vibmod / vmod

Vibrato depth in semitones.

```js
.vibmod("<.25 .5 1 2 12>")
```

Frequency adjustable via colon:
```js
.vibmod("<.25 .5 1 2 12>:8")
```

### FM Synthesis

#### fm / fmi

Controls modulation index (determines brightness/complexity).

```js
.fm("<0 1 2 8 32>")
```

#### fmh

Harmonicity ratio affecting timbre.
- Whole numbers and simple ratios sound natural/harmonic
- Complex/irrational ratios sound metallic/inharmonic

```js
.fmh("<1 2 1.5 1.61>")
```

#### fmattack

Attack time for the FM modulation envelope.

```js
.fmattack("<0 .05 .1 .2>")
```

#### fmdecay

Decay time until sustain level.

```js
.fmdecay("<.01 .05 .1 .2>")
```

#### fmsustain

Sustain level after decay.

```js
.fmsustain("<1 .75 .5 0>")
```

#### fmenv

Envelope ramp type: `lin` (linear) or `exp` (exponential).

```js
.fmenv("<exp lin>")
```

### Wavetable Synthesis

Custom waveforms loaded with `wt_` prefix. Over 1000 waveforms available from the AKWF library. Loop behavior defaults to 1 (looping on). Scanning through the wavetable is accomplished via `loopBegin` and `loopEnd`.

### ZZFX Synth

Integrated "Zuper Zmall Zound Zynth" with 20 parameters.

**Envelope parameters:**
- `.attack()` -- attack time
- `.decay()` -- decay time
- `.sustain()` -- sustain level
- `.release()` -- release time

**Special ZZFX parameters:**
- `.curve()` -- envelope curve
- `.slide()` -- pitch slide
- `.noise()` -- noise amount
- `.zmod()` -- modulation
- `.zcrush()` -- bit crush
- `.zdelay()` -- delay
- `.pitchJump()` -- pitch jump amount
- `.pitchJumpTime()` -- pitch jump timing
- `.lfo()` -- low-frequency oscillator
- `.tremolo()` -- tremolo effect
- `.deltaSlide()` -- pitch slide delta
- `.zrand()` -- randomization

**ZZFX waveforms:**
- `z_sawtooth`
- `z_tan`
- `z_noise`
- `z_sine`
- `z_square`

---

## 7. Effects Reference

Source: https://strudel.cc/learn/effects

### Audio Signal Flow

The signal chain processes events in this order:
1. Sound generation
2. Sound production
3. Effects application
4. Output splitting (dry / delay / reverb)
5. Orbit mixing
6. Final output

**Important constraint**: Multiple occurrences of single-use effects simply override values. You cannot chain the same effect type twice (e.g., `lpf(100).distort(2).lpf(800)` -- the second lpf overrides the first).

Continuous parameter changes require either ADSR envelopes, LFO modulation parameters (tremolo, phaser, vibrato), or multiple sound-generating events via `seg()`.

### Filters

Three filter types, each accepting frequency (0-20000 Hz) and optional Q-factor/resonance (0-50).

#### Low-Pass Filter

Aliases: `lpf`, `cutoff`, `ctf`, `lp`

Removes frequencies above the cutoff point.

#### High-Pass Filter

Aliases: `hpf`, `hp`, `hcutoff`

Removes frequencies below the cutoff point.

#### Band-Pass Filter

Aliases: `bpf`, `bandf`, `bp`

Isolates a frequency band around the center point.

#### Filter Type

`ftype` -- selects filter implementation:
- 0 = 12dB filter
- 1 = ladder filter
- 2 = 24dB filter

#### Filter Envelopes

Separate ADSR envelopes for each filter type:
- Low-pass: `lpa`, `lpd`, `lps`, `lpr`, `lpenv`
- High-pass: `hpa`, `hpd`, `hps`, `hpr`, `hpenv`
- Band-pass: `bpa`, `bpd`, `bps`, `bpr`, `bpenv`

### Amplitude Control

#### gain

Exponential volume control.

#### velocity

Sets a 0-1 level, multiplied with gain.

#### compressor

Dynamic range compression.

Format: `threshold:ratio:knee:attack:release`

#### postgain

Post-effects volume boost.

### Amplitude Envelope (ADSR)

- `attack` -- time to reach full volume
- `decay` -- time from peak to sustain level
- `sustain` -- held volume level (0-1)
- `release` -- time to fade out after note ends
- `adsr` -- shorthand for all four (colon-separated)

### Pitch Envelope

- `pattack` -- pitch attack time
- `pdecay` -- pitch decay time
- `prelease` -- pitch release time
- `penv` -- pitch envelope depth
- `pcurve` -- pitch envelope curve shape
- `panchor` -- pitch anchor point

### Distortion and Waveshaping

#### distort / dist

Wave shaping distortion. Typical range: 0-10+. Optional postgain and type parameters.

#### coarse

Sample rate reduction. Factor values:
- 1 = original sample rate
- 2 = half sample rate
- Higher = more lo-fi

#### crush

Bit depth reduction. Range: 1-16.
- 1 = extreme (1-bit)
- 16 = full quality

### Spatial Effects

#### pan

Stereo positioning. Range: 0 (left) to 1 (right), 0.5 = center.

#### jux

Applies a function to the right channel only (original on left).

#### juxBy

Stereo width control. 0 = mono, 1 = full stereo separation.

### Delay (Global/Orbit Effect)

#### delay

Send level to delay bus. Range: 0-1. Can include optional delaytime and delayfeedback as colon-separated values.

#### delaytime / delayt / dt

Delay time (in seconds or fractions of a cycle).

#### delayfeedback / delayfb / dfb

Feedback amount. Values >= 1 risk runaway feedback.

### Reverb (Global/Orbit Effect)

#### room

Reverb send level. Range: 0-1. Optional roomsize parameter.

#### roomsize / rsize / sz / size

Reverb room size. Range: 0-10.

#### roomfade / rfade

Reverb fade time in seconds.

#### roomlp / rlp

Reverb lowpass start frequency (Hz).

#### roomdim / rdim

Reverb damping: frequency at which reverb reaches -60dB (Hz).

#### iresponse / ir

Impulse response sample selection for convolution reverb.

### Modulation Effects

#### Tremolo (Amplitude Modulation)

- `tremolosync` / `tremsync` -- modulation speed (cycle-synced)
- `tremolodepth` -- modulation intensity (0-1)
- `tremoloskew` -- waveform skew (0-1)
- `tremolophase` -- modulation phase offset
- `tremoloshape` -- waveform type: sine, tri, square, saw, ramp

### Phaser

- `phaser` / `ph` -- modulation speed
- `phaserdepth` / `phd` / `phasdp` -- effect intensity (0-1, default 0.75)
- `phasercenter` / `phc` -- center frequency in Hz (default 1000)
- `phasersweep` / `phs` -- LFO sweep range (0-4000 typical)

### Vowel Filter

`vowel` -- formant filtering using phonetic vowel values.

Available vowels: a, e, i, o, u, ae, aa, oe, ue, y, uh, un, en, an, on.

### Duck (Sidechain Compression)

- `duckorbit` / `duck` -- target orbit number for ducking
- `duckattack` / `duckatt` -- return-to-normal time in seconds
- `duckdepth` -- modulation amount (0-1)

### Orbit System

#### orbit / o

Groups patterns into shared effect buses. Default is orbit 1.

Shared orbits can cause parameter conflicts when multiple patterns modify the same reverb/delay settings. Use distinct orbits to avoid unpredictable results.

---

## Quick Reference: All Function Names

### Sound Selection
| Function | Aliases | Description |
|----------|---------|-------------|
| `sound()` | `s()` | Select sound/sample |
| `bank()` | -- | Select drum machine bank |
| `n()` | -- | Select sample number or scale degree |
| `note()` | -- | Set pitch (MIDI number or letter) |
| `scale()` | -- | Set musical scale for n() |
| `freq()` | -- | Set frequency directly |
| `samples()` | -- | Load sample bank |
| `soundAlias()` | -- | Create sound name alias |

### Tempo and Timing
| Function | Description |
|----------|-------------|
| `setcpm()` | Set cycles per minute |
| `slow()` | Slow down pattern |
| `fast()` | Speed up pattern |

### Pattern Transformations
| Function | Description |
|----------|-------------|
| `rev()` | Reverse pattern |
| `jux()` | Juxtapose: left/right stereo split with modification |
| `add()` | Add values (transpose) |
| `ply()` | Multiply each event n times |
| `off()` | Copy, time-shift, and modify |
| `every()` | Apply function every n cycles |
| `sometimes()` | Apply function randomly |
| `superimpose()` | Layer modified copy |

### Audio Effects
| Function | Aliases | Description |
|----------|---------|-------------|
| `lpf()` | `cutoff`, `ctf`, `lp` | Low-pass filter |
| `hpf()` | `hp`, `hcutoff` | High-pass filter |
| `bpf()` | `bandf`, `bp` | Band-pass filter |
| `gain()` | -- | Volume control |
| `velocity()` | -- | Velocity (multiplied with gain) |
| `pan()` | -- | Stereo position (0-1) |
| `delay()` | -- | Delay send |
| `delaytime()` | `delayt`, `dt` | Delay time |
| `delayfeedback()` | `delayfb`, `dfb` | Delay feedback |
| `room()` | -- | Reverb send |
| `roomsize()` | `rsize`, `sz`, `size` | Reverb size |
| `roomfade()` | `rfade` | Reverb fade |
| `roomlp()` | `rlp` | Reverb low-pass |
| `roomdim()` | `rdim` | Reverb damping |
| `distort()` | `dist` | Distortion |
| `crush()` | -- | Bit crush |
| `coarse()` | -- | Sample rate reduction |
| `vowel()` | -- | Vowel formant filter |
| `speed()` | -- | Playback speed / pitch |
| `attack()` | -- | Envelope attack |
| `decay()` | -- | Envelope decay |
| `sustain()` | -- | Envelope sustain |
| `release()` | -- | Envelope release |
| `adsr()` | -- | Envelope shorthand |
| `postgain()` | -- | Post-effects gain |
| `compressor()` | -- | Dynamic compression |
| `orbit()` | `o` | Effect bus assignment |

### Synth Parameters
| Function | Aliases | Description |
|----------|---------|-------------|
| `vib()` | `vibrato`, `v` | Vibrato frequency |
| `vibmod()` | `vmod` | Vibrato depth (semitones) |
| `fm()` | `fmi` | FM modulation index |
| `fmh()` | -- | FM harmonicity ratio |
| `fmattack()` | -- | FM envelope attack |
| `fmdecay()` | -- | FM envelope decay |
| `fmsustain()` | -- | FM envelope sustain |
| `fmenv()` | -- | FM envelope type (lin/exp) |
| `noise()` | -- | Add noise to oscillator |
| `partials()` | -- | Harmonic magnitudes |
| `phases()` | -- | Harmonic phase offsets |

### Tremolo
| Function | Aliases | Description |
|----------|---------|-------------|
| `tremolosync()` | `tremsync` | Tremolo speed (cycle-synced) |
| `tremolodepth()` | -- | Tremolo intensity |
| `tremoloskew()` | -- | Tremolo waveform skew |
| `tremolophase()` | -- | Tremolo phase offset |
| `tremoloshape()` | -- | Tremolo waveform shape |

### Phaser
| Function | Aliases | Description |
|----------|---------|-------------|
| `phaser()` | `ph` | Phaser speed |
| `phaserdepth()` | `phd`, `phasdp` | Phaser intensity |
| `phasercenter()` | `phc` | Phaser center frequency |
| `phasersweep()` | `phs` | Phaser sweep range |

### Sidechain / Duck
| Function | Aliases | Description |
|----------|---------|-------------|
| `duckorbit()` | `duck` | Duck target orbit |
| `duckattack()` | `duckatt` | Duck recovery time |
| `duckdepth()` | -- | Duck modulation depth |

### Sample Playback Control
| Function | Aliases | Description |
|----------|---------|-------------|
| `begin()` | -- | Skip sample start (0-1) |
| `end()` | -- | Cut sample end (0-1) |
| `loop()` | -- | Loop sample |
| `loopBegin()` | `loopb` | Loop start point |
| `loopEnd()` | `loope` | Loop end point |
| `cut()` | -- | Choke group |
| `clip()` | `legato` | Duration multiplier |
| `loopAt()` | -- | Fit sample to n cycles |
| `fit()` | -- | Fit sample to event duration |
| `chop()` | -- | Granular slice count |
| `striate()` | -- | Progressive slice playback |
| `slice()` | -- | Pattern-controlled slicing |
| `splice()` | -- | Speed-adjusted slicing |
| `scrub()` | -- | Tape-loop scrubbing |

### Signals (Continuous Modulation)
| Signal | Description |
|--------|-------------|
| `sine` | Sine wave LFO |
| `saw` | Sawtooth wave LFO |
| `square` | Square wave LFO |
| `tri` | Triangle wave LFO |
| `rand` | Random values |
| `perlin` | Perlin noise (smooth random) |

Use `.range(min, max)` to set the output range of any signal.

### Mini-Notation Complete Reference

| Syntax | Name | Description | Example |
|--------|------|-------------|---------|
| (space) | Sequence | Events in order | `"bd sd hh"` |
| `:n` | Sample select | Choose sample number | `"hh:2"` |
| `-` or `~` | Rest | Silence | `"bd - sd -"` |
| `[...]` | Group | Sub-sequence | `"bd [hh hh]"` |
| `<...>` | Alternate | One per cycle | `"<bd sd hh>"` |
| `*n` | Repeat/Speed | Play n times | `"hh*4"` |
| `/n` | Slow | Spread over n cycles | `"[c d e f]/2"` |
| `,` | Layer | Parallel patterns | `"bd*4, hh*8"` |
| `@n` | Elongate | Hold for n units | `"c@3 e"` |
| `!n` | Replicate | Duplicate n times | `"c!3 e"` |
| `?` | Degrade | Random removal | `"hh*8?"` |
| `{ }%n` | Polymeter | Fit n steps | `"{0 1 2 3 4}%8"` |

### Multi-Pattern Syntax

```js
$: pattern1    // active pattern
_$: pattern2   // muted pattern (prefix with underscore)
```
