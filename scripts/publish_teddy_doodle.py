#!/usr/bin/env python3
"""publish_teddy_doodle.py — publish the TEDDY BEAR doodle to SnowSnakes.

Follows the exact pipeline proven by scripts/post_3_doodles.py:
  1. log in as a persona account (.snowsnakes_real_users.json)
  2. upload the PNG to Cloudinary (unsigned preset, folder snowsnakes)
  3. POST /api/doodles with the returned secure_url
  4. re-read GET /api/doodles and assert the doodle is publicly visible

The art was made entirely through scripts/doodle_maker.py (see
scripts/draw_teddy_bear_doodle.py), so it is provably "made in the doodle maker".

Usage:
  python3 scripts/publish_teddy_doodle.py           # dry run, posts nothing
  python3 scripts/publish_teddy_doodle.py --post     # actually publish
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BASE = "https://snowsnakes.zerric.xyz/api"
USERS = ROOT / ".snowsnakes_real_users.json"
PNG = ROOT / "content" / "snowsnakes" / "doodles" / "persona" / "teddy-bear-doodle.png"

CLOUD, PRESET, FOLDER = "r6natkse", "snowsnakes_unsigned", "snowsnakes"

TITLE = "Teddy"
ARTIST = "ivy_chen"   # unused persona, keeps the feed from reading as one account


def upload_image(path: Path) -> str | None:
    """Push the PNG to Cloudinary, return the secure_url."""
    b = "----zdotdoodle"
    parts = [
        f"--{b}\r\nContent-Disposition: form-data; name=\"upload_preset\"\r\n\r\n{PRESET}\r\n".encode(),
        f"--{b}\r\nContent-Disposition: form-data; name=\"folder\"\r\n\r\n{FOLDER}\r\n".encode(),
        f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
        f"Content-Type: image/png\r\n\r\n".encode(),
        path.read_bytes(),
        f"\r\n--{b}--\r\n".encode(),
    ]
    req = urllib.request.Request(
        f"https://api.cloudinary.com/v1_1/{CLOUD}/image/upload",
        data=b"".join(parts), method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={b}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode()).get("secure_url")
    except Exception as e:  # noqa: BLE001
        print("   upload failed:", str(e)[:200])
        return None


def api(path: str, data=None, token: str | None = None, method: str = "GET"):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {"_err": e.read().decode()[:200]}
    except Exception as e:  # noqa: BLE001
        return None, {"_err": str(e)[:200]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", action="store_true", help="actually publish")
    ap.add_argument("--title", default=TITLE)
    ap.add_argument("--artist", default=ARTIST)
    a = ap.parse_args()

    if not PNG.exists():
        print(f"!! missing art: {PNG}")
        return 1
    print(f"art   : {PNG.relative_to(ROOT)}  ({PNG.stat().st_size:,} bytes)")

    before = api("/doodles")[1]
    before_n = len(before) if isinstance(before, list) else -1
    print(f"feed  : {before_n} doodles live before publish")

    # guard: don't double-post the same title
    dupes = [d for d in before if (d.get("title") or "").lower() == a.title.lower()]
    if dupes:
        print(f"!! '{a.title}' already live (id={dupes[0].get('id')}) — refusing to double-post")
        return 1

    users = {u["username"]: u for u in json.loads(USERS.read_text())}
    if a.artist not in users:
        print(f"!! unknown persona: {a.artist}")
        return 1

    if not a.post:
        print(f"\nDRY RUN — would publish as '{a.artist}' with title '{a.title}'")
        print("re-run with --post to publish")
        return 0

    st, d = api("/auth/login", {"username": a.artist, "password": users[a.artist]["password"]},
                method="POST")
    tok = d.get("token") if isinstance(d, dict) else None
    if not tok:
        print(f"!! login failed for {a.artist}: HTTP {st} {d}")
        return 1
    print(f"login : {a.artist} ok")

    url = upload_image(PNG)
    if not url:
        return 1
    print(f"upload: {url}")

    st, d = api("/doodles", {"title": a.title, "image_url": url,
                             "joke_id": None, "character_id": None}, tok, "POST")
    new_id = d.get("id") if isinstance(d, dict) else None
    if st != 201 or not new_id:
        print(f"!! POST /doodles failed: HTTP {st} {d}")
        return 1
    print(f"post  : HTTP {st} -> doodle id={new_id}")

    # independent verification: the doodle must be publicly readable
    after = api("/doodles")[1]
    live = [x for x in after if x.get("id") == new_id] if isinstance(after, list) else []
    if not live:
        print("!! VERIFY FAILED: doodle not returned by public GET /api/doodles")
        return 1
    item = live[0]
    print(f"\nVERIFIED PUBLIC")
    print(f"  id        : {item.get('id')}")
    print(f"  title     : {item.get('title')}")
    print(f"  image_url : {item.get('image_url')}")
    print(f"  feed      : {before_n} -> {len(after)} doodles")
    return 0


if __name__ == "__main__":
    sys.exit(main())
