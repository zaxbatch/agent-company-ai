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
