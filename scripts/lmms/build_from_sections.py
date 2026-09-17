#!/usr/bin/env python3
"""build_from_sections.py — real LMMS-synthesized track, assembled from sections.

WHY THIS DESIGN
---------------
Verified against LMMS 1.2.2 on this box:

  WORKS  : a project with ONE BB track and ONE pattern renders with CORRECT note
           timing (calibrated: a note written at "bar 7" lands at 13.33s at
           126 BPM, exactly right).
  BROKEN : several BB tracks with <bbtco> at different song positions do NOT
           render -- only the first section sounds and LMMS warns
           "Track::getTCO(3), but TCO 3 doesn't exist". Placement is ignored.
  BROKEN : a single long pattern (32 bars) renders only ~17 bars. Neither
           pattern len, bbtco len, timeline lp1pos (tested at 1x/2x/4x) nor
           mastervol changes the truncation.

So the ONE reliable primitive is: one section in, one correct render out. This
script uses it for what it does well and assembles the arrangement by
concatenating rendered sections -- ordinary studio practice (render sections,
edit them together).

Consequence, stated plainly: the sound synthesis, instrumentation and note
sequencing are LMMS's. The section EDIT is done with ffmpeg, so this is
"LMMS-rendered, assembled outside", not "a single LMMS project".

Usage: python3 scripts/lmms/build_from_sections.py [--bpm 126] [--out DIR]
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "lmms"))
sys.path.insert(0, str(REPO / "scripts"))
from mkproj import build, section, inst_track, TPB   # noqa: E402

# authored section level (project mastervol). Needed because each section is a
# SEPARATE render, so relative balance between sections is otherwise lost.
SECTION_INTENT = {"intro": 0.32, "main": 0.78, "DIP": 0.26, "build": 0.62,
                  "CLIMAX": 1.00, "outro": 0.30}
# starting gains; the calibration pass corrects these so the measured LUFS
# matches SECTION_INTENT (a project's mastervol does not translate linearly to
# perceived loudness, and content loudness differs per section)
SECTION_MASTERVOL = {k: max(1, min(100, int(round(100 * v ** 0.7))))
                     for k, v in SECTION_INTENT.items()}

import numpy as np   # noqa: E402
import wave          # noqa: E402
import albumkit as ak   # noqa: E402


def _env():
    import os
    e = dict(os.environ)
    e["QT_QPA_PLATFORM"] = "offscreen"     # LMMS is Qt; no display on this box
    return e


def render_mmp(mmp: Path, out: Path) -> Path:
    subprocess.run(["lmms", "render", str(mmp), "-o", str(out)],
                   check=True, env=_env(), capture_output=True, timeout=180)
    if not out.exists():
        raise RuntimeError(f"LMMS wrote no output for {mmp}")
    return out


def wav_dur(p: Path) -> float:
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


# ── the arrangement: 6 sections, 32 bars ────────────────────────────────────
# beats are divided by 4 so positions are in BARS (the earlier bug that made a
# 4-beat figure span 4 bars).
def b(seq):
    return [(k, p / 4.0, l / 4.0, v) for k, p, l, v in seq]


KICK = lambda: b([(36, 0, 0.12, 100), (36, 1, 0.12, 100), (36, 2, 0.12, 100), (36, 3, 0.12, 100)])
KICKP= lambda: b([(36, 0, 0.12, 100), (36, 1, 0.12, 100), (36, 2, 0.12, 100), (36, 3, 0.12, 100), (36, 2.75, 0.10, 60)])
HATS = lambda v=52: b([(84, t, 0.06, v if t * 2 % 2 == 0 else v * 0.55) for t in (0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5)])
BASS = lambda v=90: b([(45, 0, 0.32, v), (45, 0.75, 0.2, v), (43, 1.5, 0.32, v), (45, 2, 0.32, v), (48, 2.75, 0.2, v), (43, 3.25, 0.32, v)])
KEYS = lambda v=40: b([(57 + iv, t, 1.6, v) for t in (0.0, 2.0) for iv in (0, 4, 7, 11)])
PAD  = lambda v=38: b([(57, 0, 3.6, v), (64, 0, 3.6, v), (69, 0, 3.6, v)])
LEAD = lambda v=78: b([(69 + iv, t, 0.34, v) for t, iv in ((0, 0), (0.75, 3), (1.5, 7), (2, 10), (2.75, 7), (3.5, 3))])
LEADH= lambda v=88: b([(81 + iv, t, 0.34, v) for t, iv in ((0, 0), (0.75, 3), (1.5, 7), (2, 10), (2.75, 7), (3.5, 3))])

# (name, bars, [(voice, instrument, bars-of-notes-generator, kwargs, track-vol)])
SECTIONS = [
    ("intro", 4, [("kick", "kicker", KICK, {}, 66), ("hat", "tripleosc", lambda: HATS(46), {"v1": 60}, 40),
                  ("bass", "lb302", lambda: BASS(74), {"wave": 1}, 54)]),
    ("main", 8, [("kick", "kicker", KICKP, {}, 68), ("hat", "tripleosc", lambda: HATS(58), {"v1": 62}, 42),
                 ("bass", "lb302", lambda: BASS(92), {"wave": 1}, 58),
                 ("keys", "tripleosc", lambda: KEYS(40), {"v1": 40, "v2": 30, "c1": 12}, 46),
                 ("lead", "tripleosc", lambda: LEAD(76), {"v1": 92, "v2": 36, "c1": 12}, 50)]),
    ("DIP", 4, [("pad", "tripleosc", lambda: PAD(34), {"v1": 44, "v2": 26, "c1": 12}, 40),
                ("hat", "tripleosc", lambda: HATS(20), {"v1": 50}, 34)]),
    ("build", 4, [("kick", "kicker", KICK, {}, 68), ("hat", "tripleosc", lambda: HATS(54), {"v1": 62}, 42),
                  ("bass", "lb302", lambda: BASS(88), {"wave": 1}, 56),
                  ("keys", "tripleosc", lambda: KEYS(38), {"v1": 40, "v2": 30, "c1": 12}, 46)]),
    ("CLIMAX", 10, [("kick", "kicker", KICKP, {}, 70), ("hat", "tripleosc", lambda: HATS(70), {"v1": 64}, 44),
                    ("bass", "lb302", lambda: BASS(100), {"wave": 1}, 60),
                    ("keys", "tripleosc", lambda: KEYS(46), {"v1": 42, "v2": 32, "c1": 12}, 48),
                    ("lead", "tripleosc", lambda: LEADH(88), {"v1": 96, "v2": 38, "c1": 12}, 52)]),
    ("outro", 2, [("pad", "tripleosc", lambda: PAD(30), {"v1": 42, "c1": 12}, 38)]),
]

BPM = 126


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "content" / "milkups" / "album-lmms"))
    ap.add_argument("--keep-projects", action="store_true")
    a = ap.parse_args()
    outd = Path(a.out); (outd / "sections").mkdir(parents=True, exist_ok=True)
    projd = outd / "projects"; projd.mkdir(exist_ok=True)

    def render_all():
        pieces, expect = [], []
        for name, bars, voices in SECTIONS:
            tracks = []
            for vn, instr, gen, kw, vol in voices:
                notes = [n for i in range(bars) for n in [(k, i + p, l, v) for k, p, l, v in gen()]]
                tracks.append(inst_track(vn, vol, instr, notes, bars, **kw))
            mmp = projd / f"{name}.mmp"
            build(BPM, [section(name, tracks, 0, bars)], str(mmp), bars,
                  mastervol=SECTION_MASTERVOL[name])
            w = render_mmp(mmp, outd / "sections" / f"{name}.wav")
            pieces.append(w); expect.append((name, bars, wav_dur(w) / (4 * 60 / BPM)))
        return pieces, expect

    import math
    print("calibrating section levels (targets are perceptual, LUFS-based)")
    for it in range(4):
        pieces, expect = render_all()
        rel, ref = {}, None
        L = {}
        for (name, bars, _g), w in zip(expect, pieces):
            L[name] = ak.lufs(w)
        ref = max(v for v in L.values() if v is not None)
        worst = 0.0
        for name in L:
            want = 20 * math.log10(SECTION_INTENT[name])
            got = L[name] - ref
            err = want - got
            worst = max(worst, abs(err))
            if it < 3:
                SECTION_MASTERVOL[name] = int(max(1, min(100,
                    round(SECTION_MASTERVOL[name] * (10 ** (err / 20))))))
        print(f"  pass {it+1}: worst error {worst:.1f} dB | mv=" +
              ", ".join(f"{k}:{v}" for k, v in SECTION_MASTERVOL.items()))
        if worst <= 1.5:
            break
    for name, bars, got in expect:
        print(f"    {name:<7} {bars:>2} bars -> {got:4.1f} bars, {L[name]:.1f} LUFS")

    # trim each section to its intended length, then concatenate
    trim = outd / "sections"
    for (name, bars, _g), w in zip(expect, pieces):
        tgt = bars * 4 * 60 / BPM
        outp = trim / f"{name}_t.wav"
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(w),
                        "-t", f"{tgt:.4f}", str(outp)], check=True)
        print(f"    trim {name:<7} -t {tgt:6.2f}s -> {wav_dur(outp):6.2f}s")
    listf = outd / "concat.txt"
    listf.write_text("".join(f"file '{(trim / f'{name}_t.wav').as_posix()}'\n" for name, _b, _g in expect))
    final = outd / "lmms-track.wav"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat",
                    "-safe", "0", "-i", str(listf), "-c", "copy", str(final)], check=True)
    total = sum(b for _n, b, _g in expect)
    print(f"\nassembled: {final} | {wav_dur(final):.2f}s ({total} bars intended)")

    decl = [(n, b, SECTION_INTENT[n]) for n, b, _v in SECTIONS]
    ok, checks = ak.verify_shape_lufs(final, BPM, decl)
    print("\nLUFS-BASED SHAPE VERIFICATION")
    for n, g, e in checks:
        print(f"  {'PASS' if g else 'FAIL'}  {n:<34} {e}")
    print(f"  contour: {ak.contour_summary(final, BPM, total)}")
    print(f"  -> {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
