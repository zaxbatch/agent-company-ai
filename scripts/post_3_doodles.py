#!/usr/bin/env python3
"""post_3_doodles.py — draw 3 visually DISTINCT doodles with the Doodle Maker
engine and post each one as a DIFFERENT persona account.

Why this exists: scripts/doodle_batch.py posts a whole batch as a single author
(--as), which reads as one person spamming the feed. Zerric asked for persona
accounts (plural) plus three pieces that all look different from each other.

Every mark goes through scripts/doodle_maker.py, the headless emulation of the
live maker modal (900x700 landscape, the real 12-colour palette, brush / marker /
spray / eraser / fill / stamp / lettering). Nothing is drawn outside that API, so
each piece is provably "made in the doodle maker".

Distinctness is structural, not cosmetic -- each doodle differs in subject,
palette, composition AND tool mix:
  1. ICE CUBE SNAKE  cold blues, centred subject, heavy fill + frost spray
  2. COOKOUT HEAT    warm reds/golds, diagonal dynamic layout, marker + stamps
  3. NIGHT DRIFT     violet/pink, big-shape backdrop, spray clouds + hand lettering

Usage: venv/bin/python scripts/post_3_doodles.py [--post] [--scale 2]
"""
from __future__ import annotations
import argparse, json, math, random, sys, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from doodle_maker import Canvas  # the maker engine

BASE = "https://snowsnakes.zerric.xyz/api"
USERS = ROOT / ".snowsnakes_real_users.json"
OUT = ROOT / "content" / "snowsnakes" / "doodles" / "persona"
CLOUD, PRESET, FOLDER = "r6natkse", "snowsnakes_unsigned", "snowsnakes"

# each doodle is posted by a different persona
PLAN = [
    {"n": 1, "artist": "sam_rivera", "title": "Snake on the Rocks", "tag": "ICE COLD"},
    {"n": 2, "artist": "leo_park",   "title": "Cookout Season",     "tag": "HEAT WAVE"},
    {"n": 3, "artist": "nia_brooks", "title": "Night Drift",        "tag": "COOL DOWN"},
]


def jitter_pts(pts, rng, amt=1.4):
    return [(x + rng.uniform(-amt, amt), y + rng.uniform(-amt, amt)) for x, y in pts]


# ── 1. ICE CUBE SNAKE — cold, centred, fill-heavy ────────────────────────────
def doodle_ice_cube(c, rng):
    NAVY, CYAN, WHITE, ICE = "#003399", "#00ccff", "#ffffff", "#dff2ff"
    # soft frost spray behind the subject
    c.spray([(450, 330), (430, 360), (470, 340)], CYAN, size=190, density=0.5, alpha=26)

    # ice cube: filled square, tilted off-axis by drawing each edge as a stroke
    cube = [(300, 250), (600, 235), (610, 520), (295, 530)]
    c.poly(cube, NAVY, width=9, jitter=1.5)
    c.fill(450, 380, ICE)
    # inner facets (drawn, not filled) so the cube reads 3D
    c.brush(jitter_pts([(300, 250), (450, 300), (600, 235)], rng), CYAN, 6, 1.2)
    c.brush(jitter_pts([(450, 300), (455, 400)], rng), CYAN, 6, 1.2)
    c.brush(jitter_pts([(455, 400), (610, 520)], rng), CYAN, 5, 1.2)
    c.brush(jitter_pts([(450, 300), (295, 530)], rng), CYAN, 5, 1.2)

    # snake coiled around the cube: one long sine body
    body = [(150 + i * 4.0, 470 + math.sin(i / 26.0) * 78) for i in range(151)]
    c.brush(body, NAVY, 30, 0.8)
    c.brush(body, ICE, 19, 0.8)
    c.marker(body, CYAN, size=30, alpha=42)

    # head + face
    hx, hy = 168, 470 + math.sin(0) * 78 - 10
    c.ellipse([hx - 52, hy - 40, hx + 52, hy + 40], NAVY, width=8, jitter=1.0)
    c.fill(hx, hy, WHITE)
    c.dot(hx - 20, hy - 10, NAVY, 8)
    c.dot(hx + 20, hy - 10, NAVY, 8)
    c.dot(hx - 20, hy - 10, WHITE, 3)
    c.dot(hx + 20, hy - 10, WHITE, 3)
    tongue = [(hx + 50, hy + 12), (hx + 86, hy + 20), (hx + 100, hy + 44), (hx + 122, hy + 26)]
    c.brush(tongue, "#e63946", 7)
    c.stamp("❄️", 690, 150, size=116)
    c.stamp("❄️", 140, 170, size=88)
    c.stamp("🧊", 690, 610, size=104)
    c.hand_text("ICE COLD", 320, 556, size=76, color=NAVY, wobble=2.2, rotate=3.0)
    for i in range(22):  # snow scatter
        x, y = rng.uniform(30, 870), rng.uniform(30, 670)
        c.brush([(x - 6, y), (x + 6, y)], rng.choice([CYAN, ICE]), 2.2)


