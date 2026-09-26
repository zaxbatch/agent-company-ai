#!/usr/bin/env python3
"""Probe 3: echo done the documented way, and real drum amplitude over time."""
import numpy as np
import amy

SR = amy.AMY_SAMPLE_RATE


def blocks(n):
    out = []
    for _ in range(n):
        out.append(np.array(amy._amy.render_to_list()) / 32768.0)
    return np.hstack(out).reshape((-1, amy.AMY_NCHANS))


def rms(x):
    return float(np.sqrt((x ** 2).mean())) if x.size else 0.0


print("=== echo via amy.echo() helper ===")
amy.send(reset=amy.RESET_ALL_OSCS)
amy.echo(level=0.9, delay_ms=400, max_delay_ms=2000, feedback=0.75, filter_coef=-0.3)
amy.send(osc=0, wave=amy.SINE, bp0="0,1,10,0.5,60,0", note=60, vel=1.0)
buf = blocks(320)   # 1.86s
print("  blip window rms(0-0.2s):", round(rms(buf[:int(0.2 * SR)]), 5))
for a, b in [(0.5, 0.9), (0.9, 1.3), (1.3, 1.8)]:
    print(f"  echo tail rms({a}-{b}s):", round(rms(buf[int(a * SR):int(b * SR)]), 5))

print("\n=== drum preset amplitude over time (vel sweep) ===")
for p in (0, 1, 2, 8, 12, 15):
    for vel in (1.0, 4.0):
        amy.send(reset=amy.RESET_ALL_OSCS)
        amy.send(osc=0, wave=amy.PCM, preset=p, vel=vel)
        b = blocks(60)  # 350ms
        env = [round(rms(b[i * 256:(i + 4) * 256]), 4) for i in range(0, 40, 8)]
        print(f"  preset {p:>2} vel {vel}: peak={np.abs(b).max():.3f} envelope={env}")
