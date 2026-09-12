#!/usr/bin/env python3
"""doodle_batch.py — generate VARIED SnowSnakes doodles with the site's maker style,
upload via the site's own (unsigned) Cloudinary preset, and post to /api/doodles.

WHY VARIATION MATTERS
---------------------
scripts/doodle_gen.py renders ONE fixed composition (its RNG is seeded 128, so every
run is pixel-identical). Posting a batch of those would look like spam in the feed.
This module reuses doodle_gen's drawing primitives but parameterises the pose,
palette and notes so each doodle is visually distinct.

BRANDING (policy)
-----------------
doodle_gen.py stamps "Z-DOT" on the artwork. DOMAIN-STRATEGY rule 7 says the play
domains "stay looking personal -- no Z-Dot branding". So this generator does NOT
stamp Z-DOT; it signs "SNOW SNAKES" instead. Flip --stamp to override (your call,
but the default is the policy-safe one).

Uploads use the SAME public unsigned preset the website itself uses
(cloud r6natkse / preset snowsnakes_unsigned), i.e. no credentials are needed and
no new access is being created. Note: each upload consumes the owner's Cloudinary quota.

Usage:
  python3 scripts/doodle_batch.py --count 8            # generate only
  python3 scripts/doodle_batch.py --count 8 --post     # generate + upload + post
  python3 scripts/doodle_batch.py --count 1 --post --as MilkUps
"""
from __future__ import annotations
import argparse, json, math, random, sys, urllib.request, urllib.error, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import doodle_gen as DG
from doodle_gen import jline, snowflake, font, W, H, PAPER, INK
from PIL import Image, ImageDraw

BASE = "https://snowsnakes.zerric.xyz/api"
USERS = ROOT / ".snowsnakes_real_users.json"
OUTDIR = ROOT / "content" / "experiments" / "doodles"
CLOUD, PRESET, FOLDER = "r6natkse", "snowsnakes_unsigned", "snowsnakes"

# Icy-first, then warm/vivid so the feed doesn't look monotone.
PALETTES = [
    {"body": (223, 242, 255), "accent": (226, 74, 74), "scale": (150, 200, 235)},
    {"body": (255, 234, 222), "accent": (198, 40, 40), "scale": (240, 170, 120)},
    {"body": (228, 250, 228), "accent": (46, 125, 50),  "scale": (140, 200, 140)},
    {"body": (238, 230, 255), "accent": (123, 31, 162), "scale": (180, 150, 230)},
    {"body": (255, 249, 214), "accent": (245, 160, 30), "scale": (240, 210, 120)},
    {"body": (255, 226, 240), "accent": (194, 24, 91),  "scale": (240, 160, 200)},
]
CAPTIONS = [
    ("TOO COLD TO STOP", "128 BPM"), ("ALWAYS WATCHING", "ICE COLD"),
    ("SNOW PROBLEM", "CHILL MODE"), ("KEEP IT CHILL", "FROST LINE"),
    ("STAY FROSTY", "SNOW BEATS"), ("COLD SNAP", "128 BPM"),
    ("NO THOUGHTS JUST SNOW", "DRIFT"), ("SHEDDING SEASON", "MOLT"),
    ("SNOWBOUND", "DEEP FREEZE"), ("SLITHER AND SHIVER", "COOL DOWN"),
]


