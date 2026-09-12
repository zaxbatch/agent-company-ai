#!/usr/bin/env python3
"""Render characters in flat "paper cutout" style (South Park look).

Style rules:
  - a handful of solid colours, no gradients, no soft shading
  - heavy dark outline around every shape edge
  - front-facing, readable silhouette
Depth is NOT faked with shading — it comes from layering and scale at scene
assembly time (near = larger + drawn in front, far = smaller + behind, plus an
optional hard drop shadow). All of that lives in the scene builder, not here.

    scripts/flat_style.py --in art.png --out flat.png
"""
from __future__ import annotations
import argparse, os, sys
from PIL import Image, ImageFilter

PALETTE_SIZE = 7
OUTLINE = (24, 20, 18)


def load_rgba(path):
    im = Image.open(path).convert("RGBA")
    # drop a flat dark plate if the art sits on one
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a and (0.299 * r + 0.587 * g + 0.114 * b) <= 12:
                px[x, y] = (r, g, b, 0)
    return im


def lift(im, sat=1.5, floor=0.18, ceil=1.0, p_lo=8, p_hi=97):
    """Auto-levels on the OPAQUE region: stretch the art's real (very dark) range
    up into a bright band, so flat fills read as cutout colours. Percentiles are
    taken from the character itself, so this adapts per sprite."""
    from PIL import ImageEnhance
    import numpy as np
    rgba = np.asarray(im.convert("RGBA")).astype(np.float32)
    m = rgba[..., 3] > 60
    if not m.any():
        return im.convert("RGB")
    lum = 0.299 * rgba[..., 0] + 0.587 * rgba[..., 1] + 0.114 * rgba[..., 2]
    lo = float(np.percentile(lum[m], p_lo)) / 255.0
    hi = float(np.percentile(lum[m], p_hi)) / 255.0
    if hi - lo < 1e-3:
        hi = lo + 0.05
    a = rgba[..., :3] / 255.0
    a = (a - lo) / (hi - lo)
    a = floor + (ceil - floor) * np.clip(a, 0, 1)
    out = Image.fromarray((np.clip(a, 0, 1) * 255).astype("uint8"))
    out = ImageEnhance.Color(out).enhance(sat)
    return ImageEnhance.Contrast(out).enhance(1.05)


def drop_shadow(size, offset=(7, 7), alpha=110):
    """Hard offset shadow — depth in flat style (no blur, no gradient)."""
    return offset, alpha


def flatify(path, colors=PALETTE_SIZE, outline_px=2, out=None, lift_levels=False,
            shadow=False):
    im = load_rgba(path)
    alpha = im.split()[3]
    solid = alpha.point(lambda v: 255 if v > 60 else 0)

    # 1. optional level lift, then collapse to a small flat palette
    base = lift(im.convert("RGB")) if lift_levels else im.convert("RGB")
    quant = base.quantize(colors=colors, method=Image.MEDIANCUT,
                          dither=Image.NONE).convert("RGB")

    # 2. thick outline traced from the silhouette
    edge = solid.filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 40 else 0)
    if outline_px > 0:
        edge = edge.filter(ImageFilter.MaxFilter(outline_px * 2 + 1))

    outline = Image.new("RGBA", im.size, OUTLINE + (255,))
    outline.putalpha(edge.point(lambda v: 255 if v > 60 else 0))

    # 3. flat fills on top -> outline shows only at the border, cutout style
    fill = Image.new("RGBA", im.size, (0, 0, 0, 0))
    fill.paste(quant, (0, 0), solid)

    result = Image.alpha_composite(outline, fill)

    if shadow:
        # depth: a hard offset silhouette in a hard alpha, drawn behind the art
        pad = 14
        canvas = Image.new("RGBA", (im.width + pad, im.height + pad), (0, 0, 0, 0))
        sh = Image.new("RGBA", im.size, (16, 14, 20, 255))
        sh.putalpha(solid.point(lambda v: int(v * 0.45)))
        canvas.alpha_composite(sh, (pad // 2 + 7, pad // 2 + 7))
        canvas.alpha_composite(result, (pad // 2, pad // 2))
        result = canvas

    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        result.save(out)
    return result


def stats(im):
    cols = im.convert("RGBA").getcolors(maxcolors=1 << 20) or []
    opaque = sum(c for c, col in cols if col[3] > 200)
    dark = sum(c for c, col in cols if col[3] > 200 and sum(col[:3]) < 180)
    return len(cols), opaque, (dark / opaque if opaque else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst")
    ap.add_argument("--colors", type=int, default=PALETTE_SIZE)
    ap.add_argument("--lift", action="store_true", help="levels+saturation lift")
    ap.add_argument("--shadow", action="store_true", help="hard drop shadow (depth)")
    a = ap.parse_args()
    before = Image.open(a.src).convert("RGBA")
    after = flatify(a.src, a.colors, out=a.dst, lift_levels=a.lift, shadow=a.shadow)
    b0, o0, d0 = stats(before)
    b1, o1, d1 = stats(after)
    print(f"  {os.path.basename(a.src)}")
    print(f"    colours   {b0:>7} -> {b1:>7}")
    print(f"    dark fill {d0*100:6.1f}% -> {d1*100:6.1f}%  (outline weight)")
    if a.dst:
        print(f"    wrote {a.dst}")
