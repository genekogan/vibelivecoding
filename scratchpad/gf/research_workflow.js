export const meta = {
  name: 'gf-research',
  description: 'Generative-art research corpus: fan out across the artist roster, write study cards + collect image URLs',
  phases: [{ title: 'Research', detail: 'one agent per artist group writes cards + manifest entries' }],
}

// Roster grouped for parallel fan-out (~5 artists/agent). Adjacents welcome.
const GROUPS = [
  ["Marius Watz","Manolo Gamboa Naon","Kjetil Golid","Etienne Jacob (bleuje)","Casey Reas"],
  ["Jared Tarbell","Robert Hodgin (flight404)","Joshua Davis","Karsten Schmidt (toxi)","Anders Hoff (inconvergent)"],
  ["Dave Whyte (beesandbombs)","Jonathan McCabe","Tom Beddard (subBlue)","Paul Prudence","Frederik Vanhoutte (wblut)"],
  ["Julien Gachadoat (v3ga)","Matt Pearson","Matt DesLauriers","Kazumasa Teshigawara (qubibi)","Dextro"],
  ["Leander Herzog","Saskia Freeke","Nicolas Barradeau","Reza Ali","Sage Jenson (mxsage)"],
  ["Andy Lomas","Mark J. Stock","Nervous System (Jesse Louis-Rosenberg & Jessica Rosenkrantz)","Dirk Koy","Markos Kay"],
  ["Alida Sun","Shunsuke Takawo","Nicolas Sassoon","Kim Asendorf","Zach Lieberman"],
  ["Memo Akten","Scott Draves (electric sheep)","Andreas Gysin","Jürg Lehni","Antoine Schmitt"],
  ["Holger Lippmann","Pascal Dombis","Eno Henze","Yugo Nakamura (yugop)","Rafaël Rozendaal"],
  ["Jan Vantomme","Bruno Imbrizi","Marcin Ignac","Tim Rodenbröker","Raphaël de Courville","Leo Villareal"],
  ["Íñigo Quílez (iq)","David Hoskins","Shane (Shadertoy)","Fabrice Neyret","Kali (Shadertoy)"],
  ["Martijn Steinrucken (BigWings / The Art of Code)","Evvvvil","Flopine","Nusan","nimitz (Shadertoy)"],
  ["knighty (Shadertoy)","srtuss","Leon Denise (leon)","Xor (Shadertoy)","kishimisu","diatribes"],
  ["Szenia Zadvornykh (zadvorsky)","Ryoji Ikeda","Ryoichi Kurokawa","Carsten Nicolai (Alva Noto)"],
  ["Robert Henke","Tarik Barri","Mathieu Le Sourd (Maotik)","Herman Kolgen"],
  ["Norimichi Hirakawa","Daito Manabe","William Mapan","Zancan","Piter Pasma","Tyler Hobbs"],
]

const SCHEMA = {
  type: "object",
  properties: {
    cards_written: { type: "array", items: { type: "string" }, description: "artist slugs whose card .md was written" },
    images: {
      type: "array",
      description: "direct image URLs collected (prefer hotlinkable: Wikimedia, Are.na S3/imgix, OpenProcessing, artist CDN, fxhash IPFS)",
      items: {
        type: "object",
        properties: {
          artist: { type: "string" },
          title: { type: "string" },
          url: { type: "string" },
          technique_tags: { type: "array", items: { type: "string" } },
        },
        required: ["artist","url"],
      },
    },
    notes: { type: "string", description: "artists under-covered or unreachable" },
  },
  required: ["cards_written","images"],
}

phase('Research')
const results = await parallel(GROUPS.map((group, gi) => () =>
  agent(
`You are a generative-art researcher building a private STUDY corpus for a p5.js live-coding VJ engine (learning use, organized locally, not redistributed).

Your artists (research each one's RANGE — series and eras, not just their one famous piece):
${group.map(a => "  - "+a).join("\n")}

For EACH artist do two things:

1. WRITE a study card to research/generative/_cards/<slug>.md  (slug = lowercase, spaces/punct→'_', drop parenthetical handles into the slug, e.g. "Etienne Jacob (bleuje)" -> etienne_jacob). Sections, each 1-4 sentences, CONCRETE and technical (a coder must be able to reproduce the LOOK from your card):
   # <Artist name>
   - **Bio/context**: who they are, medium (Processing/p5, plotter, GLSL/Shadertoy, installation…), era.
   - **Signature techniques**: the actual algorithms/processes (e.g. "curl-noise advected particle fields", "domain-warped fBm + iq cosine palettes", "differential line growth", "reaction-diffusion", "flocking", "physarum", "pixel sorting", "quasicrystal gratings", "IFS flame"). Name the math where you know it.
   - **Palette logic**: how they use color (limited riso duotone? iq cosine gradients? desaturated near-monochrome? CMYK? thermal false-color?).
   - **Mark-making / texture**: stroke quality, grain, halftone, additive glow, flat vs modeled.
   - **Motion/temporal qualities** (crucial for us — everything must animate): how the work evolves (slow drift, advection, growth, feedback zoom, beat-like pulse, section arcs).
   - **Key works**: 3-6 named series/pieces with a phrase each.
   - **Links**: their site/portfolio, OpenProcessing/fxhash/Shadertoy/Are.na/Behance/Vimeo.

2. COLLECT 5-12 DIRECT image URLs of their work per artist (URLs that end in .jpg/.png/.webp or resolve to an image — prefer HOTLINKABLE hosts: Wikimedia Commons, Are.na block images (S3/imgix), OpenProcessing thumbnails/fullsize, the artist's own CDN/portfolio, fxhash IPFS gateways, museum/gallery pages). Verify a few resolve with a quick \`curl -sI -A "Mozilla/5.0" <url>\` (look for 200 + image content-type) when unsure. Add them to your returned "images" array with technique_tags. Do NOT download bytes yourself — just collect good URLs; a mechanical pass downloads them.

Use WebSearch + WebFetch + curl. Are.na is an excellent source: the public API \`https://api.are.na/v2/search/channels?q=<term>\` and \`https://api.are.na/v2/channels/<slug>/contents?per=50\` return JSON with image.original.url on S3 — search channels like "generative art", "reaction diffusion", "flow field", "physarum", "shader", each artist's name.

Return JSON per the schema: cards_written (slugs), images (the collected URLs), notes (anyone you couldn't cover). Be thorough but do not get stuck — timebox each artist.`,
    { label: `research:${gi}`, phase: 'Research', schema: SCHEMA }
  ).then(r => r).catch(() => null)
))

// Collect manifest from structured returns (no file-write races).
const fs_lines = []
let cards = 0, imgs = 0
for (const r of results) {
  if (!r) continue
  cards += (r.cards_written || []).length
  for (const im of (r.images || [])) {
    if (!im || !im.url) continue
    fs_lines.push(JSON.stringify(im))
    imgs++
  }
}
log(`research: ${cards} cards, ${imgs} image URLs collected across ${GROUPS.length} groups`)
return { cards, imgs, manifest_lines: fs_lines, notes: results.filter(Boolean).map(r=>r.notes).filter(Boolean) }
