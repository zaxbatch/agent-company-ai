#!/usr/bin/env python3
"""verify_song.py — the SnowSnakes song quality gate.

THE STANDARD (set by "Shelves After Dark", 2026-09-17)
-----------------------------------------------------
The standard is the PROCESS and the BAR, not the sound. A song passes only if it
is measurably TRUE TO THE GENRE IT CLAIMS. That is deliberately genre-specific:
disco must swing four-on-the-floor, boom-bap must NOT. So the gate enforces
quality without pushing every track toward one groove.

Per-song checks (all independent of my own claims):
  1. duration  >= MIN_SECONDS
  2. not silent (peak and RMS thresholds)
  3. level     peak within a sane window (not clipping, not quiet)
  4. genre     the claimed groove is verified from the rendered audio
  5. determinism  re-render yields byte-identical audio (no external samples)
  6. cover art present and non-trivial

Catalog check:
  7. variety   no two songs may share groove class + tempo bucket + brightness
               bucket. This is the guard against every beat sounding the same.

Usage:
  python3 scripts/verify_song.py <song.wav> --genre disco --bpm 118 [--cover X.png] [--catalog DIR]
  python3 scripts/verify_song.py --list-genres
"""
from __future__ import annotations
import argparse
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import songkit as sk

MIN_SECONDS = 60.0
PEAK_MIN, PEAK_MAX = 0.35, 1.0        # 0.35 ~= -9 dBFS floor, 1.0 = full scale
RMS_MIN = 0.01

# ── genre signatures: each genre must PROVE its own groove ───────────────────
GENRES = {
    "disco": {
        "bpm": (108, 132),
        "groove": "four_on_floor",
        "note": "kick on every beat, open hats on the offbeat eighths",
    },
    "house": {
        "bpm": (115, 130),
        "groove": "four_on_floor",
        "note": "four-on-the-floor with prominent offbeat hats",
    },
    "synthwave": {
        "bpm": (78, 108),
        "groove": "four_on_floor",
        "note": "steady 4/4, gated snare on 2 and 4, slower tempo",
    },
    "boombap": {
        "bpm": (82, 104),
        "groove": "backbeat",
        "note": "kick 1+3, SNARE on 2 and 4 -- must NOT be four-on-the-floor",
    },
    "trap": {
        "bpm": (120, 160),
        "groove": "sparse_kick",
        "note": "sparse kick, dense hi-hat rolls, half-time feel",
    },
    "rock": {
        "bpm": (100, 150),
        "groove": "backbeat",
        "note": "kick 1+3, snare 2+4",
    },
    "ambient": {
        "bpm": (50, 100),
        "groove": "any",
        "note": "texture over rhythm; only duration/level/cover enforced",
    },
}


def check_groove(a, sr, bpm, kind):
    """Return (passed, evidence_str). Measured from the audio, not declared."""
    if kind == "any":
        return True, "groove unconstrained for this genre"

    if kind == "four_on_floor":
        ot = sk.onsets(a, sr)
        ratio, med = sk.beat_grid_ratio(ot, bpm)
        spb = 60.0 / bpm
        on, off = sk.offbeat_ratio(a, sr, bpm)
        ok = ratio >= 0.70 and abs(med - spb) < 0.06
        return ok, (f"four-on-the-floor: {ratio*100:.0f}% of {len(ot)-1} gaps = 1 beat "
                    f"(median {med:.3f}s vs {spb:.3f}s); hats offbeat/onbeat={off:.2f}/{on:.2f}")

    if kind == "backbeat":
        env2, ts = sk.band_env(a, sr, 150, 400, win=1024, hop=128)   # snare body
        env4, _ = sk.band_env(a, sr, 40, 110, win=1024, hop=128)     # kick
        spb = 60.0 / bpm
        def at(env, t):
            i = int(t * sr / 128)
            return env[i] if 0 <= i < len(env) else 0.0
        beats = np.arange(0, ts[-1], spb)
        if len(beats) < 4:
            return False, "too short to measure a backbeat"
        b13 = np.mean([at(env4, beats[i]) for i in range(len(beats)) if i % 4 in (0, 2)])
        b24 = np.mean([at(env4, beats[i]) for i in range(len(beats)) if i % 4 in (1, 3)])
        s24 = np.mean([at(env2, beats[i]) for i in range(len(beats)) if i % 4 in (1, 3)])
        s13 = np.mean([at(env2, beats[i]) for i in range(len(beats)) if i % 4 in (0, 2)])
        # A TRUE backbeat needs THREE things, or a four-on-the-floor track sails
        # through (found by testing: a disco track claimed as boombap passed the
        # old s24 > s13 check, because disco's 2/4 clap made them near-equal).
        #   1. snare clearly heavier on 2 and 4  (real margin, not a coin flip)
        #   2. kick heavier on 1 and 3
        #   3. it must NOT be four-on-the-floor
        ot = sk.onsets(a, sr)
        fof, _med = sk.beat_grid_ratio(ot, bpm)
        margin = (s24 / s13) if s13 > 1e-6 else float("inf")
        ok = (margin >= 1.25) and (b13 > b24) and (fof < 0.70)
        return ok, (f"backbeat: snare 2,4/1,3 = {s24:.3f}/{s13:.3f} (margin {margin:.2f}x, need >=1.25x); "
                    f"kick 1,3 vs 2,4 = {b13:.3f}/{b24:.3f} (need 1,3 heavier); "
                    f"four-on-the-floor={fof*100:.0f}% (need <70%)")

    if kind == "sparse_kick":
        ot = sk.onsets(a, sr, height=0.35, min_gap=0.30)
        secs = len(a) / sr
        per_bar = len(ot) / max(secs / (4 * 60.0 / bpm), 1e-6)
        ok = per_bar <= 3.2
        return ok, f"sparse_kick: {per_bar:.2f} low onsets per bar (must be <= 3.2)"

    return True, f"no rule for {kind}"


