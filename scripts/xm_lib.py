#!/usr/bin/env python3
"""Minimal XM (FastTracker II) module writer — the format MilkyTracker edits.

No tracker libraries needed: XM is a documented binary layout, so a module can
be authored directly and rendered anywhere with ffmpeg's libopenmpt decoder.

Layout: header(336) | patterns | instruments(header + sample headers + PCM)
8-bit samples are delta-encoded; a sample of N bytes is stored as the first
value then N-1 signed differences.
"""
from __future__ import annotations
import struct

SR = 16726          # sample rate we synthesise at; REL_NOTE 12 makes C-4 play it 1:1
REL_NOTE = 12
ROWS_PER_PATTERN = 64
NOTE_C4 = 49        # XM: note 49 == C-4
MAX_CHANNELS = 32


def note_for(freq, base_freq=55.0):
    """Note number that plays `freq` given a sample whose natural pitch is base_freq."""
    import math
    return max(1, min(96, NOTE_C4 + int(round(12 * math.log2(freq / base_freq)))))


def delta_encode(pcm_bytes):
    out = bytearray(len(pcm_bytes))
    prev = 0
    for i, b in enumerate(pcm_bytes):
        cur = b - 256 if b > 127 else b
        d = (cur - prev) & 0xFF
        out[i] = d
        prev = cur
    return bytes(out)


class Sample:
    def __init__(self, pcm, loop=None, volume=64, pan=128, rel_note=REL_NOTE,
                 finetune=0, name="sample"):
        # pcm: float in [-1,1]
        import numpy as np
        x = np.clip(np.asarray(pcm, dtype=float), -1.0, 1.0)
        self.data = (x * 127.0).astype(np.int8).tobytes()
        self.length = len(self.data)
        self.loop = loop          # (start, end) in samples, or None
        self.volume, self.pan = volume, pan
        self.rel_note, self.finetune, self.name = rel_note, finetune, name


class Instrument:
    def __init__(self, name, samples):
        self.name, self.samples = name, samples


class Module:
    def __init__(self, name="untitled", channels=16, bpm=145, speed=6, linear=True):
        self.name, self.channels = name, channels
        self.bpm, self.speed = bpm, speed
        self.flags = 1 if linear else 0
        self.instruments = []
        self.patterns = []
        self.order = []

    def add_instrument(self, inst):
        self.instruments.append(inst)
        return len(self.instruments)          # 1-based instrument number

    def add_pattern(self, cells):
        """cells: {(row,channel): (note, inst, vol, fx, param)} with 0-based channel."""
        rows = bytearray()
        for r in range(ROWS_PER_PATTERN):
            for c in range(self.channels):
                note, inst, vol, fx, param = cells.get((r, c), (0, 0, 0, 0, 0))
                rows += bytes([note & 0xFF, inst & 0xFF, vol & 0xFF,
                               fx & 0xFF, param & 0xFF])
        self.patterns.append(bytes(rows))
        return len(self.patterns) - 1

    # ---------------- serialisation ----------------
    def _header(self):
        h = bytearray()
        h += b"Extended Module: "
        h += self.name.encode()[:20].ljust(20, b"\x00")
        h += b"\x1a"
        h += b"Z-Dot MilkyTracker".ljust(20, b"\x00")
        h += struct.pack("<H", 0x0104)             # version 1.04
        h += struct.pack("<I", 276)                # header size
        order = self.order + [0] * (256 - len(self.order))
        h += struct.pack("<HHHHHHHH",
                         len(self.order), 0, self.channels, len(self.patterns),
                         len(self.instruments), self.flags, self.speed, self.bpm)
        h += bytes(order[:256])
        assert len(h) == 336, len(h)
        return bytes(h)

    def _pattern(self, data):
        head = struct.pack("<IBHH", 9, 0, ROWS_PER_PATTERN, len(data))
        return head + data

    def _instrument(self, inst):
        h = bytearray()
        h += struct.pack("<I", 263)
        h += inst.name.encode()[:22].ljust(22, b"\x00")
        h += struct.pack("<BH", 0, len(inst.samples))
        h += struct.pack("<I", 40)
        h += bytes(range(96))                      # sample map: 1:1
        h += bytes(48)                             # (empty vol envelope)
        h += bytes(48)                             # (empty pan envelope)
        h += bytes([0, 0, 0, 0, 0, 0, 0, 0])       # envelope point counts etc.
        h += bytes([0, 0, 0, 0, 0, 0])             # vibrato
        h += struct.pack("<H", 0)                  # volume fadeout
        h += bytes(22)                             # reserved
        assert len(h) == 263, len(h)
        for s in inst.samples:
            ls, le = s.loop if s.loop else (0, 0)
            h += struct.pack("<III", s.length, ls, (le - ls) if s.loop else 0)
            # volume(u8) finetune(i8) type(u8) panning(u8) relnote(i8) reserved(u8)
            h += struct.pack("<BbBBbB", s.volume, s.finetune,
                             0x01 if s.loop else 0x00, s.pan, s.rel_note, 0)
            h += s.name.encode()[:22].ljust(22, b"\x00")
        for s in inst.samples:
            h += delta_encode(s.data)
        return bytes(h)

    def tobytes(self):
        out = bytearray(self._header())
        for p in self.patterns:
            out += self._pattern(p)
        for i in self.instruments:
            out += self._instrument(i)
        return bytes(out)

    def save(self, path):
        data = self.tobytes()
        with open(path, "wb") as f:
            f.write(data)
        return len(data)
