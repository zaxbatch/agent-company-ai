#!/usr/bin/env python3
"""MilkUps voice library — a real synth kit, not four fixed waveforms.

The old pipeline had ONE lead (a square pinned 2-3 octaves up) shared by every
track. That is why all 8 songs sounded identical (measured centroid spread: 162 Hz
across eight tracks).

This module provides genuinely distinct voices. Each track picks its OWN lead,
bass and drum kit, and each voice is designed with its own oscillator stack,
filter, envelope and character.

Requires xm_lib's 16-bit mode so quiet detail survives.
"""
from __future__ import annotations
import math, sys
from pathlib import Path
import numpy as np
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xm_lib import SR

# ── filters ──────────────────────────────────────────────────────────────────
def lp(x, c, order=2):
    b, a = signal.butter(order, min(0.99, max(0.01, c / (SR / 2))), btype="low")
    return signal.lfilter(b, a, x)

def hp(x, c, order=2):
    b, a = signal.butter(order, min(0.99, max(0.01, c / (SR / 2))), btype="high")
    return signal.lfilter(b, a, x)

def bp(x, lo, hi, order=2):
    b, a = signal.butter(order, [max(0.01, lo/(SR/2)), min(0.99, hi/(SR/2))], btype="band")
    return signal.lfilter(b, a, x)

def env(n, a=0.005, d=0.25, s=0.7, r=0.12, curve=6.0):
    """ADSR-ish envelope. Attack/decay/release in seconds."""
    ai = max(1, int(a * SR)); di = max(1, int(d * SR)); ri = max(1, int(r * SR))
    si = max(1, n - ai - di - ri)
    e = np.concatenate([
        np.linspace(0, 1, ai),
        np.linspace(1, s, di),
        np.full(si, s),
        np.linspace(s, 0, ri),
    ])
    if len(e) < n: e = np.pad(e, (0, n - len(e)))
    return e[:n].astype(np.float64)

# ── oscillators ──────────────────────────────────────────────────────────────
def saw(f, t):  return 2.0 * ((t * f) % 1.0) - 1.0
def sq(f, t, duty=0.5): return np.where((t * f) % 1.0 < duty, 1.0, -1.0)
def tri(f, t):  return 2.0 * np.abs(2.0 * ((t * f) % 1.0) - 1.0) - 1.0
def sine(f, t): return np.sin(2 * np.pi * f * t)
def pulse_pwm(f, t, width=0.5, rate=0.6):
    """Width-modulated pulse — the classic 'hollow, moving' lead."""
    m = 0.5 + 0.42 * np.sin(2 * np.pi * rate * t)
    w = np.clip(width * (0.55 + m), 0.04, 0.96)
    return np.where((t * f) % 1.0 < w, 1.0, -1.0)

def fm(carrier, mod, index, t, decay=3.0):
    """Simple FM — bells, metallic tones, glassy leads."""
    m = np.sin(2 * np.pi * mod * t) * index * np.exp(-np.linspace(0, decay, len(t)))
    return np.sin(2 * np.pi * carrier * t + m)

def wavetable(f, t, harmonics, drift=0.0, seed=0):
    """Additive voice built from a harmonic series — organ, glass, brass."""
    rng = np.random.default_rng(seed)
    out = np.zeros(len(t))
    for i, amp in enumerate(harmonics, start=1):
        d = 1.0 + (rng.uniform(-drift, drift) if drift else 0.0)
        out += amp * np.sin(2 * np.pi * f * i * d * t)
    return out / max(1e-9, np.max(np.abs(out)))

# ── LEAD VOICES: eight genuinely different leads ─────────────────────────────
def lead_bright_square(f, dur):
    """1 · piercing chip lead — narrow, cutting, the classic arcade voice."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = sq(f, t, 0.5) * 0.8 + sq(f * 2.01, t, 0.5) * 0.2
    x = hp(lp(x, 7200), 260) * env(n, 0.003, 0.10, 0.62, 0.07, 5)
    return np.tanh(x * 1.5) * 0.62

def lead_detuned_saw(f, dur):
    """2 · wide detuned saw stack — aggressive, chorusy, modern."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for c in (-22, -11, 0, 11, 22):
        x += saw(f * 2 ** (c / 1200.0), t)
    x /= 5
    x = lp(x, 3000) * env(n, 0.012, 0.35, 0.68, 0.16, 4)
    return np.tanh(x * 1.9) * 0.58

def lead_soft_triangle(f, dur):
    """3 · gentle triangle — melancholy, hollow, quiet by nature."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = tri(f, t) * 0.75 + sine(f * 2, t) * 0.18
    x = lp(x, 2100) * env(n, 0.055, 0.50, 0.55, 0.34, 3)
    return x * 0.52

def lead_fm_bell(f, dur):
    """4 · glassy FM bell — dreamy, shimmering, airy."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = fm(f, f * 3.02, 2.6, t, decay=2.2) * 0.7 + fm(f * 2, f * 5.01, 1.4, t, decay=3.4) * 0.3
    x = bp(x, 240, 7600) * env(n, 0.004, 0.75, 0.35, 0.5, 2.4)
    return x * 0.5

