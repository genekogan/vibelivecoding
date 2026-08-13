#!/usr/bin/env python3
"""Setlists — a textual protocol for recombining show sections.

A show is a recorded timeline; a SECTION is its atomic unit (mark → mark).
A setlist is a plain-text file that builds a NEW show out of sections drawn
from any existing shows, in any order, with per-section overrides. Fork a set
by copying the file; recombine by reordering lines; reparameterize with
key=value; version it in git like any text.

Format (one section per line):

    name: Friday closing set          # optional headers
    desc: gqom into the dino drop
    seam: 4                           # default landing bar-line for playback

    disco_hall#3                      # section 3 (1-based) of shows/disco_hall
    disco_hall#4  cps=0.6             # same show, tempo overridden
    gqom_weight#"Weight — gqom"       # by label (quoted, substring ok)
    livecode_nyc_rehearsal_20260719#10 state.hue=200 state.intensity=0.8
    hard_techno_cs_minor#1 -tracks=rumble,acid    # drop named tracks
    disco_hall#7 only=drums,bass,floor            # keep ONLY these tracks/layers

Overrides:
    cps=<f>          override tempo for the section
    state.<k>=<v>    seed window.state.<k> (JSON parsed when possible)
    -tracks=a,b      omit named tracks     -layers=a,b   omit named layers
    only=a,b         keep only named tracks/layers (applies to both pools)
    label="..."      rename the section mark

Compilation collapses each source section to its NET state (exactly what was
live at that point — replay-perfect), so a compiled setlist is an ordinary
.show.json: steppable in shows.html, diff-transitioned on bar lines by the
engine, and itself a valid source for further setlists.

Usage:
    python3 setlist.py list  <show>              # numbered sections of a show
    python3 setlist.py compile <file.setlist> [-o shows/out.show.json]
    python3 setlist.py play  <file.setlist>      # compile to temp + load it
"""
import json, os, re, shlex, sys, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "http://localhost:8766"


# ── show access ──────────────────────────────────────────────────

def find_show(name):
    for cand in (name,
                 os.path.join(ROOT, "shows", f"{name}.show.json"),
                 os.path.join(ROOT, "shows", name),
                 os.path.join(ROOT, "shows", "unsorted", f"{name}.show.json")):
        if os.path.isfile(cand):
            return cand
    sys.exit(f"show not found: {name}")


def sections_of(doc):
    """[(label, start, end)] — start is the mark index, end exclusive."""
    steps = doc["steps"]
    marks = [(i, s.get("label", "")) for i, s in enumerate(steps)
             if s.get("route") == "/show/mark"]
    if not marks:
        return [("(whole show)", 0, len(steps))]
    out = []
    for k, (i, label) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(steps)
        out.append((label, i, end))
    return out


def net_state(steps, upto):
    """Collapse steps[0:upto] to net state — mirrors the engine's collapse."""
    tracks, layers, states = {}, {}, {}
    cps = setup = fps = None
    sends, seen = [], set()
    for s in steps[:upto]:
        r, d = s.get("route"), s.get("payload", {})
        if r == "/strudel/track":   tracks[d.get("name")] = d.get("code")
        elif r == "/strudel/stop":  tracks.pop(d.get("name"), None)
        elif r == "/strudel/hush":  tracks.clear()
        elif r == "/strudel/cps":   cps = d.get("cps")
        elif r == "/p5/layer":      layers[d.get("name")] = d.get("code")
        elif r == "/p5/remove":     layers.pop(d.get("name"), None)
        elif r == "/p5/clear":      layers.clear()
        elif r == "/p5/setup":      setup = d.get("code"); layers.clear()
        elif r == "/p5/state":      states[d.get("key")] = d.get("value")
        elif r == "/p5/fps":        fps = d.get("fps")
        elif r == "/strudel/send":
            c = d.get("code")
            if c and c not in seen:
                seen.add(c); sends.append(c)
    tracks = {n: c for n, c in tracks.items() if n and c is not None}
    layers = {n: c for n, c in layers.items() if n and c is not None}
    return dict(tracks=tracks, layers=layers, states=states,
                cps=cps, setup=setup, fps=fps, sends=sends)


# ── setlist parsing ──────────────────────────────────────────────

REF_RE = re.compile(r'^([\w.\-]+)#(?:"([^"]+)"|(\S+))')

def parse(path):
    headers, entries = {}, []
    for ln, raw in enumerate(open(path), 1):
        line = raw.split("#", 1)[0].rstrip() if raw.lstrip().startswith("#") else raw.rstrip()
        # a '#' inside a ref is meaningful; only treat leading-# as comment
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = re.match(r'^(name|desc|seam):\s*(.+)$', raw.strip())
        if m:
            headers[m.group(1)] = m.group(2).strip()
            continue
        toks = shlex.split(raw.strip())
        m = REF_RE.match(toks[0])
        if not m:
            sys.exit(f"{path}:{ln}: cannot parse section ref: {toks[0]!r}")
        show, label_ref, idx_ref = m.group(1), m.group(2), m.group(3)
        ov = {"cps": None, "states": {}, "drop_tracks": set(), "drop_layers": set(),
              "only": None, "label": None}
        for t in toks[1:]:
            if t.startswith("cps="):        ov["cps"] = float(t[4:])
            elif t.startswith("state."):
                k, _, v = t[6:].partition("=")
                try: ov["states"][k] = json.loads(v)
                except json.JSONDecodeError: ov["states"][k] = v
            elif t.startswith("-tracks="):  ov["drop_tracks"] = set(t[8:].split(","))
            elif t.startswith("-layers="):  ov["drop_layers"] = set(t[8:].split(","))
            elif t.startswith("only="):     ov["only"] = set(t[5:].split(","))
            elif t.startswith("label="):    ov["label"] = t[6:]
            else: sys.exit(f"{path}:{ln}: unknown override {t!r}")
        entries.append((show, label_ref, idx_ref, ov, ln))
    return headers, entries


