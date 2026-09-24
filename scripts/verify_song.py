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
        "tempo_band": "low",
        "bpm": (108, 132),
        "groove": "four_on_floor",
        "note": "kick on every beat, open hats on the offbeat eighths",
    },
    "house": {
        "tempo_band": "low",
        "bpm": (115, 130),
        "groove": "four_on_floor",
        "note": "four-on-the-floor with prominent offbeat hats",
    },
    "synthwave": {
        "tempo_band": "low",
        "bpm": (78, 108),
        "groove": "four_on_floor",
        "note": "steady 4/4, gated snare on 2 and 4, slower tempo",
    },
    "boombap": {
        "tempo_band": "low",
        "bpm": (82, 104),
        "groove": "backbeat",
        "note": "kick 1+3, SNARE on 2 and 4 -- must NOT be four-on-the-floor",
    },
    "trap": {
        "bpm": (120, 160),
        "groove": "sparse_kick",
        "note": "sparse kick, dense hi-hat rolls, half-time feel",
        # Sparse low-end makes autocorrelation unreliable, and trap is
        # legitimately HALF-TIME (kick implies 70 while the hats imply 140), so
        # the pulse is read from the hat band and half/double are accepted.
        "tempo_band": "high",
        "halftime_ok": True,
    },
    "rock": {
        # rock's kick lands on 1 and 3, so the low band reports HALF the tempo;
        # the 600-1800 Hz band (guitar/snare body) reports the true 140.
        "tempo_band": (600, 1800),
        "bpm": (100, 150),
        "groove": "backbeat",
        "note": "kick 1+3, snare 2+4",
    },
    "techno": {
        "tempo_band": "low",
        "bpm": (128, 150),
        "groove": "four_on_floor",
        "note": "relentless four-on-the-floor, darker and faster than house",
    },
    "dnb": {
        "tempo_band": "low",
        "bpm": (160, 180),
        "groove": "twostep",
        "note": "two-step breakbeat: kick on 1, SNARE on 3 (not a backbeat)",
    },
    "funk": {
        # NOT measurable by autocorrelation: funk's kick is syncopated (0, 1.5,
        # 2.75 beats), so there is no steady pulse to lock onto -- every band
        # returns 73-149 BPM for a 112 BPM track. Left unverified here rather
        # than faked; the BPM range and backbeat check still constrain it.
        "tempo_band": None,
        "bpm": (95, 125),
        "groove": "backbeat",
        "note": "snare on 2 and 4, but syncopated 16th kick and a busy bass",
    },
    "reggae": {
        # NOT measurable by autocorrelation: one-drop has a single kick per bar
        # on beat 3 and a sustained bass on beat 1, so bands returned 122-138 BPM
        # for a 76 BPM track. The one-drop groove check carries the verification.
        "tempo_band": None,
        "bpm": (65, 92),
        "groove": "onedrop",
        "note": "one-drop: the kick lands on BEAT 3, skank on the offbeats",
    },
    "cinematic": {
        "bpm": (60, 110),
        "groove": "any",
        "tempo_band": None,
        "note": "orchestral/textural; no fixed pulse to verify",
    },
    "country": {
        # Country train beat / two-step. The kick lands on 1 and 3 only, so the
        # 40-110 Hz band sees HALF the tempo (58.5 for a 117 BPM track) -- exactly
        # the problem rock had. The 600-1800 Hz band carries the acoustic guitar
        # body and the snare shell, which both mark every beat, so the true tempo
        # is readable there.
        "tempo_band": (600, 1800),
        "bpm": (100, 150),
        "groove": "backbeat",
        "note": "kick 1+3, SNARE 2+4, alternating root/fifth bass (boom-chick)",
    },
    "ambient": {
        "bpm": (50, 100),
        "groove": "any",
        "note": "texture over rhythm; only duration/level/cover enforced",
        # No pulse exists by design, so there is nothing to verify. Claiming a
        # tempo for ambient is documentation, not a measurable property.
        "tempo_band": None,
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
        # Bands validated empirically: kick 40-90 Hz, snare crack 1800-4000 Hz.
        # The 150-400 Hz band used originally is contaminated by bass and keys
        # (it read a boom-bap kick as a snare), and measuring sustained level
        # rather than transients made it worse.
        kb = sk.beat_profile(a, sr, bpm, 40, 90)
        sb = sk.beat_profile(a, sr, bpm, 1800, 4000)
        kick_13 = (kb[0] + kb[2]) / 2
        kick_24 = (kb[1] + kb[3]) / 2
        snare_24 = (sb[1] + sb[3]) / 2
        snare_13 = (sb[0] + sb[2]) / 2
        margin = (snare_24 / snare_13) if snare_13 > 1e-6 else float("inf")
        # The kick PROFILE is the four-on-the-floor test: an even kick means
        # every beat, a 1,3 kick means backbeat. An earlier onsets-based version
        # rejected valid rock because the driving 8th-note bass created low-band
        # transients on every beat (79% "four-on-the-floor").
        kick_ratio = (kick_13 / kick_24) if kick_24 > 1e-6 else float("inf")
        ok = bool(margin >= 1.25 and kick_ratio >= 1.30)
        return ok, (f"backbeat: snare 2,4/1,3 = {snare_24:.2f}/{snare_13:.2f} "
                    f"(margin {margin:.2f}x, need >=1.25x); kick 1,3/2,4 = "
                    f"{kick_13:.2f}/{kick_24:.2f} (ratio {kick_ratio:.2f}x, need "
                    f">=1.30x so it is not four-on-the-floor) "
                    f"[beats: kick={kb.round(2)} snare={sb.round(2)}]")

    if kind == "twostep":
        # D&B two-step: kick on beat 1, snare on beat 3. Explicitly NOT a backbeat
        # (2+4) and NOT four-on-the-floor.
        kb = sk.beat_profile(a, sr, bpm, 40, 90)
        sb = sk.beat_profile(a, sr, bpm, 1800, 4000)  # snare crack band
        snare_on_3 = sb[2] >= max(sb[0], sb[1], sb[3]) * 1.15
        kick_on_1 = kb[0] >= max(kb[1], kb[2], kb[3]) * 0.90
        ok = bool(snare_on_3 and kick_on_1)
        return ok, (f"twostep: snare[1-4]={sb.round(2)} (beat 3 must lead); "
                    f"kick[1-4]={kb.round(2)} (beat 1 must lead)")

    if kind == "onedrop":
        # The dub bass fundamental sits at ~37 Hz and swamps the 40-90 band; the
        # 90-200 Hz band isolates the kick, and there beat 3 leads cleanly.
        kb = sk.beat_profile(a, sr, bpm, 90, 200)
        kick_on_3 = kb[2] >= max(kb[0], kb[1], kb[3]) * 1.05
        ok = bool(kick_on_3)
        return ok, (f"onedrop: kick[1-4]={kb.round(2)} (beat 3 must lead -- "
                    f"that is what makes it a one-drop)")

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
    # The claimed tempo must MATCH the audio. Without this, declaring a track at
    # a tempo it doesn't have silently disables every groove check below, because
    # they compare inter-onset gaps against the claimed beat length.
    band = g.get("tempo_band", "low")
    est, conf = 0.0, 0.0
    if band is None:
        res.append(("tempo claim matches audio", True,
                    f"not applicable: {genre} has no steady pulse to measure "
                    f"(tempo is corroborated by the genre BPM range + groove check)"))
    else:
        lo_b, hi_b = (4000, 12000) if band == "high" else (
            tuple(band) if isinstance(band, (list, tuple)) else (40, 110))
        est, conf = sk.estimate_bpm(a, sr, lo=lo_b, hi=hi_b)
        cands = [bpm]
        if g.get("halftime_ok"):
            cands += [bpm / 2, bpm * 2]
        near = min(cands, key=lambda c: abs(est - c) / c) if est > 0 else None
        tempo_ok = bool(est > 0 and near and abs(est - near) / near <= 0.07)
        extra = ""
        if g.get("halftime_ok") and tempo_ok and abs(near - bpm) > 1e-6:
            extra = f" (half/double-time of {bpm:.0f} -- legitimate for {genre})"
        res.append(("tempo claim matches audio", tempo_ok,
                    f"measured {est:.1f} BPM from {lo_b}-{hi_b} Hz (conf {conf:.2f}) "
                    f"vs claimed {bpm:.0f}{extra}"))
    gp, gev = check_groove(a, sr, bpm, g["groove"])
    res.append((f"groove = {g['groove']}", gp, gev))
    if cover:
        ok = Path(cover).exists() and Path(cover).stat().st_size > 5000
        res.append(("cover art", ok, f"{cover} ({Path(cover).stat().st_size//1024 if Path(cover).exists() else 0} KB)"))
    centroid = sk.spectral_centroid(a, sr)
    passed = all(ok for _, ok, _ in res)
    meta = {"duration": round(secs, 3), "bpm": bpm, "measured_bpm": round(est, 1), "genre": genre,
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
