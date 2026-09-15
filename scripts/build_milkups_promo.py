#!/usr/bin/env python3
"""build_milkups_promo.py — South Park-style cutout promo for the MilkUps album.

Produces a 1080p MP4 with characters that MOVE (bob, limb swing, head tilt,
blink) and TALK (mouth flaps driven by the actual voice waveform envelope).

Art direction follows the locked SDW style: flat paper-cutout, thick black
outlines, simple shapes. Everything is drawn programmatically (PIL) and
animated frame-by-frame, then muxed with ffmpeg.

Voices: gTTS + ffmpeg pitch/tempo treatment so each character has a distinct
voice. Music bed: the album's own tracker cut.

Usage: python3 scripts/build_milkups_promo.py [--fps 24] [--draft]
"""
from __future__ import annotations
import argparse, json, math, os, subprocess, sys, wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ALBUM = ROOT / "content" / "milkups" / "album"
WORK = ROOT / "content" / "milkups" / "promo"
VOICE = WORK / "voice"
FRAMES = WORK / "frames"
W, H = 1920, 1080

# ── palette (flat, high-contrast, South Park-ish) ─────────────────────────────
INK = (16, 14, 22)
BG0, BG1 = (10, 9, 16), (34, 20, 54)

VIN = {"skin": (206, 216, 232), "shirt": (44, 108, 196), "pants": (28, 34, 52),
       "cap": (24, 40, 78), "hair": (30, 30, 38), "label": "VIN"}
QUE = {"skin": (232, 196, 156), "shirt": (208, 108, 44), "pants": (44, 40, 60),
       "cap": (120, 58, 20), "hair": (28, 22, 20), "label": "QUE"}
ACCENT = (255, 94, 168)
ACCENT2 = (94, 232, 255)


def font(sz, bold=True):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
              else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(p, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, **kw)


# ── voices ────────────────────────────────────────────────────────────────────
LINES = {
    "narrator": "MilkUps presents. The Shelves Raised Us.",
    "vin":      "You ain't ready for me, bro.",
    "que":      "Pass the sauce, pass the vibe.",
    "vin2":     "Five tracks. Straight off the shelves.",
    "que2":     "Real tracker cuts. Play it loud.",
    "tag":      "Out now.",
}
VOICE_FX = {                      # (tld for accent, pitch factor)
    "narrator": ("com", 0.76),
    "vin":      ("com.au", 0.90),
    "que":      ("com", 1.14),
    "vin2":     ("com.au", 0.90),
    "que2":     ("com", 1.14),
    "tag":      ("com", 0.84),
}


def make_voice():
    from gtts import gTTS
    VOICE.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, text in LINES.items():
        tld, pitch = VOICE_FX[name]
        raw = VOICE / f"{name}_raw.mp3"
        if not raw.exists():
            gTTS(text, lang="en", tld=tld).save(str(raw))
        dst = VOICE / f"{name}.wav"
        # pitch shift: asetrate moves pitch+speed, atempo restores duration
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw),
             "-af", f"asetrate=44100*{pitch},aresample=44100,atempo={1/pitch:.6f},"
                    f"highpass=f=90,acompressor=threshold=-16dB:ratio=3:attack=8:release=180",
             "-ac", "1", "-ar", "44100", str(dst)])
        out[name] = dst
    return out


