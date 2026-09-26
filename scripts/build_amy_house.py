#!/usr/bin/env python3
"""build_amy_house.py — SnowSnakes house track rendered on the REAL AMY engine
(the TulipCC synth core), offline.

Genre: house @ 123.046875 BPM, four-on-the-floor.

WHY THIS TEMPO: a 16th note must be a whole number of 256-sample blocks, or the
sequencer drifts. At 44.1 kHz one 16th = 2583.984375/BPM blocks, so with 21
blocks per 16th the tempo is exactly 2583.984375/21 = 123.046875 BPM. Samples are
placed on an exact grid; nothing is resampled.

VARIETY (why this does not homogenise against the board):
fingerprint = (groove, round(bpm/10)*10, centroid//250).
  - tempo bucket is 120. The only other four-on-the-floor track in that bucket is
    "Shelves After Dark" (disco 118), which sits in brightness bucket 8, so this
    track must avoid brightness bucket 8 to stay distinct.

Groove contract (verify_song.py, measured from audio): four_on_floor needs >=70%
of low-band onset gaps to equal exactly one beat AND the median gap within 60 ms
of the beat length. Kick is on every beat; the bass is placed on the offbeat with
a soft attack so it does not add low-band onsets between the kicks.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import amy

SR = amy.AMY_SAMPLE_RATE
BLOCKS_PER_STEP = 21                     # one 16th
BPM = 2583.984375 / BLOCKS_PER_STEP      # 123.046875, exact
BARS = 96                                # 96 * 1.948 s ~= 187 s

TITLE = "Basement Frost"
STEM = "basement-frost"

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "content" / "snowsnakes" / "songs"

# Am7 - Fmaj7 - Dm7 - Em7, one chord per bar
CHORDS = [[57, 60, 64, 67], [53, 57, 60, 64], [50, 53, 57, 60], [52, 55, 59, 62]]
ROOTS = [45, 41, 38, 40]
LEAD = [69, 72, 74, 76, 79, 76, 74, 72]      # A minor pentatonic


def hz(n):
    return 440.0 * (2.0 ** ((n - 69) / 12.0))


def step():
    out = []
    for _ in range(BLOCKS_PER_STEP):
        out.append(np.array(amy._amy.render_to_list()) / 32768.0)
    return np.hstack(out).reshape((-1, amy.AMY_NCHANS))


# ── instruments ──────────────────────────────────────────────────────────────
def kick(vel=3.1):
    amy.send(osc=0, wave=amy.PCM, preset=2, vel=vel)


def clap(vel=1.5):
    amy.send(osc=1, wave=amy.PCM, preset=3, vel=vel)


def open_hat(vel=1.15):
    amy.send(osc=2, wave=amy.PCM, preset=10, vel=vel)


def closed_hat(vel=0.55):
    amy.send(osc=3, wave=amy.PCM, preset=9, vel=vel)


def bass(note, vel=1.5):
    """Offbeat house bass. Soft 12 ms attack keeps it out of the kick-onset band."""
    amy.send(osc=8, wave=amy.SAW_DOWN, freq=hz(note), bp0="0,1,12,0.6,130,0",
             filter_type=1, filter_freq=380, vel=vel)


def sub(note, vel=0.85):
    amy.send(osc=9, wave=amy.SINE, freq=hz(note - 12), bp0="0,1,90,0.5,220,0", vel=vel)


def stab(notes, vel=0.95):
    """Warm offbeat chord stab: two detuned triangles per note."""
    for i, n in enumerate(notes):
        amy.send(osc=4 + (i % 2), wave=amy.TRIANGLE, freq=hz(n),
                 bp0="0,1,8,0.45,170,0", vel=vel)
        amy.send(osc=6 + (i % 2), wave=amy.SINE, freq=hz(n) * 2.0,
                 bp0="0,1,8,0.30,140,0", vel=vel * 0.35)


def pad(notes, vel=0.42):
    """Sustained warm pad, slow attack, one per bar."""
    for i, n in enumerate(notes[:3]):
        amy.send(osc=10 + i, wave=amy.TRIANGLE, freq=hz(n + 12),
                 bp0="0,1,300,0.7,700,0", vel=vel)


def lead(note, vel=0.8):
    amy.send(osc=13, wave=amy.SINE, freq=hz(note), bp0="0,1,30,0.6,260,0", vel=vel)
    amy.send(osc=14, wave=amy.TRIANGLE, freq=hz(note) * 1.005,
             bp0="0,1,30,0.35,200,0", vel=vel * 0.4)


# ── arrangement ──────────────────────────────────────────────────────────────
def parts(bar):
    """Which layers play in this bar."""
    if bar < 8:            # intro: drums only
        return dict(kick=1, hats=1, clap=0, bass=0, stab=0, pad=0, lead=0)
    if bar < 16:
        return dict(kick=1, hats=1, clap=1, bass=1, stab=0, pad=0, lead=0)
    if bar < 32:
        return dict(kick=1, hats=1, clap=1, bass=1, stab=1, pad=1, lead=0)
    if bar < 40:           # breakdown: no kick, no clap
        return dict(kick=0, hats=0, clap=0, bass=0, stab=1, pad=1, lead=1)
    if bar < 56:
        return dict(kick=1, hats=1, clap=1, bass=1, stab=1, pad=1, lead=1)
    if bar < 64:
        return dict(kick=1, hats=1, clap=1, bass=1, stab=1, pad=1, lead=0)
    if bar < 80:
        return dict(kick=1, hats=1, clap=1, bass=1, stab=1, pad=1, lead=1)
    return dict(kick=1, hats=1, clap=0, bass=0, stab=1, pad=1, lead=0)   # outro


def render_song():
    amy.send(reset=amy.RESET_ALL_OSCS)
    # club space: a little reverb, subtle echo on the clap, gentle chorus on the keys
    amy.echo(level=0.22, delay_ms=370, max_delay_ms=900, feedback=0.35, filter_coef=-0.5)
    amy.send(bus=0, reverb=[0.20, 0.68, 0.5, 5500])
    amy.send(bus=0, eq=[3.0, 0.0, -5.0])       # warm the low end, tame the top
    amy.send(bus=0, chorus=[0.18, 400, 0.28, 0.4])

    chunks = []
    for bar in range(BARS):
        p = parts(bar)
        ch = CHORDS[bar % 4]
        root = ROOTS[bar % 4]
        for s in range(16):
            beat = s % 4 == 0
            off8 = s % 4 == 2          # the offbeat 8th = the house "and"

            if beat and p["kick"]:
                kick(3.1 if bar % 8 != 7 else 2.5)
            if p["clap"] and s in (4, 12):
                clap(1.5)
            if p["hats"]:
                if off8:
                    open_hat(1.15)
                elif s % 2 == 1:
                    closed_hat(0.55)
            if p["bass"] and off8:
                bass(root, 1.5)
                if bar % 4 == 3:
                    sub(root, 0.85)
            if p["stab"] and off8:
                stab(ch, 0.95 if s != 6 else 1.15)
            if p["lead"] and s % 2 == 0 and (bar + s) % 5 == 0:
                lead(LEAD[(bar * 8 + s // 2) % len(LEAD)], 0.78)
            chunks.append(step())
        if p["pad"]:
            pad(ch + [c + 12 for c in ch[:2]], 0.40)
    return np.vstack(chunks)


def master(a, target_peak=0.86):
    a = a - float(a.mean())
    a = a * (target_peak / float(np.abs(a).max()))
    a = np.tanh(a * 1.05) / np.tanh(1.05)
    return (a * (target_peak / float(np.abs(a).max()))).astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUTDIR / "wav" / f"{STEM}.wav"))
    ap.add_argument("--no-master", action="store_true")
    args = ap.parse_args()

    print(f"AMY {amy.version} @ {SR} Hz | {BPM:.4f} BPM | {BARS} bars | "
          f"step={BLOCKS_PER_STEP} blocks")
    a = render_song()
    raw = float(np.abs(a).max())
    if not args.no_master:
        a = master(a)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    amy.write(a, str(out))
    print(f"  raw peak {raw:.4f} -> final {float(np.abs(a).max()):.4f}")
    print(f"  {len(a)/SR:.2f}s  {out.stat().st_size//1024} KB -> {out}")


if __name__ == "__main__":
    main()
