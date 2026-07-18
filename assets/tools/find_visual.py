#!/usr/bin/env python3
"""find_visual.py — ranked retrieval over the visual catalog from loose prose.

    python3 assets/tools/find_visual.py "underwater scene with a submarine and pirates"
    python3 assets/tools/find_visual.py --scene "misty campfire night in the forest"
    python3 assets/tools/find_visual.py --kind subject "sea creature"
    python3 assets/tools/find_visual.py -n 20 "neon rain city"

Why not grep: multi-word grep ORs flood (every row matches *some* word) and ANDs
miss (no row matches *all* words). This scores each asset per query term
(tags > id/name > blurb, synonym matches count less), boosts assets covering
several distinct terms, and — crucially — REPORTS TERMS NOTHING COVERS, so a
performing agent knows which element to hand-write instead of firing a wrong
near-match. --scene groups winners by render slot into a fireable stack.

Stdlib only; ~50 ms on the 800-asset index.
"""
import argparse, json, re, sys
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "visual" / "index.jsonl"

STOP = set("""a an the and or of with for in on at to from into make making create her his
scene visual visuals background please something stuff thing want need like really cool nice
some show me it that this then add put set piece asset style styled looking look feel vibe
""".split())

# curated fallback expansions — a synonym hit scores lower than a direct hit
SYN = {
    "undersea": ["underwater", "ocean", "sea", "marine"],
    "underwater": ["ocean", "sea", "marine", "aquatic"],
    "ocean": ["sea", "underwater", "marine"],
    "sea": ["ocean", "underwater", "marine"],
    "creature": ["animal", "fish", "monster", "beast"],
    "animal": ["creature", "bird", "fish", "cat", "dog"],
    "pirate": ["galleon", "ship", "skull", "nautical", "treasure"],
    "ship": ["boat", "sail", "nautical", "vessel"],
    "boat": ["ship", "sail", "nautical"],
    "space": ["cosmos", "cosmic", "galaxy", "stars", "nebula"],
    "cosmos": ["space", "galaxy", "stars", "nebula"],
    "forest": ["trees", "woods", "woodland", "pines"],
    "woods": ["forest", "trees"],
    "night": ["dark", "moon", "stars", "nocturnal"],
    "rain": ["storm", "wet", "drizzle", "umbrella"],
    "city": ["urban", "skyline", "street", "downtown", "metropolis"],
    "club": ["rave", "disco", "nightclub", "dance"],
    "rave": ["club", "techno", "laser", "strobe-safe"],
    "party": ["celebration", "festival", "confetti", "disco"],
    "fire": ["flame", "ember", "burning", "campfire"],
    "snow": ["winter", "ice", "frozen", "blizzard"],
    "winter": ["snow", "ice", "frozen", "cold"],
    "desert": ["dunes", "sand", "mesa", "arid"],
    "mountain": ["peak", "alpine", "ridge", "summit"],
    "flower": ["floral", "blossom", "bloom", "petal"],
    "ghost": ["spooky", "haunted", "spirit", "eerie"],
    "spooky": ["ghost", "haunted", "skull", "eerie", "halloween"],
    "robot": ["mech", "android", "machine", "cyborg"],
    "wizard": ["magic", "sorcerer", "spell", "mystic"],
    "magic": ["wizard", "mystic", "sparkle", "enchanted"],
    "retro": ["vintage", "80s", "70s", "nostalgic", "vhs"],
    "psychedelic": ["trippy", "kaleidoscope", "acid", "surreal"],
    "surreal": ["dream", "dreamlike", "psychedelic", "strange"],
    "calm": ["serene", "peaceful", "gentle", "ambient", "zen"],
    "energetic": ["intense", "fast", "wild", "driving"],
    "bird": ["birds", "flock", "wings", "flying"],
    "dance": ["dancer", "dancers", "dancing"],
    "sun": ["sunset", "sunrise", "golden", "dawn", "dusk"],
    "sunset": ["dusk", "golden", "horizon"],
    "moon": ["lunar", "night", "moonlit"],
    "star": ["stars", "starfield", "constellation", "night"],
    "water": ["ocean", "sea", "river", "lake", "ripple"],
    "glow": ["luminous", "neon", "glowing", "light"],
    "neon": ["glow", "cyber", "synthwave", "electric"],
    "cyber": ["neon", "cyberpunk", "futuristic", "tech"],
    "tropical": ["palm", "island", "beach", "jungle"],
    "beach": ["coast", "shore", "sand", "tropical"],
    "car": ["cars", "vehicle", "racing", "driving"],
    "train": ["railway", "locomotive", "rail"],
    "plane": ["airplane", "aircraft", "flying", "jet"],
    "cat": ["kitten", "feline"],
    "dog": ["puppy", "canine"],
    "horse": ["pony", "equine"],
    "skeleton": ["skull", "bones", "spooky"],
    "monster": ["creature", "beast", "kaiju"],
}

