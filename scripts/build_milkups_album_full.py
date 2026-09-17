#!/usr/bin/env python3
"""build_milkups_album_full.py — "COLD CUTS", a 6-track MilkUps album.

Applies content/snowsnakes/songs/STANDARD.md to a whole album. Two things are
enforced, not hoped for:

  1. VARIETY. Six tracks, six different genres and tempos, so no two share a
     groove + tempo bucket + brightness profile. The catalogue rule blocks it.
  2. SHAPE. Every track is arranged with an intro, a build, a climax, a real
     DIP/breakdown, and a final climax -- then verified from the rendered audio
     by albumkit.verify_structure(), which proves the dip and climax exist.

Genre-specific writing lives in GENRES below; the shape comes from albumkit.
All audio synthesized in-process. No external samples.

Usage:
  python3 scripts/build_milkups_album_full.py            # build + gate
  python3 scripts/build_milkups_album_full.py --post     # + upload to SnowSnakes
  python3 scripts/build_milkups_album_full.py --only 1   # one track
"""
from __future__ import annotations
import argparse, json, math, subprocess, sys, wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import songkit as sk
import albumkit as ak
from songkit import SR, hz, place, saw, sq, tri, sine, adsr, exp_decay, noise

OUT = ROOT / "content" / "milkups" / "album-full"
ALBUM = "COLD CUTS"

# ── the album: six genres, six tempos, six shapes ────────────────────────────
TRACKS = [
    {"n": 1, "title": "Midnight Aisle",       "genre": "disco",     "bpm": 118, "shape": "club",     },
    {"n": 2, "title": "Slack in the Cooler",  "genre": "boombap",   "bpm": 90,  "shape": "song",     },
    {"n": 3, "title": "Frostbite Boulevard",  "genre": "synthwave", "bpm": 96,  "shape": "slowburn", },
    {"n": 4, "title": "Milk Carton Club",     "genre": "house",     "bpm": 126, "shape": "club",     },
    {"n": 5, "title": "Sour Turn",            "genre": "trap",      "bpm": 140, "shape": "song",     },
    {"n": 6, "title": "Last One on the Shelf","genre": "ambient",   "bpm": 72,  "shape": "outro",    },
]


# ── shared drum kit, parameterised per genre ─────────────────────────────────
def d_kick(f0=138, f1=48, sweep=30, decay=7.5, click=0.5, dur=0.30):
    return sk.kick(f0, f1, sweep, decay, dur, click)


def d_snare(rng, decay=22, tone=190, mix=0.3):
    return sk.snare(rng, 0.20, decay, tone, mix)


def d_hat(rng, open_=False):
    return sk.hat(rng, open_, True)


# ── GENRE 1: DISCO — four-on-the-floor, offbeat string stabs ─────────────────
def g_disco(buf, bar, t0, sec, e, local, rng, ctx):
    SPB, BAR = ctx["SPB"], ctx["BAR"]
    root = [57, 53, 60, 55][bar % 4]
    if e > 0.45:
        for beat in range(4):
            place(buf, t0 + beat * SPB, d_kick(), (1.0 if beat in (0, 2) else 0.86) * e)
        for beat in (1, 3):
            place(buf, t0 + beat * SPB, sk.clap(rng), 0.85 * e)
    if e > 0.35:
        for eighth in range(8):
            place(buf, t0 + eighth * SPB / 2, d_hat(rng, eighth % 2 == 1),
                  (0.8 if eighth % 2 == 0 else 0.62) * e)
    if e > 0.30:
        for step in range(8):
            if step in (0, 3, 4, 6):
                m = root - 24 + (12 if step in (3, 6) else 0)
                place(buf, t0 + step * SPB / 2, sk.bass(m, SPB * 0.42), e)
    if e > 0.62:
        stab = sk.strings([root + 12, root + 15, root + 19, root + 24], 0.30)
        for i, g in enumerate((0.95, 0.75, 0.95, 0.85)):
            place(buf, t0 + SPB * (0.5 + i), stab, g * e)
    if e > 0.20:      # harmonic bed survives the dip so a breakdown stays musical
        place(buf, t0, sk.strings([root, root + 7, root + 12], SPB * 1.6, bright=0.55), 0.5 * e)
    if e > 0.85 and bar % 4 == 3:
        for i, m in enumerate([root + 12, root + 15, root + 19, root + 24, root + 27, root + 31]):
            place(buf, t0 + (2 + i * 0.33) * SPB, sk.strings([m], 0.22, bright=0.9), 0.9 * e)


