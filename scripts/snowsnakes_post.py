#!/usr/bin/env python3
"""Post content to SnowSnakes: upload the media to Cloudinary, then create the record.

    scripts/snowsnakes_post.py --kind doodle --file art.png --title "Title"
    scripts/snowsnakes_post.py --kind song   --file beat.mp3 --title "Title" [--cover art.png]

Credential is read from communication/credentials.txt (zdot_team) and never printed.
"""
from __future__ import annotations
import argparse, json, mimetypes, os, re, sys, urllib.error, urllib.request, uuid

BASE = "https://snowsnakes.zerric.xyz/api"
CLOUD = "r6natkse"
CREDS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "communication", "credentials.txt")
PRESET = {"image": "snowsnakes_unsigned", "video": "snowsnakes_audio"}


def creds(user="zdot_team"):
    for line in open(CREDS):
        if user in line:
            m = re.search(r'password:\s*([^\s|]+)', line)
            if m:
                return user, m.group(1)
    raise SystemExit(f"no credential for {user}")


def api(path, data=None, token=None, method="GET"):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def upload(path, rtype):
    """rtype: 'image' or 'video' (Cloudinary stores audio under /video/)."""
    fn = os.path.basename(path)
    data = open(path, "rb").read()
    ct = mimetypes.guess_type(fn)[0] or "application/octet-stream"
    b = "----zdot" + uuid.uuid4().hex
    body = b""
    for k, v in {"upload_preset": PRESET[rtype], "folder": "snowsnakes"}.items():
        body += f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    body += (f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{fn}\"\r\n"
             f"Content-Type: {ct}\r\n\r\n").encode() + data + b"\r\n"
    body += f"--{b}--\r\n".encode()
    req = urllib.request.Request(f"https://api.cloudinary.com/v1_1/{CLOUD}/{rtype}/upload",
                                 data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", required=True, choices=["doodle", "song"])
    ap.add_argument("--file", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--cover")
    ap.add_argument("--account", default="zdot_team")
    a = ap.parse_args()

    user, pw = creds(a.account)
    st, res = api("/auth/login", {"username": user, "password": pw}, method="POST")
    tok = res.get("token") if isinstance(res, dict) else None
    if not tok:
        raise SystemExit(f"login failed for {user}: {st} {res}")
    print(f"logged in as {user}")

    rtype = "image" if a.kind == "doodle" else "video"
    up = upload(a.file, rtype)
    media_url = up.get("secure_url")
    print(f"uploaded {a.file} ({up.get('bytes')} B) -> {media_url}")

    if a.kind == "doodle":
        payload = {"title": a.title, "image_url": media_url, "joke_id": None, "character_id": None}
        st, res = api("/doodles", payload, token=tok, method="POST")
    else:
        cover = upload(a.cover, "image").get("secure_url") if a.cover else None
        payload = {"title": a.title, "audio_url": media_url, "cover_url": cover}
        st, res = api("/songs", payload, token=tok, method="POST")

    print(f"POST /{'doodles' if a.kind=='doodle' else 'songs'}: {st}")
    if isinstance(res, dict) and res.get("id"):
        print(f"LIVE id={res['id']}  url={res.get('image_url') or res.get('audio_url')}")
    else:
        print("response:", res)


if __name__ == "__main__":
    main()
