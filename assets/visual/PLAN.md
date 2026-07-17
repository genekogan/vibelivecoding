# Visual Factory — Phase 1 plan (awaiting Gene's sign-off)

~200 planned assets. ★ = harvest/migrate from existing repo code (cheap wins,
stage-proven). Global requirements baked into every work order:

- **Never-static**: visible evolution over 30s–5min via `K.section`/`K.intensity`
  arcs + `K.t` drift; subjects/worlds where it fits get an `act` param with 2–3
  multi-minute dramaturgies.
- **Audio-reactive over a baseline**: glow on bass, sparkle on treble, size on
  rms — blended on top of clk-driven motion, intentional in silence.
- **Mandatory style constraint per work order**: each asset gets an assigned
  palette discipline / technique (riso duotone, ink-wash, thermal, pastel,
  neon, paper-craft…) so the catalog doesn't collapse into HSB-rainbow-neon.
- Universal seven params everywhere; subjects add `pose` (≥3 incl. idle +
  dance/action); crowds add `n`, `energy`, `pal`.

## Subjects (50)

Harvest-migrate from `autopilot/creatures/` (18):
1. ★ alien
2. ★ astronaut
3. ★ cat
4. ★ dinosaur
5. ★ dragon
6. ★ elvis
7. ★ fox
8. ★ frog
9. ★ ghost
10. ★ gremlin
11. ★ mermaid
12. ★ mushroom man
13. ★ owl
14. ★ robot
15. ★ skeleton
16. ★ snowman
17. ★ unicorn
18. ★ wizard

New animals (14):
19. penguin (dj/waddle/slide poses)
20. duck
21. dog
22. octopus (limb-per-beat, color-shift)
23. flamingo (one-leg idle, strut)
24. peacock (parametric feather fan)
25. whale (breach act)
26. jellyfish (pulse on beat)
27. butterfly
28. horse (gallop cycle, streaming mane)
29. wolf (howl pose, moon-aware)
30. chameleon (hue param is literal)
31. sloth (comedy: half-tempo mover)
32. t-rex-in-sunglasses party dino (distinct from ★dinosaur)

People (10):
33. human DJ at decks (headphone-cue, drop-arms poses)
34. disco soloist ★ (port the disco_dancers.py rig — the quality bar)
35. breakdancer (windmill/freeze/toprock)
36. ballerina (pirouette, arabesque)
37. saxophonist (sway, lean-back wail)
38. drummer (visible stick hits on beat)
39. conductor (baton on beat, swells on intensity)
40. monk sweeping temple courtyard
41. noir detective silhouette (streetlamp, cigarette smoke)
42. surfer (carve act on a wave)

Vehicles & objects (8):
43. steam train (wheels beat-locked, smoke puffs)
44. UFO (hover wobble, abduction-beam act)
45. bicycle rider (pedal cadence = beat)
46. hot-air balloon (drift, burner flare on bass)
47. retro 50s rocket (launch act)
48. lowrider car (hydraulic bounce on beat)
49. boombox (speaker cones pump w/ bass & lowmid)
50. moon-with-face (blinks, mood follows intensity)

## Crowds (12)

51. ★ disco dancer line (choreographed 16-beat phrase, from disco_dancers.py)
52. festival crowd silhouettes (hands up on the drop)
53. ★ starling flock / boids (from artscenes/boids.json)
54. fish school (cohesion follows bass)
55. penguin waddle parade
56. mixed animal parade (species param)
57. traffic stream (cars/scooters/bus)
58. marching band
59. jellyfish bloom
60. butterfly swarm
61. skeleton conga line
62. roller skaters (rink orbits)

## Worlds (25)

Harvest-migrate from `autopilot/worlds/` (8):
63. ★ arctic
64. ★ candyland
65. ★ cityscape
66. ★ desert
67. ★ jungle
68. ★ space
69. ★ underwater
70. ★ volcano

New — each with its own palette discipline (17):
71. neon club interior (the one place neon is allowed)
72. sunset beach (warm gradients, silhouette horizon)
73. rooftop city in rain (puddle reflections, Tokyo signage)
74. paper-texture daylight (craft/folk, torn-paper hills)
75. riso duotone poster (2-ink misregistration)
76. ink-wash mountains (monochrome sumi-e, fog bands)
77. thermal IR (false-color heat palette)
78. pastel dawn sky (soft gradients, slow clouds)
79. brutalist concrete (grey geometry, hard shadows)
80. cathedral interior (stained-glass god rays)
81. noir alley (fog, one streetlight, venetian-blind shadows)
82. coral reef at night (bioluminescent accents)
83. bamboo grove (vertical rhythm, swaying)
84. foggy moor with standing stones
85. mars colony dome (red exterior, warm interior glow)
86. grand ballroom (chandeliers, parquet perspective)
87. stormy ocean (lightning flashes on treble spikes)

## Floors (15)

Harvest-migrate from `autopilot/floors/` (9):
88. ★ arctic ice
89. ★ candyland
90. ★ cityscape street
91. ★ desert sand
92. ★ forest floor
93. ★ jungle floor
94. ★ space floor
95. ★ underwater floor
96. ★ volcano floor

