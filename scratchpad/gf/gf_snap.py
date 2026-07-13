#!/usr/bin/env python3
"""gf_snap.py — deploy asset(s) to the live canvas, capture t & t+8s frames,
compute motion + luminance, save frames for a contact sheet. The orchestrator's
'eyes'. Serial (one canvas) — never run concurrently with validate.py.

Usage:
  python scratchpad/gf/gf_snap.py --outdir DIR ASSET.json [ASSET.json ...]
  python scratchpad/gf/gf_snap.py --outdir DIR --glob 'assets/visual/inbox/*.json'
Writes DIR/<id>__a.png, DIR/<id>__b.png, DIR/metrics.jsonl
"""
import argparse, glob as _glob, json, shutil, time, sys
from pathlib import Path
import requests
from PIL import Image, ImageChops

BASE = "http://localhost:8766"
SNAP = Path("autopilot/snapshots/latest.png")
KIND_SLOT = {"world":"bg","genart":"bg","floor":"floor","set":"setA",
             "subject":"subA","crowd":"crowd","fx":"fxA","post":"post"}

def post(p, b):
    try: return requests.post(BASE+p, json=b, timeout=15).json()
    except Exception as e: return {"err": str(e)}
def get(p):
    try: return requests.get(BASE+p, timeout=10).json()
    except Exception as e: return {"err": str(e)}

def ensure_clk():
    st = get("/status")
    if "__clk" not in (st.get("tracks") or []):
        post("/strudel/track", {"name":"__clk","code":'sound("bd").gain(0.001).play()'})
        time.sleep(1.5)
    # engine never inits window.state.P — do it so P.<slot> pokes don't throw on null
    post("/p5/send", {"code": "window.state.P = window.state.P || {};"})
    time.sleep(0.2)

def grab320():
    for _ in range(4):
        try:
            with Image.open(SNAP) as im:
                im = im.convert("L"); w,h = im.size
                return im.resize((320, max(1, round(h*320/w))))
        except Exception:
            time.sleep(0.8)
    return None

def save_full(dest):
    for _ in range(4):
        try:
            shutil.copy(SNAP, dest); return True
        except Exception:
            time.sleep(0.6)
    return False

def mean_diff(a,b):
    if b.size!=a.size: b=b.resize(a.size)
    h=ImageChops.difference(a,b).histogram(); n=a.size[0]*a.size[1]
    return sum(i*c for i,c in enumerate(h))/n/255.0
def mean_lum(img):
    h=img.histogram(); return sum(i*c for i,c in enumerate(h))/(img.size[0]*img.size[1])/255.0

def snap_one(path, outdir):
    a = json.loads(Path(path).read_text())
    aid = a["id"]; kind = a["kind"]; slot = KIND_SLOT.get(kind,"bg")
    bed = kind not in ("world","genart")
    # clean slate
    post("/p5/clear", {})
    post("/p5/state", {"key":slot,"value":None}); post("/p5/state", {"key":f"P.{slot}","value":None})
    time.sleep(0.4)
    err0 = len(get("/errors").get("errors",[]))
    if bed: post("/p5/layer", {"name":"bg","code":"background(240,30,12);"})
    r = post("/p5/layer", {"name":slot,"code":a["code"].replace("__SLOT__",slot)})
    time.sleep(4.6)
    errs = get("/errors").get("errors",[])[err0:]
    hits = [e for e in errs if f"[{slot}]" in e.get("message","") or f'"{slot}"' in e.get("message","")]
    fps = (get("/p5/read?key=clk") or {}).get("value",{}).get("fps",0)
    save_full(outdir/f"{aid}__a_full.png")
    ia = grab320(); time.sleep(8); ib = grab320()
    save_full(outdir/f"{aid}__b_full.png")
    # COLOR downscaled copies for the contact sheet (grab320 is grayscale for motion calc only)
    for tag in ("a", "b"):
        fp = outdir/f"{aid}__{tag}_full.png"
        try:
            with Image.open(fp) as im:
                im = im.convert("RGB"); w,h = im.size
                im.resize((340, max(1, round(h*340/w)))).save(outdir/f"{aid}__{tag}.png")
        except Exception: pass
    motion = mean_diff(ia,ib) if (ia and ib) else -1
    lum = mean_lum(ib) if ib else -1
    rec = {"id":aid,"kind":kind,"fps":round(fps,1),"motion":round(motion,4),
           "lum":round(lum,3),"deploy_err":(hits[0]["message"][:120] if hits else None)}
    post("/p5/remove", {"name":slot})
    if bed: post("/p5/remove", {"name":"bg"})
    post("/p5/state", {"key":slot,"value":None}); post("/p5/state", {"key":f"P.{slot}","value":None})
    return rec

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--glob")
    ap.add_argument("paths", nargs="*")
    args = ap.parse_args()
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    paths = list(args.paths)
    if args.glob: paths += sorted(_glob.glob(args.glob))
    if not paths: sys.exit("no assets")
    ensure_clk()
    mf = open(outdir/"metrics.jsonl","a")
    for i,p in enumerate(paths):
        try:
            rec = snap_one(p, outdir)
        except Exception as e:
            rec = {"id":Path(p).stem,"error":str(e)[:150]}
        mf.write(json.dumps(rec)+"\n"); mf.flush()
        flag=""
        if rec.get("error"): flag="ERR "+rec["error"]
        elif rec.get("deploy_err"): flag="DEPLOY-ERR "+rec["deploy_err"]
        else:
            m,l=rec.get("motion",-1),rec.get("lum",-1)
            if m<=0.004: flag="STATIC"
            elif m>=0.35: flag="STROBE"
            elif not(0.02<=l<=0.92): flag="LUM"
            else: flag="ok"
        print(f"[{i+1}/{len(paths)}] {rec['id']:34s} m={rec.get('motion','?')} l={rec.get('lum','?')} fps={rec.get('fps','?')}  {flag}", flush=True)
    mf.close()
    post("/p5/clear", {})
    print("done ->", outdir)

if __name__=="__main__": main()
