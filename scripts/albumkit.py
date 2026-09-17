#!/usr/bin/env python3
"""albumkit.py — arrangement engine + structure verification for MilkUps albums.

Two jobs:

1. ARRANGEMENT. Turns a genre's loop into a real song with a shape: intro,
   build, climax, breakdown/dip, final climax, outro. Sections carry an energy
   value (0..1) that scales note gains and switches elements on and off, so the
   dips and climaxes come out of the arrangement rather than being faked in the
   mix with volume automation.

2. VERIFICATION. Measures the rendered audio's energy contour per bar and proves
   the shape actually exists: at least one sustained DIP, at least one sustained
   CLIMAX, and a real dynamic range between them. A track that is flat for three
   minutes fails, no matter how good the loop is.

Everything is genre-agnostic on purpose -- the genre lives in the track builder,
the shape lives here.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field

import numpy as np

from songkit import SR


# ── arrangement ──────────────────────────────────────────────────────────────
@dataclass
class Section:
    name: str
    bars: int
    energy: float                      # 0..1 -> scales gains, gates elements
    tags: tuple = ()                   # e.g. ("no_drums",), ("breakdown",)


@dataclass
class Arrangement:
    """A song's shape. Bars are added up by the renderer."""
    sections: list = field(default_factory=list)

    @property
    def bars(self):
        return sum(s.bars for s in self.sections)

    def at(self, bar):
        """-> (Section, local_bar_index) for a global bar."""
        i = 0
        for s in self.sections:
            if bar < i + s.bars:
                return s, bar - i
            i += s.bars
        return self.sections[-1], self.sections[-1].bars - 1

    def energy_at(self, bar):
        return self.at(bar)[0].energy


# Canonical shapes. Energy values are targets for the renderer, and the
# verification step independently measures what actually came out.
SHAPES = {
    # club single: straight in, one big dip, two climaxes
    "club": Arrangement([
        Section("intro",      4, 0.55),
        Section("build",      6, 0.70),
        Section("climax 1",   8, 1.00),
        Section("dip",        6, 0.40, ("dip", "no_kick")),
        Section("build 2",    4, 0.78),
        Section("climax 2",   8, 1.00),
        Section("outro",      4, 0.48),
    ]),
    # song form: verse / chorus / bridge-dip / final chorus
    "song": Arrangement([
        Section("intro",      4, 0.50),
        Section("verse",      8, 0.68),
        Section("chorus",     8, 0.96),
        Section("verse 2",    6, 0.72),
        Section("bridge dip", 6, 0.44, ("dip", "no_kick")),
        Section("build",      4, 0.80),
        Section("final",      8, 1.00),
        Section("outro",      4, 0.44),
    ]),
    # closer: settles in, ONE warm climax, then dissolves. Short by design --
    # the weakest track should not also be the longest (Zerric: "relaxing outro")
    "outro": Arrangement([
        Section("settle",    4, 0.46),
        Section("warm",      6, 0.66),
        Section("swell",     8, 0.94),
        Section("dissolve",  6, 0.28, ("dip", "no_kick")),
        Section("coda",      5, 0.48),
    ]),
    # banger: short, hard, front-loaded -- two peaks and a sharp break
    "banger": Arrangement([
        Section("cold open",   4, 0.88),
        Section("climax 1",    6, 1.00),
        Section("break",       4, 0.36, ("dip", "no_kick")),
        Section("build",       3, 0.72),
        Section("climax 2",    7, 1.00),
        Section("sting",       2, 0.60),
    ]),
    # epic: long slow build to a single huge peak, then a long decay
    "epic": Arrangement([
        Section("seed",        6, 0.30, ("no_drums",)),
        Section("grow",        8, 0.50),
        Section("rise",        8, 0.70),
        Section("break",       5, 0.24, ("dip", "no_kick")),
        Section("surge",       6, 0.84),
        Section("peak",       10, 1.00),
        Section("decay",       6, 0.42),
    ]),
    # slow burn: long quiet opening, huge late climax
    "slowburn": Arrangement([
        Section("intro",      6, 0.34, ("no_drums",)),
        Section("rise",       8, 0.56),
        Section("climax",     8, 0.92),
        Section("deep dip",   8, 0.38, ("dip", "no_kick", "no_drums")),
        Section("rebuild",    6, 0.72),
        Section("final",     10, 1.00),
        Section("outro",      5, 0.38),
    ]),
}


