"""Scene library — reusable, pure code-string generators.

Every scene function returns a dict like {"name": str, "code": str} that
can be passed directly to /strudel/track or /p5/layer payloads.

Scenes have no side effects — they don't call the server. Compositions
import scenes and post their output.

Reproducibility: scenes are inlined at composition time. A .show.json
captures the literal output strings, so old shows keep playing even if
scenes/ evolves.
"""
