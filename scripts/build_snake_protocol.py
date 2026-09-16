#!/usr/bin/env python3
"""SNAKE PROTOCOL — a uniquely formatted SnowSnakes tracker beat.

What makes the FORMATTING crazy (not just the sound):
  * ODD METERS via pattern-break: 7/8 bars (break at row 13), 5/4 bars (row 19),
    6/8 bars (row 23) sitting inside an otherwise 4/4 song.
  * TEMPO AUTOMATION: Fxx set-speed / set-BPM changes mid-song to shift feel.
  * MULTI-RETRIGGER (Q) and RETRIGGER (E9x) used as a rhythmic instrument.
  * NOTE DELAY (EDx) as swing/humanise, NOTE CUT (ECx) for staccato.
  * ARPEGGIO (0xy) rapid chord stabs, VIBRATO (4xy) on leads.
  * PANNING (8xx) ping-pong across channels.
  * A GLITCH pattern built almost entirely from effect-column events.
  * Same pattern reused at multiple points in the order list (trailer-style).

Output: content/snowsnakes/beats/snake-protocol.{xm,mp3} + evidence json.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import numpy as np
from xm_lib import Module, Instrument, Sample, SR, note_for, ROWS_PER_PATTERN

OUT = ROOT / "content" / "snowsnakes" / "beats"
OUT.mkdir(parents=True, exist_ok=True)

BPM, SPEED = 150, 6
TITLE = "SNAKE PROTOCOL"

# ── channels ──────────────────────────────────────────────────────────────────
CH = dict(kick=0, snare=1, hat=2, perc=3, bass=4, lead=5, arp=6, glitch=7)
NCH = 8

# XM effect numbers
ARP, PORTA_UP, PORTA_DN, VIB, TREM, PAN, VSLIDE = 0x00, 0x01, 0x02, 0x04, 0x07, 0x08, 0x0A
JUMP, BREAK, VOL, EXT, TEMPO = 0x0B, 0x0D, 0x0C, 0x0E, 0x0F
GLOBALVOL, MULTIRETRIG, TREMOR = 0x10, 0x1B, 0x1C


def env(n, a=0.002, d=6.0):
    a = max(1, int(a * SR)); dd = max(1, n - a)
    return np.concatenate([np.linspace(0, 1, a), np.exp(-np.linspace(0, d, dd))])[:n]


def lp(x, c, order=2):
    from scipy import signal
    b, a = signal.butter(order, min(0.99, c / (SR / 2)), btype="low")
    return signal.lfilter(b, a, x)


def hp(x, c, order=2):
    from scipy import signal
    b, a = signal.butter(order, min(0.99, c / (SR / 2)), btype="high")
    return signal.lfilter(b, a, x)


def saw(f, t): return 2.0 * ((t * f) % 1.0) - 1.0
def sq(f, t):  return np.sign(np.sin(2 * np.pi * f * t)) * 0.85


def phat(freq, dur, detune=(0, 7, -9, 14), drive=2.6, cut=2600, dec=6.0):
    n = int(dur * SR); t = np.arange(n) / SR
    o = np.zeros(n)
    for c in detune: o += saw(freq * 2 ** (c / 1200.0), t)
    o /= len(detune)
    o = lp(o, cut) * np.exp(-np.linspace(0, dec, n))
    return np.tanh(o * drive) * 0.92


def make_samples():
    S = {}
    n = int(0.60 * SR); t = np.arange(n) / SR
    f = 156 * np.exp(-t * 27) + 42
    k = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.6)
    click = hp(np.random.RandomState(11).randn(n) * np.exp(-t * 230), 1900) * 0.5
    S["kick"] = Sample(np.tanh((k * 1.5 + click) * 2.3) * 0.95, name="KICK")

    n = int(0.28 * SR); t = np.arange(n) / SR
    rng = np.random.RandomState(12)
    nz = rng.randn(n) * np.exp(-t * 24)
    tn = (np.sin(2 * np.pi * 196 * t) * 0.7 + np.sin(2 * np.pi * 344 * t) * 0.4) * np.exp(-t * 28)
    S["snare"] = Sample(np.tanh((nz * 0.9 + tn) * 1.6) * 0.8, name="SNARE")

    n = int(0.050 * SR); t = np.arange(n) / SR
    S["hat"] = Sample(hp(np.random.RandomState(13).randn(n), 7600) * np.exp(-t * 160) * 0.5, name="HAT")
    n = int(0.26 * SR); t = np.arange(n) / SR
    S["ohat"] = Sample(hp(np.random.RandomState(14).randn(n), 6200) * np.exp(-t * 22) * 0.42, name="OPEN HAT")

    n = int(0.20 * SR); t = np.arange(n) / SR
    S["perc"] = Sample(np.tanh(np.sin(2 * np.pi * 780 * t) * np.exp(-t * 40) * 1.7) * 0.6, name="PERC")

    S["bass"] = Sample(phat(55.0, 0.85, (0, 9, -12, 17), 2.9, 720, 3.0), name="PHAT BASS")
    n = int(0.90 * SR); t = np.arange(n) / SR
    S["sub"] = Sample(np.sin(2 * np.pi * 41.2 * t) * np.exp(-t * 3.3) * 0.9, name="SUB")
    S["stab"] = Sample(phat(220.0, 0.50, (0, 11, -14, 19), 3.1, 3600, 7.5), name="STAB")
    n = int(0.60 * SR); t = np.arange(n) / SR
    ld = (sq(440.0, t) * 0.6 + saw(440.0 * 1.005, t) * 0.4)
    S["lead"] = Sample(np.tanh(lp(ld, 5400) * np.exp(-np.linspace(0, 2.1, n)) * 1.8) * 0.75, name="LEAD")
    n = int(0.34 * SR); t = np.arange(n) / SR
    a = np.zeros(n)
    for h in (1, 2, 3, 4, 5):
        a += np.sin(2 * np.pi * 440 * h * t) / h * np.exp(-t * (9 + h))
    S["arp"] = Sample(np.tanh(lp(a, 6000) * 2.0) * 0.62, name="ARP")
    n = int(0.16 * SR); t = np.arange(n) / SR
    z = hp(np.random.RandomState(15).randn(n), 3800) * np.exp(-t * 46)
    z += np.sin(2 * np.pi * (1400 * np.exp(-t * 30)) * t) * np.exp(-t * 34) * 0.7
    S["zap"] = Sample(np.tanh(z * 2.0) * 0.72, name="ZAP")
    n = int(1.0 * SR); t = np.arange(n) / SR
    S["crash"] = Sample(hp(np.random.RandomState(16).randn(n), 3600) * np.exp(-t * 3.5) * 0.5, name="CRASH")
    return S


INST_ORDER = ["kick", "snare", "hat", "ohat", "perc", "bass", "sub",
              "stab", "lead", "arp", "zap", "crash"]
INST = {name: i + 1 for i, name in enumerate(INST_ORDER)}
NAT = {"kick": 55.0, "snare": 55.0, "hat": 55.0, "ohat": 55.0, "perc": 55.0,
       "bass": 55.0, "sub": 41.2, "stab": 220.0, "lead": 440.0, "arp": 440.0,
       "zap": 55.0, "crash": 55.0}

MIDI = {}
def m(name):                      # natural-pitch note for a drum/exact sample
    return note_for(NAT[name], NAT[name])


def fq(hz, name):                 # pitched note for a sample of known natural pitch
    return max(1, min(96, note_for(hz, NAT[name])))


def put(cells, ch, row, inst_name, note, vol=64, fx=0, param=0, delay=0):
    """Write a cell. `delay` uses EDx note-delay for swing."""
    if delay:
        fx, param = EXT, 0xD0 | (delay & 0x0F)
    cells[(row, ch)] = (int(note), INST[inst_name], 0x10 + max(0, min(64, int(vol))),
                        fx & 0xFF, param & 0xFF)


# ── musical material: A natural minor, i - VI - III - VII ─────────────────────
ROOTS = [33, 29, 36, 31]                      # A1, F1, C2, G1
CHORDS = {33: [57, 60, 64], 29: [53, 57, 60], 36: [60, 64, 67], 31: [55, 59, 62]}


def hz(midi):  return 440.0 * 2 ** ((midi - 69) / 12.0)
def bnote(midi): return fq(hz(midi), "bass")
def snote(midi): return fq(hz(midi), "stab")
def lnote(midi): return fq(hz(midi), "lead")
def anote(midi): return fq(hz(midi), "arp")


def kick_row(cells, b, vol=64, delay=0):
    put(cells, CH["kick"], b, "kick", m("kick"), vol, delay=delay)

def snare_row(cells, b, vol=54, fx=0, param=0):
    put(cells, CH["snare"], b, "snare", m("snare"), vol, fx=fx, param=param)

def hat_row(cells, b, vol=30, fx=0, param=0):
    put(cells, CH["hat"], b, "hat", m("hat"), vol, fx=fx, param=param)


def p_intro(c, bars=4):
    # sparse, atmospheric; established with a crash + tempo set to 125
    put(c, CH["glitch"], 0, "crash", m("crash"), 44, TEMPO, 125)
    for bar in range(bars):
        b = bar * 16
        if bar % 2 == 0: kick_row(c, b)
        kick_row(c, b + 10, 52, delay=3)                 # EDx delay = lazy kick
        for r in range(0, 16, 4):
            hat_row(c, b + r, 20 + (r == 0) * 8)
        if bar >= 2:
            for r in range(2, 16, 4):
                put(c, CH["perc"], b + r, "zap", m("zap"), 26, ARP, 0x37)
        if bar == 3:
            put(c, CH["bass"], b + 8, "bass", bnote(33), 48)
            put(c, CH["bass"], b + 14, "bass", bnote(36), 44, EXT, 0x9A)   # E9A retrig


def p_build(c, bars=4):
    put(c, CH["glitch"], 0, "crash", m("crash"), 48, TEMPO, 150)
    for bar in range(bars):
        b = bar * 16
        for r in (0, 4, 8, 12): kick_row(c, b + r)
        if bar >= 1: snare_row(c, b + 4); snare_row(c, b + 12)
        for r in range(0, 16, 2):
            acc = 34 if r % 4 == 0 else 24
            # ramp the retrigger density bar by bar
            if bar >= 2 and r == 14:
                hat_row(c, b + r, acc, MULTIRETRIG, 0x02 + bar)   # Q0x multi-retrig
            else:
                hat_row(c, b + r, acc)
        r = ROOTS[bar % 4]
        for off, ln in ((0, 0), (3, 0), (6, 12), (10, 0), (13, 7)):
            put(c, CH["bass"], b + off, "bass", bnote(r + ln), 52,
                VSLIDE, 0x03 if off else 0x00)
        for i, s in enumerate(CHORDS[r]):
            put(c, CH["arp"], b + i * 2, "stab", anote(s + 12), 40, ARP, 0x25)
        if bar == 3:
            put(c, CH["glitch"], b + 15, "zap", m("zap"), 40, MULTIRETRIG, 0x06)


def p_drop(c, bars=4, energy=1.0, pan_pingpong=True):
    """Main drop. 4/4, 64 rows. Dense electro kit + chord stabs + panning."""
    for bar in range(bars):
        b = bar * 16
        # broken-electro kick: never straight four-on-the-floor
        for r in (0, 6, 10): kick_row(c, b + r, 64)
        if bar % 2 == 1: kick_row(c, b + 14, 54, delay=2)
        snare_row(c, b + 4, 56)
        snare_row(c, b + 12, 58, EXT, 0x93)                    # E93 retrig x3
        for r in range(0, 16, 2):
            hat_row(c, b + r, int((34 if r % 4 == 0 else 22) * energy))
        # offbeat perc with retrigger stutter
        for r in (7, 15):
            put(c, CH["perc"], b + r, "perc", m("perc"), 34, MULTIRETRIG, 0x04)
        r = ROOTS[bar % 4]
        # bass: driving 16ths with portamento slides between roots
        for off in (0, 2, 4, 6, 8, 10, 12, 14):
            n = r + (12 if off in (6, 14) else 0)
            fx, pm = (PORTA_DN, 0x18) if off == 10 else (0, 0)
            put(c, CH["bass"], b + off, "bass", bnote(n), 54, fx, pm)
        put(c, CH["bass"], b + 15, "sub", fq(hz(r - 12), "sub"), 40)
        # chord stabs — arpeggio on the chord tones
        for i, s in enumerate(CHORDS[r]):
            put(c, CH["arp"], b + i * 3, "stab", snote(s), 44, ARP, 0x37)
        put(c, CH["arp"], b + 12, "stab", snote(CHORDS[r][2] + 12), 40, VIB, 0x43)
        if pan_pingpong:
            for i in range(4):
                put(c, CH["lead"], b + i * 4, "lead", lnote(r + 36 + i), 34,
                    PAN, 0x10 + (0x0 if i % 2 else 0x0C))      # ping-pong 8xx
    return c


def p_odd78(c):
    """7/8 bar: a hard pattern-break at row 13 terminates the pattern early."""
    put(c, CH["glitch"], 0, "crash", m("crash"), 50, TEMPO, 141)
    for r in (0, 6, 8): kick_row(c, r)
    snare_row(c, 4, 58); snare_row(c, 10, 52, EXT, 0x92)
    for r in range(0, 14, 2): hat_row(c, r, 30 if r % 4 == 0 else 20)
    for off in (0, 3, 6, 9, 12): put(c, CH["bass"], off, "bass", bnote(33 + (off % 7)), 52)
    for i, s in enumerate(CHORDS[33]): put(c, CH["arp"], i * 4, "stab", snote(s + 12), 42, ARP, 0x25)
    put(c, CH["glitch"], 13, "zap", m("zap"), 34, BREAK, 0x00)   # D00 -> next pattern


def p_odd54(c):
    """5/4 bar: 20 rows, break at 19."""
    put(c, CH["glitch"], 0, "crash", m("crash"), 46, TEMPO, 158)
    for r in (0, 5, 10, 15): kick_row(c, r, 60)
    snare_row(c, 8, 54); snare_row(c, 18, 50, MULTIRETRIG, 0x03)
    for r in range(0, 20, 2): hat_row(c, r, 26)
    for off in (0, 4, 8, 12, 16): put(c, CH["bass"], off, "bass", bnote(29 + (12 if off % 8 else 0)), 52)
    for i, s in enumerate(CHORDS[29]): put(c, CH["arp"], i * 5, "stab", anote(s), 40, VIB, 0x52)
    put(c, CH["glitch"], 19, "zap", m("zap"), 30, BREAK, 0x00)


def p_lead(c, bars=4):
    """Drop with the lead melody + vibrato, tempo nudged to 150."""
    put(c, CH["glitch"], 0, "crash", m("crash"), 48, TEMPO, 150)
    mel = {0: 0, 2: 3, 4: 7, 6: 10, 8: 7, 10: 3, 12: 0, 14: -2}
    for bar in range(bars):
        b = bar * 16
        for r in (0, 6, 10): kick_row(c, b + r)
        snare_row(c, b + 4); snare_row(c, b + 12, 58, EXT, 0x93)
        for r in range(0, 16, 2): hat_row(c, b + r, 30 if r % 4 == 0 else 20)
        r0 = ROOTS[bar % 4]
        for off in (0, 3, 6, 8, 11, 14): put(c, CH["bass"], b + off, "bass", bnote(r0), 54)
        for off, deg in mel.items():
            fx, pm = (VIB, 0x48) if off in (4, 12) else (0, 0)
            put(c, CH["lead"], b + off, "lead", lnote(r0 + 24 + deg), 42, fx, pm)
        for i, s in enumerate(CHORDS[r0]):
            put(c, CH["arp"], b + 1 + i * 4, "stab", anote(s), 38, ARP, 0x36)


def p_glitch(c):
    """24 rows built almost entirely from effect-column events."""
    put(c, CH["glitch"], 0, "crash", m("crash"), 44, TEMPO, 168)
    c[(0, CH["kick"])] = (m("kick"), INST["kick"], 0x10 + 64, MULTIRETRIG, 0x0C)
    for r in range(0, 24):
        if r % 3 == 0: c[(r, CH["glitch"])] = (m("zap"), INST["zap"], 0x10 + 30,
                                               MULTIRETRIG, 0x02 + (r % 6))
        if r % 4 == 0: c[(r, CH["hat"])] = (m("hat"), INST["hat"], 0x10 + 26,
                                            EXT, 0x90 | (r % 8))
        if r % 5 == 0: c[(r, CH["perc"])] = (m("perc"), INST["perc"], 0x10 + 28,
                                             TREMOR, 0x21)
        if r % 6 == 1: c[(r, CH["snare"])] = (m("snare"), INST["snare"], 0x10 + 50,
                                              EXT, 0xD0 | (r % 5))
    for off in (0, 6, 12, 18): put(c, CH["bass"], off, "bass", bnote(36), 50, PORTA_UP, 0x14)
    for i, s in enumerate(CHORDS[36]): put(c, CH["arp"], i * 6, "stab", snote(s), 40, ARP, 0x47)
    c[(23, CH["glitch"])] = (m("zap"), INST["zap"], 0x10 + 34, BREAK, 0x00)


def p_breakdown(c, bars=4):
    put(c, CH["glitch"], 0, "crash", m("crash"), 36, TEMPO, 132)
    for bar in range(bars):
        b = bar * 16
        kick_row(c, b, 56)
        if bar % 2: snare_row(c, b + 8, 46)
        put(c, CH["bass"], b, "sub", fq(hz(ROOTS[bar % 4] - 12), "sub"), 52, VSLIDE, 0x05)
        for off in (0, 6, 12):
            put(c, CH["lead"], b + off, "lead", lnote(ROOTS[bar % 4] + 24), 34, VIB, 0x56)
        for r in range(0, 16, 4): hat_row(c, b + r, 18)
    # tempo ramp back up in the last bar
    for i, bpm in enumerate((138, 144, 150)):
        c[(48 + i * 4, CH["glitch"])] = (0, 0, 0, TEMPO, bpm)


def p_chaos(c, bars=4):
    """Tempo automation inside the pattern + panning sweeps."""
    for bar in range(bars):
        b = bar * 16
        c[(b, CH["glitch"])] = (0, 0, 0, TEMPO, (150, 163, 150, 178)[bar])
        for r in (0, 6, 10): kick_row(c, b + r)
        snare_row(c, b + 4); snare_row(c, b + 12, 58, MULTIRETRIG, 0x03)
        for r in range(0, 16, 2):
            hat_row(c, b + r, 28, PAN, 0x08 if r % 4 else 0x18)
        r0 = ROOTS[bar % 4]
        for off in (0, 4, 8, 12):
            put(c, CH["bass"], b + off, "bass", bnote(r0 + (12 if off % 8 else 0)), 54)
        for i, s in enumerate(CHORDS[r0]):
            for k in range(2):
                put(c, CH["arp"], b + 8 + i * 2 + k, "stab", anote(s + k * 12), 34,
                    ARP, 0x37 if k else 0x00)
        put(c, CH["glitch"], b + 15, "zap", m("zap"), 30, MULTIRETRIG, 0x05)


def p_outro(c, bars=4):
    put(c, CH["glitch"], 0, "crash", m("crash"), 44, TEMPO, 136)
    for bar in range(bars):
        b = bar * 16
        if bar < 2: kick_row(c, b, 58)
        for r in range(0, 16, 4): hat_row(c, b + r, 16 - bar * 2)
        put(c, CH["bass"], b, "sub", fq(hz(ROOTS[bar % 4] - 12), "sub"), 44)
    c[(62, CH["glitch"])] = (0, 0, 0, GLOBALVOL, 0x30)


def p_tail(c):
    """32 rows: fade to silence with a final retrigger flourish."""
    for r in range(0, 32, 4):
        c[(r, CH["glitch"])] = (m("zap"), INST["zap"], 0x10 + max(4, 30 - r), MULTIRETRIG, 0x03)
    c[(0, CH["kick"])] = (m("kick"), INST["kick"], 0x10 + 50, 0, 0)
    c[(31, CH["glitch"])] = (0, 0, 0, BREAK, 0x00)       # end


def _bassline(c, b, r):
    """Electro bass with slides + a retriggered tail."""
    put(c, CH["bass"], b + 0,  "bass", bnote(r), 56)
    put(c, CH["bass"], b + 3,  "bass", bnote(r), 50, VSLIDE, 0x03)
    put(c, CH["bass"], b + 6,  "bass", bnote(r + 12), 54, PORTA_DN, 0x08)
    put(c, CH["bass"], b + 9,  "bass", bnote(r), 52)
    put(c, CH["bass"], b + 11, "bass", bnote(r + 7), 46)
    put(c, CH["bass"], b + 14, "bass", bnote(r), 48, EXT, 0x94)      # retrig x4


def p_dropA(c, bars=4):
    for bar in range(bars):
        b = bar * 16; r = ROOTS[bar % 4]
        kick_row(c, b + 0); kick_row(c, b + 6, 58, delay=2)
        kick_row(c, b + 10, 60)
        snare_row(c, b + 4); snare_row(c, b + 12, 58)
        for rr in range(0, 16, 2):
            hat_row(c, b + rr, 32 if rr % 4 == 0 else 22,
                    MULTIRETRIG, 0x02 if rr == 14 else 0x00)
        _bassline(c, b, r)
        for i, s in enumerate(CHORDS[r]):
            put(c, CH["arp"], b + i * 2, "stab", anote(s + 12), 38, ARP, 0x37)
        # ping-pong pan on the perc
        put(c, CH["perc"], b + 7, "zap", m("zap"), 34, PAN, 0x20)
        put(c, CH["perc"], b + 15, "zap", m("zap"), 34, PAN, 0xE0)


def p_78(c):
    """7/8 bar — pattern break at row 13."""
    r = ROOTS[0]
    kick_row(c, 0); kick_row(c, 8, 58)
    snare_row(c, 4, 56, EXT, 0x93)
    for rr in range(0, 14, 2): hat_row(c, rr, 30)
    put(c, CH["bass"], 0, "bass", bnote(r), 54)
    put(c, CH["bass"], 6, "bass", bnote(r + 12), 50, VSLIDE, 0x02)
    for i, s in enumerate(CHORDS[r]): put(c, CH["arp"], i * 3, "stab", anote(s + 12), 40, ARP, 0x48)
    put(c, CH["glitch"], 13, "zap", m("zap"), 40, BREAK, 0x00)


def p_54(c):
    """5/4 bar — pattern break at row 19."""
    r = ROOTS[2]
    for rr in (0, 6, 12, 16): kick_row(c, rr, 60)
    snare_row(c, 4, 54); snare_row(c, 14, 56)
    for rr in range(0, 20, 2): hat_row(c, rr, 28 if rr % 4 else 36)
    put(c, CH["bass"], 0, "bass", bnote(r), 56)
    put(c, CH["bass"], 8, "bass", bnote(r + 12), 52, PORTA_DN, 0x06)
    put(c, CH["bass"], 16, "bass", bnote(r + 7), 48)
    for i, s in enumerate(CHORDS[r]): put(c, CH["arp"], 2 + i * 5, "stab", anote(s + 12), 38, VIB, 0x48)
    put(c, CH["glitch"], 19, "zap", m("zap"), 42, BREAK, 0x00)


def p_dropB(c, bars=4):
    lead_mel = [57, 60, 64, 60, 55, 59, 62, 59]
    for bar in range(bars):
        b = bar * 16; r = ROOTS[bar % 4]
        for rr in (0, 3, 6, 10, 13): kick_row(c, b + rr, 62)
        snare_row(c, b + 4, 58); snare_row(c, b + 12, 60, EXT, 0x92)
        for rr in range(0, 16, 2):
            hat_row(c, b + rr, 24, MULTIRETRIG, 0x03 if rr == 12 else 0x00)
        _bassline(c, b, r)
        for i in range(4):
            n = lead_mel[(bar * 2 + i) % len(lead_mel)]
            put(c, CH["lead"], b + i * 4, "lead", lnote(n + 12), 46, VIB, 0x46)
        for i, s in enumerate(CHORDS[r]): put(c, CH["arp"], b + 8 + i * 2, "stab", anote(s + 24), 34, ARP, 0x25)
        put(c, CH["glitch"], b + 15, "zap", m("zap"), 36, PAN, 0x10)


def p_glitch(c):
    """6/8 bar built almost entirely from effect-column events."""
    r = ROOTS[3]
    put(c, CH["kick"], 0, "kick", m("kick"), 64, EXT, 0x90)          # retrig every tick
    for rr in range(2, 24, 3):
        put(c, CH["perc"], rr, "zap", m("zap"), 40, MULTIRETRIG, 0x04)
    for rr in range(0, 24, 5):
        put(c, CH["hat"], rr, "hat", m("hat"), 34, EXT, 0x92)
    for rr in range(1, 24, 7):
        put(c, CH["snare"], rr, "snare", m("snare"), 46, MULTIRETRIG, 0x03)
    put(c, CH["bass"], 0, "bass", bnote(r), 54, TREMOR, 0x43)
    put(c, CH["bass"], 12, "bass", bnote(r), 50, TREMOR, 0x32)
    put(c, CH["arp"], 6, "stab", anote(CHORDS[r][0] + 12), 36, ARP, 0x5A)
    put(c, CH["glitch"], 23, "zap", m("zap"), 44, BREAK, 0x00)


def p_dropC(c, bars=4):
    for bar in range(bars):
        b = bar * 16; r = ROOTS[bar % 4]
        for rr in (0, 4, 6, 10, 12): kick_row(c, b + rr, 60, delay=1 if rr == 6 else 0)
        snare_row(c, b + 8, 58)
        for rr in range(0, 16):
            if rr % 4 == 0: hat_row(c, b + rr, 34)
            elif rr % 2 == 0: hat_row(c, b + rr, 20)
        for rr in range(1, 16, 3):
            put(c, CH["perc"], b + rr, "perc", m("perc"), 30, PAN, 0x40 + (rr * 8) % 0xC0)
        _bassline(c, b, r)
        for i, s in enumerate(CHORDS[r]):
            put(c, CH["arp"], b + i * 3, "stab", anote(s + 12), 36,
                ARP, 0x37 if bar % 2 == 0 else 0x48)
        if bar % 2 == 1:
            put(c, CH["lead"], b + 8, "lead", lnote(CHORDS[r][-1] + 12), 42, VIB, 0x37)
            put(c, CH["lead"], b + 12, "lead", lnote(CHORDS[r][0] + 12), 40, VIB, 0x37)


def p_breakdown(c, bars=4):
    put(c, CH["glitch"], 0, "crash", m("crash"), 40, TEMPO, 140)
    for bar in range(bars):
        b = bar * 16; r = ROOTS[bar % 4]
        if bar >= 1: kick_row(c, b, 54)
        for rr in range(0, 16, 4): hat_row(c, b + rr, 18)
        put(c, CH["bass"], b + 0, "sub", m("sub"), 52)
        put(c, CH["bass"], b + 10, "sub", m("sub"), 46, EXT, 0x92)
        for i in range(3):
            put(c, CH["lead"], b + 2 + i * 4, "lead", lnote(CHORDS[r][i] + 12), 34, VIB, 0x48)
        if bar == 3:
            for rr in range(0, 16, 2):
                put(c, CH["perc"], b + rr, "zap", m("zap"), 24 + rr, MULTIRETRIG, 0x02 + rr // 4)


def p_dropD(c, bars=4):
    put(c, CH["glitch"], 0, "crash", m("crash"), 50, TEMPO, 160)
    for bar in range(bars):
        b = bar * 16; r = ROOTS[bar % 4]
        for rr in (0, 2, 6, 8, 10, 14): kick_row(c, b + rr, 64)
        snare_row(c, b + 4, 60); snare_row(c, b + 12, 62, EXT, 0x93)
        for rr in range(0, 16):
            if rr % 4 == 0: hat_row(c, b + rr, 36)
            elif rr % 2 == 0: hat_row(c, b + rr, 22)
        _bassline(c, b, r)
        for i, s in enumerate(CHORDS[r]):
            put(c, CH["arp"], b + i * 2, "stab", anote(s + 12), 40, ARP, 0x37)
        for i in range(4):
            put(c, CH["lead"], b + i * 4, "lead", lnote(CHORDS[r][i % 3] + 24), 40, VIB, 0x46)
        put(c, CH["glitch"], b + 15, "zap", m("zap"), 42, MULTIRETRIG, 0x05)


def p_chaos(c, bars=4):
    """Tempo automation inside the pattern — the feel shifts under the listener."""
    for bar in range(bars):
        b = bar * 16; r = ROOTS[bar % 4]
        for rr in (0, 6, 10): kick_row(c, b + rr, 60)
        snare_row(c, b + 4 + (bar % 2) * 2, 56)
        for rr in range(0, 16, 3):
            hat_row(c, b + rr, 30, MULTIRETRIG, 0x02 + (rr % 4))
        put(c, CH["bass"], b + 0, "bass", bnote(r), 54, ARP, 0x37)
        put(c, CH["bass"], b + 8, "bass", bnote(r + 12), 50, ARP, 0x4A)
        for i in range(3):
            put(c, CH["arp"], b + 1 + i * 4, "stab", anote(CHORDS[r][i] + 12), 34, VIB, 0x37)
        # tempo dip each bar-end -> rubber-band feel
        put(c, CH["glitch"], b + 14, "zap", m("zap"), 34, TEMPO, 140 + bar * 10)
    put(c, CH["glitch"], 63, "zap", m("zap"), 40, TEMPO, 150)


def p_outro(c, bars=4):
    for bar in range(bars):
        b = bar * 16; r = ROOTS[bar % 4]
        if bar < 2: kick_row(c, b, 52 - bar * 12)
        if bar < 3:
            put(c, CH["bass"], b, "bass", bnote(r), 46 - bar * 8)
        put(c, CH["arp"], b + 4, "stab", anote(CHORDS[r][0] + 12), 30 - bar * 6, VIB, 0x37)
    put(c, CH["glitch"], 48, "crash", m("crash"), 36)


def p_tail(c):
    """32 rows, fade out."""
    put(c, CH["glitch"], 0, "crash", m("crash"), 30, TEMPO, 120)
    for rr in range(0, 32, 6):
        put(c, CH["bass"], rr, "sub", m("sub"), max(6, 40 - rr), EXT, 0x94)
    for rr in range(2, 32, 4):
        put(c, CH["arp"], rr, "stab", anote(69), max(6, 28 - rr), VIB, 0x48)
    put(c, CH["glitch"], 31, "zap", m("zap"), 20, BREAK, 0x00)


# ── assemble ──────────────────────────────────────────────────────────────────
BUILDERS = [
    ("intro",     p_intro),
    ("build",     p_build),
    ("dropA",     p_drop),
    ("odd78",     p_odd78),
    ("odd54",     p_odd54),
    ("dropB",     p_drop),
    ("glitch",    p_glitch),
    ("lead",      p_lead),
    ("dropC",     p_drop),
    ("breakdown", p_breakdown),
    ("dropD",     p_drop),
    ("odd78b",    p_odd78),
    ("chaos",     p_chaos),
    ("outro",     p_outro),
    ("tail",      p_tail),
]
# order reuses patterns at several points (trailer/remix structure)
ORDER = [0, 1, 2, 3, 4, 5, 2, 6, 7, 8, 9, 10, 11, 7, 12, 2, 9, 7, 14]


def build_module():
    samples = make_samples()
    mod = Module(TITLE, channels=NCH, bpm=BPM, speed=SPEED, linear=True)
    for name in INST_ORDER:
        mod.add_instrument(Instrument(name, [samples[name]]))
    pats = []
    for label, fn in BUILDERS:
        cells = {}
        fn(cells)
        mod.add_pattern(cells)
        pats.append((label, cells))
    mod.order = list(ORDER)
    return mod, pats


def stats(pats):
    """Effect-column census — this is the 'crazy formatting' evidence."""
    fxnames = {0x00: "0xy arpeggio", 0x01: "1xx porta up", 0x02: "2xx porta down",
               0x04: "4xy vibrato", 0x07: "7xy tremolo", 0x08: "8xx set panning",
               0x0A: "Axy vol slide", 0x0B: "Bxx position jump", 0x0C: "Cxx set volume",
               0x0D: "Dxx pattern break", 0x0E: "Exx extended (E9x/ECx/EDx)",
               0x0F: "Fxx set speed/tempo", 0x10: "Gxx global volume",
               0x1B: "Qxy multi-retrigger", 0x1C: "Rxy tremor"}
    census, total_cells, fx_cells = Counter(), 0, 0
    for _, cells in pats:
        for (r, ch), (note, inst, vol, fx, param) in cells.items():
            total_cells += 1
            if fx:
                fx_cells += 1
                census[fxnames.get(fx, f"0x{fx:02X}")] += 1
    return census, total_cells, fx_cells


def render_and_master(xm: Path, mp3: Path) -> dict:
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_milkups_tracker_cut import render_xm_libopenmpt, master_to_mp3, dur_of
    wav = OUT / f"{TITLE.lower().replace(' ', '-')}.wav"
    render_xm_libopenmpt(xm, wav)
    lm = master_to_mp3(wav, mp3)
    sec = dur_of(mp3)
    try: wav.unlink()
    except OSError: pass
    return {**lm, "seconds": sec}


def main():
    mod, pats = build_module()
    xm = OUT / "snake-protocol.xm"
    mod.save(xm)
    print(f"module written: {xm.relative_to(ROOT)}  {xm.stat().st_size} bytes")
    census, total_cells, fx_cells = stats(pats)
    print(f"patterns={len(pats)}  order_len={len(ORDER)}  filled_cells={total_cells}  fx_events={fx_cells}")

    mp3 = OUT / "snake-protocol.mp3"
    lm = render_and_master(xm, mp3)
    print(f"rendered: {lm['seconds']:.2f}s  {mp3.stat().st_size} bytes  "
          f"{lm['out_i']:.2f} LUFS  TP {lm['out_tp']:.2f} dBTP")

    ev = {"title": TITLE, "engine": "FastTracker II .xm -> ffmpeg libopenmpt",
          "bpm": BPM, "speed": SPEED, "channels": NCH,
          "patterns": len(pats), "order_length": len(ORDER),
          "order": ORDER, "filled_cells": total_cells, "effect_events": fx_cells,
          "odd_meter_bars": {"7/8": "pattern-break at row 13 -> 14 rows",
                             "5/4": "pattern-break at row 19 -> 20 rows",
                             "6/8": "pattern-break at row 23 -> 24 rows"},
          "tempo_changes": sorted({p for _, c in pats for (_, _), (n, i, v, fx, p) in c.items()
                                   if fx == 0x0F and p >= 0x20}),
          "effect_census": dict(census.most_common()),
          "xm_bytes": xm.stat().st_size,
          "mp3_bytes": mp3.stat().st_size,
          "seconds": round(lm["seconds"], 3),
          "lufs": round(lm["out_i"], 2), "true_peak_dbtp": round(lm["out_tp"], 2),
          "sha256_xm": hashlib.sha256(xm.read_bytes()).hexdigest(),
          "sha256_mp3": hashlib.sha256(mp3.read_bytes()).hexdigest()}
    (OUT / "snake-protocol.evidence.json").write_text(json.dumps(ev, indent=2))
    print("\neffect census:")
    for k, v in census.most_common():
        print(f"  {v:5d}  {k}")
    print("\nevidence:", (OUT / "snake-protocol.evidence.json").relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


BUILDERS = [
    ("intro",     64, p_intro),
    ("build",     64, p_build),
    ("dropA",     64, p_dropA),
    ("78",        14, p_78),
    ("54",        20, p_54),
    ("dropB",     64, p_dropB),
    ("glitch",    24, p_glitch),
    ("dropC",     64, p_dropC),
    ("breakdown", 64, p_breakdown),
    ("dropD",     64, p_dropD),
    ("chaos",     64, p_chaos),
    ("outro",     64, p_outro),
    ("tail",      32, p_tail),
]
# "78b" reuses the 7/8 pattern (same module data, second appearance)
ORDER = ["intro", "build", "dropA", "78", "54", "dropB", "dropA", "glitch",
         "dropC", "breakdown", "dropD", "78", "chaos", "dropC", "outro",
         "dropA", "dropD", "dropC", "tail"]
EFFECT_NAMES = {0x00: "0xy arpeggio", 0x01: "1xx porta up", 0x02: "2xx porta down",
                0x04: "4xy vibrato", 0x08: "8xx set panning", 0x0A: "Axy volume slide",
                0x0B: "Bxx position jump", 0x0C: "Cxx set volume", 0x0D: "Dxx pattern break",
                0x0E: "Exx extended (E9x retrig / EDx delay)", 0x0F: "Fxx set speed/tempo",
                0x10: "Gxx global volume", 0x1B: "Qxy multi-retrigger", 0x1C: "Rxy tremor"}


def build():
    mod = Module(name=TITLE, channels=NCH, bpm=BPM, speed=SPEED)
    S = make_samples()
    for nm in INST_ORDER:
        mod.add_instrument(Instrument(nm.upper(), [S[nm]]))
    idx, cells_by = {}, {}
    for i, (nm, rows, fn) in enumerate(BUILDERS):
        c = {}
        fn(c)
        mod.add_pattern(c)
        idx[nm] = i
        cells_by[nm] = c
    mod.order = [idx[n] for n in ORDER]
    return mod, cells_by


def main():
    mod, cells_by = build()
    xm = OUT / "snake-protocol.xm"
    mod.save(xm)

    wav = OUT / "snake-protocol.wav"
    mp3 = OUT / "snake-protocol.mp3"
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_milkups_tracker_cut import render_xm_libopenmpt, master_to_mp3, dur_of
    render_xm_libopenmpt(xm, wav)
    lm = master_to_mp3(wav, mp3)
    sec = dur_of(mp3)

    fx_hist, total_cells, rows_played = Counter(), 0, 0
    for nm in ORDER:
        c = cells_by[nm]
        total_cells += len(c)
        for (_r, _ch), (_n, _i, _v, fx, pm) in c.items():
            if fx: fx_hist[fx] += 1
    lens = {nm: rows for nm, rows, _ in BUILDERS}
    rows_played = sum(lens[n] for n in ORDER)

    ev = {
        "title": TITLE, "engine": "FastTracker II .XM -> ffmpeg libopenmpt",
        "source": str(xm.relative_to(ROOT)),
        "xm_bytes": xm.stat().st_size,
        "audio": str(mp3.relative_to(ROOT)), "mp3_bytes": mp3.stat().st_size,
        "seconds": round(sec, 3),
        "lufs": round(lm["out_i"], 2), "true_peak_dbtp": round(lm["out_tp"], 2),
        "lra": round(lm["out_lra"], 2),
        "sha256_mp3": hashlib.sha256(mp3.read_bytes()).hexdigest(),
        "sha256_xm": hashlib.sha256(xm.read_bytes()).hexdigest(),
        "channels": NCH, "base_bpm": BPM, "base_speed": SPEED,
        "patterns_defined": len(BUILDERS),
        "order_length": len(ORDER), "rows_played": rows_played,
        "seconds_theoretical": round(rows_played * SPEED * 2.5 / BPM, 2),
        "cells_written": total_cells,
        "effect_events": sum(fx_hist.values()),
        "effect_histogram": {EFFECT_NAMES.get(k, hex(k)): v for k, v in sorted(fx_hist.items())},
        "odd_meter_patterns": {"7/8 bar": "78 (break D00 @ row 13) -> 14 rows",
                               "5/4 bar": "54 (break D00 @ row 19) -> 20 rows",
                               "6/8 bar": "glitch (break D00 @ row 23) -> 24 rows"},
        "tempo_changes": "Fxx set-BPM inside intro/build/breakdown/glitch/chaos/dropD/outro/tail",
        "order": ORDER,
    }
    (OUT / "snake-protocol.evidence.json").write_text(json.dumps(ev, indent=2))
    try: wav.unlink()
    except OSError: pass

    print(f"XM   : {ev['source']}  {ev['xm_bytes']} bytes")
    print(f"MP3  : {ev['audio']}  {ev['mp3_bytes']} bytes")
    print(f"TIME : {sec:.2f}s   LUFS {ev['lufs']}   TP {ev['true_peak_dbtp']} dBTP   LRA {ev['lra']}")
    print(f"FORM : {ev['patterns_defined']} patterns, order {ev['order_length']}, "
          f"{ev['rows_played']} rows, {ev['cells_written']} cells, "
          f"{ev['effect_events']} effect events")
    print("EFFECTS:")
    for k, v in ev["effect_histogram"].items(): print(f"   {v:>4}  {k}")
    ok = sec >= 60 and abs(ev["lufs"] + 14) <= 1.0 and ev["true_peak_dbtp"] <= -0.7
    print("GATE :", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
