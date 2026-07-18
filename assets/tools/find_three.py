#!/usr/bin/env python3
"""find_three.py — ranked retrieval over the three.js index from loose prose.

    python3 assets/tools/find_three.py "cosmic migration home to mars"
    python3 assets/tools/find_three.py --kind scene "cathedral of light"
    python3 assets/tools/find_three.py --kind sketchfab "overgrown ruins" -n 20
    python3 assets/tools/find_three.py --fire "the flock"     # print fire commands only

Covers all four tributaries in one query: 200 generated threejs catalog scenes
(kind=scene), the LM composite pages (lmscene: flock, the five scenes, …),
110 Little Martians archive models (lmmodel), 594 Sketchfab GLBs (sketchfab).

Same scoring as find_visual.py: literal id/name > tags > blurb, curated synonym
fallbacks (~), coverage boost only for direct hits, and an explicit warning for
query concepts nothing covers. Each hit prints its `fire` incantation — scenes
and lmscenes go straight onto the canvas via surface.py; sketchfab/lmmodel rows
give the GLB path (building blocks) plus a browsable viewer URL.

Rebuild the index after touching registries: python3 assets/tools/build_three_index.py
"""
import argparse, json, re, sys
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent.parent / "threejs" / "index.jsonl"

STOP = set("""a an the and or of with for in on at to from into make making create her his
scene visual visuals background please something stuff thing want need like really cool nice
some show me it that this then add put set piece asset style styled looking look feel vibe
""".split())

SYN = {
    "undersea": ["underwater", "ocean", "sea", "marine"],
    "underwater": ["ocean", "sea", "marine", "aquatic"],
    "ocean": ["sea", "underwater", "marine"],
    "sea": ["ocean", "underwater", "marine"],
    "creature": ["animal", "fish", "monster", "beast", "specimen"],
    "animal": ["creature", "bird", "fish", "cat", "dog", "specimen"],
    "space": ["cosmos", "cosmic", "galaxy", "stars", "nebula", "mars", "planets"],
    "cosmos": ["space", "galaxy", "stars", "nebula"],
    "martian": ["mars", "martians", "flock"],
    "forest": ["trees", "woods", "woodland", "pines", "moss"],
    "night": ["dark", "moon", "stars", "nocturnal"],
    "city": ["urban", "skyline", "street", "downtown"],
    "ruin": ["ruins", "weathered", "abandoned", "overgrown", "church"],
    "overgrown": ["moss", "ruins", "weathered", "vines"],
    "cave": ["cavern", "grotto", "underground", "tubes", "gruta"],
    "castle": ["fortress", "palace", "tower", "brass"],
    "ghost": ["spooky", "haunted", "spirit", "eerie"],
    "robot": ["mech", "android", "machine", "steampunk"],
    "magic": ["mystic", "sparkle", "enchanted", "reliquary"],
    "retro": ["vintage", "brass", "victorian", "steampunk"],
    "surreal": ["dream", "dreamlike", "strange", "impossible"],
    "calm": ["serene", "peaceful", "gentle", "ambient", "zen"],
    "statue": ["sculpture", "buddha", "angel", "stone", "monument"],
    "museum": ["specimen", "gallery", "hall", "collection"],
    "plant": ["flower", "moss", "tree", "cactus", "botanical", "specimen"],
    "mushroom": ["fungus", "fungal", "spore", "mycos"],
    "planet": ["mars", "moon", "terrain", "crater", "cosmic"],
    "temple": ["shrine", "church", "cathedral", "sacred", "buddha"],
    "ship": ["boat", "submarine", "airship", "dirigible", "vessel"],
    "architecture": ["building", "structure", "temple", "tower", "hall"],
}

KIND_LABEL = {"scene": "threejs scene", "lmscene": "LM scene", "lmmodel": "LM model",
              "sketchfab": "sketchfab GLB"}


def stem(w):
    for suf in ("ies", "ing", "ed", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: len(w) - len(suf)]
    return w


def tokens(text):
    return [w for w in re.findall(r"[a-z0-9][a-z0-9'-]*", text.lower()) if w not in STOP]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("query", nargs="+")
    ap.add_argument("-n", type=int, default=12)
    ap.add_argument("--kind", help="scene / lmscene / lmmodel / sketchfab")
    ap.add_argument("--fire", action="store_true", help="print fire commands only")
    args = ap.parse_args()

    qwords = tokens(" ".join(args.query))
    if not qwords:
        sys.exit("query reduced to nothing after stopwords")
    qterms = {}
    for w in qwords:
        sw = stem(w)
        qterms.setdefault(sw, set())
        for s in SYN.get(w, []) + SYN.get(sw, []):
            qterms[sw].add(stem(s))

    rows = [json.loads(l) for l in INDEX.open()]
    if args.kind:
        rows = [r for r in rows if r.get("kind") == args.kind]

    scored, term_hits = [], {tm: 0 for tm in qterms}
    for r in rows:
        raw_tags = r.get("tags", "")
        if isinstance(raw_tags, str):
            raw_tags = raw_tags.split()
        tagset = {stem(w) for tag in raw_tags for w in tokens(tag)}
        idname = {stem(w) for w in tokens(r["id"].replace(".", " ").replace("-", " ")
                                          + " " + r.get("name", ""))}
        blurb = {stem(w) for w in tokens(r.get("blurb", ""))}
        score, matched = 0.0, []
        for tm, syns in qterms.items():
            best = 0.0
            if tm in idname: best = 5.0
            elif tm in tagset: best = 3.0
            elif tm in blurb: best = 1.5
            elif syns & tagset: best = 1.2
            elif syns & idname: best = 1.0
            elif syns & blurb: best = 0.6
            if best:
                score += best
                matched.append(tm + ("" if best >= 1.5 else "~"))
                if best >= 1.2:
                    term_hits[tm] += 1
        if score:
            strong = sum(1 for m in matched if not m.endswith("~"))
            score *= 1 + 0.35 * max(0, strong - 1)
            scored.append((score, r, matched))
    scored.sort(key=lambda x: -x[0])

    uncovered = [tm for tm, n in term_hits.items() if n == 0]
    if uncovered:
        print(f"!! no direct match for: {', '.join(uncovered)} — hand-build that element "
              f"or drop it (synonym fallbacks marked with ~)\n")

    for score, r, matched in scored[: args.n]:
        if args.fire:
            print(r["fire"])
        else:
            kl = KIND_LABEL.get(r["kind"], r["kind"])
            print(f"{score:5.1f}  {r['id']:44s} {kl:13s} [{','.join(matched)}]  {r.get('blurb','')[:64]}")
            print(f"       fire: {r['fire']}")
    if not scored:
        print("no matches — try different words, or grep threejs/INDEX.md directly")


if __name__ == "__main__":
    main()