def lead_narrow_pulse(f, dur):
    """5 · robotic 25% pulse — dry, machine-like, staccato."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = pulse_pwm(f, t, 0.25, 0.45) * 0.85
    x = hp(lp(x, 4800), 180) * env(n, 0.002, 0.05, 0.45, 0.04, 9)
    return np.tanh(x * 1.4) * 0.6

def lead_organ(f, dur):
    """6 · stacked-sine organ — warm, chordal, hymn-like, no bite."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = wavetable(f, t, [1.0, 0.55, 0.32, 0.20, 0.12, 0.08, 0.05], drift=0.0016, seed=11)
    x = lp(x, 3600) * env(n, 0.030, 0.22, 0.80, 0.20, 2.0)
    return x * 0.55

def lead_metallic_fm(f, dur):
    """7 · inharmonic FM — industrial, clangy, unsettling."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = fm(f, f * 1.71, 4.2, t, decay=4.5) * 0.75 + fm(f * 0.5, f * 2.93, 2.1, t, decay=5.5) * 0.25
    x = bp(x, 300, 9000) * env(n, 0.003, 0.28, 0.55, 0.18, 5)
    return np.tanh(x * 1.6) * 0.52

def lead_supersaw(f, dur):
    """8 · seven-voice supersaw — anthemic, big, triumphant."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for c in (-31, -19, -8, 0, 8, 19, 31):
        x += saw(f * 2 ** (c / 1200.0), t)
    x /= 7
    x = lp(x, 4600) * env(n, 0.022, 0.40, 0.72, 0.24, 3.2)
    return np.tanh(x * 1.5) * 0.6

def lead_pluck(f, dur):
    """9 · short plucked string — percussive, dry, rhythmic."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = wavetable(f, t, [1.0, 0.5, 0.33, 0.25, 0.2, 0.16], drift=0.002, seed=3)
    x *= np.exp(-np.linspace(0, 7.5, n))
    return lp(x, 4200) * 0.56

def lead_chip_arp(f, dur):
    """10 · fast-decaying chip blip — arpeggio machine."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = sq(f, t, 0.32) * 0.7 + sq(f * 1.5, t, 0.5) * 0.3
    x *= np.exp(-np.linspace(0, 11, n))
    return hp(x, 320) * 0.58

LEADS = {
    "bright_square": lead_bright_square, "detuned_saw": lead_detuned_saw,
    "soft_triangle": lead_soft_triangle, "fm_bell": lead_fm_bell,
    "narrow_pulse": lead_narrow_pulse,   "organ": lead_organ,
    "metallic_fm": lead_metallic_fm,     "supersaw": lead_supersaw,
    "pluck": lead_pluck,                 "chip_arp": lead_chip_arp,
}