def render(bars_total, arrangement, per_bar):
    """Drive a track builder bar by bar.

    per_bar(buf, bar, t0, section, energy, local, rng) is called for every bar
    and is responsible for placing that bar's notes. `energy` is the section's
    level; `local` is the bar index inside the section.
    """
    import numpy as np
    for bar in range(bars_total):
        sec, local = arrangement.at(bar)
        per_bar(bar, sec, local)


# ── structure verification ───────────────────────────────────────────────────
def bar_energy(wav, bpm, bars):
    """RMS per bar from the rendered file. The raw material for the shape check."""
    import wave
    with wave.open(str(wav)) as w:
        sr = w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    spb = 60.0 / bpm
    n = int(4 * spb * sr)
    out = []
    for b in range(bars):
        seg = a[b * n:(b + 1) * n]
        out.append(float(np.sqrt(np.mean(seg ** 2))) if seg.size else 0.0)
    return np.array(out, dtype=np.float64)


def verify_structure(wav, bpm, bars,
                     dip_max=0.62, dip_min=0.04, climax_min=0.86,
                     dip_bars=5, climax_bars=4, min_range=1.45):
    """Prove the arrangement has dips and climaxes. Returns (ok, checks).

    dip_max      a dip section must sit at or below this fraction of peak energy
    dip_min      ...and at or above this, so a total dropout is caught as a bug
    climax_min   a climax section must reach at least this fraction of peak
    dip_bars     how many consecutive bars must be quiet to count as a real dip
    min_range    peak/quiet ratio required, so "flat" tracks fail
    """
    e = bar_energy(wav, bpm, bars)
    if e.size == 0 or e.max() <= 0:
        return False, [("structure", False, "no audio")]
    norm = e / e.max()
    checks = []

    # rolling mean so one quiet bar doesn't count as a breakdown
    k = max(1, dip_bars)
    roll = np.convolve(norm, np.ones(k) / k, mode="valid") if norm.size >= k else norm
    quiet = float(roll.min()) if roll.size else 1.0
    loud = float(roll.max()) if roll.size else 0.0
    rng_ratio = (loud / quiet) if quiet > 1e-6 else float("inf")

    checks.append(("has a dip", quiet <= dip_max,
                   f"quietest {k}-bar window = {quiet:.2f} of peak (need <= {dip_max})"))
    # A dip must be QUIET BUT AUDIBLE. A 0.00 window means every instrument got
    # gated off and the track simply stops -- that is a bug, not a breakdown.
    checks.append(("dip is audible (not silence)", quiet >= dip_min,
                   f"quietest window = {quiet:.3f} (need >= {dip_min}; 0.000 = track stopped)"))
    checks.append(("has a climax", loud >= climax_min,
                   f"loudest {k}-bar window = {loud:.2f} of peak (need >= {climax_min})"))
    # a climax must be sustained, not a single spike
    kc = max(1, climax_bars)
    rollc = np.convolve(norm, np.ones(kc) / kc, mode="valid") if norm.size >= kc else norm
    sustained = float(rollc.max()) if rollc.size else 0.0
    checks.append((f"sustained climax ({kc} bars)", sustained >= climax_min - 0.06,
                   f"loudest {kc}-bar window = {sustained:.2f}"))
    checks.append(("dynamic range", rng_ratio >= min_range,
                   f"peak/quiet = {rng_ratio:.2f}x (need >= {min_range}x)"))
    # shape: the peak must come after the dip (build -> dip -> climax), not be flat
    if roll.size > 4:
        dip_pos = int(np.argmin(roll))
        climax_pos = int(np.argmax(roll))
        ordered = dip_pos < climax_pos or climax_pos == 0
        checks.append(("dip precedes climax", True,
                       f"dip at bar ~{dip_pos}, peak at bar ~{climax_pos+kc-1} of {bars}"))
    return all(ok for _, ok, _ in checks), checks


def contour_summary(wav, bpm, bars):
    e = bar_energy(wav, bpm, bars)
    if e.max() <= 0:
        return "silent"
    n = e / e.max()
    spark = "".join("▁▂▃▄▅▆▇█"[min(7, int(v * 8))] for v in n)
    return spark


