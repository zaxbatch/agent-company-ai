#!/usr/bin/env python3
"""build_country_beat.py — "FRONT PORCH FROST", a country beat authored as a real
FastTracker II .XM module, played back by the tracker (libopenmpt via ffmpeg),
mastered to -14 LUFS and encoded MP3 320k.

Chain: numpy samples -> .XM module -> libopenmpt -> WAV -> loudnorm master -> MP3

COUNTRY, defined by the groove the gate can measure:
  * TRAIN BEAT / TWO-STEP -- kick on 1 and 3, SNARE on 2 and 4
  * alternating BOOM-CHICK bass: root on beat 1, fifth on beat 3
  * the chord "chick" lands on beats 2 and 4 (acoustic strum, 3 staggered strings)
  * quiet brushed 8th-note hats (kept low so the 2/4 backbeat stays clear)
  * G major: I-IV-V with a vi turn -- G - Em - C - D
  * acoustic guitar + banjo roll + pedal steel + fiddle

~90 seconds: 11 patterns x 64 rows = 704 rows at speed 6 / 117 BPM
             704 * (6 * 2.5 / 117) = 90.26 s

Everything is synthesized in-process at the module's own sample rate. No external
samples, no external audio. Deterministic (fixed seeds).

    python3 scripts/build_country_beat.py            # build + gate, do not post
    python3 scripts/build_country_beat.py --post      # build, gate, publish
    python3 scripts/build_country_beat.py --as rae_dunn --post
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from xm_lib import Module, Instrument, Sample, SR, ROWS_PER_PATTERN, note_for  # noqa: E402

OUT = ROOT / "content" / "snowsnakes" / "beats" / "front-porch-frost"
BASE = "https://snowsnakes.zerric.xyz/api"
USERS = ROOT / ".snowsnakes_real_users.json"
CLOUD, PRESET = "r6natkse", "snowsnakes_unsigned"

TITLE = "Front Porch Frost"
BPM, SPEED = 117, 6
NCH = 12
ROWS_PER_BAR = 16                      # 4 rows per beat
TARGET_LUFS, TARGET_TP, TARGET_LRA = -14.0, -1.0, 9.0
VOL_OFF = 0x0C                         # Cxx set-volume, used as a note-off

# ── channel / instrument map ─────────────────────────────────────────────────
CH = dict(kick=0, snare=1, hat=2, brush=3, bass=4,
          gtr1=5, gtr2=6, gtr3=7, banjo=8, steel=9, fiddle=10)
INST_ORDER = ["kick", "snare", "hat", "brush", "bass", "gtr", "banjo", "steel", "fiddle"]
INST = {n: i + 1 for i, n in enumerate(INST_ORDER)}
# natural synthesis pitch of each sample (drums are unpitched, 55 Hz by convention)
NAT = {"kick": 55.0, "snare": 55.0, "hat": 55.0, "brush": 55.0, "bass": 55.0,
       "gtr": 110.0, "banjo": 220.0, "steel": 110.0, "fiddle": 220.0}


def m(name):
    """Note that plays an unpitched sample at its natural pitch."""
    return note_for(NAT[name], NAT[name])


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12.0)


def pnote(midi, name):
    """Note that plays MIDI pitch `midi` on the sample for `name`."""
    return max(1, min(96, note_for(hz(midi), NAT[name])))


def put(cells, ch, row, inst_name, note, vol=64, fx=0, param=0):
    cells[(row, ch)] = (int(note), INST[inst_name],
                        0x10 + max(0, min(64, int(vol))), fx & 0xFF, param & 0xFF)


def r(bar, beat, sub=0):
    """Row inside a 4-bar pattern."""
    return bar * ROWS_PER_BAR + beat * 4 + sub

# ═══...
#  1. SYNTHESIS  (at SR = 16726, the module's own sample rate)
# ══════════════════════════════════════════════════════════════════════════════
def _lp1(x, a):
    """One-pole lowpass (a near 0 = dark, near 1 = bright)."""
    out = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc)
        out[i] = acc
    return out


def _hp1(x, a):
    return x - _lp1(x, a)


def perc_env(n, attack, decay):
    a = max(1, int(attack * SR))
    d = max(1, n - a)
    return np.concatenate([np.linspace(0, 1, a), np.exp(-np.linspace(0, decay, d))])[:n]


def s_kick():
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    f = 118 * np.exp(-t * 26) + 47
    body = np.sin(2 * np.pi * np.cumsum(f) / SR)
    click = np.random.RandomState(2).randn(n) * np.exp(-t * 420) * 0.35
    return np.tanh((body * np.exp(-t * 11) + click) * 1.25) * 0.92


def s_snare():
    """Crisp snare with a brush tail -- lives in the 1800-4000 Hz band the
    backbeat check listens to."""
    n = int(0.19 * SR)
    t = np.arange(n) / SR
    rng = np.random.RandomState(7)
    nz = _hp1(rng.randn(n), 0.55) * perc_env(n, 0.001, 15.0)
    body = np.sin(2 * np.pi * 196 * t) * np.exp(-t * 30) * 0.30
    return np.tanh((nz * 1.05 + body) * 1.45) * 0.80


def s_hat():
    n = int(0.055 * SR)
    rng = np.random.RandomState(11)
    return _hp1(rng.randn(n), 0.80) * perc_env(n, 0.0006, 46.0) * 0.52


def s_brush():
    """Brush swirl on the snare -- the train-beat texture."""
    n = int(0.14 * SR)
    t = np.arange(n) / SR
    rng = np.random.RandomState(13)
    return (_hp1(rng.randn(n), 0.42) * (0.55 + 0.45 * np.exp(-t * 26))
            * perc_env(n, 0.004, 13.0) * 0.40)


def ks_pluck(freq, dur, damp=0.9955, bright=0.62, seed=3):
    """Karplus-Strong plucked string -- the acoustic guitar / banjo engine."""
    n = int(dur * SR)
    N = max(2, int(round(SR / max(freq, 30.0))))
    rng = np.random.RandomState(seed)
    buf = _lp1(rng.uniform(-1.0, 1.0, N), bright)
    out = np.zeros(n, dtype=np.float64)
    idx, prev = 0, 0.0
    for i in range(n):
        cur = buf[idx]
        out[i] = cur
        buf[idx] = (cur + prev) * 0.5 * damp
        prev = cur
        idx = (idx + 1) % N
    return out * np.exp(-np.linspace(0, 1.6, n))


def s_gtr():
    body = ks_pluck(110.0, 0.95, damp=0.9962, bright=0.55, seed=3)
    body += 0.22 * ks_pluck(220.0, 0.95, damp=0.9970, bright=0.70, seed=4)
    return np.tanh(body * 1.35) * 0.62


def s_banjo():
    return np.tanh(_hp1(ks_pluck(220.0, 0.55, damp=0.9920, bright=0.86, seed=5), 0.45) * 1.7) * 0.52


def s_bass():
    """Upright bass: plucked, woody -- the 'boom'."""
    n = int(0.60 * SR)
    t = np.arange(n) / SR
    fund = np.sin(2 * np.pi * np.cumsum(55.0 * (1 + 0.10 * np.exp(-t * 45))) / SR)
    body = np.tanh(fund * 1.9) * np.exp(-t * 5.2)
    body += 0.16 * np.sin(2 * np.pi * 110 * t) * np.exp(-t * 12)
    thump = _lp1(np.random.RandomState(8).randn(n), 0.18) * np.exp(-t * 60) * 0.30
    return (body + thump) * 0.80


def s_steel():
    """Pedal steel: sustained, singing, vibrato."""
    n = int(0.95 * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.0075 * np.sin(2 * np.pi * 5.4 * t) * np.clip(t * 3, 0, 1)
    ph = 2 * np.pi * 110 * np.cumsum(vib) / SR
    tone = sum(np.sin(ph * k) * (0.42 ** (k - 1)) for k in (1, 2, 3, 4))
    return np.tanh(tone * 0.55 * perc_env(n, 0.012, 1.5)) * 0.50


def s_fiddle():
    """Bowed fiddle: slow attack, sustained, strong vibrato."""
    n = int(0.80 * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.010 * np.sin(2 * np.pi * 5.8 * t) * np.clip(t * 2.5, 0, 1)
    ph = 2 * np.pi * 220 * np.cumsum(vib) / SR
    bowed = sum(np.sin(ph * k) / k for k in (1, 2, 3, 4, 5))
    return np.tanh(bowed * 0.62 * perc_env(n, 0.075, 0.9)) * 0.46


def make_samples():
    """16-bit samples (noise floor ~-96 dB instead of 8-bit's ~-48 dB)."""
    gen = {"kick": s_kick, "snare": s_snare, "hat": s_hat, "brush": s_brush,
           "bass": s_bass, "gtr": s_gtr, "banjo": s_banjo,
           "steel": s_steel, "fiddle": s_fiddle}
    return {k: Sample(fn(), name=k.upper(), bits=16) for k, fn in gen.items()}


# ══════════════════════════════════════════════════════════════════════════════
#  2. MUSICAL MATERIAL  (G major — the country key)
# ══════════════════════════════════════════════════════════════════════════════
CHORDS = {                                  # guitar voicings, warm mid register
    "G":  [55, 59, 62],                     # G3  B3  D4
    "C":  [55, 60, 64],                     # G3  C4  E4
    "D":  [57, 62, 66],                     # A3  D4  F#4
    "Em": [52, 55, 59],                     # E3  G3  B3
}
CHORD_TONES = {                             # higher voicings for the banjo roll
    "G":  [67, 71, 74], "C": [72, 76, 79], "D": [74, 78, 81], "Em": [76, 79, 83],
}
BASS_ROOT = {"G": 31, "C": 36, "D": 38, "Em": 40}      # G1  C2  D2  E2
BASS_FIFTH = {"G": 38, "C": 43, "D": 45, "Em": 47}     # D2  G2  A2  B2

# 11 patterns x 4 bars = 44 bars = 704 rows = ~90.3 s
SECTIONS = [
    ("intro",  ["G", "G", "C", "D"],  dict(drums="none", banjo=0, fiddle=0, steel=0)),
    ("verse1", ["G", "G", "C", "D"],  dict(drums="full", banjo=0, fiddle=0, steel=1)),
    ("verse2", ["G", "G", "C", "D"],  dict(drums="full", banjo=1, fiddle=0, steel=1)),
    ("chor1",  ["G", "Em", "C", "D"], dict(drums="full", banjo=0, fiddle=1, steel=0)),
    ("chor2",  ["G", "Em", "C", "D"], dict(drums="full", banjo=1, fiddle=1, steel=0)),
    ("break",  ["C", "D", "G", "G"],  dict(drums="lite", banjo=0, fiddle=0, steel=2)),
    ("verse3", ["G", "G", "C", "D"],  dict(drums="full", banjo=1, fiddle=0, steel=1)),
    ("chor3",  ["G", "Em", "C", "D"], dict(drums="full", banjo=1, fiddle=1, steel=0)),
    ("solo",   ["C", "D", "G", "G"],  dict(drums="full", banjo=0, fiddle=2, steel=2)),
    ("chor4",  ["G", "Em", "C", "D"], dict(drums="full", banjo=1, fiddle=1, steel=0)),
    ("outro",  ["G", "D", "G", "G"],  dict(drums="lite", banjo=0, fiddle=0, steel=1)),
]

# (bar, beat, midi, held_rows) — G major, over the chorus changes
FIDDLE_MELODY = [
    (0, 0, 67, 8), (0, 2, 69, 4), (0, 3, 71, 4),
    (1, 0, 72, 8), (1, 2, 71, 6),
    (2, 0, 69, 4), (2, 1, 67, 4), (2, 2, 69, 6),
    (3, 0, 66, 8), (3, 2, 62, 8),
]
STEEL_SOLO = [
    (0, 0, 60, 10), (0, 2, 64, 6), (0, 3, 67, 4),
    (1, 0, 69, 8), (1, 2, 66, 8),
    (2, 0, 62, 10), (2, 2, 59, 6), (2, 3, 62, 4),
    (3, 0, 67, 16),
]
STEEL_FILL = [(1, 2, 71, 6), (3, 2, 69, 6)]
BANJO_ROLL = [0, 1, 2, 1, 2, 0, 1, 2]      # indices into the chord tones


# ══════════════════════════════════════════════════════════════════════════════
#  3. VOICES
# ══════════════════════════════════════════════════════════════════════════════
def drums(cells, style):
    """The country TRAIN BEAT: kick 1+3, SNARE 2+4, brushed 8ths.

    The snare must clearly dominate 2 and 4 while the kick dominates 1 and 3 --
    that contrast IS the country groove, and it is what the gate measures. Hats
    are deliberately quiet so they do not smear the backbeat margin.
    """
    if style == "none":
        return
    for bar in range(4):
        vol_k = 58 if style == "full" else 46
        vol_s = 62 if style == "full" else 48
        # BOOM: kick on 1 and 3 only -- never four-on-the-floor
        put(cells, CH["kick"], r(bar, 0), "kick", m("kick"), vol_k)
        put(cells, CH["kick"], r(bar, 2), "kick", m("kick"), vol_k - 4)
        if style == "full" and bar % 2 == 1:
            put(cells, CH["kick"], r(bar, 2, 2), "kick", m("kick"), 20)
        # CHICK: snare + brush on 2 and 4 -- the backbeat
        put(cells, CH["snare"], r(bar, 1), "snare", m("snare"), vol_s)
        put(cells, CH["snare"], r(bar, 3), "snare", m("snare"), vol_s)
        put(cells, CH["brush"], r(bar, 1), "brush", m("brush"), 46)
        put(cells, CH["brush"], r(bar, 3), "brush", m("brush"), 46)
        # brushed 8ths, low
        for beat in range(4):
            put(cells, CH["hat"], r(bar, beat), "hat", m("hat"), 22)
            put(cells, CH["hat"], r(bar, beat, 2), "hat", m("hat"), 13)


def bass_line(cells, prog):
    """Alternating boom-chick bass: root on 1, fifth on 3."""
    for bar, name in enumerate(prog):
        put(cells, CH["bass"], r(bar, 0), "bass", pnote(BASS_ROOT[name], "bass"), 62)
        put(cells, CH["bass"], r(bar, 2), "bass", pnote(BASS_FIFTH[name], "bass"), 54)
        if bar == 3:                                   # walk-up into the next 4 bars
            put(cells, CH["bass"], r(bar, 3, 2), "bass",
                pnote(BASS_ROOT[name] + 5, "bass"), 40)


def guitar(cells, prog, strum=44):
    """The 'chick': chord strum on beats 2 and 4, three strings on three channels
    staggered one 16th apart so it reads as a downstroke."""
    for bar, name in enumerate(prog):
        tones = CHORDS[name]
        if bar == 0:
            put(cells, CH["gtr1"], r(bar, 0), "gtr", pnote(tones[0] - 12, "gtr"), 32)
        for beat in (1, 3):
            for i, chn in enumerate(("gtr1", "gtr2", "gtr3")):
                put(cells, CH[chn], r(bar, beat, i), "gtr", pnote(tones[i], "gtr"),
                    strum - i * 5)
        if bar % 2 == 1:
            put(cells, CH["gtr2"], r(bar, 3, 3), "gtr", pnote(tones[1] + 2, "gtr"), 22)


def banjo(cells, prog):
    """8th-note forward roll, accented on 2 and 4 so it adds to the backbeat
    rather than flattening it."""
    for bar, name in enumerate(prog):
        tones = CHORD_TONES[name]
        for i in range(8):
            beat, sub = i // 2, (i % 2) * 2
            midi = tones[BANJO_ROLL[i]]
            loud = beat in (1, 3)
            put(cells, CH["banjo"], r(bar, beat, sub), "banjo", pnote(midi, "banjo"),
                30 if loud else 15)


def lead(cells, ch, inst, phrase, vol):
    """Place a sustained melodic phrase. The sample's own decay ends each note."""
    for bar, beat, midi, _held in phrase:
        put(cells, ch, r(bar, beat), inst, pnote(midi, inst), vol)


def build_pattern(section):
    """One 64-row pattern (4 bars) for this section."""
    name, prog, flags = section
    cells = {}
    drums(cells, flags["drums"])
    bass_line(cells, prog)
    guitar(cells, prog)
    if flags["banjo"]:
        banjo(cells, prog)
    if flags["fiddle"] == 1:
        lead(cells, CH["fiddle"], "fiddle", FIDDLE_MELODY, 40)
    elif flags["fiddle"] == 2:
        lead(cells, CH["fiddle"], "fiddle",
             [(b, bt, mi + 12, h) for b, bt, mi, h in FIDDLE_MELODY], 42)
    if flags["steel"] == 1:
        lead(cells, CH["steel"], "steel", STEEL_FILL, 36)
    elif flags["steel"] == 2:
        lead(cells, CH["steel"], "steel", STEEL_SOLO, 44)
    if name == "outro":                       # thin the ending out
        for ch in (CH["hat"], CH["brush"], CH["snare"]):
            for key in [k for k in cells if k[1] == ch and k[0] >= r(2, 0)]:
                cells.pop(key, None)
    return cells


def build_module():
    mod = Module(name=TITLE.upper()[:20], channels=NCH, bpm=BPM, speed=SPEED)
    S = make_samples()
    for nm in INST_ORDER:
        mod.add_instrument(Instrument(nm.upper(), [S[nm]]))
    for sec in SECTIONS:
        mod.add_pattern(build_pattern(sec))
    mod.order = list(range(len(SECTIONS)))
    return mod


# ══════════════════════════════════════════════════════════════════════════════
#  4. RENDER -> MASTER -> VERIFY -> POST
# ══════════════════════════════════════════════════════════════════════════════
def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def render_tracker(xm: Path, wav: Path) -> None:
    """Play the module back with the tracker decoder (libopenmpt via ffmpeg)."""
    res = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
               "-i", str(xm), "-c:a", "pcm_s16le", str(wav)])
    if res.returncode != 0:
        raise RuntimeError(f"libopenmpt render failed: {res.stderr[:400]}")


