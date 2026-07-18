#!/usr/bin/env python3
"""Swap the livecode VISUAL surface between the p5 canvas and any three.js page,
seamlessly, without touching the music.

The p5 engine keeps running (hidden) underneath a full-screen iframe overlay, so
returning to p5 is instant and every layer keeps its state. Three.js pages served
same-origin (under /lm/ or the repo root) can read window.parent.state.audio for
audio-reactivity; cross-origin URLs still display but can't read the audio bridge.

  python3 surface.py p5                 # back to the p5 canvas
  python3 surface.py flock              # -> /lm/flock.html   (named scene)
  python3 surface.py lmspace            # -> /lm_space.html
  python3 surface.py three <url|path>   # any URL or same-origin path
  python3 surface.py list               # show named scenes + current

Named scenes live in the SCENES dict below — add your own three.js pages there.
"""
import sys, json, urllib.request

BASE = "http://localhost:8766"

# name -> URL (same-origin paths preferred so the audio bridge works)
SCENES = {
    "flock":   "/lm/flock.html",       # Sporion Crossing — the flock (bloom, 24 heads)
    "lmspace": "/lm_space.html",        # martians hurtling through space
    "library": "/lm_library.html",      # mycos on a pedestal in a bookshelf library
    "journey": "/lm_journey.html",      # mycos leaps from the library into space + encounters
    "stage":   "/lm/stage.html",
    "scenes":  "/lm/scenes.html",
    "splats":  "/lm/splats.html",
}

# Idempotent helper installed once in the page; subsequent calls just invoke it.
INSTALL = r"""
window.__lcSurface = window.__lcSurface || function(url){
  var cs = document.querySelectorAll('canvas');
  var f = document.getElementById('lc-surface-frame');
  if(!url){
    if(f){ f.style.opacity='0'; setTimeout(function(){ if(f) f.remove(); }, 450); }
    cs.forEach(function(c){ if(!c.dataset.lmkeep) c.style.visibility='visible'; });
    window.__lcSurfaceCur = 'p5';
    return 'p5';
  }
  cs.forEach(function(c){ if(!c.dataset.lmkeep) c.style.visibility='hidden'; });
  if(!f){
    f = document.createElement('iframe');
    f.id = 'lc-surface-frame';
    f.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;border:0;'+
                      'z-index:9999;background:#04050c;opacity:0;transition:opacity .5s;';
    document.body.appendChild(f);
  }
  f.src = url + (url.indexOf('?')>=0?'&':'?') + 'v=' + Date.now();
  requestAnimationFrame(function(){ f.style.opacity='1'; });
  window.__lcSurfaceCur = url;
  return url;
};
"""

def send_p5(code):
    r = urllib.request.Request(BASE + "/p5/send",
        data=json.dumps({"code": code}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    return json.load(urllib.request.urlopen(r, timeout=6))

def switch(target):
    arg = "null" if target is None else json.dumps(target)
    return send_p5(INSTALL + f"\nwindow.__lcSurface({arg});")

def current():
    r = send_p5("window.__lcSurfaceCur || 'p5'")
    return (r.get("response") or {}).get("result", "?")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "list":
        cur = current()
        print(f"current surface: {cur}\n")
        for k, v in SCENES.items():
            print(f"  {k:10} -> {v}")
        print(f"  {'p5':10} -> p5 canvas")
    elif cmd == "p5":
        switch(None); print("→ p5 canvas")
    elif cmd == "three":
        if len(sys.argv) < 3: sys.exit("usage: surface.py three <url|path>")
        url = sys.argv[2]; switch(url); print(f"→ {url}")
    elif cmd in SCENES:
        switch(SCENES[cmd]); print(f"→ {cmd} ({SCENES[cmd]})")
    else:
        # treat as raw url/path
        switch(cmd); print(f"→ {cmd}")
