#!/usr/bin/env python3
"""build_final.py — full MilkUps track composed AS an LMMS project, rendered BY LMMS.

Arrangement strategy (learned from two failures):
  - Multiple BB tracks with <bbtco> at different song positions did NOT render
    reliably: sections landed at the wrong bars and LMMS warned about missing
    TCOs ("Track::getTCO(4), but TCO 4 doesn't exist").
  - So: ONE BB track, and each instrument gets ONE pattern spanning the whole
    song, containing notes only in the bars where that instrument should sound.
    The arrangement therefore lives inside the notes, which LMMS renders exactly.
      bars  0- 3  intro    kick hat bass
      bars  4-11  main     + keys + lead
      bars 12-15  DIP      pad only -- no kick, no bass, no lead
      bars 16-19  build    kick hat bass keys + stab
      bars 20-29  CLIMAX   everything, loudest
      bars 30-31  outro    pad only
Built-in instruments only. Rendered by lmms, not by any Python synth.
"""
from __future__ import annotations
import subprocess, sys
from pathlib import Path
sys.path.insert(0, "/tmp/lmmslab")
from mkproj import build, section, inst_track

BPM = 126
TOTAL = 32
SECT = {"intro": (0, 4), "main": (4, 8), "dip": (12, 4), "build": (16, 4),
        "climax": (20, 10), "outro": (30, 2)}

def rng(bars):
    return range(bars[0], bars[1])

def pattern_for(active_bars, bar_fn):
    """Place a bar-long figure into every active bar.

    THE BUG THIS FIXES: the figure's positions are in BEATS (0,1,2,3 for
    kick-on-every-beat), but the original code added them straight to the bar
    index, so a four-beat pattern spanned FOUR BARS. The rendered kick therefore
    only sounded on even bars and the arrangement was nothing like the intent.
    Beat offsets are divided by 4 (beats per bar) so positions are in bars.
    """
    out = []
    for b in rng(active_bars):
        out += [(k, b + p / 4.0, l / 4.0, v) for k, p, l, v in bar_fn()]
    return out

FULL   = lambda v=100: [(36, 0, 0.12, v), (36, 1, 0.12, v), (36, 2, 0.12, v), (36, 3, 0.12, v)]
FULLMOD= lambda v=100: FULL(v) + [(36, 2.75, 0.10, v * 0.6)]
HATS   = lambda v=58:  [(84, 0, 0.06, v), (84, 0.5, 0.06, v*0.55), (84, 1, 0.06, v*0.8),
                        (84, 1.5, 0.06, v*0.55), (84, 2, 0.06, v), (84, 2.5, 0.06, v*0.55),
                        (84, 3, 0.06, v*0.8), (84, 3.5, 0.06, v*0.55)]
BASS   = lambda v=92:  [(45,0,0.32,v),(45,0.75,0.20,v),(43,1.5,0.32,v),(45,2,0.32,v),
                        (48,2.75,0.20,v),(43,3.25,0.32,v)]
KEYS   = lambda v=40:  [(57+iv,t,1.6,v) for t in (0.0,2.0) for iv in (0,4,7,11)]
KEYSQ  = lambda v=34:  [(57+iv,2.0,1.6,v) for iv in (0,4,7,11)]
LEAD   = lambda v=76:  [(69+iv,t,0.34,v) for t,iv in [(0,0),(0.75,3),(1.5,7),(2,10),(2.75,7),(3.5,3)]]
LEADHI = lambda v=88:  [(81+iv,t,0.34,v) for t,iv in [(0,0),(0.75,3),(1.5,7),(2,10),(2.75,7),(3.5,3)]]
PAD    = lambda v=42:  [(57+iv,t,3.6,v) for t in (0.0,) for iv in (0,7,12,19)]
STAB   = lambda v=62:  [(64,2.5,0.4,v),(71,3.0,0.4,v)]

def build_track(out_mmp):
    tracks = []
    # kick: intro, main, build, climax  (NOT in the dip)
    kick = pattern_for((0,4), FULL) + pattern_for((4,12), FULLMOD) \
         + pattern_for((16,20), FULL) + pattern_for((20,30), FULLMOD)
    tracks.append(inst_track("kick", 68, "kicker", kick, TOTAL,
                             f0=45, f1=150, decay=55))
    # hats: everywhere except outro
    hats = pattern_for((0,4), lambda: HATS(50)) + pattern_for((4,12), lambda: HATS(58)) \
         + pattern_for((12,16), lambda: HATS(14)) + pattern_for((16,20), lambda: HATS(52)) \
         + pattern_for((20,30), lambda: HATS(70))
    tracks.append(inst_track("hats", 42, "tripleosc", hats, TOTAL, v1=62, v2=0, w0=0))
    # bass: intro, main, build, climax (NOT in the dip)
    bass = pattern_for((0,4), lambda: BASS(72)) + pattern_for((4,12), lambda: BASS(92)) \
         + pattern_for((16,20), lambda: BASS(84)) + pattern_for((20,30), lambda: BASS(100))
    tracks.append(inst_track("bass", 58, "lb302", bass, TOTAL, wave=1))
    # keys: main, climax + quiet pad through the dip
    keys = pattern_for((4,12), lambda: KEYS(40)) + pattern_for((12,16), lambda: [(57+iv,0,2.4,20) for iv in (0,7,12)]) \
         + pattern_for((16,20), lambda: KEYS(38)) + pattern_for((20,30), lambda: KEYS(46)) \
         + pattern_for((30,32), lambda: PAD(34))
    tracks.append(inst_track("keys", 46, "tripleosc", keys, TOTAL, v1=40, v2=30, c1=12))
    # lead: main then the higher climax line
    lead = pattern_for((4,12), lambda: LEAD(76)) + pattern_for((20,30), lambda: LEADHI(88))
    tracks.append(inst_track("lead", 50, "tripleosc", lead, TOTAL, v1=92, v2=36, c1=12))
    # stab: build + climax punctuation
    stab = pattern_for((16,20), lambda: STAB(56)) + pattern_for((20,30), lambda: STAB(68))
    tracks.append(inst_track("stab", 34, "tripleosc", stab, TOTAL, v1=80, v2=40, c1=12))
    return build(BPM, [section("ALL", tracks, 0, TOTAL)], out_mmp, TOTAL)


if __name__ == "__main__":
    mmp = build_track("/tmp/lmmslab/final.mmp")
    print(f"project: {mmp} | {TOTAL} bars @ {BPM} BPM = {TOTAL*4*60/BPM:.0f}s")