# ── BASS VOICES ──────────────────────────────────────────────────────────────
def bass_sub(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = sine(f, t) * 0.9 + sine(f * 2, t) * 0.08
    return lp(x, 180) * env(n, 0.006, 0.3, 0.8, 0.12, 2.2) * 0.72

def bass_saw(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = saw(f, t) * 0.7 + saw(f * 0.997, t) * 0.3
    x = lp(x, 700) * env(n, 0.004, 0.22, 0.7, 0.09, 4)
    return np.tanh(x * 2.0) * 0.62

def bass_square(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = sq(f, t, 0.5) * 0.8 + sine(f, t) * 0.25
    return lp(x, 520) * env(n, 0.005, 0.26, 0.72, 0.10, 3.4) * 0.66

def bass_fm(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = fm(f, f * 1.5, 1.9, t, decay=3.2) * 0.85 + sine(f, t) * 0.2
    return lp(x, 900) * env(n, 0.004, 0.28, 0.7, 0.11, 3.6) * 0.6

def bass_pluck(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = wavetable(f, t, [1.0, 0.6, 0.4, 0.26, 0.16], drift=0.003, seed=7)
    x *= np.exp(-np.linspace(0, 5.0, n))
    return lp(x, 1100) * 0.66

def bass_organ(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = wavetable(f, t, [1.0, 0.42, 0.2, 0.1, 0.05], drift=0.001, seed=5)
    return lp(x, 620) * env(n, 0.02, 0.3, 0.85, 0.18, 1.8) * 0.6

BASSES = {
    "sub": bass_sub, "saw": bass_saw, "square": bass_square,
    "fm": bass_fm, "pluck": bass_pluck, "organ": bass_organ,
}

# ── DRUM KITS: each a different character, not one kit reused ────────────────
def _click(n, seed, decay, hp_hz):
    rng = np.random.default_rng(seed)
    return hp(rng.standard_normal(n) * np.exp(-np.linspace(0, decay, n)), hp_hz)

def kit_tight():
    """Punchy, short, dry — clean electronic."""
    k = np.sin(2*np.pi*np.cumsum(160*np.exp(-np.arange(int(0.30*SR))/SR*32)+48)/SR)
    k *= np.exp(-np.linspace(0,8.5,len(k)))
    sn = _click(int(0.16*SR),2,26,1400)*0.9 + sine(200,np.arange(int(0.16*SR))/SR)*np.exp(-np.linspace(0,30,int(0.16*SR)))*0.5
    h  = _click(int(0.035*SR),3,60,8000)*0.45
    return {"kick":np.tanh(k*2.1)*0.94, "snare":np.tanh(sn*1.5)*0.8, "hat":h}

def kit_deep():
    """Deep boomy kick, fat snare — hip-hop weight."""
    k = np.sin(2*np.pi*np.cumsum(115*np.exp(-np.arange(int(0.52*SR))/SR*19)+36)/SR)
    k *= np.exp(-np.linspace(0,6.0,len(k)))
    sn = _click(int(0.26*SR),12,17,900)*0.85 + sine(170,np.arange(int(0.26*SR))/SR)*np.exp(-np.linspace(0,19,int(0.26*SR)))*0.7
    h  = _click(int(0.05*SR),13,44,6500)*0.4
    return {"kick":np.tanh(k*1.8)*0.96, "snare":np.tanh(sn*1.3)*0.82, "hat":h}

def kit_clicky():
    """Click-tuned, digital, high — machine precision."""
    k = np.sin(2*np.pi*np.cumsum(215*np.exp(-np.arange(int(0.17*SR))/SR*42)+70)/SR)
    k *= np.exp(-np.linspace(0,13,len(k)))
    k += _click(len(k),22,50,3000)*0.35
    sn = _click(int(0.12*SR),23,33,2600)*0.95 + sine(320,np.arange(int(0.12*SR))/SR)*np.exp(-np.linspace(0,38,int(0.12*SR)))*0.4
    h  = _click(int(0.026*SR),24,74,10500)*0.42
    return {"kick":np.tanh(k*2.3)*0.9, "snare":np.tanh(sn*1.7)*0.78, "hat":h}

def kit_soft():
    """Muffled, lo-fi, gentle — bedroom warmth."""
    k = np.sin(2*np.pi*np.cumsum(128*np.exp(-np.arange(int(0.38*SR))/SR*21)+42)/SR)
    k *= np.exp(-np.linspace(0,7.5,len(k)))
    k = lp(k, 900)
    sn = lp(_click(int(0.22*SR),32,19,700)*0.8, 3200) + lp(sine(180,np.arange(int(0.22*SR))/SR),2400)*np.exp(-np.linspace(0,22,int(0.22*SR)))*0.6
    h  = lp(_click(int(0.045*SR),33,40,5200), 7200)*0.32
    return {"kick":k*0.9, "snare":sn*0.72, "hat":h}

def kit_industrial():
    """Distorted, harsh, heavy — machinery."""
    k = np.sin(2*np.pi*np.cumsum(145*np.exp(-np.arange(int(0.42*SR))/SR*24)+44)/SR)
    k *= np.exp(-np.linspace(0,6.5,len(k)))
    k = np.tanh(k*3.6)
    sn = np.tanh(_click(int(0.30*SR),42,14,1100)*1.9)*0.9 + np.tanh(sine(150,np.arange(int(0.30*SR))/SR)*2.4)*np.exp(-np.linspace(0,16,int(0.30*SR)))*0.6
    h  = _click(int(0.06*SR),43,32,7000)*0.5
    return {"kick":k*0.95, "snare":sn*0.8, "hat":h}

def kit_808():
    """Long sub kick, snappy snare — trap/808 flavour."""
    k = np.sin(2*np.pi*np.cumsum(78*np.exp(-np.arange(int(1.05*SR))/SR*7.5)+34)/SR)
    k *= np.exp(-np.linspace(0,3.4,len(k)))
    sn = _click(int(0.14*SR),52,29,2000)*0.9 + sine(210,np.arange(int(0.14*SR))/SR)*np.exp(-np.linspace(0,33,int(0.14*SR)))*0.45
    h  = _click(int(0.030*SR),53,68,9500)*0.4
    return {"kick":np.tanh(k*1.9)*0.95, "snare":np.tanh(sn*1.6)*0.8, "hat":h}

KITS = {"tight":kit_tight, "deep":kit_deep, "clicky":kit_clicky,
        "soft":kit_soft, "industrial":kit_industrial, "808":kit_808}