# ── 2. COOKOUT HEAT — warm, diagonal, marker + stamps ───────────────────────
def doodle_cookout(c, rng):
    RED, GOLD, ORANGE, DARK = "#e63946", "#ffcc00", "#ff7f11", "#6d4c41"
    # diagonal heat streaks
    for i in range(7):
        x = 90 + i * 120
        c.marker([(x, 660), (min(x + 190, 840), 90)], ORANGE, size=34, alpha=40)
    # grill bars, drawn on the diagonal
    for i in range(6):
        c.brush([(150 + i * 26, 560 - i * 8), (700 + i * 26, 430 - i * 8)], DARK, 13, 1.0)
    # hot dog: bun + sausage
    c.ellipse([230, 300, 660, 430], "#c08a4a", width=9, jitter=1.4)
    c.fill(445, 365, "#e8b96f")
    c.brush([(285, 350), (620, 350)], "#a9613a", 46)
    c.marker([(300, 344), (610, 344)], GOLD, size=18, alpha=150)  # mustard
    c.marker([(310, 362), (600, 362)], RED, size=15, alpha=140)   # ketchup
    # speed lines off the sausage
    for i in range(5):
        y = 300 + i * 30
        c.brush([(690, y), (790 - i * 10, y - 22)], ORANGE, 8)
    c.stamp("🌭", 800, 200, size=120)
    c.stamp("🍅", 150, 200, size=100)
    c.stamp("🌶️", 760, 560, size=104)
    c.stamp("🥒", 130, 590, size=90)
    # spatter, like a spray-can finish
    c.spray([(430, 250), (500, 240), (380, 250)], GOLD, size=90, density=0.8, alpha=64)
    c.text("HEAT", 330, 90, size=104, color=RED)
    c.text("WAVE", 470, 90, size=104, color=ORANGE)
    c.hand_text("pass the sauce", 300, 592, size=48, color=DARK, wobble=2.0, rotate=3.5)


# ── 3. NIGHT DRIFT — violet/pink, big-shape backdrop, spray + lettering ─────
def doodle_night(c, rng):
    PURPLE, PINK, MAG, CREAM = "#8e44ad", "#ff9ecb", "#ff00ff", "#fff9d6"
    # flood the whole page with night violet first (the maker's fill tool, seeded
    # in a corner) -- this is what makes #3 read instantly different from #1/#2,
    # which both stay on white paper.
    c.fill(12, 12, "#1b0f2b")
    # big filled moon disc dominating the frame
    c.ellipse([240, 70, 780, 545], PURPLE, width=10, jitter=2.0)
    c.fill(510, 300, CREAM)
    # craters
    for (cx, cy, r) in [(400, 220, 40), (610, 350, 55), (460, 425, 34), (640, 170, 30)]:
        c.ellipse([cx - r, cy - r, cx + r, cy + r], PINK, width=6, jitter=1.6)
        c.fill(cx, cy, PINK)
    # drifting snow clouds
    for i in range(5):
        cx = 110 + i * 190
        c.spray([(cx, 100), (cx + 40, 96), (cx - 40, 104)], PINK, size=120,
                density=0.55, alpha=44)
    # a thin snake silhouette crossing the moon (contrast against the cream)
    sl = [(150 + i * 6.0, 610 - i * 1.1 + math.sin(i / 18.0) * 26) for i in range(90)]
    c.brush(sl, MAG, 17, 1.0)
    c.stamp("❄️", 830, 140, size=104)
    c.stamp("❄️", 90, 480, size=84)
    c.stamp("🥫", 820, 620, size=86)
    c.hand_text("NIGHT DRIFT", 232, 578, size=78, color=PINK, wobble=2.6, rotate=4.0)
    for i in range(30):
        x, y = rng.uniform(20, 880), rng.uniform(20, 250)
        c.dot(x, y, rng.choice([PINK, MAG, CREAM]), rng.uniform(2, 4))
    for i in range(26):  # stars against the night sky
        sx, sy = rng.uniform(30, 870), rng.uniform(560, 660)
        c.dot(sx, sy, rng.choice([CREAM, PINK]), rng.uniform(2, 4))


