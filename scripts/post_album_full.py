#!/usr/bin/env python3
"""post_album_full.py — upload the COLD CUTS album to SnowSnakes.

One persona per track (six different accounts), so the release reads like six
people sharing a record rather than one account dumping a catalogue. Gated:
every track must already pass scripts/gate_album.py (see gate-report.txt).
"""
from __future__ import annotations
import argparse, json, subprocess, sys, urllib.request, urllib.error, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALBUM = ROOT / "content" / "milkups" / "album-full"
BASE = "https://snowsnakes.zerric.xyz/api"
USERS = ROOT / ".snowsnakes_real_users.json"
CLOUD, PRESET = "r6natkse", "snowsnakes_unsigned"

ARTISTS = {1: "sam_rivera", 2: "ivy_chen", 3: "kai_torres",
           4: "elle_marsh", 5: "max_fields", 6: "nia_brooks"}


def upload(path, rtype, mime):
    b = "----zdotalbum" + uuid.uuid4().hex
    body = b"".join([
        f"--{b}\r\nContent-Disposition: form-data; name=\"upload_preset\"\r\n\r\n{PRESET}\r\n".encode(),
        f"--{b}\r\nContent-Disposition: form-data; name=\"folder\"\r\n\r\nsnowsnakes\r\n".encode(),
        f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
        f"Content-Type: {mime}\r\n\r\n".encode(),
        path.read_bytes(), f"\r\n--{b}--\r\n".encode()])
    req = urllib.request.Request(f"https://api.cloudinary.com/v1_1/{CLOUD}/{rtype}/upload",
                                 data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode()).get("secure_url")


def api(path, data=None, token=None, method="GET"):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path,
                                 data=json.dumps(data).encode() if data is not None else None,
                                 method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {"_err": e.read().decode()[:200]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", action="store_true")
    a = ap.parse_args()
    man = json.loads((ALBUM / "manifest.json").read_text())
    users = {u["username"]: u for u in json.loads(USERS.read_text())}
    posted = []
    for t in man["tracks"]:
        wav = ROOT / t["wav"]
        mp3 = wav.with_suffix(".mp3")
        if not mp3.exists():
            subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                            "-i", str(wav), "-codec:a", "libmp3lame", "-b:a", "192k",
                            str(mp3)], check=True)
        artist = ARTISTS[t["n"]]
        title = f"{t['title']} — MilkUps"
        if not a.post:
            print(f"  ready {t['n']}. {title:<34} {mp3.stat().st_size//1024}KB as {artist}")
            continue
        tok = api("/auth/login", {"username": artist,
                                  "password": users[artist]["password"]}, method="POST")[1]
        tok = tok.get("token") if isinstance(tok, dict) else None
        if not tok:
            print(f"  !! login failed {artist}"); continue
        au = upload(mp3, "video", "audio/mpeg")
        cu = upload(ROOT / t["cover"], "image", "image/png")
        st, res = api("/songs", {"title": title, "audio_url": au, "cover_url": cu},
                      token=tok, method="POST")
        ok = st == 201 and isinstance(res, dict) and res.get("id")
        print(f"  {'ok ' if ok else '!! '}{t['n']}. {title:<34} as {artist:<12} HTTP {st} id={res.get('id') if isinstance(res,dict) else res}")
        if ok:
            posted.append({"id": res["id"], "title": title, "artist": artist, "n": t["n"]})
    if posted:
        (ALBUM / "posted.json").write_text(json.dumps(posted, indent=1))
        print(f"\nposted {len(posted)} tracks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
