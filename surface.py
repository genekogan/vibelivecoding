#!/usr/bin/env python3
"""Swap the livecode VISUAL surface between the p5 canvas and any three.js page —
with background preloading, ready-gated swaps, and strict one-renderer-at-a-time
resource discipline. Music is never touched.

  python3 surface.py show flock              # preload if needed, wait ready, swap in
  python3 surface.py preload flock           # warm it in the background, keep p5 live
  python3 surface.py p5                      # back to p5 (three frame parked, 0 cost)
  python3 surface.py show scene.014.negative-space-chapel   # any threejs catalog id
  python3 surface.py show "/lm/index.html?model=kalama--characters"
  python3 surface.py drop flock              # free its GPU/memory entirely
  python3 surface.py drop all
  python3 surface.py status                  # lifecycle of every frame + current surface
  python3 surface.py list                    # named scenes
  python3 surface.py flock                   # bare name == show (legacy shorthand)

Lifecycle (the resource story):
  WARMING  iframe at opacity:0, pointer-events:none — it ticks and loads assets in
           the background while p5 keeps performing. Auto-PARKS when ready if not shown.
  LIVE     visible; p5 is noLoop()'d + canvas hidden (near-zero p5 cost). The audio
           bridge keeps running (its own rAF) so three scenes stay audio-reactive.
  PARKED   display:none — Chromium stops rAF entirely (zero CPU/GPU), JS + GPU state
           kept, so re-show is instant. At most MAX_PARKED parked frames (LRU drop).
  DROPPED  removed from DOM — all memory freed.

Ready signal: same-origin pages set document.documentElement.dataset.appReady='true'
(the threejs browser and the lm scene pages do). Fallback: load event + settle-ms.

Retrieval: python3 assets/tools/find_three.py "loose prose" — see threejs/INDEX.md.
"""
import json, sys, time, urllib.request

BASE = "http://localhost:8766"
MAX_PARKED = 2
SHOW_TIMEOUT_S = 90         # flock cold-loads in ~15s; leave slack for cold caches

# name -> (url, settleMs fallback). Composite/heavy scenes; catalog scenes resolve by id.
SCENES = {
    "flock":   ("/lm/flock.html", 90000),            # Sporion Crossing — heavy (2 big GLBs)
    "flocklite": ("/lm/flock.html?light=1", 90000),  # skips the 70–120MB characters
    "cultivator": ("/lm/scenes.html?scene=1", 90000),
    "lantern":    ("/lm/scenes.html?scene=2", 90000),
    "recursion":  ("/lm/scenes.html?scene=3", 90000),
    "brasscastle": ("/lm/scenes.html?scene=4", 90000),
    "library5":   ("/lm/scenes.html?scene=5", 90000),
    "lmspace": ("/lm_space.html", 90000),            # martians hurtling through space
    "library": ("/lm_library.html", 90000),          # mycos in the bookshelf library
    "journey": ("/lm_journey.html", 90000),          # library -> space + encounters
    "stage":   ("/lm/stage.html", 90000),
    "splats":  ("/lm/splats.html", 90000),
    "yard":    ("/lm/sketchfab/gallery.html", 8000),  # sketchfab fly-through gallery
}