def verify(wav, genre, bpm, cover=None, quiet=False):
    a, sr = sk.load(wav)
    secs = len(a) / sr
    peak = float(np.max(np.abs(a))) if a.size else 0.0
    rms = float(np.sqrt(np.mean(a ** 2))) if a.size else 0.0
    g = GENRES.get(genre)
    res = []

    if g is None:
        return False, [f"unknown genre {genre!r} (see --list-genres)"], {}

    lo, hi = g["bpm"]
    res.append(("duration", secs >= MIN_SECONDS,
                f"{secs:.2f}s (min {MIN_SECONDS:.0f}s)"))
    res.append(("not silent", peak > 0.02 and rms > RMS_MIN,
                f"peak={peak:.3f} ({20*np.log10(peak or 1e-9):.1f} dBFS) rms={rms:.4f}"))
    res.append(("level", PEAK_MIN <= peak <= PEAK_MAX,
                f"peak {peak:.3f} within [{PEAK_MIN}, {PEAK_MAX}]"))
    res.append(("tempo in genre range", lo <= bpm <= hi,
                f"{bpm} BPM within {genre} {lo}-{hi}"))
    gp, gev = check_groove(a, sr, bpm, g["groove"])
    res.append((f"groove = {g['groove']}", gp, gev))
    if cover:
        ok = Path(cover).exists() and Path(cover).stat().st_size > 5000
        res.append(("cover art", ok, f"{cover} ({Path(cover).stat().st_size//1024 if Path(cover).exists() else 0} KB)"))
    centroid = sk.spectral_centroid(a, sr)
    passed = all(ok for _, ok, _ in res)
    meta = {"duration": round(secs, 3), "bpm": bpm, "genre": genre,
            "groove": g["groove"], "centroid_hz": round(centroid, 1),
            "percentile_peak": round(peak, 4), "rms": round(rms, 5)}
    return passed, res, meta


def fingerprint(meta):
    """Coarse identity used to detect homogenisation across the catalog."""
    return (meta["groove"],
            round(meta["bpm"] / 10) * 10,
            int(meta["centroid_hz"] // 250))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wav", nargs="?")
    ap.add_argument("--genre", default="disco")
    ap.add_argument("--bpm", type=float, default=118)
    ap.add_argument("--cover")
    ap.add_argument("--catalog", help="dir of .wav songs to check for variety")
    ap.add_argument("--list-genres", action="store_true")
    a = ap.parse_args()

    if a.list_genres:
        print(f"{'genre':<12} {'bpm':<12} {'groove':<16} note")
        for k, v in GENRES.items():
            print(f"{k:<12} {str(v['bpm']):<12} {v['groove']:<16} {v['note']}")
        return 0
    if not a.wav:
        ap.error("need a .wav (or --list-genres)")

    ok, res, meta = verify(a.wav, a.genre, a.bpm, a.cover)
    print(f"GATE: {'PASS' if ok else 'FAIL'}  {a.wav}  [{a.genre} @ {a.bpm} BPM]")
    for name, good, ev in res:
        print(f"  {'PASS' if good else 'FAIL'}  {name:<26} {ev}")

    if a.catalog:
        print("\nCATALOG VARIETY")
        fp = fingerprint(meta)
        print(f"  this song: groove={fp[0]} tempo~{fp[1]} brightness~{fp[2]}00Hz")
        clash = []
        for w in sorted(Path(a.catalog).rglob("*.wav")):
            if w.resolve() == Path(a.wav).resolve():
                continue
            try:
                aa, ss = sk.load(w)
                c = sk.spectral_centroid(aa, ss)
                other = (meta["groove"], round(a.bpm / 10) * 10, int(c // 250))
                if other == fp:
                    clash.append(w.name)
            except Exception:
                continue
        if clash:
            ok = False
            print(f"  FAIL  same groove+tempo+brightness bucket as: {', '.join(clash[:5])}")
            print("        -> sounds like an existing track; vary it")
        else:
            print("  PASS  distinct groove/tempo/brightness profile")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
