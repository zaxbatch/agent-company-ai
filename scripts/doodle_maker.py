#!/usr/bin/env python3
"""doodle_maker.py — headless emulation of the SnowSnakes Doodle Maker.

Reverse-engineered from the LIVE maker bundle (static/js/main.25ca096f.js,
fetched 2026-09-13), so a doodle drawn here is byte-shape-identical in
composition to one a human draws in the browser modal:

  canvas   900 x 700 logical px  (bundle: ra=900, aa=700)
           export = round(900*N) x round(700*N), N=min(3,max(1,devicePixelRatio))
           -> N=1 gives 900x700 (what a dpr-1 desktop exports)
  tools    brush  "Draw a smooth line"
           marker "Draw a fat, see-through line"
           spray  "Splatter paint like a spray can"
           eraser "Rub bits out"
           fill   "Fill inside a closed shape"
           stamp  "Plop a condiment on the page"
  palette  ["#003399","#ff00ff","#ffcc00","#e63946","#ff7f11","#2ecc71",
            "#8e44ad","#6d4c41","#ff9ecb","#00ccff","#ffffff","#000000"]
           + arbitrary colour (the maker's <input type="color">)
  size     brush/marker/spray slider 2..48
  stamps   12 condiment/character glyphs (tomato, pepper, snake, snowflake...)
  clear    source-over white fillRect(0,0,900,700)  == start_over()

NOTE (found while building this): the older scripts/doodle_gen.py claims to
match "the maker's canvas" but renders 700x900 PORTRAIT. The live bundle is
900x700 LANDSCAPE. This module uses the real geometry.

Public API
----------
Canvas(w=900,h=700,scale=1,bg=...)      the canvas
  .brush(pts,color,size)                smooth opaque stroke
  .marker(pts,color,size)               fat translucent stroke (per-segment
                                        alpha => overlaps darken, like a real pen)
  .spray(pts,color,size,density)        spray-can scatter
  .eraser(pts,size)                     punch holes in everything drawn so far
  .fill(x,y,color,tol)                  flood fill inside a closed shape
  .stamp(glyph,x,y,size,color)          condiment stamp
  .text(...) / .hand_text(...)          lettering (straight / hand-wobbled)
  .poly / .rect / .ellipse / .dot       primitives (still "the brush")
  .save(path)                           PNG export at canvas*scale
Renderers should stay inside this API so every doodle is provably made of
maker tools only.
"""
from __future__ import annotations
import math, random, sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageChops

W, H = 900, 700          # LOGICAL canvas, matches the live bundle
PALETTE = ["#003399", "#ff00ff", "#ffcc00", "#e63946", "#ff7f11", "#2ecc71",
           "#8e44ad", "#6d4c41", "#ff9ecb", "#00ccff", "#ffffff", "#000000"]
STAMPS = ["\U0001F32D", "\U0001F96B", "\U0001F345", "\U0001F336\uFE0F",
          "\U0001F9C5", "\U0001F952", "\U0001F9C8", "\U0001F40D",
          "\u2744\uFE0F", "\U0001F9CA", "\U0001F354", "\U0001F3A8"]

FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/liberation",
             "/usr/share/fonts/truetype/liberation2"]
EMOJI_FONTS = ["/usr/lib/firefox-esr/fonts/TwemojiMozilla.ttf",
               "/snap/gnome-3-34-1804/94/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"]


def hex_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def font(size: int, bold: bool = True, family: str = "dejavu"):
    cands = []
    for d in FONT_DIRS:
        base = Path(d)
        if family == "dejavu":
            cands += [base / "DejaVuSans-Bold.ttf"] if bold else []
            cands += [base / "DejaVuSans.ttf"]
        else:
            cands += [base / "LiberationSans-Bold.ttf", base / "LiberationSerif-Bold.ttf",
                      base / "LiberationMono-Bold.ttf"]
    for p in cands:
        try:
            return ImageFont.truetype(str(p), size)
        except OSError:
            continue
    return ImageFont.load_default()


def _emoji_font(size: int):
    for p in EMOJI_FONTS:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return None


