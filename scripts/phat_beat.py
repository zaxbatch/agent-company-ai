#!/usr/bin/env python3
"""Crazy phat tracker beat: synthesise the samples, write an XM, render it.

XM is MilkyTracker's native editable format, and ffmpeg's libopenmpt decoder
renders it, so the whole thing runs headless. Chain:
    numpy -> samples -> XM module -> ffmpeg (libopenmpt) -> WAV -> MP3

    scripts/phat_beat.py --out content/experiments/milkytracker/phat-fm.xm
"""
from __future__ import annotations
import argparse, os, subprocess, sys
import numpy as np
from scipy import signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xm_lib import Module, Instrument, Sample, SR, note_for, ROWS_PER_PATTERN

BPM = 145
# ---- channel map -----------------------------------------------------------
CH = dict(kick=0, snare=1, clap=2, hat=3, ohat=4, bass=5, sub=6,
          stabA=7, stabB=8, stabC=9, lead=10, crash=11)
NCH = 16

# ---- samples ---------------------------------------------------------------
def env(n, att=0.002, dec=0.4, sr=SR):
    a = max(1, int(att * sr)); d = max(1, n - a)
    e = np.concatenate([np.linspace(0, 1, a), np.exp(-np.linspace(0, 6, d))])
    return e[:n]


def lowpass(x, cutoff, order=2):
    b, a = signal.butter(order, min(0.99, cutoff / (SR / 2)), btype="low")
    return signal.lfilter(b, a, x)


def highpass(x, cutoff, order=2):
    b, a = signal.butter(order, min(0.99, cutoff / (SR / 2)), btype="high")
    return signal.lfilter(b, a, x)


def saw(f, t):
    return 2.0 * ((t * f) % 1.0) - 1.0


def sq(f, t):
    return np.sign(np.sin(2 * np.pi * f * t)) * 0.85


def phat(freq, dur, detune=(0, 7, -9, 14), drive=2.6, lp=2600, env_decay=6.0):
    """Stacked detuned saws through a lowpass into a saturator. The Phat."""
    n = int(dur * SR); t = np.arange(n) / SR
    out = np.zeros(n)
    for c in detune:
        out += saw(freq * 2 ** (c / 1200.0), t)
    out /= len(detune)
    out = lowpass(out, lp)
    out *= np.exp(-np.linspace(0, env_decay, n))
    return np.tanh(out * drive) * 0.92


def make_samples():
    S = {}
    # --- kick: pitch-swept sine, clicked, saturated
    n = int(0.62 * SR); t = np.arange(n) / SR
    f = 150 * np.exp(-t * 26) + 44
    k = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    click = highpass(np.random.RandomState(1).randn(n) * np.exp(-t * 220), 1800) * 0.5
    k = np.tanh((k * 1.5 + click) * 2.2) * 0.95
    S["kick"] = Sample(k, name="KICK PHAT")

    # --- snare: noise + two tones, tight
    n = int(0.30 * SR); t = np.arange(n) / SR
    rng = np.random.RandomState(2)
    nz = rng.randn(n) * np.exp(-t * 22)
    tone = (np.sin(2 * np.pi * 190 * t) * 0.7 + np.sin(2 * np.pi * 330 * t) * 0.4) * np.exp(-t * 26)
    S["snare"] = Sample(np.tanh((nz * 0.9 + tone) * 1.6) * 0.8, name="SNARE")

    # --- clap: four staggered bursts
    n = int(0.34 * SR); c = np.zeros(n); rng = np.random.RandomState(3)
    for i, off in enumerate((0.0, 0.011, 0.022, 0.034)):
        s = int(off * SR); m = n - s
        tt = np.arange(m) / SR
        c[s:] += rng.randn(m) * np.exp(-tt * (34 - i * 5)) * (1.0 - i * 0.12)
    S["clap"] = Sample(highpass(c, 900) * 0.55, name="CLAP")

    # --- hats
    n = int(0.055 * SR); t = np.arange(n) / SR
    S["hat"] = Sample(highpass(np.random.RandomState(4).randn(n), 7000) *
                      np.exp(-t * 150) * 0.5, name="HAT")
    n = int(0.30 * SR); t = np.arange(n) / SR
    S["ohat"] = Sample(highpass(np.random.RandomState(5).randn(n), 6000) *
                       np.exp(-t * 20) * 0.42, name="OPEN HAT")

    # --- bass: phat saw at A1, longer lowpass tail
    S["bass"] = Sample(phat(55.0, 0.85, detune=(0, 9, -12, 17), drive=2.8,
                            lp=760, env_decay=3.0), name="PHAT BASS")

    # --- sub: pure sine one octave down relative to the bass
    n = int(0.95 * SR); t = np.arange(n) / SR
    S["sub"] = Sample(np.sin(2 * np.pi * 41.2 * t) * np.exp(-t * 3.2) * 0.9,
                      name="SUB")

    # --- stab voice: phat saw at A3, short and bright
    S["stab"] = Sample(phat(220.0, 0.55, detune=(0, 11, -14, 19), drive=3.0,
                            lp=3400, env_decay=7.0), name="STAB")

    # --- lead: square+saw, long enough to sustain
    n = int(0.60 * SR); t = np.arange(n) / SR
    ld = (sq(440.0, t) * 0.6 + saw(440.0 * 1.006, t) * 0.4)
    ld = lowpass(ld, 5200) * np.exp(-np.linspace(0, 2.2, n))
    S["lead"] = Sample(np.tanh(ld * 1.8) * 0.75, name="LEAD")

    # --- crash
    n = int(1.1 * SR); t = np.arange(n) / SR
    S["crash"] = Sample(highpass(np.random.RandomState(6).randn(n), 3500) *
                        np.exp(-t * 3.4) * 0.5, name="CRASH")
    return S


