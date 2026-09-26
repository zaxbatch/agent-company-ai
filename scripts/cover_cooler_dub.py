#!/usr/bin/env python3
"""cover_cooler_dub.py — 1000x1000 cover for "Frostline Dub" (SnowSnakes).

Dark dub aesthetic: deep teal/night background, a dub delay-tail ripple motif,
vinyl-ish texture, title + artist. Deterministic (fixed seed).
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1000
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content" / "snowsnakes" / "songs" / "art" / "frostline-dub.png"
FONT_DIR = Path("/usr/share/fonts/truetype")

TITLE = "FROSTLINE DUB"
ARTIST = "SNOWSNAKES"


def font(path, size):
    for p in (FONT_DIR / path,):
        try:
            return ImageFont.truetype(str(p), size)
        except OSError:
            continue
    return ImageFont.load_default()


def main():
    rng = np.random.default_rng(76)          # seeded -> deterministic
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)

    # vertical gradient: cold night -> deep teal
    t = (y / H)[..., None]
    top = np.array([8, 16, 26], np.float32)
    bot = np.array([14, 52, 58], np.float32)
    base = top * (1 - t) + bot * t

    # concentric delay ripples from an off-centre point (the echo motif)
    cx, cy = W * 0.40, H * 0.52
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    ripple = np.sin(r / 26.0) * np.exp(-r / 420.0)
    base[..., 1] += ripple * 16.0
    base[..., 2] += ripple * 22.0

    # soft radial glow behind the title
    glow = np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (2 * (330.0 ** 2))))
    base[..., 0] += glow * 10
    base[..., 1] += glow * 34
    base[..., 2] += glow * 44

    # fine film grain
    base += rng.normal(0, 2.4, base.shape).astype(np.float32)
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")

    # dotted bassline: a row of soft dots on the lower third (kick on beat 3)
    d = ImageDraw.Draw(img, "RGBA")
    for i in range(16):
        dx = 90 + i * 52
        strong = (i == 8)
        if strong:
            d.ellipse([dx - 15, 742, dx + 15, 772], fill=(180, 240, 235, 190))
        elif i % 4 == 2:
            d.ellipse([dx - 7, 750, dx + 7, 764], fill=(120, 200, 205, 120))

    # frame
    d.rectangle([34, 34, W - 34, H - 34], outline=(150, 220, 220, 90), width=3)

    f_title = font("dejavu/DejaVuSans-Bold.ttf", 104)
    f_sub = font("dejavu/DejaVuSans.ttf", 40)
    f_small = font("dejavu/DejaVuSans.ttf", 26)

    tw = d.textbbox((0, 0), TITLE, font=f_title)
    d.text(((W - (tw[2] - tw[0])) / 2, 300), TITLE, font=f_title, fill=(236, 252, 250))
    sw = d.textbbox((0, 0), ARTIST, font=f_sub)
    d.text(((W - (sw[2] - sw[0])) / 2, 440), ARTIST, font=f_sub, fill=(140, 232, 226))
    lw = d.textbbox((0, 0), "ONE DROP · 76 BPM", font=f_small)
    d.text(((W - (lw[2] - lw[0])) / 2, 640), "ONE DROP · 76 BPM",
           font=f_small, fill=(120, 205, 200))

    # slight blur then sharpen back -> analogue feel
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=3))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"{OUT}  {img.size}  {OUT.stat().st_size//1024} KB")


if __name__ == "__main__":
    main()
