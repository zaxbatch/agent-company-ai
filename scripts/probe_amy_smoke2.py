#!/usr/bin/env python3
"""Smoke test 2: proper AMY voice definition + envelope + offline render."""
import numpy as np
import amy

amy.send(reset=amy.RESET_ALL_OSCS)
# define osc 0: sine with an amp envelope (breakpoints in ms), then trigger a note
amy.send(osc=0, wave=amy.SINE, bp0="0,1,20,0.7,600,0", note=45, vel=1.0)
buf = amy.render(1.0)
print("peak:", float(np.abs(buf).max()), "rms:", float(np.sqrt((buf**2).mean())))

# drums via baked PCM presets (Gamma9001 banks)
amy.send(osc=1, wave=amy.PCM, preset=1)   # bass drum
amy.send(osc=1, vel=1.0)
buf2 = amy.render(0.5)
print("drum peak:", float(np.abs(buf2).max()))
amy.write(buf2, "/tmp/amy_drum.wav")
print("ok")
