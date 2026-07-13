# Music Catalog Plan — Phase 1 (for Gene's sign-off)

> **Historical.** This is the original Phase-1 sign-off plan; the catalog now
> exceeds it (**407 stems · 44 kits · 12 arcs · 41 genres**). For the current
> system and how to use it, start at **[`README.md`](README.md)**.

198 numbered entries: **161 stems** (1–161) + **27 kits** (162–188) + **10 arcs**
(189–198). Curate by number: strike, swap, or add. `[H]` = harvested from
stage-proven material (scenes/*.py, full_show.show.json, musicscenes/*.json) —
kept in character, given `${root}` + honest key labels + 3 variants.

Key spread commitment: all 12 roots, 8 modes (major, minor, dorian, phrygian,
mixolydian, lydian, major-pent, minor-pent). Non-4/4: #42 (5/4), #75 (triplet
grid), #113/115 (7/8 + polymeter), #122 (polymeter), #157 (12/8). Process
family: #118–122 (+#113, #115). No-drums texture kits: #180, #181.
All duck-pump gestures use the verified isaw gain-pump (sidechain is banned —
see BUNDLE.md).

## A. Disco / synth-funk — refresh (9) — banks: TR909, AkaiLinn · cps .48–.55

| # | id | slot | gesture | REQUIRED technique | key |
|---|----|------|---------|--------------------|-----|
| 1 | drums.disco.four_pump [H] | drums | 4-floor, ghost 16ths, fills every 8 | ply fills | — |
| 2 | drums.disco.linn_boogie | drums | AkaiLinn 80s boogie | AkaiLinn bank | — |
| 3 | perc.disco.congas | perc | uzu conga/bongo + tambourine offbeat | uzu perc names | — |
| 4 | bass.disco.octave_pump | bass | octave 8ths + sidechain feel | isaw gain-pump | F major |
| 5 | bass.disco.wah_funk [H] | bass | env-filtered funk syncopation | lpenv | D dorian |
| 6 | chords.disco.stab_9ths [H] | chords | offbeat 9th stabs | struct | Bb mixolydian |
| 7 | lead.disco.clav_riff [H] | lead | square clav riff | — | D dorian |
| 8 | lead.disco.wt_guitar | lead | wavetable disco lick | wt_eguitar | F major |
| 9 | pad.disco.warm_juno | pad | detuned saw pad, light pump | isaw pump | F major |

## B. House (9) — banks: TR909, TR707 · cps .50–.58

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 10 | drums.house.classic_909 [H] | drums | offbeat oh/hh classic | — | — |
| 11 | drums.house.deep_707 | drums | deep shuffle w/ rim | TR707 | — |
| 12 | perc.house.shaker_swing | perc | shaker 16ths + ride | late-pattern swing | — |
| 13 | bass.house.deep_sub | bass | sub w/ octave jumps + pump | isaw pump | G minor |
| 14 | chords.house.organ_stab | chords | M1-ish organ stabs | vcsl organ_full | G minor |
| 15 | chords.house.piano_house | chords | piano stabs offbeat | piano + struct | Eb major |
| 16 | lead.house.vocal_vowel | lead | saw "vocal" chops | vowel | B minor |
| 17 | pad.house.dreamhouse | pad | lush 9th pad slow bloom | — | Eb major |
| 18 | texture.house.vinyl_bed | texture | crackle + brown noise bed | noise osc | — |

## C. Techno (9) — banks: TR909, Compurhythm1000 · cps .55–.65

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 19 | drums.techno.warehouse [H] | drums | pounding kick, tuned | penv kick | — |
| 20 | drums.techno.broken_cr1000 | drums | broken techno | RolandCompurhythm1000 | — |
| 21 | perc.techno.metal_euclid | perc | rim/cowbell rotations | euclid (5,16,r) rotation | — |
| 22 | bass.techno.rumble | bass | rumbling sub, room+shape | — | C# minor |
| 23 | bass.techno.ebm_16 | bass | EBM 16th stabs | — | E phrygian |
| 24 | chords.techno.detroit_stabs | chords | m7 stabs, hpf sweeps | — | C# minor |
| 25 | lead.techno.hoover_wt | lead | wavetable hoover | wt_distorted | C# minor |
| 26 | pad.techno.dark_cluster | pad | phrygian cluster pad | — | E phrygian |
| 27 | texture.techno.white_riser | texture | 8-bar noise risers | white noise | — |

## D. Acid (5) — bank: TR909 · cps .52–.60

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 28 | bass.acid.classic_303 [H] | bass | squelch, 3-signal modulation | lpenv/lpq sweeps | E minor |
| 29 | bass.acid.slow_heavy | bass | half-time heavy acid | ftype 24db | Bb minor |
| 30 | drums.acid.909_ride | drums | kick+clap+ride | — | — |
| 31 | lead.acid.hi_squelch | lead | octave-up 303 as lead | lpenv | G phrygian |
| 32 | chords.acid.stab_echo | chords | delayed square stabs | delay | E minor |

## E. Jazz — refresh (12) — vcsl mallets, uzu brushes · cps .40–.50

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 33 | drums.jazz.brushes [H] | drums | brush kit, ghost dynamics | gain patterns | — |
| 34 | drums.jazz.ride_swing | drums | ride-led swing | elongation shuffle [x@2 x] | — |
| 35 | perc.jazz.smallhits | perc | vibraslap/woodblock accents | vcsl perc | — |
| 36 | bass.jazz.walking_251 [H] | bass | ii-V-I walk | scale-per-chord | D dorian→G mixo→C maj |
| 37 | bass.jazz.walking_ballad | bass | slow ballad walk | — | Bb major |
| 38 | bass.jazz.walking_54 | bass | **5/4 walk** (Take Five feel) | non-4/4 | Eb minor |
| 39 | chords.jazz.ireal_comp [H] | chords | voice-led comping | dict('ireal').voicing()+struct | D dorian |
| 40 | chords.jazz.ballad_piano | chords | piano ballad, clip(1) | piano | Bb major |
| 41 | lead.jazz.vibraphone_blue | lead | **vibraphone** blues line | vcsl vibraphone | C minor pent |
| 42 | lead.jazz.vibraphone_modal | lead | vibraphone_soft modal runs + off-canon | off() | D dorian |
| 43 | pad.jazz.nightclub [H] | pad | warm dark pad | — | C minor |
| 44 | vox.jazz.breath_scat [H] | vox | breath/scat texture | dirt-samples breath (nondeterministic ok) | — |

## F. Italo / Hi-NRG (9) — banks: Compurhythm1000, CasioRZ1 · cps .50–.58

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 45 | drums.italo.four_cr | drums | 4-floor + claps | CasioRZ1 or CR1000 | — |
| 46 | perc.italo.nrg_toms | perc | syncopated panned toms | — | — |
| 47 | bass.italo.octave_pump | bass | THE italo octave bass + pump | isaw pump | A major |
| 48 | bass.italo.arp16 | bass | 16th arp bass | — | F# minor |
| 49 | chords.italo.brass_stabs [H] | chords | saw brass stabs | — | D major |
| 50 | lead.italo.wt_vgame | lead | chip-adjacent wavetable lead | wt_vgame | A major |
| 51 | lead.italo.euphoric_oct [H] | lead | octave-jump euphoria | — | A major |
| 52 | pad.italo.strings [H] | pad | string machine | — | F# minor |
| 53 | vox.italo.vowel_choir | vox | "aah" choir pads | vowel | A major |

(Synthwave musicscene harvests fold into #49/#51/#52 where character fits.)

## G. Electro / Drexciya (10) — banks: TR808, AkaiLinn, CasioRZ1 · cps .50–.58

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 54 | drums.electro.linn_808 | drums | 808 electro + Linn accents | — | — |
| 55 | drums.electro.rz1_crisp | drums | crisp digital electro | CasioRZ1 | — |
| 56 | perc.electro.clap_rot | perc | clap machine rotations | euclid (5,8,r) | — |
| 57 | bass.electro.fm_growl | bass | growling FM bass | .fm(6).fmh(2.01) | G# minor |
| 58 | bass.electro.fm_hover | bass | deep FM sub hover | .fm + fmdecay | D minor |
| 59 | chords.electro.aquatic | chords | watery detuned minors + phaser | phaser | G# minor |
| 60 | lead.electro.vocoder | lead | vowel-swept robot lead | vowel | D minor |
| 61 | lead.electro.theremin | lead | eerie theremin wavetable | wt_theremin | G# minor |
| 62 | pad.electro.deep_sea | pad | dark bpf pad | bpf | G# minor |
| 63 | texture.electro.sonar | texture | delayed sonar pings | delay | — |

## H. UK Garage / 2-step (9) — banks: TR707, TR909 · cps .55–.62

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 64 | drums.ukg.two_step | drums | classic 2-step shuffle | late-swing | — |
| 65 | drums.ukg.four_flavor | drums | 4x4 UKG skippy hats | — | — |
| 66 | perc.ukg.skippy_rims | perc | rim/shaker skips, ghosts | — | — |
| 67 | bass.ukg.wobble_sub | bass | lpf-wobble sub | lpf signal | G major |
| 68 | bass.ukg.bounce | bass | bouncy organ-ish bass | — | B minor |
| 69 | chords.ukg.filtered_rnb | chords | filtered R&B 7ths | — | G major |
| 70 | lead.ukg.vocal_chops | lead | pitched "vocal" chops | vowel+speed | E minor |
| 71 | pad.ukg.smooth | pad | smooth warm pad | — | B minor |
| 72 | texture.ukg.hiss | texture | vinyl hiss bed | crackle | — |

## I. Footwork / Juke (6) — bank: TR808 · cps .62–.72

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 73 | drums.footwork.triplet_grid | drums | 160bpm triplet kicks | polymeter/triplets | — |
| 74 | drums.footwork.clap_storm | drums | rapid clap/hat bursts | ply | — |
| 75 | perc.footwork.ratchets | perc | tom ratchets | ply(3) | — |
| 76 | bass.footwork.sub_stabs | bass | triplet sub stabs | — | F minor |
| 77 | lead.footwork.chop_loop | lead | sliced break micro-loops | slice | F minor |
| 78 | texture.footwork.stutter | texture | splice stutters | splice | — |

## J. Gqom (6) — banks: ViscoSpaceDrum, TR808 · cps .50–.56

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 79 | drums.gqom.broken_kicks | drums | displaced kick clusters | ViscoSpaceDrum | — |
| 80 | perc.gqom.tom_rotation | perc | rotating tom cells | euclid (3,8,<0 2 4 6>) | — |
| 81 | perc.gqom.shaker34 | perc | 3-against-4 shaker | polymeter | — |
| 82 | bass.gqom.drone_stab | bass | drone-bass hits | — | C phrygian |
| 83 | pad.gqom.dark_chant | pad | vowel drone "o/u" | vowel | C phrygian |
| 84 | texture.gqom.rumble | texture | brown-noise lpf pulse | brown noise | — |

## K. Dub techno (8) — bank: TR909 · cps .45–.55

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 85 | drums.dubtech.soft_four [H] | drums | soft 4-floor + 16th hats | — | — |
| 86 | perc.dubtech.rim_dub [H] | perc | THE dub rim delay | delay .7/.375/.55 | — |
| 87 | bass.dubtech.sine_sub [H] | bass | subliminal sine sub | — | A minor |
| 88 | bass.dubtech.dorian_roll | bass | rolling dorian bass | — | F# dorian |
| 89 | chords.dubtech.smoke [H] | chords | filtered dub chord stabs | delay+room orbit 4 | A minor |
| 90 | pad.dubtech.tape | pad | dark hissy pad | — | F# dorian |
| 91 | texture.dubtech.hiss_field | texture | pink noise field | pink noise | — |
| 92 | vox.dubtech.echo_ghost | vox | ghost echo hits | dirt-samples (nondet.) | — |

## L. Rave / Breakbeat hardcore '91–93 (8) — clean-breaks · cps .60–.70

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 93 | drums.rave.think_break | drums | think break chopped | clean-breaks think, loopAt+chop | — |
| 94 | drums.rave.apache_stomp | drums | apache + 909 kick under | clean-breaks apache | — |
| 95 | perc.rave.crash_wash | perc | crash/ride wash | — | — |
| 96 | bass.rave.hoover | bass | hoover bass | penv + detune | F minor |
| 97 | bass.rave.reese | bass | reese detune stack | superimpose(.05) | C minor |
| 98 | chords.rave.piano_rave | chords | M1 piano rave stabs | piano+struct | C minor |
| 99 | lead.rave.mentasm | lead | mentasm riff, hpf sweeps | hpf | F minor |
| 100 | texture.rave.riser_fm | texture | FM sweep risers | fm | — |

## M. Trance (8) — bank: TR909 · cps .55–.65

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 101 | drums.trance.driving | drums | driving kick + offbeat oh | — | — |
| 102 | perc.trance.roll16 | perc | rolling snare builds | ply/fast lastOf | — |
| 103 | bass.trance.rolling | bass | offbeat rolling bass + pump | isaw pump | A major |
| 104 | chords.trance.supersaw | chords | supersaw wall, lpf bloom | supersaw+detune | E major |
| 105 | lead.trance.wt_arp | lead | wavetable 16th arp + canon | wt_* + off() | F# minor |
| 106 | lead.trance.anthem | lead | big delayed anthem line | delay | A major |
| 107 | pad.trance.wash | pad | huge wash pad | — | E major |
| 108 | texture.trance.white_lift | texture | noise lifts | white noise | — |

## N. Trap / Drill (7) — bank: TR808 · cps .35–.42

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 109 | drums.trap.hat_rolls [H] | drums | 808 kit, hat rolls | ply("<1 2 1 3>") | — |
| 110 | drums.drill.bounce | drums | drill ghost-kick bounce | — | — |
| 111 | perc.trap.rim_clicks | perc | sparse rim syncopation | — | — |
| 112 | bass.trap.808_glide | bass | gliding 808 | penv glides | C# minor |
| 113 | chords.trap.dark_bells | chords | dark inharmonic bells | fm + fmh(2.76) | C# minor |
| 114 | lead.trap.whistle | lead | eerie whistle | sine+vib | F minor |
| 115 | pad.trap.string_dread | pad | tense string pad | — | F minor |

## O. Gamelan / FM bell music (7) — vcsl metal + FM · cps .30–.50

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 116 | drums.gamelan.gong_cycle | drums | colotomic gong cycle | vcsl gong, long cycles | — |
| 117 | perc.gamelan.bonang_fm | perc | FM inharmonic interlock | fmh(2.76) inharmonic | Db major pent |
| 118 | perc.gamelan.kotekan | perc | handbells interlock **7/8** | polymeter {..}%7 | Db major pent |
| 119 | bass.gamelan.gong_bass | bass | deep sine gong hits | — | Db major pent |
| 120 | chords.gamelan.balafon | chords | cycling balafon pattern | vcsl balafon | Db major pent |
| 121 | lead.gamelan.tubular | lead | slow tubularbells song | vcsl tubularbells | F# major pent |
| 122 | texture.gamelan.shimmer | texture | marktrees/triangles + partials | partials | — |

## P. Reich / process minimalism (5) — family: process · cps .40–.55

| # | id | slot(+claims) | gesture | REQUIRED |
|---|----|---------------|---------|----------|
| 123 | process.reich.phase_pianos | chords (+lead) | two piano cells, fast(64/63) phasing | phasing ratio |
| 124 | process.reich.marimba_add | chords (+lead+pad) | In-C cell advancement over minutes | <> cell rotation |
| 125 | process.reich.clapping | perc (+drums) | Clapping Music rotation | polymeter rotation |
| 126 | process.reich.pulse_organ | pad | organ pulses, slow euclid rotation | euclid (n,k,r) drift |
| 127 | process.reich.bell_rot | lead | handchimes euclid(5,12,r) advancing | euclid rotation |

(All in C major / D mixolydian region, transposable scale-sub.)

## Q. Musique concrète / plunderphonics (6) — dirt-samples, vcsl found-objects · cps free

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 128 | texture.concrete.tape | texture | striate tape mangling | striate (nondet. ok) | none |
| 129 | perc.concrete.found | perc | anvil/brakedrum objects | vcsl found perc | none |
| 130 | drums.concrete.thuds | drums | framedrum irregular hits | euclid irregular | none |
| 131 | pad.concrete.wineglass | pad | wineglass drone | vcsl wineglass | none |
| 132 | lead.concrete.siren | lead | siren/trainwhistle swoops | vcsl siren (sparse!) | none |
| 133 | vox.concrete.breath_cuts | vox | breath chops rev/slice | slice+rev | none |

## R. Drone / Ambient (7) — vcsl bowed · cps .15–.30

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 134 | pad.drone.bowed_vibes | pad | vibraphone_bowed layers | vcsl bowed | E major |
| 135 | pad.drone.partials_organ | pad | additive drone | partials([..]) | C lydian |
| 136 | bass.drone.sub_breath | bass | slow sub swells | attack/release | C lydian |
| 137 | texture.drone.psaltery | texture | psaltery_bow shimmer | vcsl psaltery_bow | E major |
| 138 | texture.drone.night_air | texture | pink noise slow bpf | pink+bpf | — |
| 139 | lead.drone.super64 | lead | sparse super64_vib calls | vcsl super64 | E major |
| 140 | chords.drone.harmonium | chords | harmonica_soft slow chords | vcsl harmonica | C lydian |

## S. Downtempo / Trip-hop (8) — banks: EmuSP12! · cps .38–.48

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 141 | drums.downtempo.sp12 [H] | drums | SP-12 boom-bap | EmuSP12 bank | — |
| 142 | drums.triphop.dusty_break | drums | slowed funkydrummer | clean-breaks loopAt(4) | — |
| 143 | perc.downtempo.mridangam | perc | carnatic groove loop | mridangam pack | — |
| 144 | bass.downtempo.round_sub | bass | round dub sub | — | Eb minor pent |
| 145 | chords.downtempo.dusty_keys | chords | fmpiano/kawai dusty chords | vcsl keys | Ab major |
| 146 | lead.downtempo.kalimba | lead | kalimba line | vcsl kalimba | G dorian |
| 147 | pad.downtempo.tape_warm | pad | warm tape pad, slow detune | detune signal | Ab major |
| 148 | texture.downtempo.rain | texture | crackle rain bed | crackle | — |

## T. Jungle / DnB — refresh (8) — clean-breaks, uzu brk · cps .62–.75

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 149 | drums.dnb.amen_roller [H] | drums | rolling amen chops | clean-breaks amen | — |
| 150 | drums.dnb.twostep_break [H] | drums | 2-step DnB pattern | — | — |
| 151 | bass.dnb.reese_dark [H] | bass | dark reese | superimpose detune | G minor |
| 152 | bass.dnb.sub_drone [H] | bass | sub drone | — | Eb minor |
| 153 | chords.dnb.liquid_keys [H] | chords | liquid piano/keys | piano clip(1) | Bb major |
| 154 | lead.dnb.vibes_liquid | lead | liquid vibraphone line | vcsl vibraphone | Bb major |
| 155 | pad.dnb.dark [H] | pad | dark pad | — | G minor |
| 156 | texture.dnb.breath_fx [H] | texture | breath FX | — | — |

## U. Afrobeat / Highlife (5, harvest-led) — cps .50–.58

| # | id | slot | gesture | REQUIRED | key |
|---|----|------|---------|----------|-----|
| 157 | drums.afrobeat.bell_128 [H] | drums | **12/8 bell** + kit | euclid (7,12) bell | — |
| 158 | perc.afrobeat.congas [H] | perc | interlocking congas | uzu/vcsl congas | — |
| 159 | bass.afrobeat.tony_allen [H] | bass | rolling afro bass | — | E major |
| 160 | chords.afrobeat.highlife_gtr [H] | chords | highlife guitar-ish arps | — | E major |
| 161 | lead.afrobeat.horn_riff [H] | lead | horn section riff | — | E major |

## Kits (162–188) — each: home key + cps + 2 recommended arcs + tags

162 kit.disco_classic (F maj, .52) · 163 kit.disco_linn (D dorian, .5) ·
164 kit.house_deep (G min, .53) · 165 kit.house_piano (Eb maj, .55) ·
166 kit.techno_warehouse (C# min, .6) · 167 kit.techno_broken (E phryg, .58) ·
168 kit.acid_night (E min, .55) · 169 kit.jazz_combo (D dorian, .45) ·
170 kit.jazz_vibes_ballad (Bb maj, .42) · 171 kit.italo_nrg (A maj, .54) ·
172 kit.electro_deep_sea (G# min, .54) · 173 kit.ukg_2step (B min, .58) ·
174 kit.footwork_juke (F min, .67) · 175 kit.gqom_dark (C phryg, .53) ·
176 kit.dubtech_smoke (A min, .5) · 177 kit.rave_93 (C min, .65) ·
178 kit.trance_anthem (A maj, .6) · 179 kit.trap_dread (C# min, .38) ·
180 kit.gamelan_fm (Db maj pent, .4) **no-drums option** ·
181 kit.concrete_tape (unpitched, .35) **no-drums** ·
182 kit.drone_dawn (C lydian, .2) **no-drums** ·
183 kit.downtempo_sp12 (Eb min pent, .42) · 184 kit.triphop_rain (Ab maj, .4) ·
185 kit.dnb_liquid (Bb maj, .7) · 186 kit.afrobeat_sun (E maj, .54) ·
187 kit.wild_mallet_house (house drums + vibraphone + kalimba; G dorian, .52) ·
188 kit.wild_fm_techno_gamelan (techno kick + FM bells + gqom toms; C# min, .55)

## Arcs (189–198) — shared; sections carry intensity arrays for the visual handshake

| # | id | sections×cycles | shape (intensity array) |
|---|----|-----------------|--------------------------|
| 189 | arc.build_drop | 8×8 | .2 .35 .55 .9 .3 .6 1 .4 |
| 190 | arc.slow_burn | 6×12 | .15 .3 .45 .6 .8 1 |
| 191 | arc.breakdown_first | 6×8 | .25 .35 .3 .7 .9 .6 |
| 192 | arc.peak_hold | 5×8 | .85 1 .9 1 .7 |
| 193 | arc.waves | 8×6 | .3 .6 .9 .4 .5 .8 1 .35 |
| 194 | arc.sparse_bookends | 5×10 | .2 .5 .9 .5 .2 |
| 195 | arc.pulse | 8×4 | .4 .9 .4 1 .35 .9 .5 1 |
| 196 | arc.ghost_intro | 6×8 | .15 .25 .45 .65 .85 1 |
| 197 | arc.long_arch | 7×18 | .2 .4 .6 .85 1 .6 .3 |
| 198 | arc.drop_out | 5×8 | 1 .8 .55 .35 .15 |

## Technique coverage (the "unused shelves" get spent)

FM (#57,58,100,113,117) · wavetables (#8,25,50,61,105) · partials (#122,135) ·
noise osc (#18,27,84,91,108,138) · vowel (#16,53,60,70,83) · penv (#19,96,112) ·
euclid rotation (#21,56,80,126,127) · polymeter (#73,81,118,125) ·
slice/splice/striate (#77,78,128,133) · isaw pump (#4,9,13,47,103) ·
late-swing/elongation (#12,34,64) · ireal voicing (#39) · phasing (#123) ·
mridangam (#143) · EmuSP12 (#141) · all 6 unused drum banks assigned.

## Open questions for Gene

1. **Genre column swaps?** Benched but ready: IDM/glitch, vaporwave,
   latin/reggaeton (cinquillo), more afrobeat depth. Strike any column above
   to swap one in.
2. **Vox slots** are the thinnest (no real vocal samples in verified packs —
   vowel-synthesis + breath chops are the workaround). OK, or hunt a vocal
   pack first?
3. Kit count 27 OK, or trim wildcards?
