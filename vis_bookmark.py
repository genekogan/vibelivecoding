#!/usr/bin/env python3
"""Bookmark / restore livecode VISUAL scenes (layers only — never touches music).
Usage:
  python vis_bookmark.py save <name> [--title "..."] [--note "..."]
  python vis_bookmark.py load <name|path>
  python vis_bookmark.py list
Bookmarks live in shows/visuals/<name>.visuals.json (format: livecode-visuals-v1).
"""
import sys, json, os, glob, urllib.request

HOST="http://localhost:8766"
DIR=os.path.join(os.path.dirname(os.path.abspath(__file__)),"shows","visuals")

def _get(path):
    return json.load(urllib.request.urlopen(HOST+path, timeout=5))
def _post(path, body):
    r=urllib.request.Request(HOST+path, data=json.dumps(body).encode(),
        headers={"Content-Type":"application/json"}, method="POST")
    return urllib.request.urlopen(r, timeout=5).read()

def save(name, title=None, note=None):
    st=_get("/state")
    layers=st.get("layers",{})  # dict name->code, insertion-ordered
    doc={"format":"livecode-visuals-v1","name":name,
         "title":title or name,"note":note or "",
         "layers":[{"name":k,"code":v} for k,v in layers.items()]}
    os.makedirs(DIR,exist_ok=True)
    p=os.path.join(DIR,f"{name}.visuals.json")
    json.dump(doc,open(p,"w"),indent=1)
    print(f"saved {len(doc['layers'])} layers -> {p}")

def load(ref):
    p=ref if os.path.exists(ref) else os.path.join(DIR,f"{ref}.visuals.json")
    doc=json.load(open(p))
    _post("/p5/clear",{})
    for L in doc["layers"]:
        _post("/p5/layer",{"name":L["name"],"code":L["code"]})
    print(f"loaded {len(doc['layers'])} layers from {os.path.basename(p)} — {doc.get('title','')}")

def ls():
    for p in sorted(glob.glob(os.path.join(DIR,"*.visuals.json"))):
        d=json.load(open(p))
        print(f"{d['name']:24} {len(d['layers']):2}L  {d.get('title','')}  {('· '+d['note']) if d.get('note') else ''}")

if __name__=="__main__":
    a=sys.argv
    if len(a)<2: print(__doc__); sys.exit(1)
    cmd=a[1]
    if cmd=="save":
        kw={}; name=a[2]
        for i,t in enumerate(a):
            if t=="--title": kw["title"]=a[i+1]
            if t=="--note": kw["note"]=a[i+1]
        save(name,**kw)
    elif cmd=="load": load(a[2])
    elif cmd=="list": ls()
    else: print(__doc__)
