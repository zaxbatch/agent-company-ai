#!/usr/bin/env python3
"""cover_basement_frost.py — 1000x1000 cover for "Basement Frost" (SnowSnakes house).

House aesthetic: deep indigo/violet, four-on-the-floor pulse dots (every beat lit),
a warm offbeat-hat shimmer band, and a soft grid suggesting a club floor.
Deterministic (fixed seed).
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1000
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content" / "snowsnakes" / "songs" / "art" / "basement-frost.png"
FONTS = Path("/usr/share/fonts/truetype/dejavu")

TITLE = "BASEMENT FROST"
ARTIST = "SNOWSNAKES"


def font(name, size):
    try:
        return ImageFont.truetype(str(FONTS / name), size)
    except OSError:
        return ImageFont.load_default()


def main():
    rng = np.random.default_rng(123)
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)

    # deep indigo -> violet glow gradient
    t = (y / H)[..., None]
    top = np.array([16, 12, 34], np.float32)
    bot = np.array([44, 20, 62], np.float32)
    base = top * (1 - t) + bot * t

    # warm centre glow (the club floor)
    cx, cy = W * 0.5, H * 0.56
    glow = np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (2 * (340.0 ** 2))))
    base[..., 0] += glow * 52
    base[..., 1] += glow * 20
    base[..., 2] += glow * 62

    # offbeat shimmer: horizontal bands of light (hats on the "and")
    shim = (np.sin((y - cy) / 17.0) ** 2) * np.exp(-np.abs(y - cy) / 150.0)
    base[..., 0] += shim * 14
    base[..., 1] += shim * 10
    base[..., 2] += shim * 26

    base += rng.normal(0, 2.2, base.shape).astype(np.float32)
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img, "RGBA")

    # four-on-the-floor: 16 dots, every 4th (the beat) lit bright
    for i in range(16):
        dx = 92 + i * 51
        if i % 4 == 0:
            d.ellipse([dx - 14, 824, dx + 14, 852], fill=(255, 206, 232, 220))
        else:
            d.ellipse([dx - 6, 830, dx + 6, 846], fill=(196, 150, 210, 110))

    d.rectangle([34, 34, W - 34, H - 34], outline=(220, 170, 235, 85), width=3)

    f_title = font("DejaVuSans-Bold.ttf", 96)
    f_sub = font("DejaVuSans.ttf", 38)
    f_small = font("DejaVuSans.ttf", 25)

    for text, f, yy, col in ((TITLE, f_title, 296, (250, 236, 255)),
                             (ARTIST, f_sub, 428, (232, 168, 226)),
                             ("FOUR ON THE FLOOR · 123 BPM", f_small, 596, (214, 168, 226))):
        b = d.textbbox((0, 0), text, font=f)
        d.text(((W - (b[2] - b[0])) / 2, yy), text, font=f, fill=col)

    img = img.filter(ImageFilter.GaussianBlur(0.5))
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=55, threshold=3))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"{OUT}  {img.size}  {OUT.stat().st_size//1024} KB")


if __name__ == "__main__":
    main()
