#!/usr/bin/env python3
"""post_ice_cold_pockets.py — encode, upload and post "Ice Cold Pockets" to SnowSnakes.

Pipeline: wav -> mp3 (libmp3lame 192k) -> Cloudinary (unsigned preset) ->
POST /api/songs, as a rotating persona account.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import urllib.error
import urllib.request
import uuid
from pathlib import Path

BASE = "https://snowsnakes.zerric.xyz/api"
CLOUD, PRESET = "r6natkse", "snowsnakes_unsigned"
ROOT = Path(__file__).resolve().parent.parent
SONGS = ROOT / "content" / "snowsnakes" / "songs"

STEM = "ice-cold-pockets"
TITLE = "Ice Cold Pockets"
AUTHOR_ID = 74          # leo_park
USERS = ROOT / ".snowsnakes_real_users.json"

WAV = SONGS / "wav" / f"{STEM}.wav"
MP3 = SONGS / "audio" / f"{STEM}.mp3"
COVER = SONGS / "art" / f"{STEM}.png"


def api(path, data=None, token=None, method="GET"):
    h = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (zdot-song)"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
        return r.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:200]}


def encode():
    MP3.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-i", str(WAV), "-codec:a", "libmp3lame", "-b:a", "192k", str(MP3)],
                   check=True)
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(MP3), "-af", "volumedetect",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    pk = [l.split("max_volume:")[1].strip() for l in out.splitlines() if "max_volume" in l]
    print(f"  mp3 {MP3.stat().st_size//1024} KB max_volume={pk[0] if pk else '?'}")


def upload(path, rtype):
    b = "----zdottrap" + uuid.uuid4().hex
    body = b"".join([
        f"--{b}\r\nContent-Disposition: form-data; name=\"upload_preset\"\r\n\r\n{PRESET}\r\n".encode(),
        f"--{b}\r\nContent-Disposition: form-data; name=\"folder\"\r\n\r\nsnowsnakes\r\n".encode(),
        f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
        f"Content-Type: {'audio/mpeg' if rtype == 'video' else 'image/png'}\r\n\r\n".encode(),
        path.read_bytes(), f"\r\n--{b}--\r\n".encode()])
    req = urllib.request.Request(
        f"https://api.cloudinary.com/v1_1/{CLOUD}/{rtype}/upload", data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", action="store_true")
    args = ap.parse_args()

    users = {u["id"]: u for u in json.loads(USERS.read_text())}
    author = users[AUTHOR_ID]

    print("[1/4] encode"); encode()
    print("[2/4] upload audio")
    au = upload(MP3, "video").get("secure_url"); print("   ", au)
    print("[3/4] upload cover")
    cu = upload(COVER, "image").get("secure_url"); print("   ", cu)
    if not (au and cu):
        raise SystemExit("FATAL: upload failed")
    if not args.post:
        print("\ndry run — pass --post to publish"); return

    print(f"[4/4] POST /songs as {author['username']}")
    st, res = api("/auth/login", {"username": author["username"], "password": author["password"]},
                  method="POST")
    tok = res.get("token")
    if not tok:
        raise SystemExit(f"FATAL: login failed ({st})")
    st, res = api("/songs", {"title": TITLE, "audio_url": au, "cover_url": cu},
                  token=tok, method="POST")
    print(f"   HTTP {st}  {str(res)[:200]}")
    if st != 201:
        raise SystemExit("FATAL: post failed")
    sid = res.get("id")
    live = api("/songs")[1]
    row = next((s for s in live if s.get("id") == sid), None)
    print("\nVERIFY:", json.dumps(row, indent=1)[:380] if row else "NOT FOUND")
    (SONGS / f"{STEM}-post.json").write_text(
        json.dumps({"id": sid, "title": TITLE, "author": author["username"],
                    "audio_url": au, "cover_url": cu, "live": row}, indent=1))


if __name__ == "__main__":
    main()
