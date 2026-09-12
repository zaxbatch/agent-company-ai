#!/usr/bin/env python3
"""15-second MilkUps soundtrack commercial, in flat paper-cutout style.

Pencil2D has no CLI and will not start headless, but its project format (.pclx)
is a ZIP of main.xml + per-layer/frame PNGs — the same shape as .mmp and .sb3.
So this renders the commercial AND writes a real Pencil2D project containing the
same key frames, which opens in the GUI for hand editing.

    scripts/milkups_commercial.py --audio content/experiments/songs/milkups-raised-on-the-shelves-lmms.wav
"""
from __future__ import annotations
import argparse, io, math, os, shutil, subprocess, sys, zipfile
from xml.sax.saxutils import escape
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flat_style import flatify

W, H, FPS, DUR = 1280, 720, 24, 15.0
N = int(FPS * DUR)                      # 360 frames

# MilkUps palette (from their site) + flat-cutout neutrals
CREAM = (247, 240, 228)
PLUM = (108, 60, 140)
PLUM_D = (72, 38, 96)
LILAC = (176, 140, 200)
INK = (28, 22, 34)
GOLD = (232, 168, 72)
MINT = (126, 206, 178)

CARDS = [
    # start_s, end_s, kind, payload
    (0.0,   2.0,  "brand", None),
    (2.0,   5.5,  "char",  ("vin", "Raised on the shelves.")),
    (5.5,   9.0,  "char",  ("q",   "Every tape hits.")),
    (9.0,   12.0, "album", None),
    (12.0,  15.0, "end",   None),
]


def font(sz, bold=True):
    p = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
         else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    try:
        return ImageFont.truetype(p, sz)
    except OSError:
        return ImageFont.load_default()


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def crop_alpha(p):
    im = p if isinstance(p, Image.Image) else Image.open(p)
    im = im.convert("RGBA")
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def fit_h(im, h):
    s = h / im.height
    return im.resize((max(1, int(im.width * s)), h), Image.LANCZOS)


def centred(d, text, f, y, fill):
    w = d.textlength(text, font=f)
    d.text(((W - w) / 2, y), text, font=f, fill=fill)


def band(d, y0, y1, col):
    d.rectangle([0, y0, W, y1], fill=col)


class Char:
    def __init__(self, path, h):
        cropped = crop_alpha(path)                 # crop on the original art
        flat = flatify(cropped, out=None, lift_levels=True)   # then flatten
        self.im = fit_h(flat, h)


def card_brand(d, img, t):
    """MilkUps wordmark on a plum band, sliding in from below."""
    p = ease(t / 0.45)
    band(d, 0, H, CREAM)
    y = H * 0.34
    off = int((1 - p) * 90)
    f = font(150)
    centred(d, "MilkUps", f, y + off, PLUM)
    if t > 0.35:
        p2 = ease((t - 0.35) / 0.4)
        f2 = font(46)
        centred(d, "THE SOUNDTRACK", f2, y + 190 + int((1 - p2) * 40), INK)
    band(d, H - 26, H, PLUM)
    band(d, H - 26, H - 20, GOLD)


def card_char(d, img, chars, key, line, t):
    """Character enters with a slide + pop, drop shadow behind (depth)."""
    accent = {"vin": PLUM, "q": GOLD}[key]
    d.rectangle([0, 0, W, H], fill=CREAM)
    band(d, 0, 96, accent)

    ch = chars[key]
    p = ease(t / 0.35)
    h = int(H * 0.72)
    im = ch.im if ch.im.height == h else fit_h(ch.im, h)
    x = int((W - im.width) / 2 + (1 - p) * 130)
    y = int(H - im.height - 84 + (1 - p) * 60)

    # hard drop shadow = flat depth
    sh = Image.new("RGBA", im.size, (40, 30, 50, 255))
    sh.putalpha(im.split()[3].point(lambda v: int(v * 0.30)))
    img.alpha_composite(sh, (x + 14, y + 14))
    img.alpha_composite(im, (x, y))

    if t > 0.30:
        p2 = ease((t - 0.30) / 0.30)
        f = font(60)
        tw = d.textlength(line, font=f)
        bx0 = (W - tw) / 2 - 28
        d.rounded_rectangle([bx0, H - 118 + int((1 - p2) * 30),
                             bx0 + tw + 56, H - 34 + int((1 - p2) * 30)],
                            radius=14, fill=INK)
        d.text(((W - tw) / 2, H - 106 + int((1 - p2) * 30)), line, font=f, fill=CREAM)


