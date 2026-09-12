#!/usr/bin/env python3
"""Generate a doodle PNG in the SnowSnakes doodle-maker format (700x900).

The site's maker is a browser canvas that exports a PNG; this produces the same
artifact headlessly so doodles can be generated and posted unattended.
"""
from __future__ import annotations
import math, random, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 700, 900          # matches the maker's canvas
PAPER = (253, 252, 247)
INK = (36, 52, 74)
BODY = (223, 242, 255)
ACCENT = (226, 74, 74)
SNOW = (120, 190, 240)

rnd = random.Random(128)   # 128 = the tempo. reproducible output.


def jline(d, pts, jitter=1.6, width=5, fill=INK):
    """Draw a polyline with hand-drawn wobble."""
    wob = [(x + rnd.uniform(-jitter, jitter), y + rnd.uniform(-jitter, jitter)) for x, y in pts]
    d.line(wob, fill=fill, width=width, joint="curve")


def snowflake(d, cx, cy, r, col=SNOW, w=2):
    for k in range(3):
        a = math.radians(k * 60)
        x, y = math.cos(a) * r, math.sin(a) * r
        d.line([(cx - x, cy - y), (cx + x, cy + y)], fill=col, width=w)
    for k in range(3):
        a = math.radians(k * 60 + 30)
        for s in (0.55,):
            x, y = math.cos(a) * r * s, math.sin(a) * r * s
            d.line([(cx, cy), (cx + x, cy + y)], fill=col, width=w)
            d.line([(cx, cy), (cx - x, cy - y)], fill=col, width=w)


def font(sz, bold=True):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(p, sz)
        except OSError:
            continue
    return ImageFont.load_default()


def draw(path, caption="TOO COLD TO STOP", tag="128 BPM"):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # paper texture: faint dot grid
    for y in range(40, H - 40, 34):
        for x in range(40, W - 40, 34):
            d.point((x, y), fill=(226, 228, 224))

    cx, cy = 350, 660
    t0, t1 = math.radians(180), math.radians(270)
    r0, r1 = 52.0, 168.0
    N = 260
    pts = []
    for i in range(N + 1):
        t = i / N
        th = t0 + (t1 - t0) * t
        r = r0 + (r1 - r0) * t
        pts.append((cx + math.cos(th) * r * 1.12, cy + math.sin(th) * r * 0.92))

    # body shadow then body
    jline(d, [(x + 5, y + 6) for x, y in pts], jitter=0.06, width=44, fill=(238, 238, 234))
    jline(d, pts, jitter=0.06, width=42, fill=BODY)
    jline(d, pts, jitter=0.06, width=3, fill=INK)

    # snowflake scales along the body
    for i in range(14, N - 6, 22):
        x, y = pts[i]
        snowflake(d, x, y, 11, col=(150, 200, 235), w=2)

    # ---- head -------------------------------------------------------------
    hx, hy = pts[-1][0] + 2, pts[-1][1] - 34
    d.ellipse([hx - 58, hy - 46, hx + 58, hy + 46], fill=BODY, outline=INK, width=4)
    # eyes
    for sx in (-24, 24):
        d.ellipse([hx + sx - 13, hy - 8, hx + sx + 13, hy + 18], fill=(255, 255, 255),
                  outline=INK, width=3)
        d.ellipse([hx + sx - 5, hy + 2, hx + sx + 6, hy + 13], fill=INK)
        d.ellipse([hx + sx - 2, hy + 1, hx + sx + 2, hy + 5], fill=(255, 255, 255))
    # smile
    d.arc([hx - 26, hy + 8, hx + 26, hy + 40], start=15, end=165, fill=INK, width=3)
    # tongue
    d.line([(hx, hy + 44), (hx, hy + 74)], fill=ACCENT, width=4)
    d.line([(hx, hy + 74), (hx - 14, hy + 92)], fill=ACCENT, width=4)
    d.line([(hx, hy + 74), (hx + 14, hy + 92)], fill=ACCENT, width=4)

    # ---- headphones -------------------------------------------------------
    d.arc([hx - 66, hy - 84, hx + 66, hy + 30], start=185, end=355, fill=INK, width=9)
    for sx in (-64, 64):
        d.rounded_rectangle([hx + sx - 17, hy - 30, hx + sx + 17, hy + 34], radius=11,
                            fill=(44, 48, 58), outline=INK, width=3)
        d.rounded_rectangle([hx + sx - 10, hy - 16, hx + sx + 10, hy + 22], radius=7,
                            fill=ACCENT)
    # cable down from the left cup, looping to the coil
    jline(d, [(hx - 64, hy + 34), (hx - 96, hy + 96), (hx - 40, hy + 150)], width=4, fill=INK)

    # ---- music notes ------------------------------------------------------
    def note(x, y, s=1.0, col=INK):
        d.ellipse([x - 11 * s, y - 8 * s, x + 11 * s, y + 8 * s], fill=col)
        d.line([(x + 9 * s, y), (x + 9 * s, y - 54 * s)], fill=col, width=int(4 * s))
        d.line([(x + 9 * s, y - 54 * s), (x + 30 * s, y - 46 * s)], fill=col, width=int(4 * s))

    note(548, 372, 1.15, ACCENT)
    note(600, 430, 1.0, INK)
    note(112, 404, 0.95, INK)

    # ---- condiment stamp (nod to the maker's Stamp tool) ------------------
    d.ellipse([86, 726, 154, 776], fill=(196, 42, 42))
    d.ellipse([96, 716, 128, 740], fill=(196, 42, 42))
    d.ellipse([126, 712, 152, 734], fill=(196, 42, 42))
    d.text((86, 784), "SPICY", font=font(17), fill=(196, 42, 42))

    # ---- labels -----------------------------------------------------------
    d.text((44, 52), "SNOW BEATS", font=font(52), fill=INK)
    d.text((46, 116), tag, font=font(26), fill=SNOW)
    d.line([(44, 156), (300, 156)], fill=SNOW, width=4)

    f = font(34)
    tw = d.textlength(caption, font=f)
    d.text(((W - tw) / 2, 806), caption, font=f, fill=INK)
    d.text((W - 150, 858), "Z-DOT", font=font(19), fill=(150, 158, 170))

    img.save(path)
    return path


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "content/experiments/doodles/snow-beats-doodle.png"
    import os
    os.makedirs(os.path.dirname(out), exist_ok=True)
    print("wrote", draw(out))
