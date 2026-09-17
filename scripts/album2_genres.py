#!/usr/bin/env python3
"""album2_genres.py — six NEW genres for the second MilkUps album.

Deliberately shares no genre with COLD CUTS (disco/boombap/synthwave/house/
trap/ambient). Also shares no groove with each other where avoidable:
rock and funk are backbeat but sit in different tempo and brightness bands,
dnb is two-step, reggae is one-drop, techno is four-on-the-floor, cinematic
has no pulse.
"""
from __future__ import annotations
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import songkit as sk
from songkit import SR, hz, place, saw, sq, tri, sine, adsr, exp_decay, noise


# ── ROCK @ 140: backbeat, power chords, driving straight 8ths ────────────────
def g_rock(buf, bar, t0, sec, e, local, rng, ctx):
    SPB, BAR = ctx["SPB"], ctx["BAR"]
    root = [40, 45, 43, 38][bar % 4]           # E - A - G - D
    if e > 0.42:
        place(buf, t0, sk.kick(150, 50, 34, 9.0, 0.7), e)
        place(buf, t0 + 2 * SPB, sk.kick(150, 50, 34, 9.0, 0.7), 0.95 * e)
        if bar % 4 == 3:
            place(buf, t0 + 3.5 * SPB, sk.kick(150, 50, 34, 9.0, 0.7), 0.5 * e)
    if e > 0.46:
        for beat in (1, 3):                     # backbeat
            place(buf, t0 + beat * SPB, sk.snare(rng, 0.22, 16, 200, 0.35), e)
    if e > 0.26:
        for eighth in range(8):                 # straight 8th hats
            place(buf, t0 + eighth * SPB / 2, sk.hat(rng, False), 0.55 * e)
    if e > 0.34:
        for step in range(8):                   # driving root-8th bass
            m = root - 12
            place(buf, t0 + step * SPB / 2, sk.bass(m, SPB * 0.42, drive=1.5, gain=0.30), e)
    if e > 0.22:
        # Sustained bed. Every genre needs one element alive at dip energy, or
        # the breakdown becomes silence (0.000 of peak) instead of a breakdown.
        place(buf, t0, sk.strings([root, root + 12, root + 19], BAR * 1.0,
                                  bright=0.6, a=0.5, s=0.75, r=0.9, gain=0.170), e)
        place(buf, t0, sk.supersaw([root - 12], BAR * 1.0, voices=3, detune=0.05,
                                   gain=0.055, a=0.6, s=0.8, r=1.0), e)
    if e > 0.50:
        # power chords (root + fifth), palm-muted feel via short decay
        tones = [root, root + 7, root + 12]
        n = int(BAR * 0.82 * SR)
        t = np.arange(n) / SR
        v = np.zeros(n, dtype=np.float32)
        for m in tones:
            f = hz(m)
            v += (saw(2 * np.pi * f * t) * 0.6 + sq(2 * np.pi * f * 1.005 * t) * 0.4).astype(np.float32)
        v = np.tanh(v / len(tones) * 1.6) * adsr(n, 0.005, 0.10, 0.62, 0.22) * 0.115
        place(buf, t0, v, e)
    if e > 0.86 and bar % 4 == 3:               # lead fill into the next bar
        for i, m in enumerate([root + 24, root + 26, root + 28, root + 31]):
            place(buf, t0 + (2 + i * 0.5) * SPB, sk.brass(m, SPB * 0.30, 0.085), 1.0)