def draw_variant(path: Path, caption: str, tag: str, seed: int, pal: dict,
                 pose: int = 0, stamp: str = "SNOW SNAKES") -> Path:
    """One doodle in the maker's 700x900 canvas, with pose/palette variation."""
    DG.rnd = random.Random(seed)          # re-seed the shared jitter RNG
    rnd = DG.rnd
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    for y in range(40, H - 40, 34):
        for x in range(40, W - 40, 34):
            d.point((x, y), fill=(226, 228, 224))

    # ---- snake body: pose changes the arc sweep ----
    cx, cy = 350 + (pose % 3) * 12 - 12, 650 + (pose % 2) * 20
    t0, t1 = math.radians(180 + pose * 9), math.radians(268 - pose * 7)
    r0, r1 = 50.0 + pose * 5, 170.0 - pose * 6
    xs, ys = 1.10 + (pose % 3) * 0.03, 0.92 - (pose % 2) * 0.04
    N = 240
    pts = []
    for i in range(N + 1):
        t = i / N
        th = t0 + (t1 - t0) * t
        r = r0 + (r1 - r0) * t
        pts.append((cx + math.cos(th) * r * xs, cy + math.sin(th) * r * ys))

    jline(d, [(x + 5, y + 6) for x, y in pts], jitter=0.06, width=44, fill=(238, 238, 234))
    jline(d, pts, jitter=0.06, width=42, fill=pal["body"])
    jline(d, pts, jitter=0.06, width=3, fill=INK)
    for i in range(12 + pose * 3, N - 6, 20 + (pose % 4) * 4):
        x, y = pts[i]
        snowflake(d, x, y, 9 + (pose % 3) * 2, col=pal["scale"], w=2)

    # ---- head ----
    hx, hy = pts[-1][0] + 2, pts[-1][1] - 34
    d.ellipse([hx - 58, hy - 46, hx + 58, hy + 46], fill=pal["body"], outline=INK, width=4)
    for sx in (-24, 24):
        d.ellipse([hx + sx - 13, hy - 8, hx + sx + 13, hy + 18], fill=(255, 255, 255), outline=INK, width=3)
        d.ellipse([hx + sx - 5, hy + 2, hx + sx + 6, hy + 13], fill=INK)
        d.ellipse([hx + sx - 2, hy + 1, hx + sx + 2, hy + 5], fill=(255, 255, 255))
    # mouth: pose 0-1 smile, 2-3 straight line (stoic), 4+ smirk
    if pose % 5 < 2:
        d.arc([hx - 26, hy + 8, hx + 26, hy + 40], start=15, end=165, fill=INK, width=3)
    elif pose % 5 < 4:
        d.line([(hx - 24, hy + 30), (hx + 24, hy + 26)], fill=INK, width=3)
    else:
        d.arc([hx - 20, hy + 6, hx + 30, hy + 34], start=10, end=120, fill=INK, width=3)
    if pose % 3 == 0:                      # tongue only on some
        d.line([(hx, hy + 44), (hx, hy + 74)], fill=pal["accent"], width=4)
        d.line([(hx, hy + 74), (hx - 14, hy + 92)], fill=pal["accent"], width=4)
        d.line([(hx, hy + 74), (hx + 14, hy + 92)], fill=pal["accent"], width=4)

    # ---- headphones (only some poses -> visual variety) ----
    if pose % 4 != 3:
        d.arc([hx - 66, hy - 84, hx + 66, hy + 30], start=185, end=355, fill=INK, width=9)
        for sx in (-64, 64):
            d.rounded_rectangle([hx + sx - 17, hy - 30, hx + sx + 17, hy + 34], radius=11,
                                fill=(44, 48, 58), outline=INK, width=3)
            d.rounded_rectangle([hx + sx - 10, hy - 16, hx + sx + 10, hy + 22], radius=7, fill=pal["accent"])

    # ---- music notes, count/positions vary ----
    def note(x, y, s=1.0, col=INK):
        d.ellipse([x - 11 * s, y - 8 * s, x + 11 * s, y + 8 * s], fill=col)
        d.line([(x + 9 * s, y), (x + 9 * s, y - 54 * s)], fill=col, width=int(4 * s))
        d.line([(x + 9 * s, y - 54 * s), (x + 30 * s, y - 46 * s)], fill=col, width=int(4 * s))
    for k, (nx, ny) in enumerate([(548, 372), (600, 430), (112, 404), (150, 300), (520, 250)]):
        if k < 1 + (pose % 3):
            note(nx, ny, 1.15 - k * 0.08, pal["accent"] if k % 2 == 0 else INK)

    # ---- labels + signature (NO Z-DOT stamp: policy-safe) ----
    d.text((44, 52), "SNOW SNAKES", font=font(46), fill=INK)
    d.text((46, 108), tag, font=font(26), fill=pal["scale"])
    d.line([(44, 148), (300, 148)], fill=pal["scale"], width=4)
    f = font(32)
    tw = d.textlength(caption, font=f)
    d.text(((W - tw) / 2, 810), caption, font=f, fill=INK)
    if stamp:
        d.text((W - 210, 862), stamp, font=font(19), fill=(150, 158, 170))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


