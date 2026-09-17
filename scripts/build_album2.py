#!/usr/bin/env python3
"""build_album2.py — "COLD OPEN", second MilkUps album.

Six genres that share nothing with COLD CUTS. Reuses the rig from
build_milkups_album_full (shapes, covers, mastering, RNG discipline) and injects
the new genre writers from album2_genres.

Publication target is MilkUps — NOT SnowSnakes. (SnowSnakes is games only.)
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import albumkit as ak
import songkit as sk
import build_milkups_album_full as B
import album2_genres as A2

ALBUM_DIR = ROOT / "content" / "milkups" / "album2"
B.OUT = ALBUM_DIR
B.GENRES.update(A2.NEW_GENRES)
B.ALBUM = "COLD OPEN"

B.PALETTES.update({
    "rock":      ((20, 8, 10),  (230, 60, 50),  (255, 190, 60)),
    "dnb":       ((6, 10, 24),  (0, 200, 255),  (140, 90, 255)),
    "funk":      ((24, 14, 6),  (250, 150, 20), (120, 220, 90)),
    "reggae":    ((8, 20, 14),  (30, 190, 110), (250, 210, 40)),
    "techno":    ((10, 10, 12), (200, 200, 210), (120, 120, 140)),
    "cinematic": ((16, 14, 30), (240, 220, 180), (170, 150, 255)),
})

TRACKS = [
    {"n": 1, "title": "Aisle Anthem",      "genre": "rock",      "bpm": 140, "shape": "banger", "target": 92},
    {"n": 2, "title": "Carton Roll",       "genre": "dnb",       "bpm": 174, "shape": "club",   "target": 86},
    {"n": 3, "title": "Spoiled Funk",      "genre": "funk",      "bpm": 112, "shape": "song",   "target": 96},
    {"n": 4, "title": "Cooler Dub",        "genre": "reggae",    "bpm": 76,  "shape": "song",   "target": 96},
    {"n": 5, "title": "Expiration",        "genre": "techno",    "bpm": 138, "shape": "banger", "target": 88},
    {"n": 6, "title": "Thaw",              "genre": "cinematic", "bpm": 88,  "shape": "epic",   "target": 104},
]
B.TRACKS = TRACKS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=int)
    ap.add_argument("--from", dest="start", type=int, default=1)
    a = ap.parse_args()
    ALBUM_DIR.mkdir(parents=True, exist_ok=True)

    todo = [t for t in TRACKS if (not a.only or t["n"] == a.only) and t["n"] >= a.start]
    report = []
    for spec in todo:
        print(f"\n=== {spec['n']}. {spec['title']}  [{spec['genre']} @ {spec['bpm']} BPM, {spec['shape']}]", flush=True)
        wav, bars, arr = B.render_track(spec)
        cover = B.make_cover(spec, ALBUM_DIR / f"{spec['n']:02d}-cover.png")
        secs = sk.duration(wav)
        ok_s, sres = ak.verify_structure(wav, spec["bpm"], bars)
        spark = ak.contour_summary(wav, spec["bpm"], bars)
        print(f"  {secs:.1f}s | {bars} bars | cover {cover.stat().st_size//1024}KB", flush=True)
        print(f"  shape: {spark}", flush=True)
        for name, good, ev in sres:
            print(f"    {'PASS' if good else 'FAIL'}  {name:<28} {ev}", flush=True)
        report.append({"n": spec["n"], "title": spec["title"], "genre": spec["genre"],
                       "bpm": spec["bpm"], "shape": spec["shape"], "bars": bars,
                       "seconds": round(secs, 2), "wav": str(wav.relative_to(ROOT)),
                       "cover": str(cover.relative_to(ROOT)),
                       "structure_pass": ok_s,
                       "structure": [[c[0], c[1], c[2]] for c in sres],
                       "contour": spark})
        if not ok_s:
            print("  !! STRUCTURE FAILED", flush=True)

    man = ALBUM_DIR / "manifest.json"
    prev = json.loads(man.read_text())["tracks"] if man.exists() else []
    keep = {t["n"]: t for t in prev}
    for t in report:
        keep[t["n"]] = t
    man.write_text(json.dumps({"album": "COLD OPEN", "artist": "MilkUps",
                               "standard": "content/snowsnakes/songs/STANDARD.md",
                               "home": "MilkUps (NOT SnowSnakes)",
                               "tracks": [keep[k] for k in sorted(keep)]}, indent=1))
    print(f"\nmanifest: {man.relative_to(ROOT)} ({len(keep)} tracks)", flush=True)
    return 0 if all(r["structure_pass"] for r in report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
