#!/usr/bin/env python3
"""Probe: (1) per-synth bus routing + echo tail, (2) which PCM kick preset
dominates the 90-200 Hz band that verify_song uses for the reggae one-drop check."""
import numpy as np
import amy

SR = amy.AMY_SAMPLE_RATE
BLOCK = amy.AMY_BLOCK_SIZE


def blocks(n):
    """render exactly n blocks"""
    out = []
    for _ in range(n):
        out.append(np.array(amy._amy.render_to_list()) / 32768.0)
    return np.hstack(out).reshape((-1, amy.AMY_NCHANS))


def band_energy(x, lo, hi):
    mono = x[:, 0] if x.ndim > 1 else x
    f = np.fft.rfft(mono * np.hanning(len(mono)))
    fr = np.fft.rfftfreq(len(mono), 1 / SR)
    m = (fr >= lo) & (fr < hi)
    return float(np.sqrt((np.abs(f[m]) ** 2).sum()) / len(mono))


print("=== TEST 1: bus routing + echo ===")
amy.send(reset=amy.RESET_ALL_OSCS)
amy.send(bus=0, echo=[0.0, 400, 2000, 0.0, 0.0])
amy.send(bus=1, echo=[0.9, 400, 2000, 0.75, -0.3])
# synth 0 -> bus 0 (dry), synth 1 -> bus 1 (echo)
amy.send(synth=0, num_voices=1, bus=0, wave=amy.SINE, bp0="0,1,10,0.5,80,0")
amy.send(synth=1, num_voices=1, bus=1, wave=amy.SINE, bp0="0,1,10,0.5,80,0")
amy.send(synth=0, note=60, vel=1.0)
amy.send(synth=1, note=67, vel=1.0)
buf = blocks(300)          # 300*256/44100 = 1.74 s
# the blip is ~90ms; anything after 0.4s is echo tail
tail = buf[int(0.4 * SR):]
print(f"  dry tail rms={np.sqrt((tail[:,0]**2).mean()):.5f}")
print(f"  wet tail rms={np.sqrt((tail[:,1]**2).mean()):.5f}"
      if buf.shape[1] > 1 else "  mono output")

print("\n=== TEST 2: kick presets in 90-200 Hz band (one-drop check band) ===")
presets = {0: "BD1 long", 1: "BD2", 2: "BD3 punchy", 12: "snare1", 15: "rimshot"}
for p, name in presets.items():
    amy.send(reset=amy.RESET_ALL_OSCS)
    amy.send(osc=0, wave=amy.PCM, preset=p)
    amy.send(osc=0, vel=1.0)
    b = blocks(40)  # ~230ms
    e = band_energy(b, 90, 200)
    tot = band_energy(b, 20, 20000)
    print(f"  preset {p:>2} {name:<12} 90-200Hz={e:.5f}  wideband={tot:.5f} peak={np.abs(b).max():.3f}")
