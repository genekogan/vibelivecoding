# Visual Factory — resumable state

_Last updated: 2026-07-11 ~10:00 ET, mid-run._

## Where things are

- **Catalog (validated, in `assets/visual/<kind>/`): ~55** — all 50 subjects +
  5 crowds. Growing as the sweeper validates the remaining fleet's output.
- **In flight**: the "remaining fleet" (Workflow `factory-workflow-remaining.js`)
  is authoring the 146 non-subject orders (7 crowds, 25 worlds, 15 floors, 20
  sets, 20 fx, 15 post, 34 genart, 10 palettes) into `assets/visual/inbox/`.
- **Graveyard** (`assets/visual/graveyard/`): assets that failed validation
  twice. `train` is the notable straggler (motion too subtle even after a
  rescue). `.failcounts.json` there tracks per-id fail counts.

## The running machinery (all local, keep alive)

| Process | What | Restart |
|---|---|---|
| `livecode.py` (:8766) | server + canvas | already running (also a music copy on :9766 — leave it) |
| `autopilot_host.py --interval 3` | Playwright browser writing `autopilot/snapshots/latest.png` | babysitter auto-restarts it |
| babysitter (`scratchpad/babysitter.sh`, nohup) | relaunches the visual host if it dies | `nohup bash <path> &` |
| sweeper daemon (`scratchpad/sweeper-daemon.sh`, nohup) | loops `assets/tools/sweep.sh`: validate inbox → graveyard 2x-fails → index → commit | `nohup bash <path> &`; log `/tmp/lc_sweeper.log` |

NOTE: persistent **Monitor**-based watchers keep getting SIGURG-killed (exit
144) in this environment (likely the parallel music session's process sweeps) —
use **nohup detached scripts** instead, which survive.

## How to resume authoring after a quota/session-limit stop

1. Recompute what's left (excludes anything already validated into the catalog):
   ```bash
   python3 - <<'PY'
   import json,glob
   orders=json.load(open('assets/prompts/work-orders-v1.json'))
   KD={'world':'worlds','floor':'floors','set':'sets','subject':'subjects','crowd':'crowds','fx':'fx','post':'post','genart':'genart','palette':'palettes'}
   done=set()
   for d in KD.values():
       for f in glob.glob(f'assets/visual/{d}/*.json'):
           try: done.add(json.load(open(f))['id'])
           except: pass
   rem=[o for o in orders if o['id'] not in done]
   json.dump(rem, open('assets/prompts/work-orders-remaining.json','w'), indent=1)
   print(len(rem),'remaining')
   PY
   ```
2. Rebuild the batch list (see the loop in the session that generated
   `assets/prompts/remaining-batches.json`) and launch
   `factory-workflow-remaining.js` via the Workflow tool, passing the batches as
   `args` (the script does `JSON.parse(args)` if it arrives as a string).
3. Make sure the sweeper daemon + babysitter are running (table above).

## Key learnings baked into `assets/prompts/author-brief.md`

- **Motion gate**: subjects must be hero-sized (0.40–0.55× min(w,h)) and
  displace the silhouette; purely beat-locked motion can re-phase at 8s (cps
  ~0.5 → 8s = 16 beats) and read as static — always add a **real-time (K.t)
  motion floor** (drift/scroll/roll/wander) that never re-aligns.
- **Aesthetic mandate**: escape the cute-cartoon default — commit to a
  non-cartoon anchor style, ≥1 abstracted style option per asset, texture over
  flat fill, wider mood/palette range.
- **Params gate**: first two numeric params must visibly change at max; put
  scale (max ≥1.8) or energy/density first, never hue (360 wraps to red).
- Common bugs: shadowing p5 globals (`line`, `fill`…) with local vars → blank
  render (motion 0.0000); undeclared vars → same.

## Grading (after the run)
`python assets/tools/review.py visual` — deploys each asset live, keys 1–5 to
grade. Grades → `assets/review.jsonl`, folded into the index. Second pass:
improve/replace ≤2, make variations of 5s, rescue the graveyard.
