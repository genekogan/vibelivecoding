# BUNDLE.md — verified @strudel/web 1.0.3 feature matrix (port 9766, 2026-07-10)

Every feature below was fired as a live track on the factory server and judged
by `audio.rms` + `/errors` delta. **Stems may only use PASS features and packs
listed in `packs.json`.** Exact working syntax is quoted — copy it.

## PASS — synthesis

| Feature | Verified syntax | Notes |
|---------|-----------------|-------|
| FM | `note("c3 e3 g3 c4").s("sine").fm(4).fmh(2.01).fmattack(.01).fmdecay(.15)` | rms .047. Inharmonic ratios (`.fmh(1.414)`, `2.01`, `3.37`) = bells/gamelan |
| Wavetables | `note("c3 e3 g3 c4").s("wt_flute")` | Needs `wavetables` pack (see packs.json). 65 names: wt_01…wt_20, wt_flute, wt_epiano, wt_cello, wt_violin, wt_clarinett, wt_oboe, wt_altosax, wt_theremin, wt_vgame, wt_oscchip, wt_ebass, wt_dbass, wt_aguitar, wt_eguitar, wt_eorgan, wt_clavinet, wt_piano, wt_fmsynth, wt_granular, wt_hvoice, wt_overtone, wt_sinharm, wt_stringbox, wt_distorted, wt_bitreduced, wt_bw_* set… |
| Additive | `note("c3 e3 g3 c4").s("sine").partials([1,.6,.4,.3,.2])` | rms .05 |
| Noise oscillators | `s("white pink brown").decay(.25).sustain(0)` | all three audible |
| Crackle | `s("crackle*4").density(.15).gain(.8)` | QUIET (rms .004 even at gain .8) — texture-slot only, pair with other layers; validation sparse threshold only |
| Vowel filter | `note("c3*8").s("sawtooth").vowel("<a e i o u>")` | rms .028 |
| Pitch envelope | `note("c1*4").s("sine").penv(24).pdec(.08).decay(.3).sustain(0)` | 808/trap kick glides, rms .11 |
| Compressor | `.compressor("-20:20:10:.002:.02")` | works on busy patterns |

## PASS — pattern combinators

| Feature | Verified syntax |
|---------|-----------------|
| jux | `note("c3 e3 g3 b3").s("sawtooth").jux(rev)` |
| ply | `s("hh*4").ply("<1 2 3>")` |
| off | `n("0 2 4 2").scale("c4:minor").off(1/8, x=>x.add(note(7)).gain(.5))` |
| polymeter | `note("{c3 eb3 g3 bb3 c4}%4")` |
| euclid mini + rotation | `s("bd(3,8,2), hh(7,12)")` |
| euclid method | `note("c2").euclid(5,8)` |
| **arrange** | `arrange([2, note("c3 e3 g3 c4")], [2, note("f2 a2 c3 f3")]).s("sawtooth")` — **arc compiler depends on this; PASS** |
| segment signal→melody | `n(sine.segment(8).range(0,7)).scale("c3:minor:pentatonic")` |
| ireal voicings | `chord("<Dm9 G13 C^9>").dict('ireal').voicing()` |
| struct | `chord("Cm9").dict('ireal').voicing().struct("[~ x]*2")` |

## PASS — transposition (the contract's two methods)

- **add-note**: `note("c2*2").add(note(19))` — verified by FFT centroid shift (6.6 → 8.1). Compiler appends `.add(note(${root}))`.
- **scale-sub**: `n("0 2 4 6 4 2").scale("eb3:mixolydian")` and `n("0 1 4 5").scale("f#2:phrygian")` both PASS — the `${root}${oct}:${mode}` template substitutes cleanly.

## PASS — sample manipulation

All verified on clean-breaks (`amen`) and uzu (`brk`):

- `s("amen").loopAt(2).chop(16)` · `s("amen").striate(8)` · `s("amen").slice(8, "0 3 5 7")` · `s("amen").splice(8, "0 1 2 3 4 5 6 7")` · `s("brk").loopAt(2).chop(8)`
- **clean-breaks has NO `clean:N` names.** Its sounds are named: amen, think, apache, funkydrummer, king, sport, kool, around, riffin, neworleans, hitormiss, action, hotline, swat, ripple, fireeater, hungup, newday, movement, boogiewoogie, delight, eeloil, impeach, marymary, sneakin, squib, groove, useme, sesame, do, rill, mechanicalman.

## FAIL — BANNED (threw live errors or silent; never use in stems)

