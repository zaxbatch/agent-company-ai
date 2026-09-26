#!/usr/bin/env python3
"""midi_lib.py — minimal Standard MIDI File (SMF) writer.

No third-party MIDI library is used (mido/pretty_midi are not installed on this
box, and pip here is unreliable). SMF is a documented binary format, so it is
authored directly — the same approach xm_lib.py takes for XM modules.

Why this exists: it drives FluidSynth + the FluidR3_GM.sf2 soundfont, which gives
the catalogue REAL recorded instruments (piano, strings, brass, GM drum kit)
instead of oscillator stand-ins.

Layout: MThd (14 bytes) | MTrk * N
  - format 1: a tempo/meta track plus one track per voice
  - every event carries a DELTA in variable-length quantity (VLQ) ticks
  - note-off is written as an explicit 0x8n event (not note-on vel 0) so the
    output is unambiguous across synths

Timing rule that matters: all positions are ABSOLUTE ticks internally and are
converted to deltas at serialisation. That is what stops the drift the naive
delta-accumulating probe suffered from.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

# General MIDI percussion is always channel 10 (0-indexed: 9)
DRUM_CHANNEL = 9

# GM drum note numbers used by this project
KICK, SNARE, CLAP = 36, 38, 39
HAT_CLOSED, HAT_PEDAL, HAT_OPEN = 42, 44, 46
RIDE, CRASH = 51, 49
TOM_LOW, TOM_HIGH = 45, 50


def vlq(n: int) -> bytes:
    """MIDI variable-length quantity (7 bits per byte, high bit = continue)."""
    if n < 0:
        raise ValueError("negative delta")
    out = [n & 0x7F]
    n >>= 7
    while n:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    return bytes(reversed(out))


@dataclass
class Event:
    tick: int
    data: bytes
    order: int = 0          # stable tie-break so output is deterministic


@dataclass
class Track:
    name: str = ""
    events: list = field(default_factory=list)
    _seq: int = 0

    def _add(self, tick, data):
        self.events.append(Event(int(tick), data, self._seq))
        self._seq += 1

    # ── notes ────────────────────────────────────────────────────────────────
    def note(self, channel, pitch, start, dur, vel=100):
        """One note. start/dur in ticks."""
        if dur <= 0:
            raise ValueError("note duration must be positive")
        self._add(start, bytes([0x90 | channel, int(pitch) & 0x7F, max(1, min(127, int(vel)))]))
        self._add(start + dur, bytes([0x80 | channel, int(pitch) & 0x7F, 0]))
        return self

    def chord(self, channel, pitches, start, dur, vel=100):
        for p in pitches:
            self.note(channel, p, start, dur, vel)
        return self

    def drum(self, note, start, dur=30, vel=100):
        return self.note(DRUM_CHANNEL, note, start, dur, vel)

    # ── controllers ──────────────────────────────────────────────────────────
    def program(self, channel, prog, tick=0):
        self._add(tick, bytes([0xC0 | channel, int(prog) & 0x7F]))
        return self

    def cc(self, channel, num, val, tick=0):
        self._add(tick, bytes([0xB0 | channel, int(num) & 0x7F, max(0, min(127, int(val)))]))
        return self

    def volume(self, channel, val, tick=0):
        return self.cc(channel, 7, val, tick)

    def pan(self, channel, val, tick=0):
        return self.cc(channel, 10, val, tick)

    def expression(self, channel, val, tick=0):
        return self.cc(channel, 11, val, tick)

    def reverb_send(self, channel, val, tick=0):
        return self.cc(channel, 91, val, tick)

    def pitch_bend(self, channel, value, tick=0):
        """value: -8192..8191"""
        v = max(-8192, min(8191, int(value))) + 8192
        self._add(tick, bytes([0xE0 | channel, v & 0x7F, (v >> 7) & 0x7F]))
        return self

    def serialise(self) -> bytes:
        ev = sorted(self.events, key=lambda e: (e.tick, e.order))
        out, last = [], 0
        for e in ev:
            out.append(vlq(e.tick - last) + e.data)
            last = e.tick
        out.append(vlq(0) + b"\xFF\x2F\x00")          # End of Track
        data = b"".join(out)
        return b"MTrk" + struct.pack(">I", len(data)) + data


class MidiFile:
    def __init__(self, ppq=480, bpm=120.0):
        self.ppq = ppq
        self.bpm = bpm
        self.tracks: list[Track] = []
        self.time_sig = (4, 4)
        self._name = "zdot"

    # convenience -------------------------------------------------------------
    @property
    def beat(self):
        return self.ppq

    @property
    def bar(self):
        return self.ppq * self.time_sig[0]

    def ticks(self, beats):
        return int(round(beats * self.ppq))

    def add_track(self, name=""):
        t = Track(name=name)
        self.tracks.append(t)
        return t

    def serialise(self) -> bytes:
        us_per_qn = int(round(60_000_000 / float(self.bpm)))
        meta = Track(name="tempo")
        meta._add(0, b"\xFF\x03" + bytes([len(self._name)]) + self._name.encode())
        meta._add(0, b"\xFF\x51\x03" + struct.pack(">I", us_per_qn)[1:])
        meta._add(0, b"\xFF\x58\x04" + bytes([self.time_sig[0], 4, 24, 8]))
        chunks = [meta.serialise()] + [t.serialise() for t in self.tracks]
        return (b"MThd" + struct.pack(">IHHH", 6, 1, len(chunks), self.ppq)
                + b"".join(chunks))

    def write(self, path):
        from pathlib import Path
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(self.serialise())
        return p


def render(midi_path, wav_path, sf2="/usr/share/sounds/sf2/FluidR3_GM.sf2",
           gain=0.7, sr=44100, timeout=900):
    """Render a MIDI file to WAV with FluidSynth, offline (-F writes a file,
    so no audio device is required)."""
    import subprocess
    from pathlib import Path
    cmd = ["fluidsynth", "-ni", "-F", str(wav_path), "-r", str(sr),
           "-g", str(gain), sf2, str(midi_path)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0 or not Path(wav_path).exists():
        raise RuntimeError(f"fluidsynth failed rc={r.returncode}: {r.stderr[:300]}")
    return Path(wav_path)