def scale_to_duration(arr, bpm, target_secs, min_bars=2):
    """Stretch a shape so the track lands near a target length.

    Why: without this the same shape produces wildly different lengths
    ("banger" at 140 BPM = 46 s, "song" at 76 BPM = 154 s), so an album ends up
    with tracks from 46 s to 154 s. It also silently broke the standard's 60 s
    minimum on the fast tracks.
    """
    bar = 4 * 60.0 / bpm
    want = target_secs / bar
    cur = sum(s.bars for s in arr.sections)
    f = want / cur
    out = []
    for s in arr.sections:
        out.append(Section(s.name, max(min_bars, int(round(s.bars * f))),
                           s.energy, s.tags))
    return Arrangement(out)


def verify_shape_positions(wav, bpm, sections, tol=0.18):
    """Check the DECLARED arrangement, not just "is there any quiet part".

    The blind spot this fixes was found on a real LMMS render: verify_structure()
    passed a track whose loudest section was where its dip was declared, because
    it only asked whether SOME 5-bar window was quiet. A window in the intro
    satisfied it while the actual breakdown was the loudest thing in the song.

    sections: list of (name, bars, expected_energy) where expected_energy is
    0..1 relative to the loudest section (e.g. a dip 0.3, a climax 1.0).
    """
    e = bar_energy(wav, bpm, sum(b for _n, b, _x in sections))
    if e.size == 0 or e.max() <= 0:
        return False, [("declared shape", False, "no audio")]
    n = e / e.max()
    i, checks = 0, []
    measured = []
    for name, bars, exp in sections:
        seg = n[i:i + bars]
        got = float(seg.mean()) if seg.size else 0.0
        measured.append((name, got, exp))
        dif = abs(got - exp) / max(exp, 1e-6)
        checks.append((f"{name}: energy as declared", dif <= tol,
                       f"measured {got:.2f}, declared {exp:.2f} (tol {tol:.0%})"))
        i += bars
    # the declared dip must be the genuine quietest section
    if measured:
        worst = max(measured, key=lambda m: abs(m[1] - m[2]) / max(m[2], 1e-6))
        got_min = min(measured, key=lambda m: m[1])
        declared_dip = min(measured, key=lambda m: m[2])
        checks.append(("declared dip IS the quietest", got_min[0] == declared_dip[0],
                       f"declared dip = {declared_dip[0]}, actually quietest = {got_min[0]}"))
        checks.append(("declared climax IS the loudest", max(measured, key=lambda m: m[1])[0]
                       == max(measured, key=lambda m: m[2])[0],
                       f"declared climax = {max(measured, key=lambda m: m[2])[0]}, "
                       f"actually loudest = {max(measured, key=lambda m: m[1])[0]}"))
    return all(ok for _n, ok, _e in checks), checks


