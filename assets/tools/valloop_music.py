#!/usr/bin/env python3
"""Serialized validation loop for the music factory (port 9766).

Every cycle: if inbox has settled JSON files -> bridge health check (restart
host if frozen) -> validate.py --inbox music -> build_index.py -> git commit.
Twice-failed stems move to assets/music/inbox_failed/. Prints one BATCH line
per cycle (monitored). Ctrl-C/kill to stop.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

MAX_LOAD = 4.5  # 1-min loadavg above this starves browser audio scheduling:
                # the audio thread stalls for seconds and a genuinely LOUD stem
                # reads rms 0.0000 non-deterministically (verified: raw sawtooth
                # peaks 0.05 at load 5 but 0.00 at load 12). Wait for calm — never
                # lower the audibility gate to compensate.

ROOT = Path("/Users/gene/Dev/livecode")
INBOX = ROOT / "assets/music/inbox"
FAILED = ROOT / "assets/music/inbox_failed"
BASE = "http://localhost:9766"
STATE = Path(__file__).parent / "valloop_state.json"
PACKS = ROOT / "assets/music/packs.json"
PRELOADED = {"tidal-drum-machines", "uzu-drumkit", "piano", "vcsl"}


def preload_external_packs():
    """Send samples() for every non-preloaded pack the inbox depends on and wait
    generously, so external-pack stems don't false-fail on a cold cache under
    load (validate.py's per-stem 2.5s dep wait is too short when the machine is
    busy). samples() is idempotent/cached, so this is cheap on re-entry."""
    try:
        packs = json.loads(PACKS.read_text())
    except Exception:
        return
    needed = set()
    for p in INBOX.glob("*.json"):
        try:
            for d in (json.loads(p.read_text()).get("deps") or []):
                if d in packs and d not in PRELOADED and not d.startswith("_"):
                    needed.add(d)
        except Exception:
            continue
    for name in sorted(needed):
        try:
            requests.post(BASE + "/strudel/send", json={"code": packs[name]}, timeout=15)
        except Exception:
            pass
    if needed:
        time.sleep(12)


def sh(*cmd, timeout=None, **kw):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout, **kw)


def ready():
    try:
        return requests.get(BASE + "/status", timeout=5).json().get("ready")
    except Exception:
        return False


def bridge_ok():
    """Fire a known-loud track; healthy = rms rises above .03 and varies."""
    try:
        requests.post(BASE + "/strudel/track", json={
            "name": "healthcheck",
            "code": 's("bd*4, hh*8").bank("RolandTR909").gain(.7).play()'}, timeout=10)
        vals = []
        for _ in range(14):
            a = requests.get(BASE + "/p5/read?key=audio", timeout=5).json().get("value") or {}
            vals.append(round(a.get("rms", 0), 6))
            time.sleep(0.15)
        requests.post(BASE + "/strudel/stop", json={"name": "healthcheck"}, timeout=10)
        # ≥5/14 loud samples: a healthy 909 reads high nearly every sample;
        # CPU-starved dropouts give sporadic bursts that still pass max() alone.
        loud = sum(1 for v in vals if v > 0.03)
        return loud >= 5 and len(set(vals)) > 3
    except Exception:
        return False


def load_ok():
    try:
        return os.getloadavg()[0] < MAX_LOAD
    except Exception:
        return True


def server_up():
    """True if 9766 HTTP answers at all (browser may or may not be connected)."""
    try:
        requests.get(BASE + "/status", timeout=4)
        return True
    except Exception:
        return False


def restart_server():
    # Kill ONLY the 9766 server (unique --port 9766); never touch 8766/9866 (visual).
    print("SERVER DOWN — restarting livecode.py --port 9766", flush=True)
    subprocess.run(["pkill", "-f", "livecode.py --port 9766"])
    time.sleep(2)
    subprocess.Popen(
        ["python", "livecode.py", "--port", "9766"], cwd=ROOT,
        stdout=open("/tmp/lc_music_server.log", "a"),
        stderr=subprocess.STDOUT, start_new_session=True)
    time.sleep(3)


def restart_host():
    print("restarting music host (→9766)", flush=True)
    # Match ONLY my host by its unique snapshots_music dir — leave visual hosts alone.
    subprocess.run(["pkill", "-f", "autopilot_host.py.*snapshots_music"])
    time.sleep(2)
    subprocess.Popen(
        ["python", "autopilot_host.py", "--url",
         "http://localhost:9766/livecode.html", "--snapshots-dir",
         "autopilot/snapshots_music", "--interval", "10"],
        cwd=ROOT, stdout=open("/tmp/lc_music_host.log", "a"),
        stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(30):
        if ready():
            break
        time.sleep(2)
    time.sleep(1)
    try:
        requests.post(BASE + "/show/recording", json={"enabled": False}, timeout=10)
    except Exception:
        pass


def recover():
    """Full self-heal ladder: server, then host, then verify bridge."""
    if not server_up():
        restart_server()
    if not ready() or not bridge_ok():
        restart_host()
    return bridge_ok()


def settled_inbox():
    now = time.time()
    return [p for p in sorted(INBOX.glob("*.json")) if now - p.stat().st_mtime > 15]


AUDIT_EVERY = 3600  # seconds between automatic full-catalog re-audits when idle


def run_audit():
    """Re-validate the whole verified catalog against the live engine and demote
    anything now silent/broken. Its own engine health-check aborts cleanly if the
    engine is bad, so this never mass-demotes on a transient fault."""
    print("AUDIT: re-validating verified catalog (--audit music)", flush=True)
    r = sh("python", "assets/tools/validate.py", "--port", "9766",
           "--audit", "music", timeout=7200)
    out = (r.stdout or "") + (r.stderr or "")
    demoted = [l for l in out.splitlines() if "DEMOTED" in l]
    tail = out.strip().splitlines()[-1:] if out.strip() else []
    print(f"AUDIT: {len(demoted)} demoted; {' '.join(tail)}", flush=True)
    for l in demoted:
        print("  " + l.strip()[:160], flush=True)
    if demoted:
        sh("python", "assets/tools/build_index.py", "music", timeout=300)
        sh("git", "add", "assets/music")
        sh("git", "commit", "-m",
           f"music factory: audit demoted {len(demoted)} silent/broken stems to inbox"
           "\n\nCo-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>")


def main():
    FAILED.mkdir(exist_ok=True)
    fails = json.loads(STATE.read_text()) if STATE.exists() else {}
    total_pass = 0
    last_audit = 0.0
    print("valloop started", flush=True)
    while True:
        files = settled_inbox()
        if not files:
            # Idle: periodically re-audit the catalog so an engine regression
            # (like the DSP-worklet break) can never silently rot 'verified'.
            if load_ok() and (time.time() - last_audit) > AUDIT_EVERY:
                if server_up() and ready() and bridge_ok():
                    run_audit()
                    last_audit = time.time()
            time.sleep(30)
            continue
        if not load_ok():
            print(f"WAIT: loadavg {os.getloadavg()[0]:.1f} >= {MAX_LOAD} — "
                  f"deferring {len(files)} files until machine calms", flush=True)
            time.sleep(90)
            continue
        if not server_up() or not ready() or not bridge_ok():
            if not recover():
                print("BATCH: bridge unrecoverable — sleeping 120s", flush=True)
                time.sleep(120)
                continue
        preload_external_packs()  # warm the sample cache before validating
        r = sh("python", "assets/tools/validate.py", "--port", "9766",
               "--inbox", "music", timeout=3600)
        out = (r.stdout or "") + (r.stderr or "")
        npass = sum(1 for l in out.splitlines() if l.startswith("PASS "))
        nfail = sum(1 for l in out.splitlines() if l.startswith("FAIL "))
        total_pass += npass
        # quarantine twice-failed
        quarantined = 0
        for p in INBOX.glob("*.json"):
            try:
                d = json.loads(p.read_text())
            except Exception:
                continue
            if "last_fail" in d:
                fails[p.name] = fails.get(p.name, 0) + 1
                if fails[p.name] >= 2:
                    p.rename(FAILED / p.name)
                    quarantined += 1
        STATE.write_text(json.dumps(fails))
        sh("python", "assets/tools/build_index.py", "music", timeout=300)
        # commit the batch
        sh("git", "add", "assets/music")
        msg = f"music factory: batch +{npass} verified ({nfail} fail, {quarantined} quarantined) — total {total_pass} this loop"
        c = sh("git", "commit", "-m", msg + "\n\nCo-Authored-By: Claude Fable 5 <noreply@anthropic.com>")
        committed = "nothing to commit" not in (c.stdout + c.stderr)
        print(f"BATCH: +{npass} pass, {nfail} fail, {quarantined} quarantined, commit={committed}", flush=True)
        # show fail reasons briefly
        for line in out.splitlines():
            if line.startswith("FAIL"):
                print("  " + line[:160], flush=True)
        time.sleep(20)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