def loudnorm_pass1(path: Path) -> dict:
    """loudnorm pass 1: measure, so pass 2 can be linear (no pumping)."""
    res = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
               "-af", f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json",
               "-f", "null", "-"])
    blob = res.stderr[res.stderr.rfind("{"):res.stderr.rfind("}") + 1]
    return json.loads(blob)


def master(raw: Path, wav: Path, mp3: Path) -> dict:
    """Two-pass loudnorm -> -14 LUFS mastered WAV, then a TAGGED MP3 320k."""
    m = loudnorm_pass1(raw)
    af = (f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA={TARGET_LRA}"
          f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
          f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
          f":offset={m['target_offset']}:linear=true")
    res = run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(raw),
               "-af", af, "-c:a", "pcm_s16le", str(wav)])
    if res.returncode != 0:
        raise RuntimeError(f"master failed: {res.stderr[:400]}")

    # fade the tail, then FORMAT the deliverable: tagged MP3 320k
    res = run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(wav),
               "-af", "afade=t=out:st=88.4:d=1.6",
               "-metadata", f"title={TITLE}",
               "-metadata", "artist=MilkUps",
               "-metadata", "album=Front Porch Frost",
               "-metadata", "genre=Country",
               "-metadata", f"TBPM={BPM}",
               "-metadata", "date=2026",
               "-metadata", "comment=FastTracker II .XM module rendered via libopenmpt",
               "-codec:a", "libmp3lame", "-b:a", "320k", str(mp3)])
    if res.returncode != 0:
        raise RuntimeError(f"mp3 encode failed: {res.stderr[:400]}")

    out = loudnorm_pass1(mp3)
    return {"in_i": round(float(m["input_i"]), 2), "in_tp": round(float(m["input_tp"]), 2),
            "out_i": round(float(out["input_i"]), 2), "out_tp": round(float(out["input_tp"]), 2),
            "out_lra": round(float(out["input_lra"]), 2)}


