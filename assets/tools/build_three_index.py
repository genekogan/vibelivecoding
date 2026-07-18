#!/usr/bin/env python3
"""build_three_index.py — merge every three.js-side asset into one retrieval index.

Sources:
  threejs/browser/generated/scene-index.json   200 generated catalog scenes
  (hand-authored list below)                    LM composite scenes (flock, 5 scenes, …)
  lm/manifest.json                              110 Little Martians archive models
  lm/sketchfab/catalog.json                     594 borrowed Sketchfab models

Outputs:
  threejs/index.jsonl   one JSON row per asset: {id, kind, tags, blurb, url, fire, extra}
  threejs/INDEX.md      grep-friendly one-line-per-asset view

kind: scene (threejs catalog) · lmscene (composite page) · lmmodel · sketchfab
fire: the surface.py incantation that puts it on the livecode canvas.

Run after regenerating the scene registry or touching lm manifests:
  python3 assets/tools/build_three_index.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_JSONL = ROOT / "threejs" / "index.jsonl"
OUT_MD = ROOT / "threejs" / "INDEX.md"

# LM composite scenes — the hand-built pages. Keep in sync with surface.py SCENES.
LM_SCENES = [
    ("lmscene.flock", "flock", "Sporion Crossing — the flock",
     "~24 little martians (all named characters + cleanest ceramic heads) migrate together through a starfield on the long road home to Mars; Mars grows ahead with a fresnel atmosphere rim, Moon slides past, ringed Saturn and Jupiter in the deep field; members drift, bank, and turn to face each other and talk with a teal communion glow. HEAVY (~15s cold load). Params: ?n=12 flock size, ?light=1 skips the two 70-120MB characters.",
     "flock martians space stars mars migration crossing journey ceramic characters cosmic home planets saturn moon bloom"),
    ("lmscene.flocklite", "flocklite", "Sporion Crossing (light)",
     "The flock scene with ?light=1 — skips the two 70-120MB characters for a fast (~4s) load; same migration, Mars approach, planets and communion behavior.",
     "flock martians space fast light migration mars cosmic"),
    ("lmscene.cultivator", "cultivator", "The Cultivator (Verdelis / Eden Dome)",
     "Verdelis in Eden Dome at twilight: geodesic shell, mossy floor, the Golden Gate Park tree scan as her twisted root-vine, bioluminescent lamp-stalks, a glow-spore swarm pulsing with her mood; camera dollies through the garden then orbits her.",
     "verdelis eden dome garden twilight geodesic moss bioluminescent spores plants cozy green cultivator"),
    ("lmscene.lantern", "lantern", "The Lantern and the Flame (Shuijing / Enceladus)",
     "Shuijing in the Enceladus dark: vent chimneys, chemosynthetic coral, marine snow, tiger-stripe fissures shafting light through the ice; the guest breathes inside the icosahedral cage; camera rises from the vent floor and circles the lantern.",
     "shuijing enceladus ocean dark vents coral ice underwater deep lantern blue eerie marine"),
    ("lmscene.recursion", "recursion", "A Depth in the Recursion (Kweku / lava tubes)",
     "Kweku's lava tubes: mirrored Rio gruta scans form a root-cave corridor, floating Tchokwe/sona line-patterns, three Kwekus at three scales materialize and face you as a torchlit rail carries you deeper.",
     "kweku cave lava tubes maze recursion corridor torchlit dark patterns sona mystery underground"),
    ("lmscene.brasscastle", "brasscastle", "Brass & Sulfuric Acid (Ada / Venus castle)",
     "Ada's floating castle above the Venus cloud deck: ceramic temples and minarets on a floating island, brass machine glints, acid haze.",
     "ada venus castle brass floating island temples steampunk clouds acid amber"),
    ("lmscene.library5", "library5", "Scene 5 (Kalama)",
     "Kalama composite scene from the five-scenes page (key 5).",
     "kalama fire volcanic scene composite"),
    ("lmscene.lmspace", "lmspace", "Martians through space",
     "Named martians hurtling through a starfield — lightweight space flythrough page (lm_space.html), audio-reactive via the parent bridge.",
     "martians space starfield flythrough fast light audio-reactive"),
    ("lmscene.library", "library", "Mycos in the library",
     "Mycos on a pedestal in a bookshelf library (lm_library.html) — quiet interior vignette.",
     "mycos library books shelf interior pedestal quiet"),
    ("lmscene.journey", "journey", "Mycos' journey",
     "Mycos leaps from the library into space and has encounters along the way (lm_journey.html); space restarts on spacebar.",
     "mycos journey library space leap encounters narrative"),
    ("lmscene.stage", "stage", "LM stage",
     "Stage page with simulation fast-forward support (lm/stage.html?sim=SS).",
     "stage martians performance"),
    ("lmscene.splats", "splats", "Gaussian splat scenes",
     "Gaussian-splat demo scenes incl. Ada (lm/splats.html) — photoreal splat captures.",
     "splats gaussian photoreal ada capture volumetric"),
    ("lmscene.yard", "yard", "The Yard (sketchfab gallery)",
     "Fly-through gallery of the borrowed Sketchfab collection (lm/sketchfab/gallery.html).",
     "sketchfab gallery yard flythrough museum collection browse"),
]


def rows():
    out = []
    # 1. threejs catalog scenes
    idx = json.load(open(ROOT / "threejs/browser/generated/scene-index.json"))
    for r in idx["records"]:
        url = (f"/threejs/browser/index.html?stageOnly=1&scene={r['id']}"
               "&audioSource=live-rendered-master")
        out.append({
            "id": r["id"], "kind": "scene",
            "name": r["title"],
            "tags": " ".join(r.get("tags", [])),
            "blurb": r.get("thesis", ""),
            "url": url,
            "fire": f"python3 surface.py show {r['id']}",
            "extra": {"collection": r.get("collection"), "ordinal": r.get("ordinal"),
                      "acts": r.get("actIds", []), "parameterCount": r.get("parameterCount")},
        })
    # 2. LM composite scenes
    for sid, key, name, blurb, tags in LM_SCENES:
        out.append({
            "id": sid, "kind": "lmscene", "name": name, "tags": tags, "blurb": blurb,
            "url": None, "fire": f"python3 surface.py show {key}", "extra": {"surfaceKey": key},
        })
    # 3. LM archive models
    m = json.load(open(ROOT / "lm/manifest.json"))
    for r in m["models"]:
        url = f"/lm/index.html?model={r['id']}"
        out.append({
            "id": f"lmmodel.{r['id']}", "kind": "lmmodel",
            "name": r["title"],
            "tags": f"{r['category']} {r.get('group','')} little-martians ceramic",
            "blurb": r.get("notes", "") or r["title"],
            "url": url,
            "fire": f"python3 surface.py show \"{url}\"",
            "extra": {"path": f"lm/{r['path']}", "web": r.get("web"), "bytes": r.get("bytes")},
        })
    # 4. sketchfab models
    c = json.load(open(ROOT / "lm/sketchfab/catalog.json"))
    for r in c["models"]:
        use = r.get("useFor") or []
        tier = r.get("tier", "")          # prop | environment | cosmic
        terms = r.get("searchTerms") or []
        out.append({
            "id": f"sketchfab.{r['id']}", "kind": "sketchfab",
            "name": r["title"],
            "tags": " ".join(use) + " " + " ".join(terms[:12])
                    + f" {r.get('category','')} {tier} {r.get('sceneRole','')}",
            "blurb": r.get("desc") or r.get("description") or r["title"],
            "url": f"/lm/sketchfab/lore.html#{r['id']}",
            "fire": f"# GLB at lm/sketchfab/{r['path']} — load in a scene; browse: /lm/sketchfab/lore.html",
            "extra": {"path": f"lm/sketchfab/{r['path']}", "tier": tier,
                      "license": r.get("licenseSlug"), "author": r.get("author"),
                      "bytes": r.get("bytes"), "lmNote": r.get("lmNote")},
        })
    return out


def main():
    rs = rows()
    with open(OUT_JSONL, "w") as f:
        for r in rs:
            f.write(json.dumps(r) + "\n")
    kinds = {}
    for r in rs:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    counts = " · ".join(f"{v} {k}" for k, v in sorted(kinds.items()))
    with open(OUT_MD, "w") as f:
        f.write("# three.js asset index — GENERATED by assets/tools/build_three_index.py — do not edit\n")
        f.write(f"# {len(rs)} assets · {counts}\n")
        f.write("# id | kind | tags | blurb — retrieval: assets/tools/find_three.py\n\n")
        for r in sorted(rs, key=lambda r: (r["kind"], r["id"])):
            f.write(f"{r['id']} | {r['kind']} | {r['tags']} | {r['blurb']}\n")
    print(f"three: {len(rs)} assets -> {OUT_JSONL.relative_to(ROOT)} ({counts})")


if __name__ == "__main__":
    main()
