#!/usr/bin/env python3
"""songkit.py — shared toolkit for SnowSnakes original songs.

THE POINT OF THIS FILE
----------------------
"Shelves After Dark" (disco) set the quality bar. The bar is NOT the sound --
it is the PROCESS. This module holds the genre-agnostic half of that process so
every new song gets the same rigour without getting the same groove:

  * synthesis primitives      (oscillators, envelopes, placement, mastering)
  * a groove ANALYSER         (measures the actual rhythm of the rendered audio)
  * genre signatures          (what each genre must measurably be)

Genre-specific arrangements live in each song's own builder. Nothing here
hardcodes disco, so tracks cannot drift toward sounding alike.

Rule enforced by scripts/verify_song.py: a song must be measurably TRUE to the
genre it claims. Disco must swing four-on-the-floor; boom-bap must not.
"""
from __future__ import annotations
import math
import wave
from pathlib import Path

import numpy as np
from numpy.fft import rfft, rfftfreq

SR = 44100


# ── oscillator primitives (pure math: no samples, ever) ──────────────────────
def saw(ph):
    return 2.0 * ((ph / (2 * np.pi)) % 1.0) - 1.0


def sq(ph):
    return np.sign(np.sin(ph))


def tri(ph):
    return 2.0 * np.abs(2.0 * ((ph / (2 * np.pi)) % 1.0) - 1.0) - 1.0


def sine(ph):
    return np.sin(ph)


def hz(midi):
    """MIDI note -> Hz."""
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def adsr(n, a=0.01, d=0.08, s=0.6, r=0.12):
    ai, di, ri = int(a * SR), int(d * SR), int(r * SR)
    si = max(n - ai - di - ri, 0)
    return np.concatenate([
        np.linspace(0, 1, ai, endpoint=False),
        np.linspace(1, s, di, endpoint=False),
        np.full(si, s),
        np.linspace(s, 0, ri),
    ])[:n]


def place(buf, t, sig, gain=1.0):
    """Mix *sig* into *buf* starting at time t seconds."""
    i = int(t * SR)
    if i < 0:
        sig, i = sig[-i:], 0
    n = min(len(sig), len(buf) - i)
    if n > 0:
        buf[i:i + n] += sig[:n] * gain
    return buf


def noise(rng, dur):
    n = int(dur * SR)
    return rng.uniform(-1, 1, n).astype(np.float32)


def exp_decay(n, rate):
    return np.exp(-rate * np.arange(n) / SR).astype(np.float32)


# ── generic drum voices (parameterised, so genres differ by the numbers) ─────
def kick(f0=138, f1=48, sweep=30, decay=7.5, dur=0.30, click=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * np.exp(-sweep * t) + f1
    body = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return (np.tanh((body + np.exp(-260 * t) * click) * 1.5) * exp_decay(n, decay) * 0.95).astype(np.float32)


def snare(rng, dur=0.20, decay=22, tone=190, mix=0.3):
    n = int(dur * SR)
    nz = noise(rng, dur) * exp_decay(n, decay)
    body = np.sin(2 * np.pi * tone * np.arange(n) / SR) * exp_decay(n, decay * 2.2)
    return ((nz * (1 - mix) + body * mix) * 0.7).astype(np.float32)


def hat(rng, open_=False, bright=True):
    dur = 0.28 if open_ else 0.045
    n = int(dur * SR)
    nz = noise(rng, dur)
    if bright:
        nz = np.diff(np.concatenate([[0], nz]))
    return (nz * exp_decay(n, 9 if open_ else 65) * (0.20 if open_ else 0.16)).astype(np.float32)


def clap(rng, dur=0.20, bursts=(0.0, 0.011, 0.021), decay=34):
    n = int(dur * SR)
    out = np.zeros(n, dtype=np.float32)
    for k, off in enumerate(bursts):
        s = int(off * SR)
        m = n - s
        out[s:s + m] += (noise(rng, m / SR)[:m] * exp_decay(m, decay) * (1.0 - k * 0.22)).astype(np.float32)
    return (out * 0.42).astype(np.float32)


def tamb(rng, dur=0.09, decay=38):
    n = int(dur * SR)
    return (noise(rng, dur)[:n] * exp_decay(n, decay) * 0.13).astype(np.float32)


# ── sustained / pitched voices ───────────────────────────────────────────────
def strings(midis, dur, detunes=(0.996, 1.0, 1.005, 1.011), bright=1.0,
            a=0.012, d=0.08, s=0.55, r=0.18, gain=0.16):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, dtype=np.float32)
    for m in midis:
        for det in detunes:
            out += saw(2 * np.pi * hz(m) * det * t).astype(np.float32) / len(detunes)
    return (out * adsr(n, a, d, s, r) * gain * bright).astype(np.float32)


