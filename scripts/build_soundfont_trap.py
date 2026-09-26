#!/usr/bin/env python3
"""build_soundfont_trap.py — SnowSnakes trap beat rendered with FluidSynth +
the FluidR3_GM soundfont (REAL recorded instruments), via a hand-written MIDI file.

Genre: trap @ 140 BPM, sparse kick, dense hat rolls, half-time feel (the first
track in the catalogue on the soundfont engine, and the first with a sparse-kick
groove -- so the variety fingerprint is unique by construction).

Gate contract (verify_song.py, measured from audio):
  - sparse_kick: <= 3.2 low-band onsets per bar. Half-time puts the kick on beat 1
    and the clap on beat 3; the 808 sub is a long sustained note with no sharp
    attack, so it does not add low onsets (probed both ways before committing).
  - tempo is read from the HAT band (4000-12000 Hz) with half/double accepted,
    because trap is legitimately half-time.

General MIDI channels used (0-indexed):
  0 = 808 sub bass (prog 38 Synth Bass 1)
  1 = keys/chords  (prog 4  Electric Piano 1)
  2 = topline      (prog 11 Vibraphone)
  3 = pad          (prog 49 Strings Ensemble 2)
  9 = GM drum kit  (36 kick, 39 clap, 42 closed hat, 44 pedal hat, 46 open hat)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import midi_lib as ml
import songkit as sk

BPM = 140.0
BARS = 88                     # 88 * 1.7143s = 150.9s
TITLE = "Ice Cold Pockets"
STEM = "ice-cold-pockets"

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "content" / "snowsnakes" / "songs"
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"

# A minor, dark: Am7 - Fmaj7 - Dm7 - E7
CHORDS = [[57, 60, 64, 67], [53, 57, 60, 64], [50, 53, 57, 60], [52, 56, 59, 62]]
ROOTS = [45, 41, 38, 40]
TOP = [69, 72, 76, 72, 74, 72, 69, 67]        # A C E C D C A G


def section(bar):
    """Arrangement map. Returns which layers are active."""
    if bar < 8:
        return dict(drums=0, bass=0, keys=0, pad=1, top=1)          # intro
    if bar < 16:
        return dict(drums=1, bass=1, keys=0, pad=1, top=0)
    if bar < 32:
        return dict(drums=1, bass=1, keys=1, pad=1, top=1)          # drop
    if bar < 40:
        return dict(drums=0, bass=0, keys=1, pad=1, top=1)          # breakdown
    if bar < 56:
        return dict(drums=1, bass=1, keys=1, pad=1, top=1)          # drop 2
    if bar < 64:
        return dict(drums=1, bass=1, keys=1, pad=0, top=1)          # stripped
    if bar < 80:
        return dict(drums=1, bass=1, keys=1, pad=1, top=1)
    return dict(drums=1, bass=1, keys=0, pad=1, top=1)              # outro


def build():
    m = ml.MidiFile(ppq=480, bpm=BPM)
    dr = m.add_track("drums")
    bs = m.add_track("808")
    ky = m.add_track("keys")
    pd = m.add_track("pad")
    tp = m.add_track("topline")

    # programs + mix sitting
    bs.program(0, 38).volume(0, 112).pan(0, 64).reverb_send(0, 20)
    ky.program(1, 4).volume(1, 84).pan(1, 58).reverb_send(1, 55)
    pd.program(2, 49).volume(2, 58).pan(2, 70).reverb_send(2, 85)
    tp.program(3, 11).volume(3, 88).pan(3, 70).reverb_send(3, 60)

    beat = m.ticks(1)
    half = m.ticks(2)
    sixteenth = m.ticks(0.25)

    for bar in range(BARS):
        s = section(bar)
        t0 = bar * m.bar
        root = ROOTS[bar % 4]
        chord = CHORDS[bar % 4]

        # ── drums ──
        if s["drums"]:
            # sparse kick: beat 1, and a second hit on the "and" of 4 in some bars
            dr.drum(ml.KICK, t0, 30, 120)
            if bar % 4 == 3:
                dr.drum(ml.KICK, t0 + m.ticks(3.5), 30, 100)

            # half-time clap on beat 3
            dr.drum(ml.CLAP, t0 + half, 30, 104)

            # hats: straight 16ths, with a 32nd roll closing the bar
            for i in range(16):
                vel = 74 if i % 2 == 0 else 58
                dr.drum(ml.HAT_CLOSED, t0 + i * sixteenth, 18, vel)
            for i in range(6):                     # 32nd roll (trap signature)
                dr.drum(ml.HAT_CLOSED, t0 + m.ticks(3.25 + i * 0.0625), 12, 52 + i * 6)
            if bar % 8 == 7:
                dr.drum(ml.HAT_OPEN, t0 + m.ticks(2.5), 40, 92)
                dr.drum(ml.CRASH, t0 + m.ticks(3.75), 60, 96)
        elif s["pad"] and bar >= 4:
            # hats only in the intro/breakdown
            for i in range(0, 16, 2):
                dr.drum(ml.HAT_CLOSED, t0 + i * sixteenth, 16, 44)

        # ── 808 sub ──
        if s["bass"]:
            dur = m.ticks(3.0)
            bs.note(0, root, t0, dur, 104)
            # glissando tail on the last bar of each 4-bar cycle
            if bar % 4 == 3:
                bs.pitch_bend(0, -1400, t0 + m.ticks(3.0))
                bs.pitch_bend(0, 0, t0 + m.ticks(3.5))
            else:
                bs.pitch_bend(0, 0, t0)

        # ── keys: offbeat stabs, sparse ──
        if s["keys"]:
            for b in (0.5, 1.5, 2.5, 3.5):
                ky.chord(1, [n + 12 for n in chord[:3]], t0 + m.ticks(b), m.ticks(0.4),
                         62 if b in (0.5, 2.5) else 52)

        # ── pad: one sustained chord per bar ──
        if s["pad"]:
            pd.chord(2, [n + 12 for n in chord[:3]], t0, m.ticks(4), 46)

        # ── topline ──
        if s["top"]:
            if bar < 8:
                tp.note(3, TOP[bar % len(TOP)], t0, m.ticks(3.5), 70)
            else:
                for i in range(4):
                    idx = (bar * 4 + i) % len(TOP)
                    if (bar + i) % 3 != 0:
                        tp.note(3, TOP[idx], t0 + i * beat, m.ticks(0.75),
                                72 if i == 0 else 60)
    return m


def master(a, target_peak=0.86, bass_boost=1.0):
    """Light master: tone shaping + soft limit. Deterministic."""
    a = a - float(a.mean())
    # gentle high-shelf cut so the hat rolls are not harsh
    from scipy.signal import butter, sosfilt
    sos = butter(2, 9000 / (0.5 * 44100), btype="low", output="sos")
    a = sosfilt(sos, a, axis=0).astype(np.float32)
    a = a * bass_boost
    a = a * (target_peak / float(np.abs(a).max()))
    a = np.tanh(a * 1.06) / np.tanh(1.06)
    return (a * (target_peak / float(np.abs(a).max()))).astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    wav = Path(args.out) if args.out else OUTDIR / "wav" / f"{STEM}.wav"
    mid = Path("/tmp") / f"{STEM}.mid"

    m = build()
    m.write(mid)
    print(f"MIDI {mid}  {mid.stat().st_size//1024} KB  {BPM:.0f} BPM  {BARS} bars")
    ml.render(mid, wav, sf2=SF2, gain=0.6)

    a, sr = sk.load(str(wav))
    a = master(a)
    import soundfile as sf
    sf.write(str(wav), a, sr, subtype="PCM_16")
    print(f"  {len(a)/sr:.2f}s  peak {np.abs(a).max():.3f}  -> {wav}")


if __name__ == "__main__":
    main()