# ── GENRE 2: BOOM BAP — backbeat, swung hats, Rhodes ────────────────────────
def g_boombap(buf, bar, t0, sec, e, local, rng, ctx):
    SPB, SW = ctx["SPB"], 0.62
    root = [50, 46, 43, 45][bar % 4]
    def sw(el):
        return t0 + (el // 2) * SPB + (0 if el % 2 == 0 else SPB * SW * 2)
    if e > 0.40:
        place(buf, t0, d_kick(96, 42, 19, 5.2, 0.0, 0.42), e)
        place(buf, t0 + 2 * SPB, d_kick(96, 42, 19, 5.2, 0.0, 0.42), 0.94 * e)
        if bar % 2 == 1:
            place(buf, t0 + 2.75 * SPB, d_kick(96, 42, 19, 5.2, 0.0, 0.42), 0.42 * e)
    if e > 0.45:
        place(buf, t0 + 1 * SPB, d_snare(rng, 13, 178, 0.42), e)
        place(buf, t0 + 3 * SPB, d_snare(rng, 13, 178, 0.42), e)
        if bar % 4 == 3:
            place(buf, t0 + 3.5 * SPB, d_snare(rng, 13, 178, 0.42), 0.35 * e)
    if e > 0.32:
        for el in range(8):
            if el % 2 == 0 or rng.random() < 0.55:
                place(buf, sw(el), sk.hat(rng, el == 7), (0.9 if el % 2 == 0 else 0.5) * e)
    if e > 0.38:
        for beat, oct_ in ((0, 0), (1, 7), (2, 0), (3, 5)):
            place(buf, t0 + beat * SPB, sk.bass(root - 24 + oct_, SPB * 0.78), e)
    if e > 0.20:      # keeps playing through the dip
        tones = [root - 12, root - 8, root - 5, root - 3]
        place(buf, t0, sk.epiano(tones, ctx["BAR"] * 0.92), min(1.0, e * 1.35))
    if e > 0.88 and bar % 4 == 2:
        for i, m in enumerate([root + 4, root + 7, root + 11]):
            place(buf, t0 + (1.5 + i * 0.25) * SPB, sk.brass(m, SPB * 0.30, 0.085), e)


# ── GENRE 3: SYNTHWAVE — slow, gated snare, wide pads ────────────────────────
def g_synthwave(buf, bar, t0, sec, e, local, rng, ctx):
    SPB, BAR = ctx["SPB"], ctx["BAR"]
    root = [45, 41, 48, 43][bar % 4]
    if e > 0.42:
        for beat in range(4):
            place(buf, t0 + beat * SPB, d_kick(150, 52, 34, 8.0, 0.35), e)
        for beat in (1, 3):                       # gated snare on 2 and 4
            s = d_snare(rng, 9, 200, 0.5)
            # gate length must never exceed the snare itself (blew up at 96 BPM:
            # 0.42 of a beat was 11576 samples vs an 8820-sample snare)
            n = min(int(SPB * 0.42 * SR), len(s))
            gate = (np.arange(n) // 512) % 2 == 0
            place(buf, t0 + beat * SPB, (s[:n] * gate), 0.9 * e)
    if e > 0.30:
        for eighth in range(8):
            place(buf, t0 + eighth * SPB / 2, d_hat(rng), 0.45 * e)
    if e > 0.28:
        for step in range(4):                     # driving eighth bass
            place(buf, t0 + step * SPB, sk.bass(root - 24, SPB * 0.9, gain=0.30), e)
            place(buf, t0 + step * SPB + SPB / 2, sk.bass(root - 24, SPB * 0.35, gain=0.24), e * 0.8)
    if e > 0.20:
        place(buf, t0, sk.supersaw([root, root + 7, root + 12, root + 19], BAR * 0.98,
                                   voices=7, detune=0.13, gain=0.085, a=0.9), e)
    if e > 0.70:
        lead = [root + 24, root + 27, root + 31, root + 27]
        for i, m in enumerate(lead):
            if (bar + i) % 3 != 2:
                place(buf, t0 + i * SPB, sk.supersaw([m], SPB * 0.85, voices=5,
                                                     detune=0.09, gain=0.075, a=0.05), e)


# ── GENRE 4: HOUSE — four-on-the-floor, offbeat open hats, piano stabs ──────
def g_house(buf, bar, t0, sec, e, local, rng, ctx):
    SPB, BAR = ctx["SPB"], ctx["BAR"]
    root = [53, 55, 57, 50][bar % 4]
    if e > 0.42:
        for beat in range(4):
            place(buf, t0 + beat * SPB, d_kick(140, 46, 32, 6.8, 0.6), e)
    if e > 0.40:
        for beat in (1, 3):
            place(buf, t0 + beat * SPB, sk.clap(rng), 0.8 * e)
    if e > 0.30:
        for eighth in range(8):                   # OPEN hats on the offbeats
            place(buf, t0 + eighth * SPB / 2, d_hat(rng, eighth % 2 == 1),
                  (0.45 if eighth % 2 == 0 else 0.95) * e)
    if e > 0.32:
        for step in range(8):
            if step % 2 == 1:
                place(buf, t0 + step * SPB / 2, sk.bass(root - 24, SPB * 0.30, gain=0.30), e)
    if e > 0.22:
        place(buf, t0, sk.supersaw([root, root + 4, root + 7, root + 11], BAR * 0.9,
                                   voices=5, detune=0.10, gain=0.055, a=0.02, s=0.5), e)
    if e > 0.72:
        for off in (0.5, 1.5, 2.5, 3.5):          # classic piano-ish stabs
            place(buf, t0 + off * SPB, sk.epiano([root + 12, root + 16, root + 19], 0.22, 0.10), e)
    if e > 0.88 and bar % 8 == 7:
        place(buf, t0 + 3.5 * SPB, sk.supersaw([root + 12, root + 19], SPB * 1.4,
                                               voices=5, gain=0.06), e)


# ── GENRE 5: TRAP — sparse kick, rolling hats, 808 sub ──────────────────────
def g_trap(buf, bar, t0, sec, e, local, rng, ctx):
    SPB, BAR = ctx["SPB"], ctx["BAR"]
    root = [41, 44, 39, 46][bar % 4]
    if e > 0.42:
        place(buf, t0, d_kick(120, 38, 24, 9.0, 0.4, 0.34), e)     # sparse: 1-2 per bar
        if bar % 2 == 1:
            place(buf, t0 + 2.75 * SPB, d_kick(120, 38, 24, 9.0, 0.4, 0.34), 0.8 * e)
    if e > 0.46 and bar % 2 == 0:
        place(buf, t0 + 2 * SPB, sk.clap(rng, 0.16, (0.0, 0.013), 30), e)
    if e > 0.30:                                   # rolling 16th/32nd hats
        dens = 8 if e < 0.7 else 16
        for i in range(dens):
            t = t0 + i * (BAR / dens)
            g = 0.30 if i % 2 else 0.45
            if e > 0.85 and i % 4 == 3:
                g *= 1.5
            place(buf, t, sk.hat(rng, False), g * e)
    if e > 0.34:
        place(buf, t0, sk.bass(root - 12, SPB * 1.9, gain=0.36, d=0.5, s=0.6), e)  # 808 hold
        if bar % 2 == 1:
            place(buf, t0 + 3 * SPB, sk.bass(root - 12 + 5, SPB * 0.8, gain=0.30), e)
    if e > 0.22:
        place(buf, t0, sk.supersaw([root + 12, root + 15], BAR * 0.95, voices=5,
                                   detune=0.16, gain=0.05, a=0.02, s=0.4), e)
    if e > 0.88 and bar % 4 == 1:
        for i, m in enumerate([root + 24, root + 27, root + 22]):
            place(buf, t0 + (1 + i * 0.5) * SPB, sk.epiano([m], SPB * 0.4, 0.085), e)


# ── GENRE 6: AMBIENT — no beat, texture and drift ───────────────────────────
def g_ambient(buf, bar, t0, sec, e, local, rng, ctx):
    """Closer. Not a beat -- a resolution.

    Rebuilt after Zerric called this the one weak track. The gate agreed: its
    sustained climax was 0.83 vs 0.98-0.99 on every other track, and it was the
    album's LONGEST track, which is backwards for an outro. Fixes:
      - shorter (outro shape, not slowburn)
      - one clear warm swell instead of an even wash
      - a real harmonic resolve: the ending lands on a sustained tonic that rings
      - a rising bell figure as a sign-off gesture
    """
    SPB, BAR = ctx["SPB"], ctx["BAR"]
    root = [45, 41, 43, 45][bar % 4]          # A - F - G - A : resolves to A
    last = local if sec.name == "coda" else -1

    # core pad: brighter and fuller in the swell so the climax is unmistakable
    pad = [root, root + 7, root + 12, root + 15, root + 19]
    place(buf, t0, sk.supersaw(pad, BAR * 1.05, voices=9, detune=0.20,
                               gain=0.135 + 0.075 * e, a=1.2, d=0.8, s=0.78, r=1.6), e)
    # upper shimmer only when the section is warm or brighter
    if e > 0.40:
        place(buf, t0, sk.supersaw([root + 24, root + 31], BAR * 0.9, voices=5,
                                   detune=0.24, gain=0.045 + 0.055 * e,
                                   a=1.6, s=0.6, r=1.8), e)
    # low swell: the "climax" layer, low end rather than a drum
    if e > 0.60:
        place(buf, t0, sk.supersaw([root - 12, root - 5], BAR * 1.0, voices=3,
                                   detune=0.06, gain=0.070 + 0.070 * e, a=1.0, s=0.88, r=1.4), e)
    # bell motif: sparse when settling, quicker in the swell, then resolving
    if sec.name == "coda":
        # the sign-off: rising figure that lands and rings on the tonic
        fig = [root + 12, root + 16, root + 19, root + 24, root + 28, root + 31]
        for i, m in enumerate(fig):
            place(buf, t0 + i * 0.5 * SPB, sk.epiano([m], 4.5, 0.070), 1.0)
        place(buf, t0 + 3 * SPB, sk.epiano([root + 12, root + 19, root + 24, root + 28],
                                           9.0, 0.058), 1.0)      # rings out, under the swell
    elif local % 2 == 0:
        n_bells = 2 if e < 0.70 else 3
        for i, m in enumerate([root + 24, root + 19, root + 28][:n_bells]):
            place(buf, t0 + (i * 1.6 + 0.5) * SPB, sk.epiano([m], 3.4, 0.068), e)
    # a soft sub pulse in the swell only -- felt, not counted
    if e > 0.88:
        place(buf, t0, sk.kick(80, 34, 20, 5.5, 0.0, 0.34), 0.42)
        place(buf, t0 + 2 * SPB, sk.kick(80, 34, 20, 5.5, 0.0, 0.34), 0.34)
        place(buf, t0 + 1 * SPB, sk.epiano([root + 12, root + 31], SPB * 1.6, 0.060), 1.0)


GENRES = {"disco": g_disco, "boombap": g_boombap, "synthwave": g_synthwave,
          "house": g_house, "trap": g_trap, "ambient": g_ambient}


# ── render one track ─────────────────────────────────────────────────────────
def render_track(spec):
    arr = ak.SHAPES[spec["shape"]]
    bars = arr.bars
    SPB = 60.0 / spec["bpm"]
    BAR = 4 * SPB
    ctx = {"SPB": SPB, "BAR": BAR}
    total = bars * BAR + 2.0
    buf = np.zeros(int(total * SR), dtype=np.float32)
    rng = np.random.default_rng(4000 + spec["n"])
    fn = GENRES[spec["genre"]]

    def per_bar(bar, sec, local):
        fn(buf, bar, bar * BAR, sec, sec.energy, local, rng, ctx)

    for bar in range(bars):
        sec, local = arr.at(bar)
        per_bar(bar, sec, local)

    out = sk.master(buf, peak=0.90, drive=1.12, fade_in=0.25, fade_out=2.4)
    wav = OUT / f"{spec['n']:02d}-{spec['title'].lower().replace(' ', '-')}.wav"
    sk.write_wav(out, wav)
    return wav, bars, arr


# ── covers: one distinct palette per genre ───────────────────────────────────
PALETTES = {
    "disco":     ((18, 8, 34),  (255, 94, 168), (94, 232, 255)),
    "boombap":   ((34, 26, 20), (196, 154, 74), (238, 224, 200)),
    "synthwave": ((12, 6, 30),  (255, 61, 129), (0, 245, 255)),
    "house":     ((8, 24, 28),  (0, 209, 178),  (255, 214, 10)),
    "trap":      ((14, 12, 16), (192, 20, 60),  (150, 150, 160)),
    "ambient":   ((20, 20, 34), (168, 190, 255), (226, 214, 255)),
}


def make_cover(spec, path):
    from PIL import Image, ImageDraw, ImageFont
    bg, a1, a2 = PALETTES[spec["genre"]]
    W = H = 1000
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(spec["n"] * 17)
    for y in range(H):                              # gradient
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(c * (0.6 + 0.8 * t)) for c in bg))
    for i in range(16):                             # radiating bars
        x = i * 66
        d.rectangle([x, 0, x + 26, H], fill=a1 if i % 2 else a2)
    glow = im.filter(__import__("PIL.ImageFilter", fromlist=["ImageFilter"]).GaussianBlur(26))
    im = Image.fromarray((np.asarray(im, dtype=np.float32) * 0.55 +
                          np.asarray(glow, dtype=np.float32) * 0.45).astype("uint8"))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, H], outline=a1, width=10)
    f1 = _font(104, True); f2 = _font(40, False); f3 = _font(34, False)
    words = spec["title"].upper().split()
    y = 300
    for w in words:
        tw = d.textlength(w, font=f1)
        d.text(((W - tw) / 2, y), w, font=f1, fill=(255, 255, 255),
               stroke_width=9, stroke_fill=bg)
        y += 116
    sub = f"MILKUPS  ·  {spec['genre'].upper()}  ·  {spec['bpm']} BPM"
    ws = d.textlength(sub, font=f2)
    d.text(((W - ws) / 2, y + 40), sub, font=f2, fill=a2)
    al = "COLD CUTS"
    wl = d.textlength(al, font=f3)
    d.text(((W - wl) / 2, 60), al, font=f3, fill=a1)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return path


