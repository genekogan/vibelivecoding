#!/usr/bin/env python3
"""Generate assets/<domain>/index.jsonl + INDEX.md from verified assets.

Usage: python assets/tools/build_index.py [visual|music|all]   (default: all)

Only assets with a non-null "verified" stamp enter the index (palettes and
arcs are exempt). Grades from assets/review.jsonl are folded in — the latest
non-null grade per id wins. Skips inbox/. Generated files: never hand-edit.
Malformed asset files are listed to stderr and skipped; exit code 1.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"

VISUAL_KIND_DIRS = ["worlds", "floors", "sets", "subjects", "crowds",
                    "fx", "post", "genart", "palettes", "scenes"]
MUSIC_SLOTS = ["drums", "perc", "bass", "chords", "lead", "pad", "texture", "vox"]
CODE_KINDS = {"world", "floor", "set", "subject", "crowd", "fx", "post", "genart"}
VERIFY_EXEMPT = {"palette", "arc"}


def load_grades():
    """id -> latest non-null grade, in file (chronological) order."""
    grades = {}
    f = ASSETS / "review.jsonl"
    if f.exists():
        for line in f.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if isinstance(e, dict) and e.get("id") and e.get("grade") is not None:
                grades[e["id"]] = e["grade"]
    return grades


def read_asset(path, errors):
    try:
        a = json.loads(path.read_text())
        if not isinstance(a, dict):
            raise ValueError("top level is not an object")
        return a
    except (ValueError, OSError) as e:
        errors.append(f"{path.relative_to(ROOT)}: {e}")
        return None


def base_row(a, path):
    tags = a.get("tags") or []
    return {"id": a["id"], "kind": a["kind"],
            "tags": " ".join(str(t) for t in tags),
            "blurb": a.get("desc") or a.get("name") or "",
            "params": sorted((a.get("params") or {}).keys()),
            "path": str(path.relative_to(ROOT))}


def fmt_key(k):
    if isinstance(k, dict) and "root" in k:
        return f"{k.get('root', '?')}:{k.get('mode', '?')}"
    return k


def validate(a, path, errors, *, need_tags=True, need_desc=True, need_code=False,
             need_variants=False):
    probs = []
    if not a.get("id"):
        probs.append("missing id")
    if not a.get("kind"):
        probs.append("missing kind")
    if need_tags and not isinstance(a.get("tags"), list):
        probs.append("tags must be a list")
    if need_desc and not a.get("desc"):
        probs.append("missing desc")
    if need_code and not isinstance(a.get("code"), str):
        probs.append("code must be a string")
    elif need_code and "__SLOT__" not in a["code"]:
        probs.append("code lacks __SLOT__ token")
    if need_variants:
        c = a.get("code")
        if not (isinstance(c, dict) and all(isinstance(c.get(v), str)
                                            for v in ("sparse", "full", "peak"))):
            probs.append("code must be {sparse,full,peak} strings")
    if probs:
        errors.append(f"{path.relative_to(ROOT)}: " + "; ".join(probs))
        return False
    return True


def collect_visual(errors, grades):
    rows = []
    for d in VISUAL_KIND_DIRS:
        for p in sorted((ASSETS / "visual" / d).glob("*.json")):
            a = read_asset(p, errors)
            if a is None:
                continue
            kind = a.get("kind", "")
            if not validate(a, p, errors, need_code=kind in CODE_KINDS,
                            need_desc=kind != "scene", need_tags=kind != "scene"):
                continue
            if kind == "palette" and not isinstance(a.get("values"), dict):
                errors.append(f"{p.relative_to(ROOT)}: palette needs a values object")
                continue
            if kind not in VERIFY_EXEMPT and a.get("verified") is None:
                continue  # unverified: invisible, not an error
            r = base_row(a, p)
            if a.get("budget") is not None:
                r["budget"] = a["budget"]
            r["grade"] = grades.get(a["id"])
            rows.append(r)
    return rows


def collect_music(errors, grades):
    rows = []
    for slot_dir in MUSIC_SLOTS:
        for p in sorted((ASSETS / "music" / "stems" / slot_dir).glob("*.json")):
            a = read_asset(p, errors)
            if a is None:
                continue
            if not validate(a, p, errors, need_variants=True):
                continue
            slot = a.get("slot") or slot_dir
            if slot != slot_dir:
                errors.append(f"{p.relative_to(ROOT)}: slot '{slot}' but lives in stems/{slot_dir}/")
                continue
            if a.get("verified") is None:
                continue
            r = base_row(a, p)
            r["slot"] = slot
            for f in ("energy", "cps"):
                if a.get(f) is not None:
                    r[f] = a[f]
            if a.get("key") is not None:
                r["key"] = fmt_key(a["key"])
            r["grade"] = grades.get(a["id"])
            rows.append(r)
    for p in sorted((ASSETS / "music" / "kits").glob("*.json")):
        a = read_asset(p, errors)
        if a is None:
            continue
        a.setdefault("kind", "kit")
        if not validate(a, p, errors, need_desc=False):
            continue
        if a.get("verified") is None:
            continue
        r = base_row(a, p)
        for f in ("energy", "cps"):
            if a.get(f) is not None:
                r[f] = a[f]
        if a.get("key") is not None:
            r["key"] = fmt_key(a["key"])
        r["grade"] = grades.get(a["id"])
        rows.append(r)
    for p in sorted((ASSETS / "music" / "arcs").glob("*.json")):
        a = read_asset(p, errors)
        if a is None:
            continue
        a.setdefault("kind", "arc")
        if not validate(a, p, errors, need_tags=False, need_desc=False):
            continue
        r = base_row(a, p)  # arcs: verification-exempt, always included
        r["grade"] = grades.get(a["id"])
        rows.append(r)
    return rows


def write_domain(domain, rows):
    rows.sort(key=lambda r: (r["kind"], r["id"]))
    jp = ASSETS / domain / "index.jsonl"
    with open(jp, "w") as f:
        for r in rows:
            f.write(json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n")
    lines = [f"# {domain} asset index — GENERATED by assets/tools/build_index.py — do not edit",
             f"# {len(rows)} assets · id | kind | tags | grade | blurb", ""]
    for r in rows:
        g = "-" if r.get("grade") is None else str(r["grade"])
        lines.append(f"{r['id']} | {r['kind']} | {r['tags']} | {g} | {r['blurb']}")
    (ASSETS / domain / "INDEX.md").write_text("\n".join(lines) + "\n")
    print(f"{domain}: {len(rows)} assets -> {jp.relative_to(ROOT)}")


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which not in ("visual", "music", "all"):
        sys.exit(f"usage: {Path(sys.argv[0]).name} [visual|music|all]")
    errors = []
    grades = load_grades()
    if which in ("visual", "all"):
        write_domain("visual", collect_visual(errors, grades))
    if which in ("music", "all"):
        write_domain("music", collect_music(errors, grades))
    if errors:
        print(f"\n{len(errors)} malformed asset file(s) skipped:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
