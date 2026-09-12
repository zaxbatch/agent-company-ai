#!/usr/bin/env python3
"""Spec model for the local LMMS beat tool.

A "spec" is a JSON dict describing a beat declaratively:

{
  "title": "beat-16bar",
  "bpm": 128,
  "progression": ["Am", "F", "C", "G"],
  "sections": [
    {"name": "intro", "bars": 2, "layers": ["kick", "bass"]},
    {"name": "build", "bars": 2, "layers": ["kick", "snare", "hat", "bass"]},
    {"name": "drop",  "bars": 4, "layers": ["kick","snare","hat","openhat","bass","stab"]},
    {"name": "break", "bars": 2, "layers": ["hat", "bass", "stab"]},
    {"name": "drop2", "bars": 6,
     "layers": ["kick","snare","clap","hat","openhat","bass","stab"], "fill": true}
  ]
}

Layers drive which tracks get notes per bar; that is what makes section
contrast (and therefore arrangement) a *measurable* property, not a vibe.
"""
from __future__ import annotations
import json

LAYERS = ("kick", "snare", "clap", "hat", "openhat", "crash", "bass", "stab")

# semitone offsets for the chord progression, keyed by chord name
CHORDS = {
    "Am": (45, 48, 52), "A":  (45, 49, 52),
    "F":  (41, 45, 48), "Fm": (41, 44, 48),
    "C":  (48, 52, 55), "G":  (43, 47, 50),
    "Dm": (38, 41, 45), "Em": (40, 43, 47),
    "D":  (38, 42, 45), "E":  (40, 44, 47), "Bb": (46, 50, 53),
}

TICKS_PER_BAR = 192   # LMMS internal resolution, 4/4
Q, E, S = 48, 24, 12  # quarter / eighth / sixteenth note in ticks


DEFAULT_SPEC = {
    "title": "beat-16bar",
    "bpm": 128,
    "progression": ["Am", "F", "C", "G"],
    "sections": [
        {"name": "intro", "bars": 2, "layers": ["kick", "bass"]},
        {"name": "build", "bars": 2, "layers": ["kick", "snare", "hat", "bass"]},
        {"name": "drop",  "bars": 4,
         "layers": ["kick", "snare", "hat", "openhat", "bass", "stab"]},
        {"name": "break", "bars": 2, "layers": ["hat", "bass", "stab"]},
        {"name": "drop2", "bars": 6, "fill": True,
         "layers": ["kick", "snare", "clap", "hat", "openhat", "bass", "stab"]},
    ],
}


def load(path):
    with open(path) as f:
        return validate(json.load(f))


def validate(spec):
    spec.setdefault("bpm", 128)
    spec.setdefault("progression", ["Am", "F", "C", "G"])
    spec.setdefault("title", "beat")
    bad = [c for c in spec["progression"] if c not in CHORDS]
    if bad:
        raise SystemExit(f"unknown chord(s): {bad}. known: {sorted(CHORDS)}")
    for sec in spec["sections"]:
        unknown = [l for l in sec["layers"] if l not in LAYERS]
        if unknown:
            raise SystemExit(f"section {sec['name']!r}: unknown layer(s) {unknown}")
        if sec["bars"] < 1:
            raise SystemExit(f"section {sec['name']!r}: bars must be >= 1")
    spec["total_bars"] = sum(s["bars"] for s in spec["sections"])
    return spec


def section_map(spec):
    """-> [(section_name, first_bar_index, bar_count), ...]"""
    out, bar = [], 0
    for sec in spec["sections"]:
        out.append((sec["name"], bar, sec["bars"]))
        bar += sec["bars"]
    return out


def chord_for_bar(spec, bar_idx, bars_per_chord=1):
    prog = spec["progression"]
    return prog[(bar_idx // bars_per_chord) % len(prog)]


def layer_bar_map(spec):
    """-> list, one entry per bar: (frozenset(layers), is_fill)."""
    out = []
    for sec in spec["sections"]:
        for i in range(sec["bars"]):
            is_fill = bool(sec.get("fill")) and i == sec["bars"] - 1
            out.append((frozenset(sec["layers"]), is_fill))
    return out