DRAWERS = {1: doodle_ice_cube, 2: doodle_cookout, 3: doodle_night}


# ── upload + post ───────────────────────────────────────────────────────────
def upload_image(path):
    b = "----zdotdoodle"
    parts = [
        f"--{b}\r\nContent-Disposition: form-data; name=\"upload_preset\"\r\n\r\n{PRESET}\r\n".encode(),
        f"--{b}\r\nContent-Disposition: form-data; name=\"folder\"\r\n\r\n{FOLDER}\r\n".encode(),
        f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
        f"Content-Type: image/png\r\n\r\n".encode(),
        path.read_bytes(), f"\r\n--{b}--\r\n".encode(),
    ]
    req = urllib.request.Request(
        f"https://api.cloudinary.com/v1_1/{CLOUD}/image/upload",
        data=b"".join(parts), method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode()).get("secure_url")
    except Exception as e:
        print("   upload failed:", str(e)[:160])
        return None


def api(path, data=None, token=None, method="GET"):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {"_err": e.read().decode()[:160]}
    except Exception as e:
        return None, {"_err": str(e)[:160]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", action="store_true")
    ap.add_argument("--scale", type=int, default=2)
    a = ap.parse_args()

    users = {u["username"]: u for u in json.loads(USERS.read_text())}
    OUT.mkdir(parents=True, exist_ok=True)
    before = len(api("/doodles")[1])
    made, posted = [], []

    for spec in PLAN:
        n, artist = spec["n"], spec["artist"]
        rng = random.Random(1000 + n)
        c = Canvas(scale=a.scale, bg=(255, 255, 255))
        c.seed(1000 + n)
        DRAWERS[n](c, rng)
        path = OUT / f"persona-{n}-{artist}.png"
        c.save(path)
        print(f"[{n}] {spec['title']:<18} by {artist:<12} {path.stat().st_size//1024:>4} KB")
        made.append({"n": n, "title": spec["title"], "tag": spec["tag"],
                     "artist": artist, "path": str(path.relative_to(ROOT))})

        if not a.post:
            continue
        tok = api("/auth/login", {"username": artist, "password": users[artist]["password"]},
                  method="POST")[1]
        tok = tok.get("token") if isinstance(tok, dict) else None
        if not tok:
            print(f"    !! cannot log in as {artist}")
            continue
        url = upload_image(path)
        if not url:
            continue
        st, d = api("/doodles", {"title": spec["title"], "image_url": url,
                                 "joke_id": None, "character_id": None}, tok, "POST")
        ok = st == 201 and isinstance(d, dict) and d.get("id")
        print(f"    {'ok ' if ok else '!! '}POST /doodles as {artist} -> HTTP {st} id={d.get('id') if isinstance(d,dict) else d}")
        if ok:
            posted.append({"id": d["id"], "title": spec["title"], "artist": artist,
                           "image_url": url})

    after = api("/doodles")[1]
    print(f"\ndoodles: {before} -> {len(after)} (created {len(posted)})")
    if posted:
        live = {x.get("id"): x for x in after}
        print("VERIFIED live:")
        for p in posted:
            g = live.get(p["id"])
            print(f"  id={p['id']} '{p['title']}' author_id={g.get('author_id') if g else '?'} img={str(p['image_url'])[:58]}")
    ev = ROOT / ".agent-company-ai" / "doodle_persona_state.json"
    ev.write_text(json.dumps({"made": made, "posted": posted,
                              "before": before, "after": len(after)}, indent=1))
    print("evidence:", ev.relative_to(ROOT))


if __name__ == "__main__":
    main()
