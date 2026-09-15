#!/usr/bin/env python3
"""MilkUps — TRACKER CUT. Fresh chiptune/PSG tracks authored as real FastTracker II
.XM modules in pure Python, rendered through ffmpeg libopenmpt, mastered to a
uniform -14 LUFS, encoded MP3 320k CBR.

Chain: numpy samples -> .xm module -> ffmpeg (libopenmpt) -> WAV -> loudnorm master -> MP3

    python3 scripts/build_milkups_tracker_cut.py
"""
from __future__ import annotations
import json, math, os, re, subprocess, sys, hashlib, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import numpy as np
from build_milkups_album import make_song, xm_write

OUT   = ROOT / "content" / "milkups" / "tracker"
XM    = OUT / "xm"; WAV = OUT / "wav"; MP3 = OUT / "audio"
for d in (XM, WAV, MP3): d.mkdir(parents=True, exist_ok=True)

TARGET_LUFS, TARGET_TP, TARGET_LRA = -14.0, -1.0, 9.0

# 8 fresh tracker tracks — varied tempo, key and mood so variety is audible
TRACKS = [
    {"n": 1, "title": "Cold Aisle Chip",  "slug": "01-cold-aisle-chip",  "bpm": 168, "root": 45, "bars": 28, "seed": 101},
    {"n": 2, "title": "Carton Static",    "slug": "02-carton-static",    "bpm": 152, "root": 48, "bars": 28, "seed": 113},
    {"n": 3, "title": "Expiration Date",  "slug": "03-expiration-date",  "bpm": 140, "root": 43, "bars": 26, "seed": 127},
    {"n": 4, "title": "Dairy Case Dreams","slug": "04-dairy-case-dreams","bpm": 176, "root": 50, "bars": 30, "seed": 139},
    {"n": 5, "title": "2% Signal",        "slug": "05-2pct-signal",      "bpm": 132, "root": 41, "bars": 24, "seed": 151},
    {"n": 6, "title": "Shelf Life",       "slug": "06-shelf-life",       "bpm": 160, "root": 47, "bars": 28, "seed": 163},
    {"n": 7, "title": "Homogenized",      "slug": "07-homogenized",      "bpm": 128, "root": 44, "bars": 24, "seed": 179},
    {"n": 8, "title": "Last Carton",      "slug": "08-last-carton",      "bpm": 184, "root": 52, "bars": 32, "seed": 191},
]


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def render_xm_libopenmpt(xm_path: Path, wav_path: Path) -> None:
    """Authentic tracker playback via ffmpeg's libopenmpt decoder."""
    r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
             "-i", str(xm_path), "-c:a", "pcm_s16le", str(wav_path)])
    if r.returncode != 0:
        raise RuntimeError(f"libopenmpt render failed: {r.stderr[:300]}")


def measure_pass1(wav: Path) -> dict:
    """loudnorm pass 1 — returns measured values for the linear pass 2."""
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(wav),
             "-af", f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json",
             "-f", "null", "-"])
    blob = r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1]
    return json.loads(blob)


def master_to_mp3(wav: Path, mp3_path: Path) -> dict:
    """Two-pass loudnorm -> MP3 320k CBR, then verify the OUTPUT."""
    m = measure_pass1(wav)
    af = (f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA={TARGET_LRA}"
          f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
          f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
          f":offset={m['target_offset']}:linear=true:print_format=json")
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", str(wav),
             "-af", af, "-c:a", "libmp3lame", "-b:a", "320k", str(mp3_path)])
    if r.returncode != 0:
        raise RuntimeError(f"master/encode failed: {r.stderr[:300]}")
    # verify the encoded file
    r2 = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp3_path),
              "-af", f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json",
              "-f", "null", "-"])
    blob = r2.stderr[r2.stderr.rfind("{"):r2.stderr.rfind("}") + 1]
    out = json.loads(blob)
    return {"in_i": float(m["input_i"]), "in_tp": float(m["input_tp"]),
            "out_i": float(out["input_i"]), "out_tp": float(out["input_tp"]),
            "out_lra": float(out["input_lra"])}


def dur_of(p: Path) -> float:
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(p)])
    return float(r.stdout.strip() or 0)


def build():
    manifest = {"artist": "MilkUps", "cut": "tracker", "engine": "FastTracker II (.xm) -> libopenmpt",
                "master": {"target_lufs": TARGET_LUFS, "target_tp": TARGET_TP, "target_lra": TARGET_LRA},
                "tracks": []}
    print(f"{'#':>2}  {'title':<20} {'xm':>8} {'sec':>7} {'LUFS':>7} {'TP':>6} {'MP3':>9}")
    for t in TRACKS:
        song = make_song(t)
        xm  = XM  / f"{t['slug']}.xm"
        wav = WAV / f"{t['slug']}.wav"
        mp3 = MP3 / f"{t['slug']}.mp3"
        xm_write(t, song, xm)
        render_xm_libopenmpt(xm, wav)
        lm = master_to_mp3(wav, mp3)
        sec = dur_of(mp3)
        rec = {"no": t["n"], "title": t["title"], "slug": t["slug"], "bpm": t["bpm"],
               "xm_bytes": xm.stat().st_size, "seconds": round(sec, 2),
               "lufs": round(lm["out_i"], 2), "true_peak_dbtp": round(lm["out_tp"], 2),
               "lra": round(lm["out_lra"], 2), "mp3_bytes": mp3.stat().st_size,
               "sha256": hashlib.sha256(mp3.read_bytes()).hexdigest()}
        manifest["tracks"].append(rec)
        print(f"{t['n']:>2}  {t['title']:<20} {rec['xm_bytes']:>8} {sec:>7.2f} "
              f"{rec['lufs']:>7.2f} {rec['out_tp'] if False else rec['true_peak_dbtp']:>6.2f} {rec['mp3_bytes']:>9}")
    return manifest


def gate(m):
    fails = []
    for r in m["tracks"]:
        if r["seconds"] < 60:                       fails.append(f"{r['slug']}: {r['seconds']}s < 60s")
        if abs(r["lufs"] - TARGET_LUFS) > 1.0:      fails.append(f"{r['slug']}: {r['lufs']} LUFS off -14 by >1 LU")
        if r["true_peak_dbtp"] > TARGET_TP + 0.3:   fails.append(f"{r['slug']}: TP {r['true_peak_dbtp']} dBTP > -1")
    return fails


def main():
    m = build()
    fails = gate(m)
    m["gate"] = {"passed": not fails, "failures": fails}
    (OUT / "manifest.json").write_text(json.dumps(m, indent=2))
    tl = "\n".join(f"{r['no']:02d} - {r['title']}.mp3 ({r['bpm']} BPM) "
                   f"{int(r['seconds'])//60}:{int(r['seconds'])%60:02d}" for r in m["tracks"])
    (OUT / "tracklist.txt").write_text(f"MILKUPS — TRACKER CUT\n8 tracks\n\n{tl}\n")
    print("\nGATE:", "PASS" if not fails else "FAIL")
    for f in fails: print("  -", f)
    print("manifest:", (OUT / "manifest.json").relative_to(ROOT))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