# ── D&B @ 174: two-step, kick 1 + snare 3, sub bass ─────────────────────────
def g_dnb(buf, bar, t0, sec, e, local, rng, ctx):
    SPB, BAR = ctx["SPB"], ctx["BAR"]
    root = [38, 41, 36, 43][bar % 4]
    if e > 0.40:
        place(buf, t0, sk.kick(160, 52, 40, 12.0, 0.5, 0.26), e)          # beat 1
        if bar % 2 == 1:
            place(buf, t0 + 2.5 * SPB, sk.kick(160, 52, 40, 12.0, 0.5, 0.26), 0.8 * e)
    if e > 0.44:
        place(buf, t0 + 2 * SPB, sk.snare(rng, 0.20, 17, 240, 0.30), 0.95 * e)  # SNARE on 3
        if e > 0.80:
            place(buf, t0 + 3.5 * SPB, sk.snare(rng, 0.16, 22, 240, 0.30), 0.45 * e)
    if e > 0.28:                                   # fast breakbeat hats
        for i in range(16):
            t = t0 + i * (BAR / 16)
            place(buf, t, sk.hat(rng, False), (0.42 if i % 2 == 0 else 0.26) * e)
    if e > 0.30:                                   # sub bass, long notes
        place(buf, t0, sk.bass(root - 12, SPB * 2.6, drive=1.3, gain=0.34, d=0.5, s=0.7), e)
        if bar % 2 == 1:
            place(buf, t0 + 3 * SPB, sk.bass(root - 12 + 7, SPB * 0.9, gain=0.28), e)
    if e > 0.55:                                   # reese-style detuned pad
        place(buf, t0, sk.supersaw([root, root + 7, root + 15], BAR * 0.95,
                                   voices=5, detune=0.22, gain=0.055, a=0.05, s=0.5), e)
    if e > 0.88 and bar % 4 == 2:
        for i, m in enumerate([root + 24, root + 27, root + 31]):
            place(buf, t0 + (1 + i * 0.4) * SPB, sk.epiano([m], SPB * 0.5, 0.075), e)


# ── FUNK @ 112: backbeat, syncopated 16ths, slap bass ───────────────────────
def g_funk(buf, bar, t0, sec, e, local, rng, ctx):
    SPB, BAR = ctx["SPB"], ctx["BAR"]
    root = [45, 45, 43, 41][bar % 4]
    if e > 0.42:
        # syncopated kick on 1, the "and" of 2, and the 16th before 4
        for off in (0.0, 1.5, 2.75):
            place(buf, t0 + off * SPB, sk.kick(120, 46, 26, 8.0, 0.55, 0.28), e)
    if e > 0.46:
        for beat in (1, 3):                     # backbeat
            place(buf, t0 + beat * SPB, sk.snare(rng, 0.18, 20, 200, 0.30), 0.92 * e)
        if bar % 2 == 1:
            place(buf, t0 + 3.75 * SPB, sk.snare(rng, 0.12, 26, 200, 0.30), 0.34 * e)
    if e > 0.30:
        for i in range(16):                     # busy 16th hats, accent on the 8ths
            t = t0 + i * (BAR / 16)
            place(buf, t, sk.hat(rng, i % 8 == 7), (0.50 if i % 4 == 0 else 0.26) * e)
    if e > 0.32:
        # slap bass: octaves + syncopated 16ths
        pat = [(0.0, 0), (0.5, 12), (0.75, 0), (1.5, 7), (2.0, 0), (2.5, 12), (3.25, 10)]
        for off, iv in pat:
            place(buf, t0 + off * SPB, sk.bass(root - 24 + iv, SPB * 0.26,
                                               drive=1.6, gain=0.30, d=0.06, s=0.3), e)
    if e > 0.56:
        # clav-style stabs on the offbeats
        for off in (0.5, 1.5, 2.5, 3.5):
            place(buf, t0 + off * SPB, sk.skank([root + 12, root + 15, root + 19], 0.14, 0.115), e)
    if e > 0.84 and bar % 4 == 3:
        for i, m in enumerate([root + 24, root + 22, root + 19]):
            place(buf, t0 + (1 + i * 0.5) * SPB, sk.brass(m, SPB * 0.35, 0.09), 1.0)


# ── REGGAE/DUB @ 76: one-drop (kick on 3), offbeat skank, deep bass ─────────
def g_dub(buf, bar, t0, sec, e, local, rng, ctx):
    SPB, BAR = ctx["SPB"], ctx["BAR"]
    root = [38, 38, 41, 36][bar % 4]
    if e > 0.40:
        place(buf, t0 + 2 * SPB, sk.kick(90, 40, 18, 5.0, 0.0, 0.40), e)   # ONE-DROP: beat 3
        if bar % 8 == 7:
            place(buf, t0, sk.kick(90, 40, 18, 5.0, 0.0, 0.40), 0.6 * e)
    if e > 0.44:
        place(buf, t0 + 2 * SPB, sk.snare(rng, 0.20, 15, 170, 0.40), 0.55 * e)
        place(buf, t0 + 1 * SPB, sk.hat(rng, False), 0.30 * e)
        place(buf, t0 + 3 * SPB, sk.hat(rng, False), 0.30 * e)
    if e > 0.28:
        # the skank: short chords on the OFFBEATS only -- the signature sound
        for off in (0.5, 1.5, 2.5, 3.5):
            place(buf, t0 + off * SPB, sk.skank([root + 12, root + 16, root + 19], 0.13, 0.125), e)
    if e > 0.30:
        # deep, slow, round bass -- one long note per bar with a pickup
        place(buf, t0, sk.bass(root - 12, SPB * 2.4, drive=1.15, gain=0.36, d=0.4, s=0.75), e)
        place(buf, t0 + 2.5 * SPB, sk.bass(root - 5, SPB * 1.1, gain=0.30), e)
    if e > 0.52:
        place(buf, t0, sk.epiano([root + 12, root + 19], BAR * 0.9, 0.070), e)   # organ-ish
    if e > 0.82:                                    # dub echo stab
        place(buf, t0 + 3.5 * SPB, sk.epiano([root + 24], SPB * 1.5, 0.085), 1.0)