def dur_of(p: Path) -> float:
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "default=nw=1:nk=1", str(p)]).stdout.strip() or 0)


def _font(sz, bold):
    path = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    try:
        return ImageFont.truetype(path, sz)
    except OSError:
        return ImageFont.load_default()


def make_cover(path: Path):
    """Sunset, barn, fence and wheat -- country, drawn not stock."""
    W = H = 1000
    im = Image.new("RGB", (W, H), (28, 20, 16))
    d = ImageDraw.Draw(im)
    for y in range(H):                                          # sunset gradient
        t = y / H
        d.line([(0, y), (W, y)],
               fill=(max(int(226 - 150 * t), 22), max(int(140 - 96 * t), 16),
                     max(int(74 - 54 * t), 14)))
    d.ellipse([312, 132, 688, 508], fill=(255, 198, 96))         # low sun
    d.ellipse([312, 132, 688, 508], outline=(255, 230, 168), width=6)
    d.rectangle([0, 556, W, H], fill=(48, 33, 23))              # ground
    d.polygon([(120, 556), (330, 404), (540, 556)], fill=(72, 41, 30))    # barn roof
    d.rectangle([330, 404, 540, 556], fill=(116, 68, 45))                 # barn body
    d.rectangle([408, 470, 462, 556], fill=(62, 34, 24))                  # barn door
    d.polygon([(600, 556), (742, 440), (884, 556)], fill=(72, 41, 30))
    d.rectangle([600, 440, 884, 556], fill=(98, 57, 38))
    for x in range(96, W, 104):                                 # fence
        d.line([(x, 556), (x, 452)], fill=(64, 47, 33), width=6)
        d.line([(x - 52, 492), (x + 52, 484)], fill=(78, 57, 40), width=5)
    for x in range(30, W, 21):                                  # wheat
        h = 38 + (x * 7) % 44
        d.line([(x, 604), (x + 4, 604 - h)], fill=(198, 158, 80), width=3)
    f1, f2 = _font(86, True), _font(33, False)
    t1 = TITLE.upper()
    w = d.textlength(t1, font=f1)
    d.text(((W - w) / 2, 668), t1, font=f1, fill=(255, 242, 218),
           stroke_width=8, stroke_fill=(26, 16, 10))
    sub = f"MILKUPS  ·  COUNTRY TRAIN BEAT  ·  {BPM} BPM"
    ws = d.textlength(sub, font=f2)
    d.text(((W - ws) / 2, 782), sub, font=f2, fill=(240, 202, 142))
    sub2 = "FASTTRACKER II  .XM  MODULE  ·  RENDERED VIA LIBOPENMPT"
    ws2 = d.textlength(sub2, font=f2)
    d.text(((W - ws2) / 2, 832), sub2, font=f2, fill=(206, 158, 98))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return path