# The manager lives in livecode.html's window; installed idempotently.
INSTALL = r"""
window.__lcS2 = window.__lcS2 || (function(){
  var M = { frames:{}, live:null, maxParked:%(MAX_PARKED)d };
  function p5Pause(on){
    try {
      if (on) { noLoop(); } else { loop(); }
      document.querySelectorAll('canvas').forEach(function(c){
        if (!c.dataset.lmkeep) c.style.visibility = on ? 'hidden' : 'visible';
      });
    } catch(e) {}
  }
  function isReady(fr){
    try {
      var d = fr.el.contentDocument;
      if (d && d.documentElement && d.documentElement.dataset.appReady === 'true') return true;
    } catch(e) {}
    return !!fr.loadedAt && (performance.now() - fr.loadedAt > (fr.settleMs || 2500));
  }
  function park(fr){ fr.el.style.display='none'; fr.el.style.opacity='0';
    fr.el.style.pointerEvents='none'; fr.state='parked'; }
  function prune(){
    var parked = Object.keys(M.frames).filter(function(k){ return M.frames[k].state==='parked'; })
      .sort(function(a,b){ return (M.frames[a].ts||0)-(M.frames[b].ts||0); });
    while (parked.length > M.maxParked) {
      var k = parked.shift(); try { M.frames[k].el.remove(); } catch(e) {}
      delete M.frames[k];
    }
  }
  // auto-park warmed-but-unshown frames so preloads stop ticking once loaded
  setInterval(function(){
    Object.keys(M.frames).forEach(function(k){
      var fr = M.frames[k];
      if (fr.state === 'warming' && !fr.wantLive && isReady(fr)) { park(fr); prune(); }
    });
  }, 700);
  return {
    preload: function(key, url, settleMs){
      var fr = M.frames[key];
      if (fr) return fr.state;
      var f = document.createElement('iframe');
      f.id = 'lc-s2-' + key;
      f.style.cssText = 'position:fixed;inset:0;width:100vw;height:100vh;border:0;'+
        'z-index:9999;background:#04050c;opacity:0;transition:opacity .5s;pointer-events:none;';
      fr = { el:f, state:'warming', url:url, settleMs:settleMs, ts:Date.now() };
      f.addEventListener('load', function(){ fr.loadedAt = performance.now(); });
      f.src = url;
      document.body.appendChild(f);
      M.frames[key] = fr;
      return 'warming';
    },
    ready: function(key){
      var fr = M.frames[key]; if (!fr) return 'missing';
      if (fr.state === 'parked' || fr.state === 'live') return 'yes';
      return isReady(fr) ? 'yes' : 'no';
    },
    show: function(key){
      var fr = M.frames[key]; if (!fr) return 'missing';
      fr.wantLive = true;
      if (fr.state === 'warming' && !isReady(fr)) return 'warming';
      if (M.live && M.live !== key) {
        var c = M.frames[M.live];
        if (c) { park(c); c.ts = Date.now(); c.wantLive = false; }
      }
      fr.el.style.display = 'block';
      fr.el.style.pointerEvents = 'auto';
      requestAnimationFrame(function(){ fr.el.style.opacity = '1'; });
      fr.state = 'live'; fr.ts = Date.now(); M.live = key;
      p5Pause(true); prune();
      return 'live';
    },
    p5: function(){
      if (M.live) {
        var c = M.frames[M.live]; M.live = null;
        if (c) {
          c.wantLive = false;
          p5Pause(false);                      // p5 visible+looping under the fade
          c.el.style.opacity = '0'; c.el.style.pointerEvents = 'none';
          var el = c.el, fr = c;
          setTimeout(function(){ if (fr.state !== 'live') el.style.display = 'none'; }, 550);
          c.state = 'parked'; c.ts = Date.now();
        }
      } else { p5Pause(false); }
      prune();
      return 'p5';
    },
    drop: function(key){
      var keys = key === 'all' ? Object.keys(M.frames) : [key];
      var n = 0;
      keys.forEach(function(k){
        var fr = M.frames[k]; if (!fr) return;
        if (M.live === k) { M.live = null; p5Pause(false); }
        try { fr.el.remove(); } catch(e) {}
        delete M.frames[k]; n++;
      });
      return 'dropped:' + n;
    },
    status: function(){
      var out = { live: M.live || 'p5', frames: {} };
      Object.keys(M.frames).forEach(function(k){
        var fr = M.frames[k];
        out.frames[k] = { state: fr.state, url: fr.url, ready: isReady(fr) };
      });
      return JSON.stringify(out);
    }
  };
})();
""" % {"MAX_PARKED": MAX_PARKED}


def send_p5(code):
    r = urllib.request.Request(BASE + "/p5/send",
        data=json.dumps({"code": code}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    return json.load(urllib.request.urlopen(r, timeout=8))


def call(expr):
    r = send_p5(INSTALL + "\n" + expr)
    return (r.get("response") or {}).get("result")


def resolve(target):
    """name | threejs scene id | raw url  ->  (key, url, settleMs)"""
    if target in SCENES:
        url, settle = SCENES[target]
        return target, url, settle
    if target.startswith("scene."):
        url = ("/threejs/browser/index.html?stageOnly=1&scene=" + target
               + "&audioSource=live-rendered-master")
        return target.replace(".", "_").replace("-", "_"), url, 120000  # appReady is authoritative
    key = "".join(ch if ch.isalnum() else "_" for ch in target)[-48:]
    return key, target, 2500


def show(target):
    key, url, settle = resolve(target)
    call(f"window.__lcS2.preload({json.dumps(key)}, {json.dumps(url)}, {settle})")
    t0 = time.time()
    while time.time() - t0 < SHOW_TIMEOUT_S:
        state = call(f"window.__lcS2.show({json.dumps(key)})")
        if state == "live":
            print(f"live: {key} ({url})  [{time.time()-t0:.1f}s]")
            return
        if state == "missing":
            sys.exit(f"frame vanished while waiting: {key}")
        time.sleep(0.6)
    sys.exit(f"timed out waiting for {key} to become ready ({SHOW_TIMEOUT_S}s)")


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "list":
        print("status:", call("window.__lcS2.status()"))
        for k, (u, _) in SCENES.items():
            print(f"  {k:11s} {u}")
    elif cmd == "status":
        print(call("window.__lcS2.status()"))
    elif cmd == "p5":
        print(call("window.__lcS2.p5()"))
    elif cmd == "preload" and len(sys.argv) > 2:
        key, url, settle = resolve(sys.argv[2])
        print(key, call(f"window.__lcS2.preload({json.dumps(key)}, {json.dumps(url)}, {settle})"))
    elif cmd == "show" and len(sys.argv) > 2:
        show(sys.argv[2])
    elif cmd == "drop" and len(sys.argv) > 2:
        key = sys.argv[2] if sys.argv[2] == "all" else resolve(sys.argv[2])[0]
        print(call(f"window.__lcS2.drop({json.dumps(key)})"))
    elif cmd == "three" and len(sys.argv) > 2:   # legacy alias for show <url>
        show(sys.argv[2])
    else:
        show(cmd)                                 # bare scene name / id / url
    return


if __name__ == "__main__":
    main()
