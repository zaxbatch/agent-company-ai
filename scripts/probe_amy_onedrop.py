#!/usr/bin/env python3
"""Probe 4 (decisive): does beat 3 lead in the 90-200 Hz band for a one-drop?
Uses the verifier's own songkit.beat_profile, so the result is what the gate sees."""
import sys
from pathlib import Path

import numpy as np
import amy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import songkit as sk

SR = amy.AMY_SAMPLE_RATE
BPM = 76.0
STEP_BLOCKS = 34          # one 16th at 76 BPM = 0.19737 s = exactly 34 blocks of 256 @44.1k


def render_bar(kick_preset, kick_vel=3.0, tom=None, tom_vel=0.0, with_bass=False):
    amy.send(reset=amy.RESET_ALL_OSCS)
    frames = []
    for bar in range(4):
        for step in range(16):
            if step == 8:      # beat 3 -> the one drop
                amy.send(osc=0, wave=amy.PCM, preset=kick_preset, vel=kick_vel)
                if tom is not None:
                    amy.send(osc=1, wave=amy.PCM, preset=tom, vel=tom_vel)
            if with_bass and step == 0:
                amy.send(osc=2, wave=amy.SINE, bp0="0,1,30,0.8,200,0", note=33, vel=1.2)
            for _ in range(STEP_BLOCKS):
                frames.append(np.array(amy._amy.render_to_list()) / 32768.0)
    a = np.hstack(frames).reshape((-1, amy.AMY_NCHANS))
    return a


def show(label, a):
    mono = a[:, 0]
    kb = sk.beat_profile(mono, SR, BPM, 90, 200)
    lead = kb[2] >= max(kb[0], kb[1], kb[3]) * 1.05
    print(f"  {label:<34} kick[1-4]={kb.round(2)}  beat3_leads={lead}")


print("one-drop 90-200 Hz check (verifier's own measure):")
show("kick preset 0 (BD1 long)", render_bar(0))
show("kick preset 1 (BD2)", render_bar(1))
show("kick preset 2 (BD3 punchy)", render_bar(2))
show("kick 1 + tom16", render_bar(1, tom=16, tom_vel=1.5))
show("kick 0 + tom16", render_bar(0, tom=16, tom_vel=1.5))
show("kick 1 + bass on beat 1", render_bar(1, with_bass=True))
show("kick 0 + bass on beat 1", render_bar(0, with_bass=True))
