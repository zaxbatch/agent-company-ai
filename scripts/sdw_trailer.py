#!/usr/bin/env python3
"""Build a trailer-style SDW scene: frames + MP4, cut to the 128 BPM beat.

Timing is derived from the music, not guessed: 64 beats at 128 BPM = 30.0 s,
and at 24 fps that is exactly 720 frames. Every card change lands on a beat.

    scripts/sdw_trailer.py --outdir /tmp/sdw
"""
from __future__ import annotations
import argparse, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
FPS = 24
BPM = 128
SPB = 60.0 / BPM                       # 0.46875 s per beat
FRAMES = int(round(64 * SPB * FPS))    # 720
BAR = int(4 * SPB * FPS)               # 45 frames per bar
BEAT = SPB * FPS                       # 11.25 frames

BG_DARK = (6, 8, 14)
ACCENTS = {
    "vin":     (52, 152, 219),
    "q":       (241, 196, 15),
    "manny":   (41, 128, 185),
    "miracle": (142, 68, 173),
    "tom":     (192, 57, 43),
    "jr":      (230, 126, 34),
    "family":  (243, 156, 18),
}
# roster order = escalation; last card is the group
CARDS = [
    ("vin",     "VIN NEGAR",            "THE REALEST"),
    ("q",       "Q",                    "THE HYPE MAN"),
    ("manny",   "MANNY 'DA MAN' AYES",  ""),
    ("miracle", "MIRACLE AYES",         ""),
    ("tom",     "TOM",                  "32OZ REDNECK PATRIARCH"),
    ("jr",      "TOM JR.",              "14OZ OPTIMIST"),
    ("family",  "THE FAMILY",           "SPREAD DA WORD"),
]


def font(sz):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(p, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def key_out(path):
    """Character art sits on a near-black plate; key it to transparency."""
    im = Image.open(path).convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if lum <= 14:
                px[x, y] = (r, g, b, 0)
            elif lum < 40:
                px[x, y] = (r, g, b, int(255 * (lum - 14) / 26))
    return im


def zoom(im, s):
    if abs(s - 1.0) < 0.005:
        return im
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


def glow(im, col, radius=26, strength=0.55):
    a = im.split()[3].filter(ImageFilter.GaussianBlur(radius))
    g = Image.new("RGBA", im.size, col + (0,))
    g.putalpha(a.point(lambda v: int(v * strength)))
    return Image.alpha_composite(g, im)


def ease(t):
    return t * t * (3 - 2 * t)


def letterbox(img, ratio=2.39):
    bar = int((H - W / ratio) / 2)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, bar], fill=(0, 0, 0))
    d.rectangle([0, H - bar, W, H], fill=(0, 0, 0))
    return img


def vignette(img):
    v = Image.new("L", (W, H), 0)
    dv = ImageDraw.Draw(v)
    dv.ellipse([-W * 0.25, -H * 0.35, W * 1.25, H * 1.35], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(140))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    return Image.composite(img, dark, v)


