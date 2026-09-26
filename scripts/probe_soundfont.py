#!/usr/bin/env python3
"""Probe: can we drive FluidSynth from a hand-written MIDI file, offline, and does
the result pass the SnowSnakes gate?

MIDI (SMF type 0/1) is a documented binary format, so no third-party MIDI library
is needed -- same approach as xm_lib.py writing XM byte-by-byte.

Test: a short General MIDI arrangement using real instruments from the soundfont
(acoustic bass, electric piano, strings) and render it with fluidsynth -F (file
output, no audio device required).
"""
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parent.parent
OUT = Path("/tmp/sf_probe")
OUT.mkdir(exist_ok=True)
SF2 = "/usr/share/sounds/sf2/FluidR3_GM.sf2"

PPQ = 480                      # ticks per quarter note
BPM = 100
US_PER_QN = int(60_000_000 / BPM)


def vlq(n):
    """MIDI variable-length quantity."""
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


def track(events):
    """events: list of (delta_ticks, bytes). Returns a complete MTrk chunk."""
    data = b"".join(vlq(d) + e for d, e in events)
    data += vlq(0) + b"\xFF\x2F\x00"          # end of track
    return b"MTrk" + struct.pack(">I", len(data)) + data


def hdr(ntracks):
    return b"MThd" + struct.pack(">IHHH", 6, 1, ntracks, PPQ)


# General MIDI program numbers (0-based): 33 = Electric Bass (finger),
# 4 = Electric Piano 1, 48 = Strings Ensemble 1
def build(tempo_events, notes_by_channel):
    ev = list(tempo_events)
    return track(ev)


def main():
    # track 1: tempo + meta, track 2: bass, track 3: keys, track 4: strings
    all_ev = []

    # --- bass: root notes, GM prog 33 on channel 0 ---
    bass = [(0, bytes([0xC0, 33])), (0, bytes([0xB0, 7, 100]))]
    # --- keys: GM prog 4 on channel 1 ---
    keys = [(0, bytes([0xC1, 4])), (0, bytes([0xB1, 7, 80]))]
    # --- strings: GM prog 48 on channel 2 ---
    strings = [(0, bytes([0xC2, 48])), (0, bytes([0xB2, 7, 70]))]

    prog = [45, 41, 38, 40]                    # A2 F2 D2 E2
    chords = [[57, 60, 64], [53, 57, 60], [50, 53, 57], [52, 55, 59]]
    for bar in range(4):
        root = prog[bar]
        bass.append((0, bytes([0x90, root, 100])))
        bass.append((PPQ * 3, bytes([0x80, root, 0])))
        for n in chords[bar]:
            keys.append((0, bytes([0x91, n + 12, 70])))
        for n in chords[bar]:
            keys.append((PPQ * 2, bytes([0x81, n + 12, 0])))
        for n in chords[bar][:2]:
            strings.append((0, bytes([0x92, n + 24, 60])))
        for n in chords[bar][:2]:
            strings.append((PPQ * 4, bytes([0x82, n + 24, 0])))

    # assemble tracks (each track must start with its own delta-0 events)
    tempo = [(0, bytes([0xFF, 0x51, 0x03]) + struct.pack(">I", US_PER_QN)[1:]),
             (0, bytes([0xFF, 0x58, 0x04, 4, 2, 24, 8]))]
    tracks = [track(tempo), track(bass), track(keys), track(strings)]

    mid = hdr(len(tracks)) + b"".join(tracks)
    mf = OUT / "probe.mid"
    mf.write_bytes(mid)
    print(f"midi written: {mf}  {len(mid)} bytes  ({len(tracks)} tracks, {PPQ} ppq, {BPM} BPM)")

    wav = OUT / "probe.wav"
    cmd = ["fluidsynth", "-ni", "-F", str(wav), "-r", "44100", "-g", "0.8", SF2, str(mf)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    print("fluidsynth rc:", r.returncode)
    if r.stderr.strip():
        print("stderr:", r.stderr.strip()[:400])
    if wav.exists():
        print(f"wav: {wav.stat().st_size//1024} KB")
        import wave
        with wave.open(str(wav)) as w:
            print(f"  {w.getnframes()/w.getframerate():.2f}s  {w.getframerate()} Hz  "
                  f"{w.getnchannels()} ch  {w.getsampwidth()*8}-bit")
    else:
        print("NO WAV PRODUCED")


if __name__ == "__main__":
    main()
