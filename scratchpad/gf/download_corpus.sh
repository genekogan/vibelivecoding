#!/bin/bash
# Mechanical corpus download from MANIFEST.jsonl — free, no LLM tokens.
cd /Users/gene/Dev/livecode
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
python3 - <<'PY'
import json, os, hashlib, subprocess, re
ok=0; fail=0
for L in open("research/generative/MANIFEST.jsonl"):
    try: e=json.loads(L)
    except: continue
    u=e["url"]; sl=e.get("artist_slug","misc")
    d=f"research/generative/{sl}"; os.makedirs(d,exist_ok=True)
    ext=re.sub(r'\?.*$','',u).split('.')[-1].lower()
    if ext not in ("jpg","jpeg","png","webp","gif","avif"): ext="jpg"
    fn=f"{d}/{hashlib.md5(u.encode()).hexdigest()[:12]}.{ext}"
    if os.path.exists(fn) and os.path.getsize(fn)>2000: ok+=1; continue
    r=subprocess.run(["curl","-sL","--max-time","25","-A","Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36","-o",fn,u])
    if os.path.exists(fn) and os.path.getsize(fn)>2000: ok+=1
    else:
        fail+=1
        if os.path.exists(fn): os.remove(fn)
print(f"downloaded {ok} ok, {fail} failed")
PY
