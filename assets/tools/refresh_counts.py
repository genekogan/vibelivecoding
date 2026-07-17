#!/usr/bin/env python
"""Rewrite the catalog-count lines in the docs from the generated index.jsonl.

    python assets/tools/refresh_counts.py                  # patch both domains
    python assets/tools/refresh_counts.py --domain visual  # just one
    python assets/tools/refresh_counts.py --check          # exit 1 if stale (CI-able)

Hand-maintained counts rot the moment a factory batch lands: README.md and
AGENTS.md both advertised "407 stems · 44 kits" while the index held 696; the
visual docs advertised "166 pieces" over a catalog three times that size.
Run this after build_index.py so the prose can't drift from the data.

The regexes below match the CANONICAL count-line format each doc uses, so this
is idempotent and safe to re-run. If a doc's prose is rewritten and the pattern
stops matching, the tool prints a WARN rather than silently doing nothing.
"""
import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Visual families, in the canonical display order used across the docs.
VIS_FAMILIES = ["genart", "world", "subject", "fx", "set",
                "floor", "post", "crowd", "palette"]


def _rows(domain):
    idx = ROOT / "assets" / domain / "index.jsonl"
    if not idx.exists():
        return []
    return [json.loads(l) for l in idx.read_text().splitlines() if l.strip()]


def music_stats():
    rows = _rows("music")
    kind = collections.Counter(r["kind"] for r in rows)
    genres = {r["id"].split(".")[1] for r in rows if r["kind"] == "stem"}
    return {
        "stems": kind["stem"], "kits": kind["kit"], "arcs": kind["arc"],
        "genres": len(genres), "indexed": len(rows),
    }


def visual_stats():
    rows = _rows("visual")
    fam = collections.Counter(r["id"].split(".")[0] for r in rows)
    st = {f: fam.get(f, 0) for f in VIS_FAMILIES}
    st["indexed"] = len(rows)
    # "166 genart · 25 world · …" one-liner reused by several docs
    st["breakdown"] = " · ".join(f"{st[f]} {f}" for f in VIS_FAMILIES if st[f])
    return st


def music_summary(st):
    return (f"{st['stems']} stems · {st['kits']} kits · {st['arcs']} arcs · "
            f"{st['genres']} genres · {st['indexed']} indexed")


def visual_summary(st):
    return f"{st['indexed']} indexed assets — {st['breakdown']}"


# (path, regex, replacement-template) per domain. The regex must match whatever
# numbers are there now, so re-running is a no-op once the docs are canonical.
TARGETS = {
    "music": [
        ("assets/music/README.md",
         r"\*\*Current catalog:\*\* \d+ stems · \d+ kits · \d+ arcs · \d+ genres · \d+ indexed\s*\nassets\.",
         "**Current catalog:** {stems} stems · {kits} kits · {arcs} arcs · {genres} genres · {indexed} indexed\nassets."),
        ("AGENTS.md",
         r"\(\d+ stems · \d+ kits · \d+ arcs · \d+ genres\)",
         "({stems} stems · {kits} kits · {arcs} arcs · {genres} genres)"),
    ],
    "visual": [
        # .claude/skills/p5.md — the "what's in the catalog now" line
        (".claude/skills/p5.md",
         r"\*\*Current catalog:\*\* \d+ indexed assets — [^\n]+",
         "**Current catalog:** {indexed} indexed assets — {breakdown}"),
        # AGENTS.md — the visual catalog pointer in the docs table
        ("AGENTS.md",
         r"\*\*What's in the genart catalog now\*\* \(\d+ genart of \d+ indexed visual assets\)",
         "**What's in the genart catalog now** ({genart} genart of {indexed} indexed visual assets)"),
        # AGENTS.md — the visual catalog prose blurb
        ("AGENTS.md",
         r"\(\d+ genart · \d+ world · \d+ subject · [^)]*?\d+ indexed\)",
         "({genart} genart · {world} world · {subject} subject · {fx} fx · {set} set · "
         "{floor} floor · {post} post · {crowd} crowd · {palette} palette · {indexed} indexed)"),
        # research/generative/FINAL_REPORT.md — headline count
        ("research/generative/FINAL_REPORT.md",
         r"\*\*Catalog: \d+ genart of \d+ indexed visual assets\*\*",
         "**Catalog: {genart} genart of {indexed} indexed visual assets**"),
    ],
}

STATS = {"music": (music_stats, music_summary), "visual": (visual_stats, visual_summary)}


def run_domain(domain, check):
    stat_fn, summ_fn = STATS[domain]
    st = stat_fn()
    if not st.get("indexed"):
        print(f"{domain}: no index.jsonl rows — skipped")
        return []
    stale = []
    for rel, pat, tmpl in TARGETS[domain]:
        p = ROOT / rel
        if not p.exists():
            print(f"WARN {rel}: missing")
            continue
        text = p.read_text()
        if not re.search(pat, text):
            print(f"WARN {rel}: {domain} count line not found — pattern drifted?")
            continue
        new = re.sub(pat, tmpl.format(**st), text)
        if new == text:
            continue
        stale.append(rel)
        if not check:
            p.write_text(new)
    print(f"{domain}: {summ_fn(st)}")
    verb = "stale" if check else "updated"
    print(f"{domain}: {verb}: {', '.join(stale) if stale else 'none — docs match the index'}")
    return stale


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="report staleness without writing; exit 1 if stale")
    ap.add_argument("--domain", choices=["music", "visual", "all"], default="all")
    a = ap.parse_args()
    domains = ["music", "visual"] if a.domain == "all" else [a.domain]
    stale = []
    for d in domains:
        stale += run_domain(d, a.check)
    if a.check and stale:
        sys.exit(1)


if __name__ == "__main__":
    main()
