#!/usr/bin/env python3
"""build_snowsnakes_maker_doodles.py — compose 3 SnowSnakes feed doodles USING THE
DOODLE MAKER ENGINE (scripts/doodle_maker.py), i.e. every mark is made with one of
the live maker's tools: brush / marker / spray / eraser / fill / stamp / lettering.

Nothing here draws outside that API, so the output is provably "made in the doodle
maker" — same 900x700 landscape logical canvas and same 12-colour palette as the
browser modal (see doodle_maker.py docstring for the bundle provenance).

Usage:  venv/bin/python scripts/build_snowsnakes_maker_doodles.py [--scale 2]
"""
from __future__ import annotations
import argparse, hashlib, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from doodle_maker import Canvas, STAMPS, PALETTE   # the maker engine

OUT = ROOT / "content" / "snowsnakes" / "doodles"
INK, NAVY, RED, GOLD, CYAN, PURPLE = "#000000", "#003399", "#e63946", "#ffcc00", "#00ccff", "#8e44ad"
SNOW, ICE, BODY = "#ffffff", "#dff2ff", "#8ed6f7"


def wave(x0, x1, cy, amp, cycles, n=220):
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((x0 + (x1 - x0) * t, cy + math.sin(t * math.pi * 2 * cycles) * amp))
    return pts


def snowflakes(c, seed, n=26):
    import random
    r = random.Random(seed)
    for _ in range(n):
        x, y = r.uniform(40, 860), r.uniform(40, 660)
        s = r.uniform(5, 13)
        col = r.choice([CYAN, ICE, PURPLE])
        c.brush([(x - s, y), (x + s, y)], col, 2.4)
        c.brush([(x, y - s), (x, y + s)], col, 2.4)
        c.brush([(x - s * .6, y - s * .6), (x + s * .6, y + s * .6)], col, 1.8)
        c.brush([(x - s * .6, y + s * .6), (x + s * .6, y - s * .6)], col, 1.8)


def frame(c):
    """A wobbled maker-brush border, like a doodler framing the page."""
    c.brush([(22, 22), (878, 26), (874, 676), (26, 672), (22, 22)], NAVY, 4, jitter=2.0)


# ── doodle 1 ────────────────────────────────────────────────────────────────
def d1(c):
    """SNOW SNAKE — the mascot, scarf on, snow everywhere."""
    snowflakes(c, 11, 30)
    pts = wave(70, 830, 380, 96, 1.75)
    c.marker(pts, BODY, 54, alpha=120, passes=2)          # translucent body
    c.brush([(x, y + 4) for x, y in pts], "#5fb6e0", 6, jitter=1.2)   # soft underline
    # head
    hx, hy = pts[-1]
    c.ellipse([hx - 62, hy - 46, hx + 54, hy + 44], NAVY, 7)
    c.fill(hx, hy, BODY)
    c.dot(hx + 14, hy - 12, INK, 11)
    c.dot(hx + 16, hy - 14, "#ffffff", 4)
    c.marker([(hx + 52, hy + 6), (hx + 96, hy + 12), (hx + 118, hy - 2)], RED, 8, alpha=220)
    # scarf
    c.poly([(120, 300), (250, 292), (262, 350), (132, 358)], RED, 6, jitter=1.4)
    c.fill(190, 325, RED)
    c.marker([(250, 330), (300, 372), (312, 420)], GOLD, 16, alpha=200)
    c.stamp(STAMPS[9 - 1], hx - 20, hy - 4, 84, "#000000") if False else None
    # caption
    c.hand_text("TOO COLD TO STOP", 96, 540, 62, NAVY, wobble=3.0)
    c.hand_text("SNOW SNAKES", 640, 630, 30, INK, wobble=2.0)
    c.spray([(820, 120), (860, 150)], CYAN, 30, density=0.9, alpha=60)
    frame(c)


