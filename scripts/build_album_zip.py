#!/usr/bin/env python3
"""Build the MilkUps 'The Shelves Raised Us' album ZIP (paid download artifact).

Usage:
    python3 scripts/build_album_zip.py [--out PATH] [--token TOKEN]

Produces a ZIP containing the 8 album MP3s (renamed with track numbers),
cover art (PNG + SVG), tracklist.txt and README.txt.

The ZIP is the whole-album download offered on milkups.zerric.xyz/album
for $5 via Cash App (honor-system gate). Rebuild/re-upload any time the
audio or metadata changes.
"""
import argparse
import hashlib
import os
import secrets
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(ROOT, "resources", "snowsnakes", "spread-da-word", "audio")
ASSETS_DIR = os.path.join(ROOT, "content", "milkups", "assets")
OUT_DIR = os.path.join(ROOT, "content", "milkups")

# (album title, genre, duration, source file)
TRACKS = [
    ("01 - Trap Cabnets.mp3",    "Trap",       "0:55", "banger-trap-cabnets.mp3"),
    ("02 - Lofi Midnight.mp3",   "Lo-Fi",      "1:39", "banger-lofi-midnight.mp3"),
    ("03 - Electro Neon.mp3",    "Electro",    "1:00", "banger-electro-neon.mp3"),
    ("04 - Pop Radio.mp3",       "Pop",        "1:05", "banger-pop-radio.mp3"),
    ("05 - Country Fridge.mp3",  "Country",    "1:17", "banger-country-fridge.mp3"),
    ("06 - Funk Cookout.mp3",    "Funk",       "1:11", "banger-funk-cookout.mp3"),
    ("07 - Synthwave Retro.mp3", "Synthwave",  "1:09", "banger-synthwave-retro.mp3"),
    ("08 - Icy.mp3",             "Icy",        "1:36", "banger-icy.mp3"),
]

README = """THE SHELVES RAISED US
by milkup (MilkUps)

8 tracks, cold vibes, fresh beats, straight from the cab-nets. 🥛
Retro 80s / synthwave. The music behind Spread Da Word.

TRACKLIST
01 - Trap Cabnets      (Trap)       0:55
02 - Lofi Midnight     (Lo-Fi)      1:39
03 - Electro Neon      (Electro)    1:00
04 - Pop Radio         (Pop)        1:05
05 - Country Fridge    (Country)    1:17
06 - Funk Cookout      (Funk)       1:11
07 - Synthwave Retro   (Synthwave)  1:09
08 - Icy               (Icy)        1:36

(c) 2026 MilkUps / Z-Dot LLC. All rights reserved.
MilkUps is an independent Z-Dot band. Music for Spread Da Word.
Web: https://milkups.zerric.xyz
Contact: milkups@zerric.xyz
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help="Output ZIP path (default: content/milkups/TheShelvesRaisedUs-milkups-<token>.zip)")
    ap.add_argument("--token", default=None, help="Random token for filename (default: auto-generated)")
    args = ap.parse_args()

    token = args.token or secrets.token_hex(3)
    out = args.out or os.path.join(OUT_DIR, f"TheShelvesRaisedUs-milkups-{token}.zip")

    missing = [t[3] for t in TRACKS if not os.path.exists(os.path.join(AUDIO_DIR, t[3]))]
    if missing:
        raise SystemExit(f"MISSING SOURCE AUDIO: {missing}")

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for album_name, genre, dur, src in TRACKS:
            zf.write(os.path.join(AUDIO_DIR, src), album_name)
            print(f"  + {album_name}")
        zf.write(os.path.join(ASSETS_DIR, "cover-1500.png"), "cover.png")
        zf.write(os.path.join(ASSETS_DIR, "cover.svg"), "cover.svg")
        zf.writestr("tracklist.txt", "".join(
            f"{n} - {t} ({g}) {d}\n" for n, t, g, d, _ in [(a.split(' - ')[0], a.split(' - ')[1].replace('.mp3',''), g, d, s) for a, g, d, s in TRACKS]
        ))
        zf.writestr("README.txt", README)

    sha = hashlib.sha256(open(out, "rb").read()).hexdigest()
    size = os.path.getsize(out)
    print(f"\nZIP: {out}")
    print(f"SIZE: {size} bytes ({size/1024/1024:.2f} MiB)")
    print(f"SHA256: {sha}")
    print(f"TOKEN: {token}")
    return out, token


if __name__ == "__main__":
    main()