class Canvas:
    """The Doodle Maker canvas. Every public method is one of the maker's tools."""

    def __init__(self, w: int = W, h: int = H, scale: int = 1, bg=(255, 255, 255)):
        self.w, self.h, self.scale = w, h, scale
        self.paint = Image.new("RGBA", (w, h), tuple(bg) + (255,))
        self.rng = random.Random(0)

    # ── internals ─────────────────────────────────────────────────────────
    def seed(self, n: int):
        self.rng = random.Random(n)
        return self

    def _layer(self):
        return Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))

    def _commit(self, layer: Image.Image):
        self.paint = Image.alpha_composite(self.paint, layer)

    def _round_caps(self, d: ImageDraw.ImageDraw, pts, color, size):
        r = size / 2.0
        for (x, y) in (pts[0], pts[-1]):
            d.ellipse([x - r, y - r, x + r, y + r], fill=color)

    def _stroke(self, pts, color, size, alpha=255, jitter=0.0, rng=None):
        if len(pts) < 2:
            return
        rng = rng or self.rng
        col = tuple(color) + (alpha,)
        if jitter:
            pts = [(x + rng.uniform(-jitter, jitter), y + rng.uniform(-jitter, jitter))
                   for x, y in pts]
        layer = self._layer()
        d = ImageDraw.Draw(layer)
        d.line(pts, fill=col, width=max(1, int(round(size))), joint="curve")
        self._round_caps(d, pts, col, size)
        self._commit(layer)

    def _stroke_per_segment(self, pts, color, size, alpha, jitter=0.0):
        """Marker: each segment is its own alpha pass, so crossings darken."""
        rng = self.rng
        if jitter:
            pts = [(x + rng.uniform(-jitter, jitter), y + rng.uniform(-jitter, jitter))
                   for x, y in pts]
        for a, b in zip(pts, pts[1:]):
            self._stroke([a, b], color, size, alpha=alpha)

    # ── tools ─────────────────────────────────────────────────────────────
    def brush(self, pts, color, size=8, jitter=0.0):
        self._stroke(pts, hex_rgb(color) if isinstance(color, str) else color,
                     size, 255, jitter)

    def marker(self, pts, color, size=18, alpha=95, jitter=0.0, passes=1):
        c = hex_rgb(color) if isinstance(color, str) else color
        for _ in range(passes):
            self._stroke_per_segment(pts, c, size, alpha, jitter)

    def spray(self, pts, color, size=24, density=1.0, alpha=70):
        c = hex_rgb(color) if isinstance(color, str) else color
        rng = self.rng
        n = max(6, int(size * density))
        layer = self._layer()
        d = ImageDraw.Draw(layer)
        for (x, y) in pts:
            for _ in range(n):
                a = rng.uniform(0, 2 * math.pi)
                r = rng.uniform(0, size)
                px, py = x + math.cos(a) * r, y + math.sin(a) * r * rng.uniform(.7, 1.3)
                dot = rng.uniform(0.7, 2.2)
                d.ellipse([px - dot, py - dot, px + dot, py + dot],
                          fill=c + (int(alpha * rng.uniform(.5, 1.4)),))
        self._commit(layer)

    def eraser(self, pts, size=24):
        m = Image.new("L", (self.w, self.h), 0)
        d = ImageDraw.Draw(m)
        d.line(pts, fill=255, width=max(1, int(size)), joint="curve")
        self._round_caps(d, pts, 255, size)
        a = self.paint.getchannel("A")
        a = ImageChops.subtract(a, m)
        self.paint.putalpha(a)

    def fill(self, x, y, color, tol=32):
        """Real flood fill (the maker's Fill tool) — scanline, numpy-backed."""
        c = hex_rgb(color) if isinstance(color, str) else tuple(color)
        arr = np.asarray(self.paint.convert("RGB")).astype(np.int16)
        x, y = int(x), int(y)
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        target = arr[y, x].copy()
        if np.abs(target - np.array(c)).max() <= 2:
            return
        close = (np.abs(arr - target).max(axis=2) <= tol)
        seen = np.zeros((self.h, self.w), bool)
        q = deque([(x, y)])
        seen[y, x] = True
        px = self.paint.load()
        col = tuple(c) + (255,)
        while q:
            cx, cy = q.popleft()
            px[cx, cy] = col
            for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if 0 <= nx < self.w and 0 <= ny < self.h and not seen[ny, nx] and close[ny, nx]:
                    seen[ny, nx] = True
                    q.append((nx, ny))

    def stamp(self, glyph, x, y, size=72, color="#000000"):
        f = _emoji_font(int(size))
        c = hex_rgb(color) if isinstance(color, str) else tuple(color)
        layer = self._layer()
        d = ImageDraw.Draw(layer)
        if f is None:
            self._stroke([(x - size, y), (x + size, y)], c, size * 0.4)
            return
        try:
            d.text((x, y), glyph, font=f, fill=c + (255,), anchor="mm",
                   embedded_color=False)
        except TypeError:
            d.text((x, y), glyph, font=f, fill=c + (255,), anchor="mm")
        self._commit(layer)

    # ── primitives (still brush strokes) ──────────────────────────────────
    def rect(self, box, color, width=6, jitter=0.0):
        x0, y0, x1, y1 = box
        self.brush([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], color, width, jitter)

    def ellipse(self, box, color, width=6, jitter=0.0, fill=None):
        x0, y0, x1, y1 = box
        if fill:
            self.fill((x0 + x1) / 2, (y0 + y1) / 2, fill)
        n = 48
        cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
        pts = [(cx + math.cos(2 * math.pi * i / n) * rx,
                cy + math.sin(2 * math.pi * i / n) * ry) for i in range(n + 1)]
        self.brush(pts, color, width, jitter)

    def poly(self, pts, color, width=6, jitter=0.0, close=True, fill=None):
        p = list(pts) + ([pts[0]] if close else [])
        if fill:
            cx = sum(x for x, _ in pts) / len(pts)
            cy = sum(y for _, y in pts) / len(pts)
            self.fill(cx, cy, fill)
        self.brush(p, color, width, jitter)

    def dot(self, x, y, color, r=5):
        self.brush([(x, y), (x + 0.01, y)], color, r * 2)

    def text(self, s, x, y, size=40, color="#000000", bold=True, anchor="la",
             family="dejavu"):
        c = hex_rgb(color) if isinstance(color, str) else tuple(color)
        layer = self._layer()
        d = ImageDraw.Draw(layer)
        d.text((x, y), s, font=font(size, bold, family), fill=c + (255,), anchor=anchor)
        self._commit(layer)
        return d.textlength(s, font=font(size, bold, family))

    def hand_text(self, s, x, y, size=40, color="#000000", bold=True,
                  wobble=1.6, spacing=1.0, rotate=2.0):
        """Lettering with per-glyph wobble — the 'drawn by hand' look."""
        c = hex_rgb(color) if isinstance(color, str) else tuple(color)
        f = font(size, bold)
        layer = self._layer()
        d = ImageDraw.Draw(layer)
        cx = x
        for ch in s:
            w = d.textlength(ch, font=f)
            g = Image.new("RGBA", (int(w) + 24, int(size * 1.8)), (0, 0, 0, 0))
            gd = ImageDraw.Draw(g)
            gd.text((12, size * 0.35), ch, font=f, fill=c + (255,))
            g = g.rotate(self.rng.uniform(-rotate, rotate), resample=Image.BICUBIC,
                         expand=False)
            layer.alpha_composite(g, (int(cx), int(y + self.rng.uniform(-wobble, wobble))))
            cx += (w + 2) * spacing
        self._commit(layer)
        return cx - x

    # ── export ────────────────────────────────────────────────────────────
    def save(self, path):
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        img = self.paint.convert("RGB")
        if self.scale != 1:
            img = img.resize((self.w * self.scale, self.h * self.scale), Image.LANCZOS)
        img.save(p)
        return p


if __name__ == "__main__":
    c = Canvas().seed(1)
    c.spray([(300, 300), (340, 320), (380, 290)], "#ff00ff", 40)
    c.marker([(120, 480), (400, 420), (700, 500)], "#003399", 26)
    c.brush([(100, 100), (300, 160), (500, 110)], "#e63946", 10, jitter=2)
    c.fill(450, 600, "#ffcc00")
    c.stamp(STAMPS[7], 760, 140, 90, "#2ecc71")
    print("wrote", c.save("content/experiments/doodles/maker-smoke-test.png"))
