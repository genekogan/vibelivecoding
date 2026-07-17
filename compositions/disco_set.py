"""Disco set — 8-section composition built from scenes.disco primitives.

Usage:
  python livecode.py            # in another shell
  python compositions/disco_set.py --step --save shows/unsorted/disco_set.show.json
  python autoplay.py --show shows/unsorted/disco_set.show.json --dwell 16beats
"""

import os
import sys

# allow `from scenes import ...` when run from anywhere
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scenes import disco
from scenes._common import Composition


with Composition("disco_set", default_dwell="16beats") as show:
    # Reset audio + visuals to a clean baseline
    show.hush()
    show.clear()
    show.cps(disco.CPS)

    # Music — each section adds one track
    show.mark("Disco: Drums")
    show.track(**disco.drums())

    show.mark("Disco: Bass")
    show.track(**disco.bass())

    show.mark("Disco: Strings")
    show.track(**disco.strings())

    show.mark("Disco: Wah")
    show.track(**disco.wah())

    show.mark("Disco: Clav")
    show.track(**disco.clav())

    show.mark("Disco: Shimmer")
    show.track(**disco.shimmer())

    # Visuals — bg first so it draws under everything
    show.mark("Disco: Floor + Beams")
    show.layer(**disco.bg())
    show.layer(**disco.floor())
    show.layer(**disco.beams())

    show.mark("Disco: Ball + Sparkles")
    show.layer(**disco.ball())
    show.layer(**disco.sparkles())