# ── compile ──────────────────────────────────────────────────────

def compile_setlist(path, out=None):
    headers, entries = parse(path)
    shows_cache = {}
    all_steps, all_sends, seen_sends = [], [], set()
    base = os.path.splitext(os.path.basename(path))[0].replace(".setlist", "")

    for show, label_ref, idx_ref, ov, ln in entries:
        if show not in shows_cache:
            shows_cache[show] = json.load(open(find_show(show)))
        doc = shows_cache[show]
        secs = sections_of(doc)
        if label_ref:
            hits = [(k, s) for k, s in enumerate(secs) if label_ref.lower() in s[0].lower()]
            if not hits:
                sys.exit(f"{path}:{ln}: no section label matching {label_ref!r} in {show}")
            k, (label, start, end) = hits[0]
        else:
            k = int(idx_ref) - 1
            if not (0 <= k < len(secs)):
                sys.exit(f"{path}:{ln}: {show} has {len(secs)} sections, asked for {idx_ref}")
            label, start, end = secs[k]

        net = net_state(doc["steps"], end)      # what was live at section end
        if ov["only"] is not None:
            net["tracks"] = {n: c for n, c in net["tracks"].items() if n in ov["only"]}
            net["layers"] = {n: c for n, c in net["layers"].items() if n in ov["only"]}
        net["tracks"] = {n: c for n, c in net["tracks"].items() if n not in ov["drop_tracks"]}
        net["layers"] = {n: c for n, c in net["layers"].items() if n not in ov["drop_layers"]}
        if ov["cps"] is not None:
            net["cps"] = ov["cps"]
        net["states"].update(ov["states"])

        mark = ov["label"] or f"{label or f'§{k+1}'}  ⟨{show}#{k+1}⟩"
        # hush+clear make each section's net state SELF-CONTAINED — without
        # them, collapse accumulates every prior section and old tracks keep
        # playing underneath. They are folded away inside the engine's collapse
        # (dict.clear(), never fired at the browser), so stepping stays
        # seamless: the diff stops removed tracks ON the bar line, no silence.
        steps = [{"route": "/show/mark", "payload": {}, "label": mark},
                 {"route": "/strudel/hush", "payload": {}},
                 {"route": "/p5/clear", "payload": {}}]
        for c in net["sends"]:
            if c not in seen_sends:
                seen_sends.add(c)
                all_sends.append({"route": "/strudel/send", "payload": {"code": c}})
        if net["cps"] is not None:
            steps.append({"route": "/strudel/cps", "payload": {"cps": net["cps"]}})
        for kk, v in net["states"].items():
            steps.append({"route": "/p5/state", "payload": {"key": kk, "value": v}})
        for n, c in net["layers"].items():
            steps.append({"route": "/p5/layer", "payload": {"name": n, "code": c}})
        for n, c in net["tracks"].items():
            steps.append({"route": "/strudel/track", "payload": {"name": n, "code": c}})
        # the engine diffs at playback, so emitting full net state per section
        # is both replay-perfect AND transitions cleanly.
        all_steps.append(steps)

    doc = {
        "format": "livecode-show-v1",
        "name": headers.get("name", base),
        "created": None,
        "kind": "both",
        "desc": headers.get("desc", f"compiled from {os.path.basename(path)}"),
        "setlist": os.path.basename(path),
        "seam": float(headers["seam"]) if "seam" in headers else None,
        "cps_at_start": None,
        "steps": all_sends + [s for sec in all_steps for s in sec],
    }
    import datetime
    doc["created"] = datetime.date.today().isoformat()
    out = out or os.path.join(ROOT, "shows", f"{base}.show.json")
    json.dump(doc, open(out, "w"), indent=1)
    n_sec = len(all_steps)
    print(f"compiled {n_sec} sections from {len(shows_cache)} shows -> {out}")
    return out


# ── commands ─────────────────────────────────────────────────────

def cmd_list(name):
    doc = json.load(open(find_show(name)))
    secs = sections_of(doc)
    print(f"{doc.get('name', name)} — {len(secs)} sections")
    for k, (label, start, end) in enumerate(secs):
        net = net_state(doc["steps"], end)
        print(f"  #{k+1:<3} {label or '(unnamed)':44} "
              f"{len(net['tracks'])}trk {len(net['layers'])}lay"
              f"{'  cps=' + str(net['cps']) if net['cps'] else ''}")

def cmd_play(path):
    out = compile_setlist(path, out=os.path.join(ROOT, "shows", "unsorted", "_setlist_preview.show.json"))
    r = urllib.request.Request(BASE + "/show/load_file",
        data=json.dumps({"path": out}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    print(json.load(urllib.request.urlopen(r, timeout=10)))

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(1)
    if a[0] == "list" and len(a) > 1:
        cmd_list(a[1])
    elif a[0] == "compile" and len(a) > 1:
        out = a[a.index("-o") + 1] if "-o" in a else None
        compile_setlist(a[1], out)
    elif a[0] == "play" and len(a) > 1:
        cmd_play(a[1])
    else:
        print(__doc__); sys.exit(1)