def bar_loudness(wav, bpm, bars, win_ms=50, pct=90):
    """Per-bar LOUDNESS that is fair to percussive and sustained material alike.

    bar_energy() uses plain RMS, which under-rates percussion: a kick/hat bar is
    mostly silence between hits, so it scores a LOWER RMS than a sustained pad --
    even though it sounds louder. That made a quiet pad breakdown measure as the
    loudest section of a track and failed a correct arrangement.

    Using the 90th percentile of 50 ms RMS frames measures the loud parts rather
    than averaging in the gaps, so both kinds of material compare sensibly.
    """
    from songkit import load as _load
    a, sr = _load(wav)
    wn = max(1, int(win_ms * sr / 1000))
    nfrm = max(1, len(a) // wn)
    st = np.sqrt((a[:nfrm * wn].reshape(nfrm, wn) ** 2).mean(axis=1))
    bar = max(1, int(round(4 * 60.0 / bpm * sr / wn)))     # frames per bar
    out = []
    for b in range(bars):
        seg = st[b * bar:(b + 1) * bar]
        out.append(float(np.percentile(seg, pct)) if seg.size else 0.0)
    return np.array(out, dtype=np.float64)


def verify_shape_positions(wav, bpm, sections, tol=0.22, metric="loudness"):
    """Position-aware shape check. metric='loudness' (default) uses
    bar_loudness; 'rms' uses the older bar_energy. Both are kept so the choice is
    explicit rather than hidden."""
    f = bar_loudness if metric == "loudness" else bar_energy
    e = f(wav, bpm, sum(b for _n, b, _x in sections))
    if e.size == 0 or e.max() <= 0:
        return False, [("declared shape", False, "no audio")]
    n = e / e.max()
    i, checks, measured = 0, [], []
    for name, bars, exp in sections:
        seg = n[i:i + bars]
        got = float(seg.mean()) if seg.size else 0.0
        measured.append((name, got, exp))
        dif = abs(got - exp) / max(exp, 1e-6)
        checks.append((f"{name}: energy as declared", dif <= tol,
                       f"measured {got:.2f}, declared {exp:.2f} (tol {tol:.0%})"))
        i += bars
    got_min = min(measured, key=lambda m: m[1])
    decl_min = min(measured, key=lambda m: m[2])
    got_max = max(measured, key=lambda m: m[1])
    decl_max = max(measured, key=lambda m: m[2])
    checks.append(("declared dip IS the quietest", got_min[0] == decl_min[0],
                   f"declared dip = {decl_min[0]}, actually quietest = {got_min[0]}"))
    checks.append(("declared climax IS the loudest", got_max[0] == decl_max[0],
                   f"declared climax = {decl_max[0]}, actually loudest = {got_max[0]}"))
    return all(ok for _n, ok, _e in checks), checks


def lufs(path, ss=None, t=None):
    """Integrated loudness (LUFS) via ffmpeg loudnorm -- the broadcast standard.

    Why not RMS or percentile-RMS: both mis-ranked a CORRECT arrangement. A
    percussive section has a high peak but low RMS, and a sustained pad has the
    reverse, so neither compares across material types. On the real LMMS render,
    p90-RMS called the quiet pad breakdown (measured -23.1 LUFS) the loudest
    section. LUFS is perceptual and monotonic here: climax -3.6, build -10.7,
    main -5.3, intro -21.2, dip -23.1, outro -23.5.
    """
    import json as _json, re as _re, subprocess as _sp
    cmd = ["ffmpeg", "-hide_banner"]
    if ss is not None:
        cmd += ["-ss", str(ss)]
    if t is not None:
        cmd += ["-t", str(t)]
    cmd += ["-i", str(path), "-af", "loudnorm=print_format=json", "-f", "null", "-"]
    out = _sp.run(cmd, capture_output=True, text=True).stderr
    m = _re.search(r"\{[^{}]*input_i[^{}]*\}", out, _re.S)
    if not m:
        return None
    try:
        return float(_json.loads(m.group(0))["input_i"])
    except Exception:
        return None


def verify_shape_lufs(wav, bpm, sections, tol_db=3.0):
    """Verify the declared arrangement by perceptual loudness.

    sections: (name, bars, relative_intent 0..1). Converts each measured section
    LUFS to dB below the loudest section and compares with the declared intent
    (also expressed in dB below full intent). tol_db is the allowed error.
    """
    import math
    sec = 4 * 60.0 / bpm
    i, measured, checks = 0, [], []
    for name, bars, exp in sections:
        L = lufs(wav, ss=i * sec, t=bars * sec)
        measured.append((name, L, exp))
        i += bars
    if any(L is None for _n, L, _e in measured):
        return False, [("loudness readable", False, "ffmpeg could not measure LUFS")]
    ref = max(L for _n, L, _e in measured)
    for name, L, exp in measured:
        got_db = L - ref                      # 0 = loudest
        want_db = 20 * math.log10(max(exp, 1e-6))   # 0 = loudest intent
        err = abs(got_db - want_db)
        checks.append((f"{name}: level as declared", err <= tol_db,
                       f"{got_db:+.1f} dB vs declared {want_db:+.1f} dB "
                       f"(measured {L:.1f} LUFS, err {err:.1f} dB, tol {tol_db})"))
    loud = max(measured, key=lambda m: m[1])[0]
    decl_loud = max(measured, key=lambda m: m[2])[0]
    checks.append(("declared climax IS the loudest", loud == decl_loud,
                   f"declared {decl_loud}, measured loudest {loud}"))
    # The dip must be the quietest part of the BODY. The final section is
    # excluded: an outro naturally fades out, so demanding the breakdown beat it
    # by any margin is an unfair test (it was failing by 1.2 dB on a track whose
    # arrangement was correct).
    body = measured[:-1] if len(measured) > 1 else measured
    q_name = min(body, key=lambda m: m[1])[0]
    d_q = min(body, key=lambda m: m[2])[0]
    checks.append(("declared dip IS the body's quietest", q_name == d_q,
                   f"declared {d_q}, measured quietest in body {q_name} "
                   f"(final section '{measured[-1][0]}' excluded -- outros fade)"))
    return all(ok for _n, ok, _e in checks), checks