def card_duo(d, img, chars, t):
    """Vin and Q side by side, back character smaller = depth."""
    d.rectangle([0, 0, W, H], fill=CREAM)
    band(d, 0, 96, PLUM)
    f = font(42)
    centred(d, "SPREAD DA WORD  ·  THE SOUNDTRACK", f, 28, CREAM)

    p = ease(t / 0.4)
    back = chars["q"]; front = chars["vin"]
    bh = int(H * 0.60); fh = int(H * 0.78)
    bi = back.im if back.im.height == bh else fit_h(back.im, bh)
    fi = front.im if front.im.height == fh else fit_h(front.im, fh)
    bx = int(W * 0.20 - bi.width / 2 + (1 - p) * -90)
    fx = int(W * 0.62 - fi.width / 2 + (1 - p) * 90)
    by = H - bi.height - 96          # back row: higher, drawn first
    fy = H - fi.height - 62          # front row: lower, drawn on top

    sh = Image.new("RGBA", bi.size, (40, 30, 50, 255))
    sh.putalpha(bi.split()[3].point(lambda v: int(v * 0.26)))
    img.alpha_composite(sh, (bx + 10, by + 10))
    img.alpha_composite(bi, (bx, by))
    sh2 = Image.new("RGBA", fi.size, (40, 30, 50, 255))
    sh2.putalpha(fi.split()[3].point(lambda v: int(v * 0.34)))
    img.alpha_composite(sh2, (fx + 15, fy + 15))
    img.alpha_composite(fi, (fx, fy))

    if t > 0.34:
        p2 = ease((t - 0.34) / 0.3)
        f2 = font(56)
        line = "The shelves raised us."
        tw = d.textlength(line, font=f2)
        bx0 = (W - tw) / 2 - 26
        d.rounded_rectangle([bx0, H - 116 + int((1 - p2) * 26), bx0 + tw + 52,
                             H - 36 + int((1 - p2) * 26)], radius=14, fill=INK)
        d.text(((W - tw) / 2, H - 104 + int((1 - p2) * 26)), line, font=f2, fill=CREAM)


def card_album(d, t):
    d.rectangle([0, 0, W, H], fill=PLUM_D)
    for i in range(7):
        p = ease(max(0.0, min(1.0, (t - i * 0.07) / 0.4)))
        w = int(W * p)
        d.rectangle([0, 60 + i * 96, w, 60 + i * 96 + 6], fill=LILAC)

    p = ease(t / 0.5)
    f1 = font(46)
    centred(d, "THE ALBUM", f1, 190 + int((1 - p) * 30), LILAC)
    f2 = font(112)
    line1, line2 = "THE SHELVES", "RAISED US"
    w1 = d.textlength(line1, font=f2)
    d.text(((W - w1) / 2, 262 + int((1 - ease(t / 0.55)) * 40)), line1, font=f2, fill=CREAM)
    if t > 0.25:
        p3 = ease((t - 0.25) / 0.5)
        w2 = d.textlength(line2, font=f2)
        d.text(((W - w2) / 2, 380 + int((1 - p3) * 40)), line2, font=f2, fill=GOLD)
    d.rectangle([(W - 260) / 2, 528, (W + 260) / 2, 536], fill=MINT)


def card_end(d, t):
    d.rectangle([0, 0, W, H], fill=CREAM)
    band(d, 0, 14, PLUM)
    band(d, H - 14, H, PLUM)
    p = ease(t / 0.45)
    f1 = font(92)
    centred(d, "MilkUps", f1, 132 + int((1 - p) * 30), PLUM)
    f2 = font(40)
    centred(d, "milkups.zerric.xyz", f2, 268, INK)

    if t > 0.28:
        p2 = ease((t - 0.28) / 0.45)
        d.rounded_rectangle([(W - 660) / 2, 348 + int((1 - p2) * 24),
                             (W + 660) / 2, 452 + int((1 - p2) * 24)],
                            radius=18, fill=PLUM)
        f3 = font(52)
        centred(d, "SUPPORT THE TAPES  ·  $zdotllc", f3, 372 + int((1 - p2) * 24), CREAM)

    if t > 0.55:
        p3 = ease((t - 0.55) / 0.4)
        f4 = font(30, False)
        centred(d, "Cash App  ·  scan or send", f4, 486 + int((1 - p3) * 20), (120, 110, 130))
    if t > 0.75:
        p4 = ease((t - 0.75) / 0.25)
        f5 = font(28, False)
        centred(d, "a Z-Dot production", f5, 600, (150, 140, 160))