| Feature | Error | Verified replacement |
|---------|-------|----------------------|
| `.swingBy()` | `…swingBy is not a function` | shuffle via elongation `s("[hh@2 hh]*4")` (triplet feel), or patterned late `s("hh*8").late("[0 .03]*4")` — both PASS |
| `.swing()` | `…swing is not a function` (same shim missing) | same as above |
| `.duckorbit()` / `.duck()` / `.duckattack()` / `.duckdepth()` | `…duckorbit is not a function` — **sidechain does not exist in this bundle at all** (tested both trigger/victim directions) | THE PUMP IDIOM (verified): gain is sampled at event ONSET (no continuous modulation per voice). Rhythmic parts: `.gain(saw.range(FLOOR, TOP).fast(4))` — on-beat onsets duck to FLOOR, later subdivisions rise toward TOP (rms .14). Sustained pads MUST RE-TRIGGER to pump: `note("[c3,e3,g3]*4").attack(.05).decay(.4).sustain(.3).release(.15).gain(saw.range(.12,.32).fast(4))` (rms .11). NEVER `range(TOP, FLOOR)` ordering with saw — it inverts the duck and can fail audibility. |
| `.tremolosync()` / tremolo family | `…tremolosync is not a function` | re-trigger pump idiom above, or `.gain("` per-step gain patterns `")` (plain numbers only in mini-notation — NO `${x}*.5` math inside quoted patterns; math like `${gain}*.5` is legal ONLY as a JS argument) |
| `.scrub()` | `…scrub is not a function` | use `.slice`/`.splice`/`.striate`/`.begin`/`.end` |
| `gm_*` soundfonts | (contract-known) | vcsl instruments — see packs.json |
| `setcps()` / `.cps()` in stems | (contract) | server `/strudel/cps` is the only tempo authority |
| `github:tidalcycles/strudel-samples` | 404 (contract-known) | dirt-samples, clean-breaks |

## Duck experiment detail (for the record)

Drums orbit 1 (gain .06) + sustained pad orbit 6, sampled lowmid+mid at 80–100ms:
baseline cv 0.47–0.55; `.duckorbit(1)`/`.duck(1)` on pad → runtime error, whole
stack degraded; `.duck(6)` on drums → runtime error, both tracks silenced.
Conclusion: the parameters are absent from superdough in this bundle, not
mis-directioned. The isaw gain-pump is the sanctioned pump gesture.

## Loudness reference (peak rms at listed gain — calibrate stem gains)

| Source | gain | peak rms |
|--------|------|----------|
| 909 `bd sd hh sd` | .7 | .42 |
| 808 same | .7 | .11 (808 is much quieter — gain up or shape) |
| euclid `bd(3,8,2), hh(7,12)` 909 | .6 | .38 |
| amen loopAt(2).chop(16) | .7 | .21 |
| sawtooth triad pad lpf 900 | .3 | ~.30 sustained band energy |
| piano chord arps | .6 | .15 |
| vibraphone | .7 | .049 (mallets are quiet — budget gain accordingly) |
| tubularbells | 1.0 | .06 |
| timpani | 1.0 | .015 (very quiet, layer only) |
| wt_flute | .5 | .12 |
| mridangam hits | .8 | .23 |

Audibility gate: full/peak variants need peak rms > .01 within 2.5s; sparse > .003.

## PASS — vocals (verified live)

- **dirt-samples vocal shelf** (dep `dirt-samples`): `n("0 1 2 3").s("speech")` rms .22 ·
  `s("yeah:0 yeah:2")` (28 variants) rms .14 · `n("0 3 7").s("diphone")` (pitchable!) ·
  `n("0 1 2").s("numbers")` · `s("ades2")` · also speechless, speakspell, diphone2,
  alphabet, miniyeah, baa, breath (texture).
- **shabda TTS** (deps `shabda-vox-f` / `shabda-vox-m`): custom spoken words.
  `samples('shabda/speech/en-US/f:groove,sunshine')` then `s("groove sunshine")` — PASS
  rms .10. Each word = its own sound name. External service at load (~5s) — stems using
  it should also work musically if the vox drops out; don't build a kit's backbone on it.
  Chop/pitch them: `.speed("<1 1.2 .8>")`, `.chop(4)`, `.slice(4,"0 2 1 3")`, vowel filter.

## Environment facts

- Server: port **9766** (`/strudel/cps` for tempo). Recording disabled all session.
- Preloaded at browser init (0s, no samples() call needed): tidal-drum-machines,
  uzu-drumkit, piano, vcsl.
- All 9 drum banks verified: RolandTR808/909/707/505, AkaiLinn, RhythmAce,
  ViscoSpaceDrum, RolandCompurhythm1000, CasioRZ1 — plus EmuSP12 via pack.
- uzu bare names: bd sd hh oh cp cr rd rim sh tb cb lt mt ht + `brk` (break) + `misc`.
- vcsl highlights (128 sounds): vibraphone / vibraphone_soft / vibraphone_bowed,
  marimba, kalimba…kalimba5, balafon(_hard/_soft), glockenspiel, xylophone_{soft,medium,hard}_{pp,ff},
  tubularbells(2), handbells, handchimes, timpani(2, _roll), folkharp, harp, psaltery_{pluck,bow,spiccato},
  strumstick, dantranh(_tremolo,_vibrato), didgeridoo, ocarina(…), recorders (sop/alto/tenor/bass ×stacc/sus/vib),
  sax/saxello(_stacc/_vib), harmonica(_soft/_vib), organ_{4inch,8inch,full}, pipeorgan_{loud,quiet}(_pedal),
  steinway, kawai, fmpiano, clavisynth, super64(_acc/_vib), gong(2), sus_cymbal(2), oceandrum,
  framedrum, darbuka, bongo, conga, cajon, agogo, cabasa, guiro, clave, woodblock, slitdrum,
  brakedrum, anvil, flexatone, vibraslap, ratchet, siren, trainwhistle, wineglass(_slow), triangles, sleighbells, marktrees.
