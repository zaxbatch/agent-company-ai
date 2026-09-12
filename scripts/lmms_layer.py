#!/usr/bin/env python3
"""Layer synths over an imported audio loop in LMMS.

The loop is imported as an AudioFileProcessor track (one note per repeat, note
length = loop length so the sample plays through), then synth tracks are written
over it with a progressive arrangement so the mix actually develops.

    scripts/lmms_layer.py --loop content/experiments/lmms/snow-beats-drums-128.wav \
        --bars 16 --bpm 128 --out content/experiments/lmms/snow-drums-and-synths.mmp --render
"""
from __future__ import annotations
import argparse, os, re, subprocess, sys
from xml.sax.saxutils import quoteattr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmms_beat import Track, afp, tripleosc, run_lmms, MASTER_FADER
from lmms_spec import CHORDS, Q, E, S, TICKS_PER_BAR

BAR = TICKS_PER_BAR
LOOP_BARS = 4                      # Snow Beats renders 4 bars per loop


def audio_track(name, wav_path, repeat_every_bars, total_bars, vol=70):
    """AFP track that plays an imported loop once per repeat window."""
    t = Track(name, afp(os.path.abspath(wav_path), amp=100), vol=vol)
    span = repeat_every_bars * BAR
    for b in range(0, total_bars, repeat_every_bars):
        t.n(b * BAR, 57, 100, span)   # len == loop length -> plays through
    return t


def build(loop, total_bars, bpm, prog=("Am", "F", "C", "G")):
    tracks = [audio_track("Drums (Snow Beats)", loop, LOOP_BARS, total_bars, vol=68)]

    bass = Track("Synth Bass", tripleosc(wave0=2, wave1=0, vol1=0, vol2=0, coarse2=0), vol=80)
    pad = Track("Pad", tripleosc(wave0=2, wave1=2, vol1=44, vol2=30, coarse2=12), vol=38, pan=16)
    lead = Track("Lead", tripleosc(vol1=58, vol2=40, coarse2=12), vol=54, pan=-14)

    eighth = [8, 5, 3, 5, 8, 5, 3, 1]      # scale degrees within the chord
    eighth_b = [5, 8, 10, 8, 5, 3, 5, 1]   # busier variant for the last cycle

    for b in range(total_bars):
        bar0 = b * BAR
        root, third, fifth = CHORDS[prog[b % len(prog)]]
        tones = {1: root, 3: third, 5: fifth, 8: root + 12,
                 10: third + 12, 12: fifth + 12}
        stage = b // LOOP_BARS          # 0..3, one stage per loop repeat

        # bass: always in, eighth pulse with octave accents
        for i in range(8):
            key = root + (12 if i in (3, 7) else 0)
            bass.n(bar0 + i * E, key, 94 if i % 2 == 0 else 72, E - 6)
        if stage == 3 and b % 4 == 3:
            bass.n(bar0 + 7 * E, root + 7, 86, E - 6)   # walk-up

        # pad: enters at stage 1, sustained triads
        if stage >= 1:
            for key in (root, third, fifth):
                pad.n(bar0, key, 52, BAR - 8)
            if stage >= 3:
                pad.n(bar0 + 2 * Q, root + 12, 40, BAR - Q * 2)  # upper voice

        # lead: enters at stage 2
        if stage >= 2:
            line = eighth_b if stage == 3 else eighth
            for i, d in enumerate(line):
                lead.n(bar0 + i * E, tones[d], 58 if i % 2 == 0 else 46, E - 8)

    return [t for t in tracks + [bass, pad, lead] if t.notes], TOTAL_BARS


TOTAL_BARS = 16


def project_xml(tracks, total_bars, bpm, title, loop_name):
    body = "\n".join(t.xml(total_bars) for t in tracks)
    return f'''<?xml version="1.0"?>
<!DOCTYPE lmms-project>
<lmms-project type="song" version="1.0" creator="Z-Dot Team" creatorversion="1.2.0">
  <head timesig_denominator="4" bpm="{bpm}" masterpitch="0" mastervol="100" timesig_numerator="4"/>
  <song>
    <trackcontainer visible="1" width="1100" height="440" type="song" x="12" y="1" maximized="0" minimized="0">
      <track muted="0" name={quoteattr(title)} solo="0" type="1">
        <bbtrack>
          <trackcontainer visible="1" width="972" height="352" type="bbtrackcontainer" x="541" y="531" maximized="0" minimized="0">
{body}
          </trackcontainer>
        </bbtrack>
        <bbtco usestyle="1" muted="0" name={quoteattr(loop_name)} pos="0" len="{BAR * total_bars}" color="4282417407"/>
      </track>
    </trackcontainer>
    <fxmixer visible="1" width="530" height="332" x="9" y="530" maximized="0" minimized="0">
      <fxchannel muted="0" num="0" name="Master" volume="{MASTER_FADER}" soloed="0">
        <fxchain numofeffects="0" enabled="0"/>
      </fxchannel>
    </fxmixer>
    <ControllerRackView visible="1" width="258" height="173" x="664" y="444" maximized="0" minimized="0"/>
    <pianoroll visible="0" width="640" height="480" x="1" y="1" maximized="1" minimized="0"/>
    <automationeditor visible="0" width="640" height="400" x="356" y="129" maximized="0" minimized="0"/>
  </song>
</lmms-project>
'''


def main():
    global TOTAL_BARS
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", required=True)
    ap.add_argument("--bars", type=int, default=16)
    ap.add_argument("--bpm", type=int, default=128)
    ap.add_argument("--out", default="content/experiments/lmms/snow-drums-and-synths.mmp")
    ap.add_argument("--title", default="Snow Drums + Synths")
    ap.add_argument("--stems", action="store_true")
    ap.add_argument("--mp3", action="store_true")
    a = ap.parse_args()
    TOTAL_BARS = a.bars

    if not os.path.exists(a.loop):
        raise SystemExit(f"loop not found: {a.loop}")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)

    tracks, total = build(a.loop, a.bars, a.bpm)
    xml = project_xml(tracks, total, a.bpm, a.title, os.path.basename(a.loop))
    with open(a.out, "w") as f:
        f.write(xml)
    print(f"wrote {a.out} ({len(xml)} B, {total} bars @ {a.bpm} bpm)")
    print("tracks: " + ", ".join(f"{t.name}({len(t.notes)} notes)" for t in tracks))

    wav = re.sub(r"\.mmp$", ".wav", a.out)
    run_lmms(["render", a.out, "-o", wav, "-f", "wav", "-s", "44100"])
    print("rendered", wav)

    if a.stems:
        sd = re.sub(r"\.mmp$", "-stems", a.out)
        os.makedirs(sd, exist_ok=True)
        run_lmms(["rendertracks", a.out, "-o", sd, "-f", "wav"])
        print(f"stems -> {sd}/ ({len(os.listdir(sd))})")
    if a.mp3:
        mp3 = re.sub(r"\.mmp$", ".mp3", a.out)
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                        "-i", wav, "-b:a", "192k", mp3], check=True)
        print("encoded", mp3)


if __name__ == "__main__":
    main()
