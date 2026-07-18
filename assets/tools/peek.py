#!/usr/bin/env python
"""Grab the live canvas right now -> PNG. On-demand eyes, no host timer."""
import argparse, base64, json, sys
import requests
ap = argparse.ArgumentParser(); ap.add_argument("--port", type=int, default=9976)
ap.add_argument("--out", default="/tmp/peek.png"); ap.add_argument("--w", type=int, default=420)
a = ap.parse_args()
code = ("(function(){var c=document.querySelector('canvas');if(!c)return 'NOCANVAS';"
        "var w=%d,h=Math.round(c.height*w/c.width);"
        "var o=document.createElement('canvas');o.width=w;o.height=h;"
        "o.getContext('2d').drawImage(c,0,0,w,h);"
        "return o.toDataURL('image/png');})()" % a.w)
r = requests.post(f"http://localhost:{a.port}/p5/send", json={"code": code}, timeout=20).json()
res = (r.get("response") or {}).get("result") or ""
if not res.startswith("data:image"):
    sys.exit(f"failed: {str(res)[:120]}")
open(a.out, "wb").write(base64.b64decode(res.split(",", 1)[1]))
print(a.out)