def upload_image(p: Path) -> str | None:
    boundary = "----zdot" + uuid.uuid4().hex
    parts = []
    for n, v in (("upload_preset", PRESET), ("folder", FOLDER)):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{n}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{p.name}"\r\n'
                 f'Content-Type: image/png\r\n\r\n'.encode() + p.read_bytes() + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(f"https://api.cloudinary.com/v1_1/{CLOUD}/image/upload",
                                 data=b"".join(parts), method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode()).get("secure_url")
    except Exception as e:
        print("   upload failed:", e)
        return None


def api(path, data=None, token=None, method="GET"):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode()
            try:
                return r.status, json.loads(raw)
            except Exception:
                return r.status, {"_nonjson": raw[:100]}
    except urllib.error.HTTPError as e:
        return e.code, {"_err": e.read().decode()[:140]}
    except Exception as e:
        return None, {"_err": str(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=8)
    ap.add_argument("--post", action="store_true")
    ap.add_argument("--as", dest="author", default="MilkUps", help="persona/brand account to post as")
    ap.add_argument("--stamp", default="SNOW SNAKES", help="footer signature ('' = none)")
    ap.add_argument("--start-seed", type=int, default=1)
    a = ap.parse_args()

    users = json.loads(USERS.read_text())
    tokens = {u["username"]: u["token"] for u in users}
    # MilkUps is a brand account, not in the persona file
    if a.post and a.author not in tokens:
        tok = api("/auth/login", {"username": "MilkUps", "password": "MilkUps2026!"}, method="POST")[1]
        tok = tok.get("token") if isinstance(tok, dict) else None
        if not tok:
            sys.exit(f"FATAL: cannot log in as {a.author}")
        tokens[a.author] = tok
    before = len(api("/doodles")[1])

    made, posted = [], []
    for i in range(a.count):
        seed = a.start_seed + i
        caption, tag = CAPTIONS[i % len(CAPTIONS)]
        pal = PALETTES[i % len(PALETTES)]
        pose = i % 6
        p = OUTDIR / f"snake-doodle-{seed:03d}.png"
        draw_variant(p, caption, tag, seed, pal, pose=pose, stamp=a.stamp)
        print(f"  drew {p.name}  ({p.stat().st_size//1024} KB)  '{caption}'  palette={i % len(PALETTES)} pose={pose}")
        made.append({"path": str(p), "caption": caption, "tag": tag, "seed": seed})
        if a.post:
            url = upload_image(p)
            if not url:
                continue
            st, d = api("/doodles", {"title": f"Snow Snakes — {caption.title()}", "image_url": url,
                                     "joke_id": None, "character_id": None}, tokens[a.author], "POST")
            ok = st == 201 and isinstance(d, dict) and d.get("id")
            print(f"   {'ok ' if ok else '!! '}POST /doodles as {a.author} -> HTTP {st} id={d.get('id') if isinstance(d,dict) else d}")
            if ok:
                posted.append({"id": d["id"], "title": d.get("title"), "url": url, "caption": caption})

    after = api("/doodles")[1]
    print(f"\ndoodles: {before} -> {len(after)} (created {len(posted)})")
    ev = ROOT / ".agent-company-ai" / "doodle_batch_state.json"
    ev.parent.mkdir(parents=True, exist_ok=True)
    ev.write_text(json.dumps({"made": made, "posted": posted, "before": before, "after": len(after)}, indent=1))
    if posted:
        live = {x["id"]: x for x in after}
        print("VERIFIED live:")
        for x in posted:
            g = live.get(x["id"])
            print(f"  id={x['id']} '{x['title'][:34]}' author={g.get('author_id') if g else '?'} img={str(x['url'])[:56]}")
    print("evidence:", ev)


if __name__ == "__main__":
    main()