def build_frames(refdir, outdir):
    os.makedirs(outdir, exist_ok=True)
    chars = {}
    for k in ("vin", "q"):
        p = os.path.join(refdir, f"{k}.png")
        chars[k] = Char(p, int(H * 0.72))
        print(f"  character {k}: {chars[k].im.size}")

    # pre-render each card once (they are static within a card except motion)
    for i in range(N):
        tsec = i / FPS
        card = next(c for c in CARDS if c[0] <= tsec < c[1])
        start, end, kind, payload = card
        t = (tsec - start) / (end - start)

        img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
        d = ImageDraw.Draw(img)
        if kind == "brand":
            card_brand(d, img, t)
        elif kind == "char":
            card_char(d, img, chars, payload[0], payload[1], t)
        elif kind == "duo":
            card_duo(d, img, chars, t)
        elif kind == "album":
            card_album(d, t)
        else:
            card_end(d, t)

        # 4-frame white flash on every cut (flat, punchy)
        if i % (FPS * 1) == 0 and i > 0:
            img = Image.blend(img, Image.new("RGBA", (W, H), (255, 255, 255, 255)), 0.35)
        img.convert("RGB").save(os.path.join(outdir, f"c{i:04d}.png"))
    return chars


def write_pclx(path, framedir, keys):
    """A real Pencil2D project: 3 layers, key frames at each card boundary."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    layers = [("Background", 1), ("Characters", 2), ("Titles", 3)]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "application/x-pencil2d-pclx")
        imgs = []
        for lname, lid in layers:
            for kf in keys:
                src = os.path.join(framedir, f"c{kf:04d}.png")
                if not os.path.exists(src):
                    continue
                name = f"data/{lid:03d}.{kf+1:03d}.png"
                z.write(src, name)
                imgs.append((lid, kf + 1, f"{lid:03d}.{kf+1:03d}.png"))
        obj = []
        obj.append(f'<layer name="Camera Layer" type="5" width="{W}" height="{H}" id="1" visibility="1">'
                   f'<camera frame="1" dx="0" dy="0" r="0" s="1"/></layer>')
        for lname, lid in layers:
            ent = "".join(f'<image src="{s}" frame="{f}" topLeftX="0" topLeftY="0" opacity="1"/>'
                          for l, f, s in imgs if l == lid)
            obj.append(f'<layer name="{lname}" type="1" id="{lid+10}" visibility="1">{ent}</layer>')
        main = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE PencilDocument>\n<document>\n'
                '  <projectdata><currentFrame value="1"/><currentColor b="0" g="0" r="0" a="255"/>'
                '<currentLayer value="1"/><fps value="24"/><isLoop value="false"/>'
                '<isRangedPlayback value="false"/><markInFrame value="1"/>'
                f'<markOutFrame value="{N}"/></projectdata>\n  <object>\n    '
                + "\n    ".join(obj) +
                f'\n  </object>\n  <version>0.6.6</version>\n</document>\n')
        z.writestr("main.xml", main)
    return os.path.getsize(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refdir", default="/tmp/sdwref")
    ap.add_argument("--audio", default="content/experiments/songs/milkups-raised-on-the-shelves-lmms.wav")
    ap.add_argument("--outdir", default="/tmp/milkups_ad")
    ap.add_argument("--out", default="content/experiments/milkups/milkups-commercial.mp4")
    ap.add_argument("--pclx", default="content/experiments/milkups/milkups-commercial.pclx")
    a = ap.parse_args()

    framedir = os.path.join(a.outdir, "frames")
    shutil.rmtree(framedir, ignore_errors=True)
    print(f"frames: {N} @ {FPS}fps = {N/FPS:.1f}s, {W}x{H}")
    chars = build_frames(a.refdir, framedir)

    # audio: first 15s of the MilkUps soundtrack, faded out
    mp4 = a.out
    os.makedirs(os.path.dirname(os.path.abspath(mp4)), exist_ok=True)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-framerate", str(FPS), "-i", os.path.join(framedir, "c%04d.png")]
    if a.audio and os.path.exists(a.audio):
        cmd += ["-i", a.audio]
    cmd += ["-t", str(DUR)]
    if a.audio and os.path.exists(a.audio):
        cmd += ["-map", "0:v", "-map", "1:a",
                "-af", f"atrim=0:{DUR},afade=t=out:st={DUR-1.6}:d=1.6",
                "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
            "-preset", "slow", "-movflags", "+faststart", mp4]
    subprocess.run(cmd, check=True)
    print("wrote", mp4, os.path.getsize(mp4), "bytes")

    keys = [int(c[0] * FPS) for c in CARDS]
    size = write_pclx(a.pclx, framedir, keys)
    print(f"wrote {a.pclx} ({size} B) — key frames at {keys}")


if __name__ == "__main__":
    main()