# ── audio envelope (drives the mouth flaps from the REAL waveform) ────────────
def envelope(wav_path, fps):
    """Per-frame RMS of the voice, normalised 0..1. Mouth follows this."""
    with wave.open(str(wav_path)) as w:
        sr = w.getframerate()
        raw = w.readframes(w.getnframes())
    a = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    n = int(sr / fps)
    if a.size < n:
        return np.zeros(1, dtype=np.float32)
    trimmed = a[: (a.size // n) * n].reshape(-1, n)
    rms = np.sqrt(np.mean(trimmed ** 2, axis=1))
    peak = rms.max() or 1.0
    e = np.clip(rms / peak, 0, 1) ** 0.6
    # gate: below ~8% is silence -> keep the mouth shut
    e[e < 0.08] = 0.0
    return e.astype(np.float32)


def duration(wav_path):
    with wave.open(str(wav_path)) as w:
        return w.getnframes() / w.getframerate()


# ── character rig: parts drawn once, posed per frame ─────────────────────────
def _outline(d, pts, fill, width=6):
    d.polygon(pts, fill=fill, outline=INK, width=width)


def head_img(pal, mouth=0.0, blink=False):
    """Head as its own RGBA tile so it can tilt. mouth 0..1."""
    S = 260
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, top, bot = S // 2, 26, 224
    # ears
    for sx in (-1, 1):
        d.ellipse([cx + sx * 74 - 12, 104, cx + sx * 74 + 12, 140],
                  fill=pal["skin"], outline=INK, width=5)
    # head
    d.ellipse([cx - 78, top, cx + 78, bot], fill=pal["skin"], outline=INK, width=6)
    # hair / cap
    d.pieslice([cx - 78, top - 6, cx + 78, bot - 40], 180, 360, fill=pal["hair"], outline=INK, width=6)
    d.rectangle([cx - 82, top + 2, cx + 82, top + 26], fill=pal["cap"], outline=INK, width=5)
    d.rectangle([cx - 34, top + 20, cx + 34, top + 34], fill=pal["cap"], outline=INK, width=5)
    # eyes
    for sx in (-1, 1):
        ex = cx + sx * 30
        if blink:
            d.line([ex - 15, 118, ex + 15, 118], fill=INK, width=6)
        else:
            d.ellipse([ex - 16, 100, ex + 16, 134], fill=(255, 255, 255), outline=INK, width=5)
            d.ellipse([ex - 6, 110, ex + 6, 126], fill=INK)
    # brows
    for sx in (-1, 1):
        ex = cx + sx * 30
        d.line([ex - 17, 92 + sx * 2, ex + 17, 88 - sx * 2], fill=INK, width=7)
    # nose (a couple of South Park characters have one)
    d.line([cx, 138, cx, 152], fill=INK, width=5)
    # mouth: opens with the voice
    mh = 6 + int(mouth * 52)
    mw = 34 + int(mouth * 16)
    d.ellipse([cx - mw // 2, 166, cx + mw // 2, 166 + mh],
              fill=(58, 16, 24), outline=INK, width=5)
    if mh > 30:                       # teeth hint when wide open
        d.rectangle([cx - mw // 2 + 5, 166 + 4, cx + mw // 2 - 5, 176], fill=(238, 238, 232))
    return im


def torso_img(pal, label=""):
    S = (300, 300)
    im = Image.new("RGBA", S, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # jacket
    d.polygon([(64, 20), (236, 20), (250, 250), (50, 250)], fill=pal["shirt"], outline=INK, width=6)
    d.polygon([(122, 20), (178, 20), (188, 132), (112, 132)], fill=(238, 238, 232), outline=INK, width=5)
    d.line([(150, 20), (150, 250)], fill=INK, width=4)
    # collar
    d.polygon([(104, 18), (150, 76), (196, 18)], fill=pal["pants"], outline=INK, width=5)
    return im


def arm_img(pal, upper=True):
    S = (70, 190)
    im = Image.new("RGBA", S, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([8, 6, 62, 150 if upper else 170], radius=26,
                        fill=pal["shirt"] if upper else pal["skin"], outline=INK, width=6)
    if not upper:
        d.ellipse([6, 128, 64, 186], fill=pal["skin"], outline=INK, width=6)   # fist
    return im


def legs_img(pal):
    S = (300, 150)
    im = Image.new("RGBA", S, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for x0 in (60, 168):
        d.rounded_rectangle([x0, 0, x0 + 72, 112], radius=18,
                            fill=pal["pants"], outline=INK, width=6)
        d.rounded_rectangle([x0 - 12, 104, x0 + 84, 140], radius=16,
                            fill=(240, 240, 236), outline=INK, width=6)
    return im


# ── backdrops ────────────────────────────────────────────────────────────────
def backdrop_city():
    im = Image.new("RGB", (W, H), BG0)
    d = ImageDraw.Draw(im)
    for y in range(H):                                   # night gradient
        t = y / H
        d.line([(0, y), (W, y)],
               fill=(int(BG0[0] + (BG1[0] - BG0[0]) * t),
                     int(BG0[1] + (BG1[1] - BG0[1]) * t),
                     int(BG0[2] + (BG1[2] - BG0[2]) * t)))
    rng = np.random.default_rng(4)
    x = -40
    while x < W + 40:                                    # skyline
        bw = int(rng.integers(90, 190))
        bh = int(rng.integers(240, 620))
        d.rectangle([x, H - bh, x + bw, H], fill=(20, 18, 32), outline=(38, 34, 58), width=2)
        for wy in range(H - bh + 26, H - 40, 44):        # lit windows
            for wx in range(x + 16, x + bw - 20, 38):
                if rng.random() < 0.42:
                    c = ACCENT2 if rng.random() < 0.5 else (255, 206, 120)
                    d.rectangle([wx, wy, wx + 16, wy + 22], fill=c)
        x += bw + int(rng.integers(10, 40))
    glow = im.filter(ImageFilter.GaussianBlur(27))
    im = Image.blend(im, glow, 0.22)
    d = ImageDraw.Draw(im)
    d.rectangle([0, H - 96, W, H], fill=(14, 12, 22))    # road
    for sx in range(0, W, 160):                          # lane dashes
        d.rectangle([sx, H - 52, sx + 78, H - 42], fill=(214, 214, 226))
    return im


def backdrop_stage():
    im = Image.new("RGB", (W, H), (12, 10, 20))
    d = ImageDraw.Draw(im)
    for i in range(26):                                  # neon light beams
        a = math.radians(-120 + i * 6)
        col = ACCENT if i % 2 else ACCENT2
        x2, y2 = W / 2 + math.cos(a) * 2400, H + math.sin(a) * 2400
        d.line([(W / 2, H), (x2, y2)], fill=col, width=6)
    im = im.filter(ImageFilter.GaussianBlur(21))
    return Image.blend(im, Image.new("RGB", (W, H), (10, 9, 16)), 0.55)


# ── posing + compositing ─────────────────────────────────────────────────────
class Rig:
    def __init__(self, pal, label=""):
        self.pal, self.label = pal, label
        self.heads = {}
        for i in range(7):
            for b in (False, True):
                self.heads[(i, b)] = head_img(pal, i / 6.0, b)
        self.torso = torso_img(pal, label)
        self.arm_u, self.arm_l = arm_img(pal, True), arm_img(pal, False)
        self.legs = legs_img(pal)

    def draw(self, base, x, y, s, mouth, arm_l, arm_r, tilt, lean=0.0, blink=False):
        """Composite the character at (x, y) = feet centre. s = scale."""
        def sc(im, f):
            return im.resize((max(1, int(im.width * f)), max(1, int(im.height * f))), Image.LANCZOS)
        legs = sc(self.legs, s * 0.62)
        torso = sc(self.torso, s * 0.60)
        armu, arml = sc(self.arm_u, s * 0.44), sc(self.arm_l, s * 0.42)
        hi = self.heads[(min(6, int(mouth * 6)), blink)]
        head = sc(hi, s * 0.66)

        fx, fy = int(x), int(y)
        base.alpha_composite(legs, (fx - legs.width // 2, fy - legs.height))
        ty = fy - legs.height - torso.height + int(torso.height * 0.10)
        base.alpha_composite(torso, (fx - torso.width // 2 + int(lean * 20), ty))

        for side, ang in ((-1, arm_l), (1, arm_r)):
            arm = armu.rotate(-ang, resample=Image.BICUBIC, expand=True) if side < 0 \
                else armu.rotate(ang, resample=Image.BICUBIC, expand=True)
            ax = fx + side * int(torso.width * 0.44) - (arm.width if side < 0 else 0)
            base.alpha_composite(arm, (ax, ty + int(torso.height * 0.10)))
            hand = arml.rotate(-ang, resample=Image.BICUBIC, expand=True) if side < 0 \
                else arml.rotate(ang, resample=Image.BICUBIC, expand=True)
            hx = fx + side * int(torso.width * 0.52) - (hand.width if side < 0 else 0)
            base.alpha_composite(hand, (hx, ty + int(torso.height * 0.44)))

        h = head.rotate(-tilt, resample=Image.BICUBIC, expand=True)
        base.alpha_composite(h, (fx - h.width // 2 + int(lean * 26),
                                 ty - h.height + int(h.height * 0.14)))


# ── cached scaling (frame rendering must stay fast) ──────────────────────────
_SCACHE: dict = {}


def cached(im, f):
    key = (id(im), round(f, 4))
    got = _SCACHE.get(key)
    if got is None:
        got = im.resize((max(1, int(im.width * f)), max(1, int(im.height * f))), Image.LANCZOS)
        _SCACHE[key] = got
    return got


def draw_rig(rig, base, x, y, s, mouth, arm_l, arm_r, tilt, blink=False, lean=0.0):
    """Same composition as Rig.draw, but with cached part scaling."""
    legs = cached(rig.legs, s * 0.62)
    torso = cached(rig.torso, s * 0.60)
    armu = cached(rig.arm_u, s * 0.44)
    arml = cached(rig.arm_l, s * 0.42)
    head = cached(rig.heads[(min(6, int(mouth * 6)), blink)], s * 0.66)

    fx, fy = int(x), int(y)
    base.alpha_composite(legs, (fx - legs.width // 2, fy - legs.height))
    ty = fy - legs.height - torso.height + int(torso.height * 0.10)
    base.alpha_composite(torso, (fx - torso.width // 2 + int(lean * 20), ty))
    for side, ang in ((-1, arm_l), (1, arm_r)):
        rot = -ang if side < 0 else ang
        arm = cached(armu, 1.0).rotate(rot, resample=Image.BICUBIC, expand=True)
        ax = fx + side * int(torso.width * 0.44) - (arm.width if side < 0 else 0)
        base.alpha_composite(arm, (ax, ty + int(torso.height * 0.10)))
        hand = cached(arml, 1.0).rotate(rot, resample=Image.BICUBIC, expand=True)
        hx = fx + side * int(torso.width * 0.52) - (hand.width if side < 0 else 0)
        base.alpha_composite(hand, (hx, ty + int(torso.height * 0.44)))
    h = head.rotate(-tilt, resample=Image.BICUBIC, expand=True)
    base.alpha_composite(h, (fx - h.width // 2 + int(lean * 26),
                             ty - h.height + int(h.height * 0.14)))


def overlay_text(base, text, y, size=112, color=(255, 255, 255),
                 stroke=INK, sw=9, shadow=True, subtitle=None):
    d = ImageDraw.Draw(base)
    f = font(size)
    bbox = d.textbbox((0, 0), text, font=f, stroke_width=sw)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2 - bbox[0]
    if shadow:
        d.text((x + 7, y + 7), text, font=f, fill=(0, 0, 0, 170), stroke_width=sw, stroke_fill=(0, 0, 0, 170))
    d.text((x, y), text, font=f, fill=color, stroke_width=sw, stroke_fill=stroke)
    if subtitle:
        fs = font(int(size * 0.44))
        bb = d.textbbox((0, 0), subtitle, font=fs, stroke_width=5)
        sx = (W - (bb[2] - bb[0])) // 2 - bb[0]
        sy = y + (bbox[3] - bbox[1]) + 34
        d.text((sx + 4, sy + 4), subtitle, font=fs, fill=(0, 0, 0, 160), stroke_width=5,
               stroke_fill=(0, 0, 0, 160))
        d.text((sx, sy), subtitle, font=fs, fill=ACCENT2, stroke_width=5, stroke_fill=INK)


def neon_bar(base, y, h=8, col=ACCENT):
    d = ImageDraw.Draw(base)
    d.rectangle([0, y, W, y + h], fill=col)


# ── timeline ─────────────────────────────────────────────────────────────────
def build_timeline(vo):
    d = {k: duration(p) for k, p in vo.items()}
    t = 0.0
    seq = []
    narr = 0.55
    seq.append(("title", 0.0, narr + d["narrator"] + 0.75, None))
    t = narr + d["narrator"] + 0.75
    for line, scene, who in (("vin", "vin", "vin"), ("que", "que", "que"),
                             ("vin2", "both", "vin"), ("que2", "both", "que")):
        start = t + 0.35
        seq.append((scene, t, start + d[line] + 0.55, (line, who, start)))
        t = start + d[line] + 0.55
    seq.append(("end", t, t + d["tag"] + 2.4, ("tag", "narrator", t + 0.35)))
    return seq, d


def speaking_map(seq):
    """frame-time -> (who, line_key, line_start) for mouth sync."""
    items = [(a, b, meta) for _s, a, b, meta in seq if meta]
    def look(tt):
        for a, b, meta in items:
            line, who, start = meta
            if start <= tt <= start + 9.0:
                return who, line, start
        return None, None, 0.0
    return look


def scene_at(seq, tt):
    for name, a, b, _m in seq:
        if a <= tt < b:
            return name, (tt - a) / max(b - a, 1e-6)
    return seq[-1][0], 1.0


def render_frames(vo, fps, outdir, draft=False):
    outdir.mkdir(parents=True, exist_ok=True)
    seq, durs = build_timeline(vo)
    total = seq[-1][2] + 0.6
    n_frames = int(total * fps)
    speak = speaking_map(seq)
    envs = {k: envelope(p, fps) for k, p in vo.items()}

    city = backdrop_city().resize((int(W * 1.35), int(H * 1.35)), Image.LANCZOS)
    stage = backdrop_stage().resize((int(W * 1.35), int(H * 1.35)), Image.LANCZOS)

    vin, que = Rig(VIN, "VIN"), Rig(QUE, "QUE")

    def env_of(line, tt, start):
        e = envs.get(line)
        if e is None:
            return 0.0
        idx = int((tt - start) * fps)
        return float(e[idx]) if 0 <= idx < len(e) else 0.0

    def cam_for(scene, p):
        if scene in ("title", "vin"):
            return 1.06 + 0.10 * p, -60 + 90 * p
        if scene == "que":
            return 1.08 + 0.09 * p, 70 - 100 * p
        if scene == "both":
            return 1.02 + 0.12 * p, 0
        return 1.04 + 0.06 * p, 0

    def place(scene, p):
        """-> (vin_pos, que_pos, vin_scale, que_scale) with entrances."""
        ease = min(1.0, p * 2.6)
        if scene == "title":
            return (560 - 700 * (1 - ease), H - 132), (1360 + 700 * (1 - ease), H - 132), 1.0, 1.0
        if scene == "vin":
            return (760, H - 132), (1470, H - 138), 1.18, 0.94
        if scene == "que":
            return (470, H - 138), (1150, H - 132), 0.94, 1.18
        if scene == "both":
            return (700, H - 140), (1230, H - 140), 1.08, 1.08
        return (520, H - 150), (1400, H - 150), 0.92, 0.92

    for fi in range(n_frames):
        tt = fi / fps
        scene, p = scene_at(seq, tt)
        who, line, start = speak(tt)
        z, dx = cam_for(scene, p)

        bg = stage if scene in ("both", "end") else city
        cw, chh = int(W / z), int(H / z)
        ox = int((bg.width - cw) / 2 + dx)
        oy = int((bg.height - chh) / 2)
        ox = max(0, min(bg.width - cw, ox)); oy = max(0, min(bg.height - chh, oy))
        frame = bg.crop((ox, oy, ox + cw, oy + chh)).resize((W, H), Image.BILINEAR).convert("RGBA")

        (vx, vy), (qx, qy), vs, qs = place(scene, p)
        # world -> screen through the camera
        def cam(x, y, s):
            return ((x - W / 2) * z + W / 2 + dx * 0.5, (y - H / 2) * z + H / 2, s * z)

        bob_v = math.sin(2 * math.pi * 1.35 * tt) * 7
        bob_q = math.sin(2 * math.pi * 1.15 * tt + 1.1) * 7
        mv = env_of(line, tt, start) if who == "vin" else 0.0
        mq = env_of(line, tt, start) if who == "que" else 0.0
        gest_v = (1.0 if who == "vin" else 0.35)
        gest_q = (1.0 if who == "que" else 0.35)

        if scene != "title":
            cx, cy, cs = cam(*((vx, vy + bob_v)), vs)
            draw_rig(vin, frame, cx, cy, cs, mv,
                     22 + 34 * gest_v * abs(math.sin(2 * math.pi * 0.9 * tt)),
                     12 + 30 * gest_v * abs(math.sin(2 * math.pi * 0.75 * tt + 0.7)),
                     2.5 * math.sin(2 * math.pi * 0.5 * tt), blink=(int(tt * fps) % 97) < 3)
        cx, cy, cs = cam(*((qx, qy + bob_q)), qs)
        draw_rig(que, frame, cx, cy, cs, mq,
                 20 + 30 * gest_q * abs(math.sin(2 * math.pi * 0.8 * tt + 0.3)),
                 14 + 34 * gest_q * abs(math.sin(2 * math.pi * 0.95 * tt)),
                 -2.5 * math.sin(2 * math.pi * 0.55 * tt), blink=(int(tt * fps) % 113) < 3)

        overlay_frame_text(frame, scene, tt, seq, p)
        frame.convert("RGB").save(outdir / f"f{fi:05d}.png")
        if draft and fi > 40:
            break
    return n_frames, total, seq


def overlay_frame_text(frame, scene, tt, seq, p):
    """Titles, captions and the end card."""
    if scene == "title":
        if p < 0.34:
            overlay_text(frame, "MILKUPS", 300, 210, ACCENT)
            overlay_text(frame, "PRESENTS", 540, 92, (255, 255, 255))
        else:
            overlay_text(frame, "THE SHELVES", 300, 150, (255, 255, 255))
            overlay_text(frame, "RAISED US", 480, 150, ACCENT2)
            overlay_text(frame, "A TRACKER ALBUM", 700, 60, (222, 222, 236))
        neon_bar(frame, 250, 8, ACCENT)
        neon_bar(frame, 830, 8, ACCENT2)
    elif scene == "vin":
        overlay_text(frame, "\u201cYou ain\u2019t ready for me, bro.\u201d", 870, 74, (255, 255, 255))
        overlay_text(frame, "VIN NEGAR", 118, 78, ACCENT)
    elif scene == "que":
        overlay_text(frame, "\u201cPass the sauce, pass the vibe.\u201d", 870, 74, (255, 255, 255))
        overlay_text(frame, "QUE", 118, 78, ACCENT2)
    elif scene == "both":
        overlay_text(frame, "5 TRACKS \u00b7 TRACKER CUTS", 110, 84, (255, 255, 255))
        overlay_text(frame, "NO SAMPLES \u00b7 ALL BUILT IN-HOUSE", 840, 58, ACCENT2)
    elif scene == "end":
        cover = ALBUM.parent / "art" / "cover-1500.png"
        if cover.exists():
            c = Image.open(cover).convert("RGB")
            c.thumbnail((520, 520), Image.LANCZOS)
            frame.alpha_composite(c.convert("RGBA"), ((W - c.width) // 2, 250))
        overlay_text(frame, "OUT NOW", 82, 96, ACCENT)
        overlay_text(frame, "shelves-raised-us.netlify.app", 828, 62, ACCENT2, sw=7)
        neon_bar(frame, 200, 6, ACCENT)
        neon_bar(frame, 800, 6, ACCENT2)


# ── audio assembly ───────────────────────────────────────────────────────────
def build_audio(vo, seq, out_path, music):
    ins, filters, mix = [], [], []
    ins += ["-i", str(music)]
    idx = 1
    for _scene, a, b, meta in seq:
        if not meta:
            continue
        line, who, start = meta
        base = (idx - 1) * (2 if line == "tag" else 1)
        ins += ["-i", str(vo[line])]
        filters.append(f"[{idx}:a]adelay={int(start*1000)}|{int(start*1000)},volume=1.35[v{idx}]")
        mix.append(f"[v{idx}]")
        idx += 1
    fc = ";".join(filters)
    fc += ";" + "".join(mix) + f"amix=inputs={len(mix)}:normalize=0[voice]"
    fc += ";[voice]asplit=2[vsc][vmix]"
    fc += (";[0:a]atrim=0:40,afade=t=in:st=0:d=1.2,volume=0.85[bed]"
           ";[bed][vsc]sidechaincompress=threshold=0.045:ratio=9:attack=6:release=320[duck]")
    fc += ";[duck][vmix]amix=inputs=2:normalize=0[aout]"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *ins,
         "-filter_complex", fc, "-map", "[aout]", "-ar", "44100", "-ac", "2", str(out_path)])
    return out_path


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--skip-voice", action="store_true")
    a = ap.parse_args()

    WORK.mkdir(parents=True, exist_ok=True)
    print("[1/5] voices")
    vo = make_voice() if not a.skip_voice else {k: VOICE / f"{k}.wav" for k in LINES}
    for k, p in vo.items():
        print(f"   {k:<9} {duration(p):6.2f}s")

    print("[2/5] audio bed")
    music = ALBUM / "renders" / "lmms" / "trk02.wav"
    if not music.exists():
        music = ALBUM / "renders" / "xm" / "trk02.wav"
    seq, durs = build_timeline(vo)
    audio = WORK / "promo_audio.wav"
    build_audio(vo, seq, audio, music)
    print(f"   {audio.name}: {duration(audio):.2f}s")

    print("[3/5] frames")
    n, total, seq = render_frames(vo, a.fps, FRAMES, draft=a.draft)
    print(f"   {n} frames @ {a.fps}fps = {n/a.fps:.2f}s of video")

    print("[4/5] mux")
    mp4 = WORK / "milkups-promo.mp4"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-framerate", str(a.fps), "-i", str(FRAMES / "f%05d.png"),
         "-i", str(audio),
         "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium",
         "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
         "-c:a", "aac", "-b:a", "192k", "-shortest", str(mp4)])

    print("[5/5] verify")
    probe = run(["ffprobe", "-v", "error", "-show_entries",
                 "format=duration,size,bit_rate", "-show_entries",
                 "stream=codec_type,codec_name,width,height,r_frame_rate",
                 "-of", "json", str(mp4)]).stdout.decode()
    info = json.loads(probe)
    print(json.dumps(info, indent=1))
    (WORK / "promo-manifest.json").write_text(json.dumps(
        {"fps": a.fps, "frames": n, "video_seconds": n / a.fps,
         "timeline": [{"scene": s, "start": round(x, 3), "end": round(y, 3),
                       "line": (m[0] if m else None)} for s, x, y, m in seq],
         "voices": {k: round(duration(p), 3) for k, p in vo.items()},
         "ffprobe": info}, indent=2))
    print("manifest:", (WORK / "promo-manifest.json").relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
