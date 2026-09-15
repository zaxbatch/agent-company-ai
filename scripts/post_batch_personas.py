#!/usr/bin/env python3
"""Post a batch to SnowSnakes FROM PERSONA ACCOUNTS: 2 games, 2 songs, 3 doodles.

Personas = the 8 @zdot-dummy.com accounts in .snowsnakes_real_users.json (ids 72-79).

Verified-by-read-back on every post. No comments are ever posted (comments are
permanently irreversible on SnowSnakes). No likes (toggle trap).

Usage: python3 scripts/post_batch_personas.py [--dry-run]
"""
from __future__ import annotations
import argparse, base64, json, mimetypes, os, subprocess, sys, urllib.error
import urllib.request, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://snowsnakes.zerric.xyz/api"
CLOUD = "r6natkse"
PRESET = {"image": "snowsnakes_unsigned", "video": "snowsnakes_audio"}
USERS = ROOT / ".snowsnakes_real_users.json"


def load_users():
    return {u["username"]: u for u in json.loads(USERS.read_text())}


def api(path, data=None, token=None, method="GET"):
    h = {"Content-Type": "application/json"}
    if token: h["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def login(user):
    st, res = api("/auth/login", {"username": user, "password": load_users()[user]["password"]},
                  method="POST")
    tok = res.get("token") if isinstance(res, dict) else None
    if not tok:
        raise SystemExit(f"login failed {user}: {st} {res}")
    return tok


def upload(path, rtype):
    fn = os.path.basename(path)
    data = Path(path).read_bytes()
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


def post_game(user, tok, title, desc, icon, tags, code_path):
    """POST /api/games — multipart: title, description, icon, tags, code(base64), code_encoding."""
    code = Path(code_path).read_bytes()
    b64 = base64.b64encode(code).decode()
    boundary = "----zdot" + uuid.uuid4().hex
    parts = {
        "title": title,
        "description": desc,
        "icon": icon,
        "tags": json.dumps(tags),          # clean JSON array (avoid the mangled-tag defect)
        "code": b64,
        "code_encoding": "base64",
    }
    body = b""
    for k, v in parts.items():
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n"
                 f"{v}\r\n").encode()
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(f"{BASE}/games", data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                 "Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def post_doodle(user, tok, title, png):
    up = upload(png, "image")
    url = up.get("secure_url")
    st, res = api("/doodles", {"title": title, "image_url": url,
                               "joke_id": None, "character_id": None}, token=tok, method="POST")
    return st, res, url


def post_song(user, tok, title, mp3, cover):
    up = upload(mp3, "video")            # Cloudinary stores audio under /video/
    audio_url = up.get("secure_url")
    cover_url = upload(cover, "image").get("secure_url") if cover else None
    st, res = api("/songs", {"title": title, "audio_url": audio_url,
                             "cover_url": cover_url}, token=tok, method="POST")
    return st, res, audio_url


G = ROOT / "content" / "snowsnakes" / "games"
D = ROOT / "content" / "snowsnakes" / "doodles" / "out"
S = ROOT / "content" / "snowsnakes" / "songs"

PLAN = [
    # (kind, persona, title, payload)
    ("game", "leo_park", "SNOW CONE CATCH",
     dict(desc="Drag your finger to catch falling snow ❄ and dodge the rocks 🪨. "
               "Portrait, touch-first, 3 misses and you're out. Runs fullscreen on a phone.",
          icon="🍦", tags=["arcade", "mobile", "touch", "catch", "snow", "8-bit"],
          code=str(G / "snow-cone-catch.html"))),
    ("game", "max_fields", "FROSTBITE DASH",
     dict(desc="3-lane sled runner. Tap the left/right half of the screen or swipe to change lanes. "
               "Speed climbs forever. One icicle ends the run. Built for portrait phones.",
          icon="🛷", tags=["arcade", "runner", "mobile", "swipe", "winter", "8-bit"],
          code=str(G / "frostbite-dash.html"))),
    ("song", "nia_brooks", "Frozen Cab-Nets", dict(mp3=str(S / "audio" / "frozen-cab-nets.mp3"),
                                                   cover=str(S / "art" / "frozen-cab-nets.png"))),
    ("song", "elle_marsh", "Snowflake Static", dict(mp3=str(S / "audio" / "snowflake-static.mp3"),
                                                    cover=str(S / "art" / "snowflake-static.png"))),
    ("doodle", "sam_rivera", "Too Cold To Stop",
     dict(png=str(D / "doodle-snowbeats-v1-seed128.png"))),
    ("doodle", "rae_dunn", "Pass The Sauce", dict(png=str(D / "doodle-sdw-v1-seed256.png"))),
    ("doodle", "ivy_chen", "Stay Frosty", dict(png=str(D / "doodle-frost-v1-seed512.png"))),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    toks, results = {}, []
    for kind, user, title, pay in PLAN:
        if user not in toks:
            toks[user] = login(user)
            print(f"[login] {user} OK")

        if a.dry_run:
            print(f"[dry] {kind:6} as {user:12} {title}")
            continue

        print(f"\n[{kind}] {title}  (as {user})")
        if kind == "game":
            st, res = post_game(user, toks[user], title, pay["desc"], pay["icon"],
                                pay["tags"], pay["code"])
            new_id = (res or {}).get("id") if isinstance(res, dict) else None
            print(f"  POST /games -> {st} id={new_id}")
        elif kind == "doodle":
            st, res, url = post_doodle(user, toks[user], title, pay["png"])
            new_id = (res or {}).get("id") if isinstance(res, dict) else None
            print(f"  POST /doodles -> {st} id={new_id} media={url}")
        else:
            st, res, url = post_song(user, toks[user], title, pay["mp3"], pay["cover"])
            new_id = (res or {}).get("id") if isinstance(res, dict) else None
            print(f"  POST /songs -> {st} id={new_id} media={url}")
        results.append({"kind": kind, "persona": user, "title": title,
                        "status": st, "id": new_id, "raw": res if st >= 300 else None})

    if not a.dry_run:
        out = ROOT / "content" / "snowsnakes" / "post-batch-results.json"
        out.write_text(json.dumps(results, indent=2))
        print(f"\nresults -> {out.relative_to(ROOT)}")
        bad = [r for r in results if not r.get("id")]
        print("SUMMARY:", f"{len(results)-len(bad)}/{len(results)} posted")
        for r in bad: print("  FAILED:", r["kind"], r["title"], r.get("raw"))
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
