#!/usr/bin/env python3
"""Probe: four-on-the-floor groove for the house track, measured with the gate's own
songkit. Tempo choice: 16th must be a whole number of 256-sample blocks, so
BPM = 2583.984375 / 21 = 123.046875 (21 blocks per 16th). That lands in the 120
tempo bucket, so brightness must AVOID bucket 8 (Shelves After Dark, disco 118)."""
import sys
from pathlib import Path

import numpy as np
import amy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import songkit as sk

SR = amy.AMY_SAMPLE_RATE
BPM = 2583.984375 / 21          # 123.046875, exact integer-block 16ths
BLOCKS_PER_STEP = 21            # one 16th


def hz(n):
    return 440.0 * (2.0 ** ((n - 69) / 12.0))


def render(nbars, kick_preset=2, kick_vel=3.0, bass_on_offbeat=True,
           bass_note=45, bass_vel=1.4, hats=True, clap=True, sub=False):
    amy.send(reset=amy.RESET_ALL_OSCS)
    amy.echo(level=0.0)
    frames = []
    for bar in range(nbars):
        for step in range(16):
            if step % 4 == 0:                                   # KICK every beat
                amy.send(osc=0, wave=amy.PCM, preset=kick_preset, vel=kick_vel)
            if clap and step in (4, 12):                        # clap on 2 and 4
                amy.send(osc=1, wave=amy.PCM, preset=3, vel=1.6)
            if hats:
                if step % 4 == 2:                               # OPEN hat offbeat 8ths
                    amy.send(osc=2, wave=amy.PCM, preset=10, vel=1.5)
                elif step % 2 == 1:                             # closed 16th ghosts
                    amy.send(osc=3, wave=amy.PCM, preset=9, vel=0.7)
            if bass_on_offbeat and step % 4 == 2:               # offbeat bass
                amy.send(osc=8, wave=amy.SAW_DOWN, freq=hz(bass_note),
                         bp0="0,1,12,0.6,120,0", filter_type=1, filter_freq=400, vel=bass_vel)
            if sub and step % 4 == 2:
                amy.send(osc=9, wave=amy.SINE, freq=hz(bass_note - 12),
                         bp0="0,1,90,0.5,200,0", vel=0.9)
            for _ in range(BLOCKS_PER_STEP):
                frames.append(np.array(amy._amy.render_to_list()) / 32768.0)
    return np.hstack(frames).reshape((-1, amy.AMY_NCHANS))


def check(label, a):
    mono = a[:, 0]
    ot = sk.onsets(mono, SR)
    ratio, med = sk.beat_grid_ratio(ot, BPM)
    spb = 60.0 / BPM
    on, off = sk.offbeat_ratio(mono, SR, BPM)
    cent = sk.spectral_centroid(mono, SR)
    ok = ratio >= 0.70 and abs(med - spb) < 0.06
    print(f"  {label:<38} onsets={len(ot):>3} ratio={ratio:.2f} med={med:.3f} "
          f"(spb {spb:.3f}) -> {'PASS' if ok else 'FAIL'} | cent={cent:.0f} "
          f"(bkt {int(cent//250)}) hats off/on={off:.2f}/{on:.2f}")


print(f"BPM {BPM:.4f}  spb {60/BPM:.4f}s  step {BLOCKS_PER_STEP} blocks")
print("four-on-the-floor candidates (8 bars each):")
check("kick only", render(8, clap=False, hats=False, bass_on_offbeat=False))
check("kick+hats", render(8, clap=False, bass_on_offbeat=False))
check("kick+hats+clap", render(8, bass_on_offbeat=False))
check("full: +offbeat saw bass", render(8))
check("full + sub layer", render(8, sub=True))
check("full, bass note 41 (F2)", render(8, bass_note=41))