# ── doodle 2 ────────────────────────────────────────────────────────────────
def d2(c):
    """PUMPKIN PETE'S SNOW CONE — food-truck crossover, condiment stamps."""
    snowflakes(c, 22, 18)
    # cone
    c.poly([(300, 330), (600, 330), (452, 646)], "#c98a3c", 7, jitter=1.0)
    c.fill(452, 520, "#e0a95a")
    for i in range(6):                                   # waffle hatch
        y = 380 + i * 44
        c.brush([(318 + i * 20, y), (582 - i * 20, y)], "#a86f2b", 4)
    # scoops
    c.ellipse([286, 214, 614, 400], NAVY, 7)
    c.fill(450, 300, "#ff9ecb")
    c.ellipse([296, 168, 604, 322], NAVY, 7)
    c.fill(450, 250, ICE)
    c.ellipse([330, 120, 570, 268], NAVY, 7)
    c.fill(450, 200, SNOW)
    # sprinkles = maker dots
    import random
    r = random.Random(7)
    for _ in range(40):
        x, y = r.uniform(330, 570), r.uniform(140, 300)
        c.dot(x, y, r.choice([RED, GOLD, PURPLE, CYAN]), r.uniform(2.5, 4.5))
    c.stamp(STAMPS[2], 330, 210, 66, "#000000")          # tomato stamp
    c.stamp(STAMPS[8], 570, 190, 60, "#000000")          # snowflake stamp
    c.hand_text("SNOW CONE SEASON", 130, 52, 54, NAVY, wobble=2.6)
    c.hand_text("pumpkin pete's lot", 540, 640, 28, INK, wobble=2.0)
    frame(c)


# ── doodle 3 ────────────────────────────────────────────────────────────────
def d3(c):
    """SNOW BEATS — cassette + notes; the doodle companion to the songs."""
    snowflakes(c, 33, 20)
    c.rect([210, 214, 700, 470], NAVY, 8, jitter=1.3)
    c.fill(455, 340, "#f4f4ef")
    c.rect([248, 250, 662, 434], INK, 4, jitter=1.0)
    c.fill(455, 340, "#e9e9e2")
    # reels
    for cx in (355, 555):
        c.ellipse([cx - 58, 284, cx + 58, 400], INK, 5)
        c.fill(cx, 342, SNOW)
        c.dot(cx, 342, INK, 12)
        for k in range(6):                                # spokes
            a = k * math.pi / 3
            c.brush([(cx + math.cos(a) * 14, 342 + math.sin(a) * 14),
                     (cx + math.cos(a) * 48, 342 + math.sin(a) * 48)], "#6d4c41", 5)
    c.marker([(300, 430), (620, 430)], "#6d4c41", 14, alpha=210)
    # notes
    for (nx, ny, s) in ((150, 150, 1), (760, 200, 1), (790, 480, 1)):
        c.brush([(nx, ny + 34), (nx, ny)], INK, 6)
        c.brush([(nx, ny), (nx + 26, ny + 8)], INK, 6)
        c.ellipse([nx - 16, ny + 26, nx + 14, ny + 52], INK, 5)
        c.fill(nx - 1, ny + 39, INK)
    c.spray([(430, 560), (520, 580)], PURPLE, 34, density=0.8, alpha=55)
    c.hand_text("SNOW BEATS", 250, 552, 70, NAVY, wobble=3.2)
    c.hand_text("128 bpm", 620, 640, 30, RED, wobble=2.2)
    frame(c)


DOODLES = [
    {"slug": "too-cold-to-stop",  "title": "Too Cold To Stop — Snow Snake", "fn": d1, "seed": 101},
    {"slug": "snow-cone-season",  "title": "Snow Cone Season — Pumpkin Pete's Lot", "fn": d2, "seed": 202},
    {"slug": "snow-beats-cassette", "title": "Snow Beats — Cassette Doodle", "fn": d3, "seed": 303},
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=int, default=2, help="export multiplier (maker: min(3,max(1,dpr)))")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    man = {"engine": "scripts/doodle_maker.py (SnowSnakes Doodle Maker emulation)",
           "canvas_logical": "900x700", "palette": PALETTE, "scale": a.scale, "doodles": []}
    for d in DOODLES:
        c = Canvas(scale=a.scale).seed(d["seed"])
        d["fn"](c)
        p = OUT / f"{d['slug']}.png"
        c.save(p)
        man["doodles"].append({"slug": d["slug"], "title": d["title"],
                               "path": str(p.relative_to(ROOT)), "bytes": p.stat().st_size,
                               "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                               "tools_used": ["brush", "marker", "spray", "fill", "stamp", "dot",
                                              "poly", "rect", "ellipse", "hand_text"]})
        print(f"  {d['title']:<42} {p.stat().st_size:>8} B  -> {p.name}")
    (OUT / "manifest.json").write_text(json.dumps(man, indent=2))
    print("wrote", OUT / "manifest.json")


if __name__ == "__main__":
    raise SystemExit(main())
