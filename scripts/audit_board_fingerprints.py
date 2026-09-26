#!/usr/bin/env python3
"""Measure the live SnowSnakes board's fingerprint components (brightness, tempo)
so a new track can be checked for homogenisation against what is actually published."""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import songkit as sk

BASE = "https://snowsnakes.zerric.xyz/api"
TMP = Path("/tmp/board_audio")
TMP.mkdir(exist_ok=True)


def get(path):
    r = urllib.request.Request(BASE + path, headers={"User-Agent": "Mozilla/5.0 (zdot-cto)"})
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.load(resp)


songs = get("/songs")
rows = []
for s in songs:
    mp3 = TMP / f"{s['id']}.mp3"
    wav = TMP / f"{s['id']}.wav"
    if not mp3.exists():
        try:
            urllib.request.urlretrieve(s["audio_url"], mp3)
        except Exception as e:
            print(f"  !! download {s['id']}: {e}")
            continue
    if not wav.exists():
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                        "-i", str(mp3), "-ac", "1", "-ar", "22050", str(wav)], check=False)
    if not wav.exists():
        continue
    a, sr = sk.load(str(wav))
    cent = sk.spectral_centroid(a, sr)
    est, conf = sk.estimate_bpm(a, sr)
    rows.append({"id": s["id"], "title": s["title"], "author": s.get("author_name"),
                 "secs": round(len(a) / sr, 1), "centroid": round(cent),
                 "bright_bucket": int(cent // 250), "bpm": round(est, 1)})

rows.sort(key=lambda r: r["id"], reverse=True)
print(f"{'id':>3} {'title':<28} {'secs':>6} {'centroid':>9} {'bright_bkt':>10} {'bpm_est':>8}")
for r in rows:
    print(f"{r['id']:>3} {r['title']:<28} {r['secs']:>6} {r['centroid']:>9} "
          f"{r['bright_bucket']:>10} {r['bpm']:>8}")
(Path("/tmp/board_fingerprints.json")).write_text(json.dumps(rows, indent=1))
print("\nsaved /tmp/board_fingerprints.json")
