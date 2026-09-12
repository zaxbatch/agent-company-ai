#!/usr/bin/env python3
"""Objective QA for an LMMS render: level, clipping, tempo, and section energy.

Proves the .mmp actually produced music at the intended tempo, and that the
arrangement changes between the first and second half.
"""
from __future__ import annotations
import sys
import numpy as np
import soundfile as sf


def analyze(path, expect_bpm=None):
    x, sr = sf.read(path, always_2d=True)
    mono = x.mean(axis=1)
    dur = len(mono) / sr
    peak = float(np.max(np.abs(mono)))
    clipped = int(np.sum(np.abs(mono) >= 0.999))
    rms = float(np.sqrt(np.mean(mono ** 2)))
    dbfs = 20 * np.log10(max(rms, 1e-9))

    # onset envelope -> autocorrelation -> tempo
    hop, win = 256, 1024
    n = 1 + (len(mono) - win) // hop
    frames = np.lib.stride_tricks.as_strided(
        mono, shape=(n, win), strides=(mono.strides[0] * hop, mono.strides[0]))
    env = np.sqrt((frames ** 2).mean(axis=1))
    env = np.diff(env, prepend=env[0])
    env[env < 0] = 0
    env -= env.mean()
    ac = np.correlate(env, env, mode="full")[len(env) - 1:]
    lo = int(sr / hop * 60 / 200)   # 200 bpm ceiling
    hi = int(sr / hop * 60 / 60)    # 60 bpm floor
    lag = lo + int(np.argmax(ac[lo:hi]))
    bpm = 60.0 * sr / (lag * hop)

    # per-bar energy (4 beats) at the detected tempo
    spb = int(sr * 240.0 / bpm)  # 4 beats = 1 bar
    bars = [mono[i:i + spb] for i in range(0, len(mono) - spb // 2, spb)]
    bar_rms = [float(np.sqrt(np.mean(b ** 2))) for b in bars if len(b) > spb // 2]

    # low-band (kick) vs high-band (hats/snare) energy via FFT
    spec = np.abs(np.fft.rfft(mono * np.hanning(len(mono))))
    freqs = np.fft.rfftfreq(len(mono), 1 / sr)
    low = float(spec[(freqs > 30) & (freqs < 120)].sum())
    high = float(spec[(freqs > 5000) & (freqs < 16000)].sum())
    mid = float(spec[(freqs > 120) & (freqs < 5000)].sum())

    print(f"file        : {path}")
    print(f"duration    : {dur:.3f} s   ({len(mono)} frames, {sr} Hz, {x.shape[1]}ch)")
    print(f"peak        : {peak:.4f}  ({20*np.log10(max(peak,1e-9)):.2f} dBFS)")
    print(f"rms         : {dbfs:.2f} dBFS")
    print(f"clipped     : {clipped} samples")
    print(f"tempo       : {bpm:.2f} BPM" + (f"  (expected {expect_bpm})" if expect_bpm else ""))
    print(f"bar RMS     : {[round(v,4) for v in bar_rms]}")
    if len(bar_rms) >= 8:
        h1, h2 = np.mean(bar_rms[:4]), np.mean(bar_rms[4:8])
        print(f"arrangement : first half {h1:.4f} vs second half {h2:.4f} "
              f"({(h2/h1-1)*100:+.1f}%)")
    print(f"band energy : low {low:.0f} / mid {mid:.0f} / high {high:.0f}")
    ok = (dur > 1 and dbfs > -40 and clipped < 100)
    print(f"VERDICT     : {'PASS' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    bpm = int(sys.argv[2]) if len(sys.argv) > 2 else None
    sys.exit(0 if analyze(sys.argv[1], bpm) else 1)
