#!/usr/bin/env python
"""Bar/section-boundary timing — so transitions land ON the grid, not whenever
the agent happened to finish thinking.

CLI:
  python assets/tools/boundary.py --bars 8 --port 9976     # block until the next 8-bar line
  python assets/tools/boundary.py --bars 8 --port 9976 --dry   # just report, don't wait

Library:
  from boundary import wait_boundary, bar_seconds
  wait_boundary(port=9976, bars=8)   # returns after landing on the boundary

Why this exists: at cps C, one cycle == one bar and lasts 1/C seconds. `clk.cyc`
is the fractional position inside the current cycle and `clk.bar` counts bars.
Firing mid-bar is what makes a transition sound abrupt — the new material starts
on an off-beat and the ear hears a seam. Waiting costs at most one phrase.
"""
import argparse, time

import requests


def read_clk(port):
    r = requests.get(f"http://localhost:{port}/p5/read?key=clk", timeout=10).json()
    v = r.get("value") or {}
    if not v:
        raise RuntimeError("no clock — is a track playing? the clock is transport-driven")
    return v


def bar_seconds(clk):
    return 1.0 / (clk.get("cps") or 0.5)


def seconds_to_boundary(clk, bars):
    """Seconds until the next multiple-of-`bars` bar line."""
    bar = clk.get("bar", 0.0)
    nxt = (int(bar // bars) + 1) * bars
    return (nxt - bar) * bar_seconds(clk), nxt


def wait_boundary(port=9766, bars=8, max_wait=None, verbose=True):
    clk = read_clk(port)
    dt, nxt = seconds_to_boundary(clk, bars)
    if max_wait is not None and dt > max_wait:
        if verbose:
            print(f"boundary in {dt:.1f}s > max_wait {max_wait}s — firing now")
        return 0.0
    if verbose:
        print(f"bar {clk.get('bar', 0):.2f} -> waiting {dt:.2f}s for bar {nxt} "
              f"({bars}-bar line, cps {clk.get('cps')})")
    time.sleep(max(0.0, dt - 0.08))  # lead-in: land just before the downbeat
    return dt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bars", type=int, default=8)
    ap.add_argument("--port", type=int, default=9766)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    clk = read_clk(a.port)
    dt, nxt = seconds_to_boundary(clk, a.bars)
    print(f"cps {clk.get('cps')} | bar {clk.get('bar', 0):.2f} | "
          f"next {a.bars}-bar line: bar {nxt} in {dt:.2f}s")
    if not a.dry:
        wait_boundary(a.port, a.bars, verbose=False)
        print("landed")


if __name__ == "__main__":
    main()
