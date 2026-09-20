#!/usr/bin/env python3
"""Probe: is xm_lib's pattern cell encoding correct?

xm_lib.add_pattern() writes a FIXED 5 bytes per cell (note, inst, vol, fx, param)
with no packed-flag byte. The XM spec says a cell starts with a flag byte whose
bits say which fields follow. If xm_lib is wrong, modules still "render" (header
tempo is correct) but the notes land in the wrong places.

Test: one 440 Hz note per bar on channel 0, silence elsewhere, BPM 120 speed 6
=> row = 0.125s, notes expected at t = 0, 2, 4, 6s of an 8s pattern.
"""
import sys, subprocess
from pathlib import Path
import numpy as np

ROOT = Path("/home/zax/Biz/z-dot-team")
sys.path.insert(0, str(ROOT / "scripts"))
from xm_lib import Module, Instrument, Sample, SR, note_for  # noqa: E402

OUT = Path("/tmp/xmprobe"); OUT.mkdir(exist_ok=True)


def sine_burst(freq=440.0, dur=0.20):
    t = np.arange(int(dur * SR)) / SR
    return (np.sin(2 * np.pi * freq * t) * np.exp(-t * 6) * 0.9).astype(np.float32)


def build_with_xm_lib(path):
    mod = Module(name="PROBE-XMLIB", channels=4, bpm=120, speed=6)
    s = Sample(sine_burst(), name="SINE")          # natural pitch 440
    mod.add_instrument(Instrument("SINE", [s]))
    note = note_for(440.0, 440.0)
    cells = {}
    for r in (0, 16, 32, 48):                       # one note per bar
        cells[(r, 0)] = (note, 1, 0x10 + 64, 0, 0)  # vol column = 0x10+64
    mod.add_pattern(cells)
    mod.order = [0]
    mod.save(path)
    return path


def build_correct(path):
    """Same module, but with the real XM packed-cell encoding."""
    import struct
    mod = Module(name="PROBE-CORRECT", channels=4, bpm=120, speed=6)
    s = Sample(sine_burst(), name="SINE")
    mod.add_instrument(Instrument("SINE", [s]))
    note = note_for(440.0, 440.0)

    rows = bytearray()
    for r in range(64):
        for c in range(4):
            if (r, c) in {(0, 0), (16, 0), (32, 0), (48, 0)}:
                rows += bytes([0x80 | 0x40 | 0x20,   # note + inst + vol present
                               note, 1, 0x40])       # note, inst, volume 64
            else:
                rows.append(0x80)                    # empty cell
    head = struct.pack("<IBHH", 9, 0, 64, len(rows))
    pat = head + bytes(rows)

    out = bytearray(mod._header())
    out += pat
    out += mod._instrument(mod.instruments[0])
    Path(path).write_bytes(bytes(out))
    return Path(path)


def render(xm, wav):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-i", str(xm), "-c:a", "pcm_s16le", str(wav)], check=True)
    return wav


def analyse(wav, label):
    import wave
    w = wave.open(str(wav), "rb")
    n = w.getnframes()
    a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
    if w.getnchannels() == 2:
        a = a.reshape(-1, 2).mean(axis=1)
    sr = w.getframerate()
    secs = len(a) / sr
    # envelope in 50 ms blocks
    blk = int(0.05 * sr)
    env = np.array([np.max(np.abs(a[i:i + blk])) for i in range(0, len(a) - blk, blk)])
    onsets = [round(i * 0.05, 2) for i in range(1, len(env))
              if env[i] > 0.05 and env[i] > env[i - 1] * 1.6]
    print(f"\n{label}: {secs:.2f}s  peak={np.max(np.abs(a)):.3f}  rms={np.sqrt(np.mean(a**2)):.4f}")
    print(f"  onsets detected at: {onsets[:12]}")
    print(f"  expected          : [0.0, 2.0, 4.0, 6.0]")
    return onsets, secs


xm1 = build_with_xm_lib(OUT / "probe-xmlib.xm")
xm2 = build_correct(OUT / "probe-correct.xm")
r1 = render(xm1, OUT / "probe-xmlib.wav")
r2 = render(xm2, OUT / "probe-correct.wav")
analyse(r1, "xm_lib (as-is, fixed 5-byte cells)")
analyse(r2, "correct packed encoding")
print(f"\nxmlib bytes : {xm1.stat().st_size}")
print(f"correct bytes: {xm2.stat().st_size}")
