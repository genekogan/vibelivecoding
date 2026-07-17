#!/bin/bash
# One validation sweep for the visual factory.
#   validate inbox -> for anything that has failed TWICE, move to graveyard/
#   -> rebuild index -> commit catalog + index.
# Idempotent; safe to run repeatedly as authors fill the inbox.
set -uo pipefail
cd /Users/gene/Dev/livecode
GY=assets/visual/graveyard
mkdir -p "$GY"

echo "=== sweep $(date +%H:%M:%S) — inbox: $(ls assets/visual/inbox/*.json 2>/dev/null | wc -l | tr -d ' ') ==="
python3 assets/tools/validate.py --inbox visual 2>&1 | grep -E "^(PASS|FAIL)" || true

# graveyard: any inbox asset whose last_fail count (tracked in a sidecar) hit 2
python3 - <<'PY'
import json, glob, os
GY = "assets/visual/graveyard"
track_path = "assets/visual/graveyard/.failcounts.json"
track = {}
if os.path.exists(track_path):
    try: track = json.load(open(track_path))
    except Exception: track = {}
for f in glob.glob("assets/visual/inbox/*.json"):
    try:
        a = json.load(open(f))
    except Exception:
        continue  # half-written; leave it for next sweep
    lf = a.get("last_fail")
    if not lf:
        continue
    aid = a.get("id", os.path.basename(f))
    track[aid] = track.get(aid, 0) + 1
    if track[aid] >= 2:
        dest = os.path.join(GY, os.path.basename(f))
        os.rename(f, dest)
        print(f"GRAVEYARD {aid} (failed {track[aid]}x): {lf.get('gate')}: {str(lf.get('detail'))[:70]}")
json.dump(track, open(track_path, "w"), indent=1)
PY

python3 assets/tools/build_index.py visual 2>&1 | grep -E "assets ->" || true

# commit whatever moved into the catalog
git add assets/visual/worlds assets/visual/floors assets/visual/sets \
        assets/visual/subjects assets/visual/crowds assets/visual/fx \
        assets/visual/post assets/visual/genart assets/visual/palettes \
        assets/visual/index.jsonl assets/visual/INDEX.md 2>/dev/null
if ! git diff --cached --quiet 2>/dev/null; then
  n=$(for d in worlds floors sets subjects crowds fx post genart palettes; do ls assets/visual/$d/*.json 2>/dev/null; done | wc -l | tr -d ' ')
  git commit -q -m "visual factory: validated batch (catalog now $n assets)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" --no-gpg-sign
  echo "committed — catalog total: $n"
else
  echo "nothing new to commit"
fi
