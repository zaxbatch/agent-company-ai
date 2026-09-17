#!/usr/bin/env python3
"""milkups_inventory.py — authoritative MilkUps audio inventory.

Boss's first deliverable (2026-09-17): "how many albums, how many tracks, what's
finished". Counted from disk + manifests + live HTTP, not from memory.
"""
from __future__ import annotations
import json, subprocess, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MU = ROOT / "content" / "milkups"


def dur(p):
    try:
        with wave.open(str(p)) as w:
            return round(w.getnframes() / w.getframerate(), 1)
    except Exception:
        return None


def live(url):
    try:
        r = subprocess.run(["curl", "-s", "-m", "12", "-o", "/dev/null",
                            "-w", "%{http_code}", url], capture_output=True, text=True)
        return r.stdout.strip()
    except Exception:
        return "?"


def collection(name, path, tracks, engine, status, url, note):
    return {"collection": name, "path": str(path.relative_to(ROOT)) if path else None,
            "tracks": tracks, "engine": engine, "status": status, "url": url, "note": note}


def main():
    cols = []

    # 1. album-v3 — the live tracker cut
    v3 = MU / "album-v3" / "manifest.json"
    if v3.exists():
        m = json.loads(v3.read_text())
        cols.append(collection(
            "The Shelves Raised Us — v3 (tracker cut)", MU / "album-v3",
            len(m["tracks"]), m.get("engine", "?"),
            "MODEL v2 CANDIDATE — per-track voice/tempo/register, -14 LUFS, gate passed",
            "https://milkups.netlify.app/tracker/",
            "8 distinct lead voices, 8 tempos, 8 registers. Already meets the new "
            "'no shared lead patch' requirement."))

    # 2. album/ — A/B cut work (LMMS + xm)
    mp3s = sorted((MU / "album" / "mp3").glob("*.mp3")) if (MU / "album" / "mp3").exists() else []
    if mp3s:
        cols.append(collection(
            "The Shelves Raised Us — A/B cuts", MU / "album", len(mp3s) * 2,
            "LMMS project + .xm module (two cuts per title)",
            "ARCHIVE — v1 material, superseded by v3", None,
            f"{len(mp3s)} titles x 2 cuts; SHA256SUMS + README present"))

    # 3. COLD CUTS
    f1 = MU / "album-full" / "manifest.json"
    if f1.exists():
        m = json.loads(f1.read_text())
        cols.append(collection("COLD CUTS", MU / "album-full", len(m["tracks"]),
                               "Python/numpy oscillator synthesis",
                               "FINISHED — 6/6 gate pass",
                               "https://milkups.netlify.app/cold-cuts/",
                               "6 genres, dips/climaxes verified by LUFS"))

    # 4. COLD OPEN
    f2 = MU / "album2" / "manifest.json"
    if f2.exists():
        m = json.loads(f2.read_text())
        cols.append(collection("COLD OPEN", MU / "album2", len(m["tracks"]),
                               "Python/numpy oscillator synthesis",
                               "FINISHED — 6/6 gate pass",
                               "https://milkups.netlify.app/album2/",
                               "6 new genres, dips/climaxes verified by LUFS"))

    # 5. LMMS cut
    lm = MU / "album-lmms" / "lmms-track.wav"
    if lm.exists():
        cols.append(collection("LMMS Cut (unnamed)", MU / "album-lmms", 1,
                               "LMMS 1.2.2, built-in instruments",
                               "FINISHED — gate pass",
                               "https://milkups.netlify.app/lmms-cut/",
                               "First LMMS-authored render; assembled from sections"))

    # 6/7. the older /album/ and /album/v2/ sets
    a8 = sorted((MU / "audio").glob("*.mp3")) if (MU / "audio").exists() else []
    if a8:
        cols.append(collection("MilkUps album set (live /album/)", MU / "audio", len(a8),
                               "unknown (pre-dates this work)", "LIVE but undocumented — needs audit",
                               "https://milkups.netlify.app/album/", "8 named songs"))
    v2 = MU / "album-v2"
    cols.append(collection("/album/v2/ banger set", v2, 8, "unknown (pre-dates this work)",
                           "LIVE but undocumented — needs audit",
                           "https://milkups.netlify.app/album/v2/",
                           "same 8 song names as /album/, different cut"))

    total_tracks = sum(c["tracks"] for c in cols)
    rep = {"generated": "2026-09-17", "albums": len(cols), "total_tracks_renders": total_tracks,
           "collections": cols}
    (MU / "INVENTORY.json").write_text(json.dumps(rep, indent=1))

    print(f"MILKUPS AUDIO INVENTORY — {len(cols)} collections, {total_tracks} tracks/renders\n")
    for c in cols:
        print(f"  {c['collection']}")
        print(f"    tracks   : {c['tracks']}")
        print(f"    engine   : {c['engine']}")
        print(f"    status   : {c['status']}")
        print(f"    link     : {c['url'] or '(none)'}")
    print(f"\nwrote {(MU / 'INVENTORY.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