# ---- musical material: F minor, 4-bar cycle ---------------------------------
# (root freq, [chord freqs])
PROG = [
    (43.65, [349.23, 415.30, 523.25]),   # Fm
    (34.65, [277.18, 349.23, 415.30]),   # Db
    (51.91, [415.30, 523.25, 622.25]),   # Ab
    (38.89, [311.13, 415.30, 466.16]),   # Eb
]
BASS_BASE, STAB_BASE = 55.0, 220.0

BASS_FULL = [(0, 0), (2, 0), (4, 12), (6, 0), (8, 0), (10, 0), (12, 12), (14, 7)]
BASS_HALF = [(0, 0), (3, 0), (6, 12), (8, 0), (11, 0), (14, 7)]
BASS_SPARSE = [(0, 0), (6, 0), (10, 12)]


def put(cells, ch, row, inst, note, vol=64, fx=0, param=0):
    cells[(row % ROWS_PER_PATTERN, CH[ch])] = (
        int(note), int(inst), 0x10 + max(0, min(64, int(vol))), fx & 0xFF, param & 0xFF)


def kick_row(cells, inst, row, vol=64):
    put(cells, "kick", row, inst, note_for(55.0), vol)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="content/experiments/milkytracker/phat-fm.xm")
    ap.add_argument("--stems", action="store_true")
    a = ap.parse_args()
    outdir = os.path.dirname(os.path.abspath(a.out))
    os.makedirs(outdir, exist_ok=True)

    S = make_samples()
    m = Module("PHAT FM - Z-DOT", channels=NCH, bpm=BPM, speed=6)
    I = {k: m.add_instrument(Instrument(k.upper(), [s])) for k, s in S.items()}
    print(f"instruments: {len(I)}  ({', '.join(I)})")

    patterns = []
    for p in range(6):
        cells = {}
        for bar in range(4):                      # each pattern = 4 bars
            b0 = bar * 16
            root, chord = PROG[bar]
            bass_note = note_for(root, BASS_BASE)
            chord_notes = [note_for(f, STAB_BASE) for f in chord]

            # ---- drums
            if p == 0:                             # intro: sparse
                if bar >= 2:
                    for s in (0, 6, 10):
                        kick_row(cells, I["kick"], b0 + s, 60)
                if bar >= 3:
                    for s in range(0, 16, 2):
                        put(cells, "hat", b0 + s, I["hat"], note_for(55.0),
                            44 if s % 4 else 56)
            elif p == 1:                           # build
                for s in (0, 4, 8, 12):
                    kick_row(cells, I["kick"], b0 + s, 58)
                for s in (4, 12):
                    put(cells, "snare", b0 + s, I["snare"], note_for(55.0), 58)
                for s in range(0, 16):
                    put(cells, "hat", b0 + s, I["hat"], note_for(55.0),
                        36 if s % 2 else 52)
                if bar == 3:
                    for s in range(8, 16):
                        put(cells, "snare", b0 + s, I["snare"], note_for(55.0),
                            20 + (s - 8) * 5)
            else:                                  # drops / breakdown
                four = p != 4
                if four:
                    for s in (0, 4, 8, 12):
                        kick_row(cells, I["kick"], b0 + s, 64 if s in (0, 8) else 54)
                    for s in (4, 6, 12, 14):
                        put(cells, "snare", b0 + s, I["snare"], note_for(55.0),
                            60 if s in (4, 12) else 30)
                    for s in range(0, 16):
                        put(cells, "hat", b0 + s, I["hat"], note_for(55.0),
                            34 if s % 2 else 58)
                        if s % 4 == 3:
                            put(cells, "ohat", b0 + s, I["ohat"], note_for(55.0), 40)
                    if p >= 2:
                        for s in (4, 12):
                            put(cells, "clap", b0 + s, I["clap"], note_for(55.0), 50)
                else:                               # breakdown: no kick
                    for s in (4, 12):
                        put(cells, "clap", b0 + s, I["clap"], note_for(55.0), 48)
                    for s in range(0, 16, 2):
                        put(cells, "hat", b0 + s, I["hat"], note_for(55.0), 30)

            # ---- bass + sub
            bassline = {0: BASS_SPARSE, 1: BASS_HALF,
                        2: BASS_FULL, 3: BASS_FULL,
                        4: BASS_HALF, 5: BASS_FULL}[p]
            for step, off in bassline:
                put(cells, "bass", b0 + step, I["bass"], bass_note + off,
                    60 if step in (0, 8) else 46)
            if p >= 2:
                for step in (0, 8):
                    put(cells, "sub", b0 + step, I["sub"], bass_note - 12, 54)

            # ---- chord stabs: offbeats, the phat chord
            if p in (2, 3, 4, 5):
                hits = (2, 6, 10, 14) if p != 4 else (0, 8)
                for i, ch_name in enumerate(("stabA", "stabB", "stabC")):
                    for s in hits:
                        put(cells, ch_name, b0 + s, I["stab"], chord_notes[i],
                            44 if i == 0 else 36)

            # ---- lead from the third pattern on
            if p in (3, 5):
                line = [(0, 0), (3, 3), (6, 7), (10, 5), (12, 3), (14, 0)]
                oct_up = 12 if p == 5 else 0
                for s, off in line:
                    put(cells, "lead", b0 + s, I["lead"],
                        note_for(chord[0], 440.0) + off + oct_up, 50 if s % 4 == 0 else 40)

            # ---- phat finish: sub drop at the end of the last bar
            if p == 5 and bar == 3:
                put(cells, "sub", b0 + 12, I["sub"], bass_note - 12, 56,
                    fx=0x02, param=0x18)          # portamento down = bass drop
            if p in (1, 3, 5) and bar == 0:
                put(cells, "crash", b0, I["crash"], note_for(55.0), 52,
                    fx=0x0C, param=0x0C)          # note cut after a few ticks

        patterns.append(m.add_pattern(cells))

    m.order = [0, 1, 2, 3, 4, 5, 2, 5]
    size = m.save(a.out)
    rows = ROWS_PER_PATTERN
    print(f"wrote {a.out} ({size} B)  patterns={len(patterns)} order={m.order}")
    print(f"  {len(m.order)*rows} rows @ {BPM}bpm speed 6 -> "
          f"{len(m.order)*rows*6*2.5/BPM:.1f}s")

    wav = os.path.join(outdir, "phat-fm.wav")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
                    "-i", a.out, "-c:a", "pcm_s16le", "-ar", "44100", wav], check=True)
    print("rendered", wav)

    mp3 = os.path.join(outdir, "phat-fm.mp3")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", wav, "-b:a", "192k", mp3], check=True)
    print("encoded", mp3)


if __name__ == "__main__":
    main()