def card_frame(chars, key, name, sub, accent, prog, bar_shift=0):
    """prog 0..1 within the card: push-in, name slam, subtitle fade."""
    img = Image.new("RGBA", (W, H), BG_DARK + (255,))

    # background wash in the accent colour, brighter on the hit
    wash = Image.new("RGBA", (W, H), accent + (0,))
    base = 26 + 46 * (1 - prog) ** 2
    wash.putalpha(int(base))
    img = Image.alpha_composite(img, wash)

    art = chars.get(key)
    if art:
        s = 1.06 + 0.10 * ease(prog)          # slow push-in
        a = zoom(art, s)
        if a.width > W:
            a = a.crop(((a.width - W) // 2, 0, (a.width - W) // 2 + W, a.height))
        y = int(H * 0.42) - a.height // 2 + int(18 * (1 - prog))
        x = (W - a.width) // 2
        img.alpha_composite(a, (x, y))

    img = vignette(img)
    d = ImageDraw.Draw(img)

    # name slams in over the first 30% of the card
    t = min(1.0, prog / 0.3)
    if t > 0:
        off = int((1 - ease(t)) * 90)
        f = font(104)
        tw = d.textlength(name, font=f)
        x = (W - tw) / 2
        y = H - 330 + off
        for dx, dy in ((5, 5),):
            d.text((x + dx, y + dy), name, font=f, fill=(0, 0, 0, 200))
        d.text((x, y), name, font=f, fill=(255, 255, 255))
        d.rectangle([(W - tw) / 2 - 26, y + 128, (W + tw) / 2 + 26, y + 134], fill=accent)
    if sub and prog > 0.35:
        t2 = min(1.0, (prog - 0.35) / 0.35)
        f2 = font(40)
        tw2 = d.textlength(sub, font=f2)
        d.text(((W - tw2) / 2, H - 175), sub, font=f2,
               fill=(230, 230, 230, int(255 * t2)))
    return letterbox(img)


def plain_frame(lines, accent=(240, 240, 240), sub=None, size=118, bg=BG_DARK):
    img = Image.new("RGBA", (W, H), bg + (255,))
    if accent != (240, 240, 240):
        wash = Image.new("RGBA", (W, H), accent + (30,))
        img = Image.alpha_composite(img, wash)
    img = vignette(img)
    d = ImageDraw.Draw(img)
    f = font(size)
    y0 = H / 2 - len(lines) * size * 0.62
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=f)
        y = y0 + i * size * 1.24
        if accent != (240, 240, 240) and i == len(lines) - 1:
            d.text(((W - tw) / 2, y + 4), ln, font=f, fill=accent)
        d.text(((W - tw) / 2, y), ln, font=f, fill=(255, 255, 255))
    if sub:
        fs = font(38)
        tw = d.textlength(sub, font=fs)
        d.text(((W - tw) / 2, H - 210), sub, font=fs, fill=(190, 195, 205))
    return letterbox(img)


def build_frames(chars, outdir):
    os.makedirs(outdir, exist_ok=True)
    # beat-indexed plan: (start_beat, card_index or None) — planned on the grid
    plan = []
    plan.append((0,  ("studio",)))
    plan.append((8,  ("title",)))
    b = 16
    for i, c in enumerate(CARDS):
        plan.append((b, ("card", i)))
        b += 4
    plan.append((b, ("end",)))
    b += 8
    plan.append((b, ("sting",)))

    def seg_at(beat):
        cur = plan[0]
        for p in plan:
            if beat >= p[0]:
                cur = p
            else:
                break
        return cur

    for fi in range(FRAMES):
        beat = fi / BEAT
        sb, spec = seg_at(beat)
        nxt = next((p[0] for p in plan if p[0] > sb), 64)
        prog = min(1.0, (beat - sb) / max(1e-6, (nxt - sb)))
        kind = spec[0]

        if kind == "studio":
            img = plain_frame(["Z-DOT", "PICTURES"], accent=(120, 180, 240),
                              sub="presents", size=124)
        elif kind == "title":
            img = plain_frame(["SPREAD DA WORD"], accent=(243, 156, 18),
                              sub="a Z-Dot original series", size=150)
        elif kind == "card":
            key, name, sub = CARDS[spec[1]]
            img = card_frame(chars, key, name, sub, ACCENTS[key], prog)
        elif kind == "end":
            img = plain_frame(["THE FAMILY", "SPREAD DA WORD"], accent=(243, 156, 18),
                              sub="new episodes coming", size=112)
        else:
            img = plain_frame(["SPREAD DA WORD"], accent=(243, 156, 18), size=132)

        # hard cut feel: first 2 frames of a card get a white flash
        if kind == "card" and prog * (nxt - sb) < 0.12:
            img = Image.blend(img, Image.new("RGBA", (W, H), (255, 255, 255, 255)), 0.28)

        # fade from black at the top and to black at the tail
        if fi < 12:
            img = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), img, fi / 12)
        if fi > FRAMES - 18:
            img = Image.blend(img, Image.new("RGBA", (W, H), (0, 0, 0, 255)),
                              (fi - (FRAMES - 18)) / 18)
        img.convert("RGB").save(os.path.join(outdir, f"f{fi:04d}.png"))
    return plan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="/tmp/sdw")
    ap.add_argument("--refdir", default="/tmp/sdwref")
    ap.add_argument("--beat", default="content/experiments/lmms/beat-16bar.wav")
    a = ap.parse_args()
    fdir = os.path.join(a.outdir, "frames")
    os.makedirs(a.outdir, exist_ok=True)

    chars = {}
    for k in ACCENTS:
        p = os.path.join(a.refdir, f"{k}.png")
        if os.path.exists(p):
            chars[k] = key_out(p)
            print(f"keyed {k}: {chars[k].size}")

    print(f"frames: {FRAMES} @ {FPS}fps  ({FRAMES/FPS:.2f}s, 64 beats @ {BPM}bpm)")
    build_frames(chars, fdir)

    mp4 = os.path.join(a.outdir, "sdw-trailer.mp4")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-framerate", str(FPS), "-i", os.path.join(fdir, "f%04d.png"),
                    "-i", a.beat, "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                    "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
                    "-af", "afade=t=out:st=28:d=2", "-shortest", mp4], check=True)
    print("wrote", mp4, os.path.getsize(mp4), "bytes")


if __name__ == "__main__":
    main()
