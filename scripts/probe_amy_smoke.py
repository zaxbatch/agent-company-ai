#!/usr/bin/env python3
"""Smoke test: can the real AMY (TulipCC synth) render offline to a WAV here?"""
import numpy as np
import amy

print("sample rate:", amy.AMY_SAMPLE_RATE, "block:", amy.AMY_BLOCK_SIZE, "channels:", amy.AMY_NCHANS)
print("version:", amy.version)

# basic tone: a sine voice
amy.send(reset=amy.RESET_ALL_OSCS)
amy.send(synth=0, num_voices=1, wave=amy.SINE, freq=220, vel=1.0)
buf = amy.render(1.0)
print("rendered:", buf.shape, "peak:", float(np.abs(buf).max()), "rms:", float(np.sqrt((buf**2).mean())))

amy.write(buf, "/tmp/amy_smoke.wav")
import os
print("/tmp/amy_smoke.wav bytes:", os.path.getsize("/tmp/amy_smoke.wav"))