def upload(path: Path, rtype: str):
    b = "----zdotcf" + uuid.uuid4().hex
    mime = "audio/mpeg" if rtype == "video" else "image/png"
    body = b"".join([
        f"--{b}\r\nContent-Disposition: form-data; name=\"upload_preset\"\r\n\r\n{PRESET}\r\n".encode(),
        f"--{b}\r\nContent-Disposition: form-data; name=\"folder\"\r\n\r\nsnowsnakes\r\n".encode(),
        f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
        f"Content-Type: {mime}\r\n\r\n".encode(),
        path.read_bytes(), f"\r\n--{b}--\r\n".encode()])
    req = urllib.request.Request(f"https://api.cloudinary.com/v1_1/{CLOUD}/{rtype}/upload",
                                 data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode()).get("secure_url")
    except Exception as exc:  # noqa: BLE001
        print("   upload failed:", str(exc)[:200])
        return None


def api(path, data=None, token=None, method="GET"):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path,
                                 data=json.dumps(data).encode() if data is not None else None,
                                 method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {"_err": e.read().decode()[:200]}
    except Exception as e:  # noqa: BLE001
        return None, {"_err": str(e)[:200]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", action="store_true")
    ap.add_argument("--as", dest="author", default="rae_dunn")
    a = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    xm = OUT / "front-porch-frost.xm"
    raw = OUT / "front-porch-frost-raw.wav"
    wav = OUT / "front-porch-frost.wav"
    mp3 = OUT / "front-porch-frost.mp3"
    cover = OUT / "front-porch-frost-cover.png"

    mod = build_module()
    nbytes = mod.save(xm)
    rows_total = len(SECTIONS) * ROWS_PER_PATTERN
    row_secs = SPEED * 2.5 / BPM
    print(f"module : {TITLE} — {nbytes:,} B, {len(SECTIONS)} patterns, "
          f"{rows_total} rows -> {rows_total * row_secs:.1f}s expected")

    render_tracker(xm, raw)
    lm = master(raw, wav, mp3)
    make_cover(cover)

    dur = dur_of(mp3)
    print(f"render : {dur:.2f}s   wav {wav.stat().st_size // 1024} KB   "
          f"mp3 {mp3.stat().st_size // 1024} KB   cover {cover.stat().st_size // 1024} KB")
    print(f"master : in {lm['in_i']} LUFS / {lm['in_tp']} dBTP -> "
          f"out {lm['out_i']} LUFS / {lm['out_tp']} dBTP (LRA {lm['out_lra']})")

    ver = run([sys.executable, str(ROOT / "scripts" / "verify_song.py"), str(wav),
               "--genre", "country", "--bpm", str(BPM), "--cover", str(cover),
               "--catalog", str(OUT)])
    print(ver.stdout)
    if ver.returncode != 0:
        print("GATE FAILED — not posting")
        return 1

    evidence = {"title": TITLE, "genre": "country", "bpm": BPM, "speed": SPEED,
                "channels": NCH, "module": xm.name, "module_bytes": nbytes,
                "patterns": len(SECTIONS), "rows": rows_total,
                "expected_seconds": round(rows_total * row_secs, 2),
                "measured_seconds": round(dur, 2), "master": lm,
                "sections": [s[0] for s in SECTIONS],
                "chain": "numpy samples -> .XM (FastTracker II) -> libopenmpt -> WAV -> loudnorm -> MP3 320k"}
    (OUT / "evidence.json").write_text(json.dumps(evidence, indent=2))

    if not a.post:
        print("(dry run — pass --post to publish)")
        return 0

    users = {u["username"]: u for u in json.loads(USERS.read_text())}
    if a.author not in users:
        print(f"!! unknown persona {a.author}")
        return 1
    st, d = api("/auth/login", {"username": a.author, "password": users[a.author]["password"]},
                method="POST")
    tok = d.get("token") if isinstance(d, dict) else None
    if not tok:
        print(f"!! login failed: {st} {d}")
        return 1
    au = upload(mp3, "video")
    cu = upload(cover, "image")
    if not au or not cu:
        print("!! upload failed")
        return 1
    st, res = api("/songs", {"title": TITLE, "audio_url": au, "cover_url": cu},
                  token=tok, method="POST")
    sid = res.get("id") if isinstance(res, dict) else None
    print(f"{'ok ' if st == 201 else '!! '}POST /songs as {a.author} -> HTTP {st} id={sid}")

    live = api("/songs")[1]
    found = ([x for x in live if isinstance(x, dict) and x.get("id") == sid]
             if isinstance(live, list) else [])
    if found:
        print(f"VERIFIED LIVE: {found[0]['title']}")
        evidence.update({"song_id": sid, "audio_url": au, "cover_url": cu})
        (OUT / "evidence.json").write_text(json.dumps(evidence, indent=2))
    else:
        print("!! not found in live /songs after posting")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