New (6):
97. LED grid disco floor (cells fire on beat/fft bins)
98. checkerboard (perspective, tile-flip on beat)
99. water surface (reflections of what's above)
100. spinning vinyl record (label, grooves, tonearm)
101. circuit board (traces light up with signal pulses)
102. cloud floor (walking on clouds)

## Sets / props (20)

103. DJ booth
104. mirror ball (rotating specular dots swim over scene)
105. speaker stacks (cones visibly pump on bass)
106. laser rig (truss housing + moving beams)
107. ★ campfire (from draw_campfire.py)
108. palm trees (sway = wind + lowmid)
109. arcade cabinet (screen attract-mode glow)
110. stage trusses + moving heads
111. neon sign (TEXT param — say anything, flicker act)
112. ★ desert building (from draw_desert_building.py)
113. lighthouse (sweeping beam)
114. ferris wheel (cabins, beat-locked rotation)
115. fountain (particle water arcs)
116. street lamp + moths
117. grand piano (keys ripple with mid-band fft)
118. jukebox (bubbling tubes, glow)
119. torii gate
120. cactus cluster (saguaro trio, moods)
121. giant fan (drives wind for other assets' flags/hair)
122. inflatable tube dancer (wacky-waving, energy param)

## FX (20)

Harvest-migrate from `autopilot/fx/` (5):
123. ★ confetti
124. ★ fireworks
125. ★ bubbles
126. ★ balloons
127. ★ spotlights

New (15):
128. laser beams (fan/scan patterns, treble-reactive)
129. rain (+ground splashes)
130. snow (drift, accumulation hint)
131. fireflies (wander, synchronize blink over minutes)
132. fog machine (rolling low fog)
133. cherry petals
134. embers (rise from below, bass gusts)
135. floating lanterns (slow ascent)
136. shooting stars
137. god rays (volumetric shafts, dust)
138. dust motes (idle-friendly, catch the light)
139. lightning flashes (treble/bass triggered, with afterglow)
140. autumn leaves (tumble physics)
141. glitter sparkles (treble-driven)
142. heat shimmer (rippling distortion band)

## Post (15)

143. beat flash (K.pulse luminance kick)
144. feedback zoom (cached-buffer echo tunnel)
145. chromatic aberration (RGB fringe, bass-weighted)
146. vignette (breathing darkness)
147. scanlines / CRT curvature
148. halftone (dot-grid re-render, cheap sampled version)
149. film grain + gate weave
150. kaleidoscope mirror (2/4/6-way)
151. screen shake (bass impacts only)
152. slit-scan smear (row-delay buffer)
153. posterize / palette quantize
154. letterbox + film-burn edges (cinema act)
155. RGB glitch slices (horizontal displacement bursts)
156. pixelate mosaic (resolution pumps with intensity)
157. VHS wobble (tracking noise, timestamp)

## Genart (34)

Harvest-migrate from `autopilot/artscenes/` (4):
158. ★ strange attractor
159. ★ flow field
160. ★ L-system
161. ★ voronoi

New — one distinct palette discipline each (30):
162. voronoi triangles + 3D-look extrusion (Gene's canonical test phrase)
163. reaction-diffusion (coarse offscreen grid, organic spots)
164. metaballs / marching squares
165. recursive subdivision (Mondrian-ish, settles then reshuffles)
166. truchet tiles (rotate on beat, path highlights)
167. circle packing (grows, pops on bass)
168. differential growth lines
169. cellular automata (GoL + rule-morphing eras)
170. wave interference / moiré pool
171. animated dither field (Bayer↔noise, image emerges)
172. kinetic typography: word storm (letters assemble phrases)
173. kinetic typography: giant rotating pseudo-3D word
174. ASCII rain (resolves into shapes, Matrix-adjacent)
175. feedback-buffer painting (video-feedback blooms)
176. wireframe tunnel / wormhole (pseudo-3D fly-through)
177. isometric city generator (blocks grow per section)
178. spring-mesh cloth flag (wind + audio gusts)
179. hand-drawn wobbly-line doodle world (sketch aesthetic)
180. chladni plate sand patterns (mode changes per section)
181. phyllotaxis bloom (sunflower spirals)
182. DLA crystal growth
183. girih / Islamic tessellation unfolding
184. op-art depth illusion (Vasarely warp)
185. constellation map (lines draw, mythic figures glimmer)
186. solar-system orrery (scaled orbital speeds)
187. black-hole accretion disk
188. ukiyo-e great wave (parametric foam claws)
189. sand mandala (radial construction, dissolve act)
190. aurora ribbons full-frame
191. marbled-ink swirls (paper-marbling flow)

## Palettes (10)

192. neon club (magenta/cyan/UV)
193. sunset desert (sand/coral/dusk-purple)
194. arctic aurora (teal/green/ice-blue/ink)
195. deep sea (navy/biolum-cyan/violet)
196. pastel dawn (peach/lavender/powder-blue)
197. riso duotone (fluorescent red + blue, paper-white)
198. ink wash (paper, greys, one vermilion accent)
199. thermal IR (black-blue-magenta-orange-white ramp)
200. autumn folk (rust/ochre/moss/cream)
201. vaporwave (pink/teal/chrome)

---

**Phase 2 mechanics after sign-off**: work orders w/ mandatory style
constraints → harvest batch first → Workflow author waves (10–16 parallel)
into `assets/visual/inbox/` → serialized validate+index loop → commit every
batch → spot-compose full scene every ~50 assets.
