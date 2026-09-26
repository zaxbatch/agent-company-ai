#!/usr/bin/env python3
"""Probe: is the MIDI sequencer bar-accurate, and what does a trap groove measure
under the gate's own checks?

Checks:
  1. TIMING   - a 8-bar render must last exactly the musical length (no drift).
  2. DETERMINISM - two renders byte-identical.
  3. sparse_kick - <= 3.2 low-band onsets per bar (the trap gate).
  4. tempo     - read from the hat band (4000-12000 Hz), half-time accepted.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import midi_lib as ml
import songkit as sk
import numpy as np

OUT = Path("/tmp/trap_probe")
OUT.mkdir(exist_ok=True)

BPM = 140.0
BARS = 8
PPQ = 480


def build(drums=True, bass=True, sub_soft=False):
    m = ml.MidiFile(ppq=PPQ, bpm=BPM)
    d = m.add_track("drums")
    b = m.add_track("bass")

    for bar in range(BARS):
        bar_t = bar * m.bar
        # HALF-TIME: kick on beat 1, clap on beat 3
        d.drum(ml.KICK, bar_t, 30, 118)
        if drums:
            d.drum(ml.CLAP, bar_t + m.ticks(2), 30, 100)
            # dense hat rolls: 16ths with 32nd bursts
            for s in range(16):
                t = bar_t + m.ticks(s * 0.25)
                d.drum(ml.HAT_CLOSED, t, 20, 78)
            # a 32nd roll at the end of the bar (trap signature)
            for s in range(8):
                t = bar_t + m.ticks(3.5 + s * 0.0625)
                d.drum(ml.HAT_CLOSED, t, 15, 62)
        if bass:
            # 808-style sub, one long note per bar
            b.program(0, 38 if sub_soft else 38)
            b.note(0, 33, bar_t, m.ticks(3.5), 96)
    return m


def measure(label, wav):
    a, sr = sk.load(str(wav))
    mono = a if a.ndim == 1 else a[:, 0]
    secs = len(mono) / sr
    # sparse_kick, as verify_song does it
    ot = sk.onsets(mono, sr, height=0.35, min_gap=0.30)
    bar_secs = 4 * 60.0 / BPM
    per_bar = len(ot) / max(secs / bar_secs, 1e-6)
    est, conf = sk.estimate_bpm(mono, sr, lo=4000, hi=12000)
    cent = sk.spectral_centroid(mono, sr)
    print(f"  {label:<26} {secs:6.2f}s onsets={len(ot):>3} per_bar={per_bar:.2f} "
          f"({'PASS' if per_bar <= 3.2 else 'FAIL'}) | tempo_est={est:6.1f}(conf {conf:.2f}) "
          f"| cent={cent:.0f}")


print(f"BPM {BPM}  bar={4*60/BPM:.4f}s  expected music length {BARS*4*60/BPM:.2f}s\n")

print("1. TIMING TEST (bars=8, no round-trip padding)")
m = build()
p = m.write(OUT / "timing.mid")
print(f"   midi bytes: {p.stat().st_size}")
ml.render(p, OUT / "timing.wav", gain=0.7)
a, sr = sk.load(str(OUT / "timing.wav"))
nz = np.nonzero(np.abs(a) > 1e-4)[0]
print(f"   music spans 0.00 -> {nz[-1]/sr:.2f}s   (expected ~{BARS*4*60/BPM:.2f}s)")

print("\n2. DETERMINISM")
ml.render(p, OUT / "d1.wav", gain=0.7)
ml.render(p, OUT / "d2.wav", gain=0.7)
import hashlib
h = lambda f: hashlib.md5(Path(f).read_bytes()).hexdigest()
print(f"   {h(OUT/'d1.wav')}\n   {h(OUT/'d2.wav')}  -> "
      f"{'IDENTICAL' if h(OUT/'d1.wav')==h(OUT/'d2.wav') else 'DIFFERENT'}")

print("\n3/4. GROOVE MEASURES")
measure("kick+clap+hats+bass", OUT / "timing.wav")
m2 = build(drums=True, bass=False)
p2 = m2.write(OUT / "nobass.mid")
ml.render(p2, OUT / "nobass.wav", gain=0.7)
measure("no 808 bass", OUT / "nobass.wav")
