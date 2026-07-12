#!/usr/bin/env python3
"""gf_sheet.py — assemble captured a-frames into one labeled contact-sheet PNG
so the orchestrator can vision-critique a whole batch in one Read.

Usage: python scratchpad/gf/gf_sheet.py --dir DIR --out SHEET.png [--cols 4] [--ab]
Border: green=passes mechanical floors, red=fails (static/strobe/lum/err).
Label: id · m=motion l=lum fps.
"""
import argparse, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def load_metrics(d):
    m={}
    f=Path(d)/"metrics.jsonl"
    if f.exists():
        for line in f.read_text().splitlines():
            line=line.strip()
            if not line: continue
            try: r=json.loads(line)
            except: continue
            m[r.get("id")]=r  # last wins
    return m

def font(sz):
    for p in ["/System/Library/Fonts/Supplemental/Arial.ttf",
              "/System/Library/Fonts/Helvetica.ttc",
              "/Library/Fonts/Arial.ttf"]:
        try: return ImageFont.truetype(p, sz)
        except: pass
    return ImageFont.load_default()

def status(r):
    if not r: return "nofile", (120,120,120)
    if r.get("error"): return "ERR", (220,40,40)
    if r.get("deploy_err"): return "DEPLOY-ERR", (220,40,40)
    m,l=r.get("motion",-1),r.get("lum",-1)
    if m<=0.004: return "STATIC", (220,120,20)
    if m>=0.35: return "STROBE", (220,120,20)
    if not(0.02<=l<=0.92): return "LUM", (220,120,20)
    return "ok", (40,180,60)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--ab", action="store_true", help="show a|b frames side by side")
    ap.add_argument("--ids", help="comma-separated id filter")
    args=ap.parse_args()
    d=Path(args.dir); metrics=load_metrics(d)
    ids=sorted({p.name.split("__")[0] for p in d.glob("*__a.png")})
    if args.ids:
        want=set(args.ids.split(",")); ids=[i for i in ids if i in want]
    if not ids:
        print("no frames in", d); return
    CW = 340 if not args.ab else 660
    ratio = 9/16
    cellw, cellh = CW, int(CW*ratio*(0.5 if args.ab else 1) if args.ab else CW*ratio)
    if args.ab: cellh=int((CW/2)*ratio)
    lab=26
    cols=args.cols; rows=(len(ids)+cols-1)//cols
    pad=6
    W=cols*(cellw+pad)+pad; H=rows*(cellh+lab+pad)+pad
    sheet=Image.new("RGB",(W,H),(18,18,20)); dr=ImageDraw.Draw(sheet); fnt=font(15); fnt2=font(13)
    for idx,aid in enumerate(ids):
        r=idx//cols; c=idx%cols
        x=pad+c*(cellw+pad); y=pad+r*(cellh+lab+pad)
        st,col=status(metrics.get(aid))
        try:
            a=Image.open(d/f"{aid}__a.png").convert("RGB")
            if args.ab and (d/f"{aid}__b.png").exists():
                b=Image.open(d/f"{aid}__b.png").convert("RGB")
                hw=cellw//2
                a=a.resize((hw,cellh)); b=b.resize((cellw-hw,cellh))
                sheet.paste(a,(x,y+lab)); sheet.paste(b,(x+hw,y+lab))
            else:
                a=a.resize((cellw,cellh)); sheet.paste(a,(x,y+lab))
        except Exception:
            dr.rectangle([x,y+lab,x+cellw,y+cellh+lab], fill=(40,40,44))
        dr.rectangle([x,y+lab,x+cellw-1,y+cellh+lab-1], outline=col, width=3)
        m=metrics.get(aid,{})
        info=f"m={m.get('motion','?')} l={m.get('lum','?')} {st}"
        dr.text((x+3,y+1), aid, fill=(235,235,235), font=fnt)
        dr.text((x+3,y+lab-13), info, fill=col, font=fnt2)
    sheet.save(args.out)
    print(f"sheet: {len(ids)} cells -> {args.out} ({W}x{H})")

if __name__=="__main__": main()