def brass(midi, dur, gain=0.15):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(midi)
    v = 0.6 * saw(2 * np.pi * f * t) + 0.35 * sq(2 * np.pi * f * 1.002 * t) + 0.15 * tri(2 * np.pi * f * 0.5 * t)
    return (v * adsr(n, 0.01, 0.06, 0.7, 0.16) * gain).astype(np.float32)


def bass(midi, dur, drive=1.25, gain=0.34, a=0.004, d=0.10, s=0.45, r=0.07):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(midi)
    v = 0.75 * saw(2 * np.pi * f * t) + 0.45 * sine(2 * np.pi * f * 0.5 * t)
    return (np.tanh(v * adsr(n, a, d, s, r) * drive) * gain).astype(np.float32)


def skank(midis, dur=0.10, gain=0.10):
    n = int(dur * SR)
    out = np.zeros(n, dtype=np.float32)
    for m in midis:
        t = np.arange(n) / SR
        out += (saw(2 * np.pi * hz(m) * t) * 0.5 + sq(2 * np.pi * hz(m) * 1.004 * t) * 0.2).astype(np.float32)
    return (out * exp_decay(n, 40) * gain).astype(np.float32)


# ── mastering ────────────────────────────────────────────────────────────────
def master(buf, peak=0.92, drive=1.15, fade_in=0.15, fade_out=1.8):
    p = float(np.max(np.abs(buf))) or 1.0
    out = np.tanh((buf / p * peak) * drive).astype(np.float32)
    ni, no = int(fade_in * SR), int(fade_out * SR)
    if ni:
        out[:ni] *= np.linspace(0, 1, ni)
    if no and no < len(out):
        out[-no:] *= np.linspace(1, 0, no)
    return out


def write_wav(buf, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(buf * 32767, -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


# ── groove analysis: measure the rhythm that actually got rendered ───────────
def load(path):
    with wave.open(str(path)) as w:
        sr = w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    return a, sr


def band_env(a, sr, lo, hi, win=2048, hop=256):
    """Energy in a frequency band over time, normalised 0..1, plus a time axis."""
    f = rfftfreq(win, 1 / sr)
    m = (f >= lo) & (f <= hi)
    env = np.array([np.abs(rfft(a[i:i + win] * np.hanning(win)))[m].sum()
                    for i in range(0, max(0, len(a) - win), hop)], dtype=np.float64)
    if env.size == 0:
        return np.zeros(1), np.zeros(1)
    env = (env - env.min()) / (env.max() - env.min() or 1.0)
    return env, np.arange(len(env)) * hop / sr


def onsets(a, sr, lo=40, hi=110, win=2048, hop=256, height=0.25, min_gap=0.28):
    """Onset times (seconds) of low-band hits -- i.e. where the kicks land."""
    from scipy.signal import find_peaks
    env, ts = band_env(a, sr, lo, hi, win, hop)
    idx, _ = find_peaks(env, distance=max(1, int(min_gap * sr / hop)), height=height)
    return ts[idx]


def beat_grid_ratio(onset_times, bpm, tol=0.06):
    """Fraction of inter-onset gaps that equal exactly ONE beat."""
    if len(onset_times) < 3:
        return 0.0, 0.0
    spb = 60.0 / bpm
    d = np.diff(onset_times)
    return float((np.abs(d - spb) < tol).mean()), float(np.median(d))


def offbeat_ratio(a, sr, bpm, lo=6000, hi=12000):
    """Hi-hat balance: mean high-band energy on offbeats vs on-beats."""
    env, ts = band_env(a, sr, lo, hi, win=1024, hop=128)
    spb = 60.0 / bpm
    if env.size < 4:
        return 0.0, 0.0
    def at(t):
        i = int(t * sr / 128)
        return env[i] if 0 <= i < len(env) else 0.0
    beats = np.arange(0, ts[-1], spb)
    on = np.mean([at(t) for t in beats]) if len(beats) else 0.0
    off = np.mean([at(t + spb / 2) for t in beats]) if len(beats) else 0.0
    return float(on), float(off)


def spectral_centroid(a, sr):
    """Brightness in Hz -- a cheap timbral fingerprint for variety checks."""
    n = min(65536, len(a))
    seg = a[:n] * np.hanning(n)
    S = np.abs(rfft(seg))
    f = rfftfreq(n, 1 / sr)
    return float((S * f).sum() / (S.sum() or 1.0))


def duration(path):
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()