KIND_SLOT = {"world": "bg", "genart": "bg", "floor": "floor", "set": "setA/B",
             "subject": "subA/B/C", "crowd": "crowd", "fx": "fxA/B",
             "post": "post", "palette": "palette"}
SLOT_ORDER = ["bg", "floor", "setA/B", "subA/B/C", "crowd", "fxA/B", "post", "palette"]


def stem(w):
    for suf in ("ies", "ing", "ed", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: len(w) - len(suf)]
    return w


def tokens(text):
    return [w for w in re.findall(r"[a-z0-9][a-z0-9'-]*", text.lower()) if w not in STOP]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("query", nargs="+", help="loose search prose")
    ap.add_argument("-n", type=int, default=12, help="max results (default 12)")
    ap.add_argument("--kind", help="restrict to kind (world/subject/fx/post/floor/set/crowd/palette/genart)")
    ap.add_argument("--scene", action="store_true", help="group top hits by render slot into a fireable stack")
    args = ap.parse_args()

    qwords = tokens(" ".join(args.query))
    if not qwords:
        sys.exit("query reduced to nothing after stopwords")
    qterms = {}  # stemmed term -> set of stemmed synonym terms
    for w in qwords:
        sw = stem(w)
        qterms.setdefault(sw, set())
        for s in SYN.get(w, []) + SYN.get(sw, []):
            qterms[sw].add(stem(s))

    rows = [json.loads(l) for l in INDEX.open()]
    if args.kind:
        rows = [r for r in rows if r.get("kind") == args.kind]

    scored = []
    term_hits = {tm: 0 for tm in qterms}
    for r in rows:
        raw_tags = r.get("tags", [])
        if isinstance(raw_tags, str): raw_tags = raw_tags.split()
        tagset = {stem(w) for tag in raw_tags for w in tokens(tag)}
        idname = {stem(w) for w in tokens(r["id"].replace(".", " ") + " " + r.get("name", ""))}
        blurb = {stem(w) for w in tokens(r.get("blurb", r.get("desc", "")))}
        score, matched = 0.0, []
        for tm, syns in qterms.items():
            best = 0.0
            if tm in idname: best = 5.0      # literal word in the asset's own name
            elif tm in tagset: best = 3.0
            elif tm in blurb: best = 1.5
            elif syns & tagset: best = 1.2
            elif syns & idname: best = 1.0
            elif syns & blurb: best = 0.6
            if best:
                score += best
                matched.append(tm + ("" if best >= 1.5 else "~"))
                if best >= 1.2:  # direct hit or synonym-tag hit = concept covered
                    term_hits[tm] += 1
        if score:
            strong = sum(1 for m in matched if not m.endswith("~"))
            score *= 1 + 0.35 * max(0, strong - 1)  # boost only for multiple DIRECT hits
            scored.append((score, r, matched))
    scored.sort(key=lambda x: -x[0])

    uncovered = [tm for tm, n in term_hits.items() if n == 0]
    if uncovered:
        print(f"!! no direct match for: {', '.join(uncovered)} — hand-write that element "
              f"or drop it (synonym fallbacks marked with ~)\n")

    if args.scene:
        by_slot = {}
        for score, r, matched in scored:
            slot = KIND_SLOT.get(r["kind"], r["kind"])
            cap = 3 if slot == "subA/B/C" else 2
            by_slot.setdefault(slot, [])
            if len(by_slot[slot]) < cap:
                by_slot[slot].append((score, r, matched))
        print("scene stack (fire with assets/tools/fire_visual.py <id>):")
        for slot in SLOT_ORDER:
            for score, r, matched in by_slot.get(slot, []):
                print(f"  {slot:9s} {score:5.1f}  {r['id']:32s} [{','.join(matched)}]  {r.get('blurb','')[:76]}")
    else:
        for score, r, matched in scored[: args.n]:
            print(f"{score:5.1f}  {r['id']:34s} {r['kind']:8s} [{','.join(matched)}]  {r.get('blurb','')[:70]}")
    if not scored:
        print("no matches — try different words, or grep assets/visual/INDEX.md directly")


if __name__ == "__main__":
    main()
