#!/usr/bin/env python3
"""draw_teddy_bear_doodle.py — draw a TEDDY BEAR doodle with the Doodle Maker engine.

Every mark goes through scripts/doodle_maker.py (the headless emulation of the LIVE
SnowSnakes Doodle Maker modal: 900x700 landscape canvas, the real 12-colour palette,
brush / marker / spray / eraser / fill / stamp / hand-lettering). Nothing is drawn
outside that API, so the piece is provably "made in the doodle maker".

Composition (left-to-right, top-to-bottom, exactly the order the code runs):
  1. soft cyan spray in both top corners (background air)
  2. ears (outer fur + pink inner)  ->  head on top so the ears tuck behind
  3. muzzle + nose + eyes
  4. body, belly patch, arms, legs + pink paw pads
  5. seam stitches
  6. SNOW SNAKE easter egg, bottom-left (canon: a snow snake in every frame-art)
  7. hand-lettered "TEDDY"

Usage: venv/bin/python scripts/draw_teddy_bear_doodle.py [--scale 2]
Writes content/snowsnakes/doodles/persona/teddy-bear-doodle.png (default 1800x1400).
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from doodle_maker import Canvas  # noqa: E402  the maker engine

OUT_DIR = ROOT / "content" / "snowsnakes" / "doodles" / "persona"

# the maker's own palette (doodle_maker.PALETTE) — no off-palette colours
NAVY = "#003399"     # outline + snow-snake body
WHITE = "#ffffff"
PINK = "#ff9ecb"     # inner ear / paw pads
BROWN = "#6d4c41"    # fur
BLACK = "#000000"
CYAN = "#00ccff"     # background air
GOLD = "#ffcc00"


def rot_ellipse(cx, cy, rx, ry, deg=0.0, n=44):
    """Point list for an ellipse rotated by `deg` — drawn as brush strokes."""
    a = math.radians(deg)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        pts.append((cx + x * math.cos(a) - y * math.sin(a),
                    cy + x * math.sin(a) + y * math.cos(a)))
    pts.append(pts[0])
    return pts


def draw(c: Canvas, seed: int = 7) -> None:
    c.seed(seed)

    # ── 1. background air ────────────────────────────────────────────────
    c.spray([(120, 90), (170, 150), (90, 170)], CYAN, size=120, density=0.28, alpha=22)
    c.spray([(800, 110), (760, 170), (830, 200)], CYAN, size=120, density=0.28, alpha=22)

    # ── 2. ears, then head on top so they tuck behind ───────────────────
    for ex, ey in ((338, 138), (562, 138)):
        c.brush(rot_ellipse(ex, ey, 78, 74, 0), NAVY, 12)
        c.fill(ex, ey, BROWN, tol=40)
        c.brush(rot_ellipse(ex, ey + 4, 40, 36, 0), NAVY, 8)
        c.fill(ex, ey + 4, PINK, tol=40)

    c.brush(rot_ellipse(450, 252, 158, 142, 0), NAVY, 13)
    c.fill(450, 252, BROWN, tol=45)

    # ── 3. muzzle + nose + eyes ──────────────────────────────────────────
    c.brush(rot_ellipse(450, 322, 88, 62, 0), NAVY, 10)
    c.fill(450, 322, WHITE, tol=40)
    # nose: a fat triangle pointing down, filled black
    nose = [(408, 292), (492, 292), (450, 344), (408, 292)]
    c.brush(nose, NAVY, 8)
    c.fill(450, 302, BLACK, tol=40)
    # smile: two short strokes under the nose
    c.brush(_curve(425, 350, 450, 362, 8), NAVY, 7)
    c.brush(_curve(475, 350, 450, 362, 8), NAVY, 7)
    # eyes with a white glint
    for ex in (392, 508):
        c.dot(ex, 244, BLACK, 17)
        c.dot(ex - 5, 238, WHITE, 6)

    # ── 4. body / belly / arms / legs ────────────────────────────────────
    c.brush(rot_ellipse(450, 520, 186, 148, 0), NAVY, 13)
    c.fill(450, 520, BROWN, tol=45)
    # belly patch
    c.brush(rot_ellipse(450, 560, 104, 84, 0), NAVY, 9)
    c.fill(450, 560, WHITE, tol=40)
    # arms (rotated ellipses) — left then right
    for ax, ay, deg in ((278, 476, 28), (622, 476, -28)):
        c.brush(rot_ellipse(ax, ay, 60, 104, deg), NAVY, 12)
        c.fill(ax, ay, BROWN, tol=45)
        c.brush(rot_ellipse(ax - 4, ay + 74, 34, 30, deg), NAVY, 8)
        c.fill(ax - 4, ay + 74, PINK, tol=40)
    # legs + paw pads
    for lx in (372, 528):
        c.brush(rot_ellipse(lx, 646, 84, 62, 0), NAVY, 12)
        c.fill(lx, 646, BROWN, tol=45)
        c.brush(rot_ellipse(lx, 656, 40, 30, 0), NAVY, 8)
        c.fill(lx, 656, PINK, tol=40)

    # ── 5. seam stitches ─────────────────────────────────────────────────
    for i in range(4):
        x = 412 + i * 26
        c.brush([(x, 612), (x + 12, 600)], NAVY, 5)

    # ── 6. SNOW SNAKE easter egg (bottom-left) ───────────────────────────
    body = [(96, 672), (140, 640), (190, 660), (236, 626), (268, 604)]
    c.brush(body, NAVY, 20)
    c.brush(body, WHITE, 12)
    c.dot(272, 600, NAVY, 15)          # head
    c.dot(268, 596, WHITE, 5)          # eye
    c.brush([(262, 586), (250, 570)], "#e63946", 6)   # tongue
    for sx, sy in ((150, 600), (204, 636)):
        c.stamp("\u2744\ufe0f", sx, sy, 46, CYAN)

    # ── 7. hand lettering ────────────────────────────────────────────────
    c.hand_text("TEDDY", 336, 108, size=64, color=NAVY, wobble=2.2, spacing=1.05)


def _curve(x0, y0, x1, y1, steps=10):
    """A slight quadratic bow between two points (hand-drawn smile halves)."""
    pts = []
    for i in range(steps + 1):
        t = i / steps
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2 + 8
        x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * mx + t ** 2 * x1
        y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * my + t ** 2 * y1
        pts.append((x, y))
    return pts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--out", default=str(OUT_DIR / "teddy-bear-doodle.png"))
    a = ap.parse_args()

    c = Canvas(scale=a.scale)
    draw(c)
    p = c.save(a.out)
    print(f"wrote {p}  ({p.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