def _font(sz, bold):
    from PIL import ImageFont
    p = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
         else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    try:
        return ImageFont.truetype(p, sz)
    except OSError:
        return ImageFont.load_default()


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=int)
    ap.add_argument("--from", dest="start", type=int, default=1)
    ap.add_argument("--no-structure", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    todo = [t for t in TRACKS if (not a.only or t["n"] == a.only) and t["n"] >= a.start]
    report = []
    for spec in todo:
        print(f"\n=== {spec['n']}. {spec['title']}  [{spec['genre']} @ {spec['bpm']} BPM, shape={spec['shape']}]")
        wav, bars, arr = render_track(spec)
        cover = make_cover(spec, OUT / f"{spec['n']:02d}-cover.png")
        secs = sk.duration(wav)
        ok_s, sres = ak.verify_structure(wav, spec["bpm"], bars)
        spark = ak.contour_summary(wav, spec["bpm"], bars)
        print(f"  {secs:.1f}s | {bars} bars | cover {cover.stat().st_size//1024}KB")
        print(f"  shape: {spark}")
        for name, good, ev in sres:
            print(f"    {'PASS' if good else 'FAIL'}  {name:<26} {ev}")
        report.append({"n": spec["n"], "title": spec["title"], "genre": spec["genre"],
                       "bpm": spec["bpm"], "shape": spec["shape"], "bars": bars,
                       "seconds": round(secs, 2), "wav": str(wav.relative_to(ROOT)),
                       "cover": str(cover.relative_to(ROOT)),
                       "structure_pass": ok_s, "structure": sres,
                       "contour": spark})
        if not ok_s:
            print("  !! STRUCTURE FAILED")

    man = OUT / "manifest.json"
    prev = json.loads(man.read_text())["tracks"] if man.exists() else []
    keep = {t["n"]: t for t in prev}
    for t in report:
        keep[t["n"]] = t
    man.write_text(json.dumps({"album": ALBUM, "artist": "MilkUps",
                               "standard": "content/snowsnakes/songs/STANDARD.md",
                               "tracks": [keep[k] for k in sorted(keep)]}, indent=1))
    print(f"\nmanifest: {man.relative_to(ROOT)}  ({len(keep)} tracks)")
    return 0 if all(r["structure_pass"] for r in report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
