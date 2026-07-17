#!/usr/bin/env python3
"""prune_graded.py — apply Gene's taste grades from grades.jsonl.

Grades (set in browse.html, persisted to assets/music/grades.jsonl):
  bad  -> remove from the active catalog (moved to assets/music/graveyard/,
          NOT hard-deleted, so the content survives as a taste/RL signal).
  ok   -> keep in the vocabulary (no action).
  good -> keep + flagged outstanding (no action; use for taste RL).

Latest grade per id wins. Default is a DRY RUN — pass --apply to move files.
After applying it rebuilds the index so pruned assets leave index.jsonl.

  python assets/tools/prune_graded.py             # dry run: show the plan
  python assets/tools/prune_graded.py --apply     # move bad -> graveyard, reindex

Safety: if a `bad` STEM is still referenced by a kept (ok/good/ungraded) kit,
it is reported as a CONFLICT and SKIPPED (never silently breaks a kept kit).
Grade a conflicting kit `bad` too, or re-point it, then re-run.
"""
import argparse, glob, json, os, shutil, subprocess, sys, collections

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "music"))
TOOLS = os.path.dirname(os.path.abspath(__file__))


def load_grades():
    g, p = {}, os.path.join(ROOT, "grades.jsonl")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("id") and r.get("grade"):
                g[r["id"]] = r["grade"]     # latest wins (file is append-only, in order)
    return g


def all_assets():
    """id -> (path, doc) for every stem/kit/arc in the active catalog."""
    out = {}
    for sub in ("stems/*", "kits", "arcs"):
        for p in glob.glob(os.path.join(ROOT, sub, "*.json")):
            try:
                d = json.load(open(p))
            except Exception:
                continue
            if d.get("id"):
                out[d["id"]] = (p, d)
    return out


def kind_dir(doc):
    k = doc.get("kind") or doc.get("format", "")
    if "kit" in str(k):
        return "kits"
    if "arc" in str(k) or doc.get("sections"):
        return "arcs"
    return os.path.join("stems", doc.get("slot", "misc"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--apply", action="store_true", help="actually move bad assets to graveyard + reindex")
    args = ap.parse_args()

    grades = load_grades()
    assets = all_assets()
    counts = collections.Counter(grades.values())
    bad = [i for i, g in grades.items() if g == "bad"]
    good = [i for i, g in grades.items() if g == "good"]

    print(f"grades.jsonl: {len(grades)} graded  (★good {counts['good']} · ○ok {counts['ok']} · ✗bad {counts['bad']})")
    if good:
        print("\n★ GOOD (outstanding — taste signal to reinforce):")
        for i in sorted(good):
            print(f"   {i}")

    # kits kept (not graded bad) and the stems they depend on
    kept_kit_stems = collections.defaultdict(list)   # stem_id -> [kit_id,...]
    for aid, (p, d) in assets.items():
        if d.get("kind") == "kit" and grades.get(aid) != "bad":
            for slot, sid in (d.get("stems") or {}).items():
                kept_kit_stems[sid].append(aid)

    to_move, conflicts, missing = [], [], []
    for aid in bad:
        if aid not in assets:
            missing.append(aid); continue
        p, d = assets[aid]
        if d.get("kind") == "stem" and kept_kit_stems.get(aid):
            conflicts.append((aid, kept_kit_stems[aid]))
        else:
            to_move.append((aid, p, d))

    print(f"\n✗ BAD to remove: {len(to_move)}  (→ assets/music/graveyard/)")
    for aid, p, d in to_move:
        print(f"   {aid}")
    if conflicts:
        print(f"\n⚠ CONFLICTS — bad stems still used by kept kits (SKIPPED; grade those kits bad or re-point them):")
        for aid, kits in conflicts:
            print(f"   {aid}  ← used by {', '.join(kits)}")
    if missing:
        print(f"\n(note: {len(missing)} bad-graded ids not found in catalog — already gone: {', '.join(missing)})")

    if not args.apply:
        print(f"\nDRY RUN. Re-run with --apply to move {len(to_move)} asset(s) to graveyard and reindex.")
        return

    moved = 0
    for aid, p, d in to_move:
        dest_dir = os.path.join(ROOT, "graveyard", kind_dir(d))
        os.makedirs(dest_dir, exist_ok=True)
        shutil.move(p, os.path.join(dest_dir, os.path.basename(p)))
        moved += 1
    print(f"\nmoved {moved} asset(s) to graveyard.")
    if moved:
        r = subprocess.run(["python", "build_index.py", "music"], cwd=TOOLS.replace("/tools", ""),
                           capture_output=True, text=True)
        print("reindex:", (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout+r.stderr).strip() else "done")
    print("Done. Commit the result. (grades.jsonl is the durable taste record — keep it.)")


if __name__ == "__main__":
    main()
