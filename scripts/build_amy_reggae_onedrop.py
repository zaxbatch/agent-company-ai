#!/usr/bin/env python3
"""build_amy_reggae_onedrop.py — SnowSnakes track rendered on the REAL AMY engine
(the TulipCC synth core), offline.

Genre: reggae / one-drop @ 76 BPM. Distinct profile on the board: the onedrop
groove, the 76 BPM bucket and a dark brightness are all unused (the board's
existing tracks are backbeat ~92-96 and four-on-floor ~118-126).

Groove contract (verify_song.py, measured from the audio, not declared):
  - one-drop: the KICK lands on beat 3 of the bar and must LEAD in the 90-200 Hz
    band. Kick is placed on 16th step 8 (= beat 3 exactly), verified on probes
    before the full render.
  - the dub bass fundamental sits on beat 1, which swamps the 40-90 Hz band, so
    the verifier isolates the kick at 90-200 Hz for this genre.

Deterministic: no randomness anywhere, so a re-render is byte-identical.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import amy

SR = amy.AMY_SAMPLE_RATE
BPM = 76.0
BEAT = 60.0 / BPM
STEP_BLOCKS = int(round((BEAT / 4) * SR / amy.AMY_BLOCK_SIZE))   # 34 blocks = one 16th

TITLE = "Frostline Dub"
N_BARS = 40                       # 40 bars ~= 126 s
PROGRESSION = [57, 53, 60, 55]    # Am - F - C - G, one chord per bar
MEL = [69, 72, 71, 69, 67, 69, 72, 74]

ROOT = Path(__file__).resolve().parent.parent
OUTDIR = ROOT / "content" / "snowsnakes" / "songs"
STEM = "frostline-dub"


def render_steps(n):
    """Render exactly n 16th-note steps of audio from AMY."""
    out = []
    for _ in range(n):
        for _b in range(STEP_BLOCKS):
            out.append(np.array(amy._amy.render_to_list()) / 32768.0)
    return np.hstack(out).reshape((-1, amy.AMY_NCHANS))


def hz(note):
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


def kick(vel):
    amy.send(osc=0, wave=amy.PCM, preset=1, vel=vel)


def snare(vel):
    amy.send(osc=1, wave=amy.PCM, preset=12, vel=vel)


def hat(vel, open_=False):
    amy.send(osc=2, wave=amy.PCM, preset=10 if open_ else 9, vel=vel)


def bass(note, vel):
    amy.send(osc=8, wave=amy.SINE, freq=hz(note), bp0="0,1,60,0.85,150,0", vel=vel)


def skank(note, vel):
    """Offbeat chop: two slightly detuned saws, short stab."""
    amy.send(osc=3, wave=amy.SAW_DOWN, freq=hz(note), bp0="0,1,6,0.4,80,0", vel=vel)
    amy.send(osc=4, wave=amy.SAW_DOWN, freq=hz(note) * 1.006, bp0="0,1,6,0.4,80,0", vel=vel)


def lead(note, vel):
    amy.send(osc=5, wave=amy.TRIANGLE, freq=hz(note), bp0="0,1,25,0.7,240,0", vel=vel)


def render_song():
    amy.send(reset=amy.RESET_ALL_OSCS)
    # the dub signature: slow filtered echo with long feedback
    amy.echo(level=0.5, delay_ms=460, max_delay_ms=1400, feedback=0.68, filter_coef=-0.35)
    amy.send(bus=0, reverb=[0.2, 0.7, 0.55, 6000])

    chunks = []
    for bar in range(N_BARS):
        chord = PROGRESSION[bar % 4]
        intro, outro = bar < 4, bar >= N_BARS - 4
        dropout = (bar % 8) == 7           # reggae bar-8 drop-out
        for step in range(16):
            if step == 8 and not dropout:                      # THE ONE DROP
                kick(3.4 if not outro else 2.6)
                if bar % 4 == 2:
                    snare(0.85)
            if not outro:
                if step % 2 == 0:
                    hat(0.8, open_=(step % 4 == 2))
                elif bar >= 4:
                    hat(0.4)
            if step == 0 and not intro:
                bass(chord, 1.4 if not dropout else 0.9)
            if step == 10 and not intro and not dropout:
                bass(chord + 7, 0.85)
            if step % 4 == 2 and bar >= 4 and not dropout:
                skank(chord + 12, 1.25 if step == 6 else 1.0)
            if bar >= 24 and not outro and step % 2 == 0 and (bar + step) % 3 == 0:
                lead(MEL[(bar * 8 + step // 2) % len(MEL)], 0.8)
            chunks.append(render_steps(1))
    return np.vstack(chunks)


def master(a, target_peak=0.86):
    """Normalise to a sane peak and soft-clip the few stray transients."""
    a = a - float(a.mean())
    peak = float(np.abs(a).max())
    if peak > 0:
        a = a * (target_peak / peak)
    a = np.tanh(a * 1.05) / np.tanh(1.05)     # gentle soft limit
    a = a * (target_peak / float(np.abs(a).max()))
    return a.astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUTDIR / "wav" / f"{STEM}.wav"))
    ap.add_argument("--no-master", action="store_true")
    args = ap.parse_args()

    print(f"AMY {amy.version} @ {SR} Hz | {BPM:.0f} BPM | {N_BARS} bars | "
          f"step={STEP_BLOCKS} blocks")
    a = render_song()
    raw_peak = float(np.abs(a).max())
    if not args.no_master:
        a = master(a)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    amy.write(a, str(out))
    print(f"  raw peak {raw_peak:.4f} -> final peak {float(np.abs(a).max()):.4f}")
    print(f"  {len(a)/SR:.2f}s  {out.stat().st_size//1024} KB  -> {out}")


if __name__ == "__main__":
    main()