# ── TECHNO @ 138: relentless four-on-the-floor, dark, minimal ───────────────
def g_techno(buf, bar, t0, sec, e, local, rng, ctx):
    SPB, BAR = ctx["SPB"], ctx["BAR"]
    root = [38, 38, 41, 39][bar % 4]
    if e > 0.38:
        for beat in range(4):
            place(buf, t0 + beat * SPB, sk.kick(140, 44, 36, 9.5, 0.8), e)
    if e > 0.34:
        for i in range(8):                          # offbeat open hats
            place(buf, t0 + i * SPB / 2, sk.hat(rng, i % 2 == 1),
                  (0.35 if i % 2 == 0 else 0.80) * e)
    if e > 0.28:
        for step in range(8):                       # rolling offbeat bass
            if step % 2 == 1:
                place(buf, t0 + step * SPB / 2, sk.bass(root - 12, SPB * 0.26,
                                                        drive=1.4, gain=0.32, d=0.05, s=0.35), e)
    if e > 0.30:
        place(buf, t0 + 1.5 * SPB, sk.clap(rng, 0.16, (0.0, 0.012), 32), 0.55 * e)
    if e > 0.48:
        place(buf, t0, sk.supersaw([root, root + 12, root + 19], BAR * 0.95,
                                   voices=5, detune=0.08, gain=0.048, a=0.02, s=0.45), e)
    if e > 0.80 and bar % 4 == 3:                   # metallic stab
        for i, m in enumerate([root + 24, root + 25]):
            place(buf, t0 + (2 + i * 0.5) * SPB, sk.epiano([m], SPB * 0.35, 0.080), 1.0)


# ── CINEMATIC @ 88: orchestral, no pulse, swells and a big peak ─────────────
def g_cinematic(buf, bar, t0, sec, e, local, rng, ctx):
    BAR, SPB = ctx["BAR"], ctx["SPB"]
    root = [38, 41, 43, 45][bar % 4]
    # string section: low sustain + mid swell, growing with energy
    place(buf, t0, sk.strings([root, root + 7, root + 12], BAR * 1.02,
                              bright=0.85 + 0.5 * e, a=0.9, s=0.8, r=1.4), e)
    if e > 0.42:
        place(buf, t0, sk.strings([root + 12, root + 19, root + 24, root + 31], BAR * 0.98,
                                  bright=1.05, a=0.6, s=0.8, r=1.2), e)
    if e > 0.30:
        place(buf, t0, sk.supersaw([root - 12], BAR * 1.0, voices=3, detune=0.05,
                                   gain=0.075 + 0.05 * e, a=1.2, s=0.85, r=1.6), e)
    if e > 0.62:                                     # timpani-ish hits, sparse
        for off in (0.0, 2.0):
            place(buf, t0 + off * SPB, sk.kick(70, 32, 14, 4.2, 0.0, 0.55), 0.34)
    if e > 0.80:                                     # brass fanfare at the peak
        fan = [(0.0, root + 24), (0.75, root + 28), (1.5, root + 31), (2.5, root + 36)]
        for off, m in fan:
            place(buf, t0 + off * SPB, sk.brass(m, SPB * 1.4, 0.105), 1.0)
    if e > 0.86 and local % 4 == 0:                  # bell motif over the peak
        for i, m in enumerate([root + 36, root + 31]):
            place(buf, t0 + (i * 2 + 0.5) * SPB, sk.epiano([m], 3.6, 0.062), 1.0)


NEW_GENRES = {"rock": g_rock, "dnb": g_dnb, "funk": g_funk,
              "reggae": g_dub, "techno": g_techno, "cinematic": g_cinematic}
