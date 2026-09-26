#!/usr/bin/env python3
"""cover_ice_cold_pockets.py — 1000x1000 cover for "Ice Cold Pockets" (trap).

Trap aesthetic: near-black frost with a cold blue/steel cast, half-time pulse
strip (one strong mark per bar), a dense 32nd-note hat roll rendered as a hatched
band, and a chrome title. Deterministic (fixed seed).
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1000
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content" / "snowsnakes" / "songs" / "art" / "ice-cold-pockets.png"
FONTS = Path("/usr/share/fonts/truetype/dejavu")

TITLE = "ICE COLD POCKETS"
ARTIST = "SNOWSNAKES"


def font(name, size):
    try:
        return ImageFont.truetype(str(FONTS / name), size)
    except OSError:
        return ImageFont.load_default()


def main():
    rng = np.random.default_rng(140)
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)

    # cold near-black -> steel blue gradient
    t = (y / H)[..., None]
    base = np.array([10, 12, 16], np.float32) * (1 - t) + np.array([26, 38, 52], np.float32) * t
    # horizontal steel banding
    base[..., 2] += (np.sin(y / 90.0) ** 2) * 10

    # cold glow behind the title
    cx, cy = W * 0.5, H * 0.52
    glow = np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (2 * (330.0 ** 2))))
    base[..., 0] += glow * 20
    base[..., 1] += glow * 34
    base[..., 2] += glow * 58

    base += rng.normal(0, 2.0, base.shape).astype(np.float32)
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img, "RGBA")

    # dense 32nd hat-roll band (hatching)
    for i in range(84):
        hx = 70 + i * 10.4
        d.line([hx, 214, hx + 4, 246], fill=(150, 200, 240, 46), width=2)

    # half-time pulse: one strong kick mark per bar, clap on the half
    for b in range(8):
        bx = 92 + b * 104
        d.rectangle([bx - 3, 288, bx + 3, 316], fill=(190, 235, 255, 165))
        d.rectangle([bx + 49, 298, bx + 52, 310], fill=(120, 175, 215, 95))

    d.rectangle([34, 34, W - 34, H - 34], outline=(150, 200, 235, 80), width=3)

    f_title = font("DejaVuSans-Bold.ttf", 82)
    f_sub = font("DejaVuSans.ttf", 38)
    f_small = font("DejaVuSans.ttf", 25)

    for text, f, yy, col in ((TITLE, f_title, 400, (238, 248, 255)),
                             (ARTIST, f_sub, 520, (160, 208, 246)),
                             ("HALF-TIME · 140 BPM", f_small, 676, (150, 195, 232))):
        bb = d.textbbox((0, 0), text, font=f)
        d.text(((W - (bb[2] - bb[0])) / 2, yy), text, font=f, fill=col)

    img = img.filter(ImageFilter.GaussianBlur(0.45))
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=55, threshold=3))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"{OUT}  {img.size}  {OUT.stat().st_size//1024} KB")


if __name__ == "__main__":
    main()
