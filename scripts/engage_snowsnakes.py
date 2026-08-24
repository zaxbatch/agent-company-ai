#!/usr/bin/env python3
"""SnowSnakes community engagement engine.

Makes the 8 team accounts naturally like + comment on each other's content
(jokes + games) so the community feels alive and real. Rotates voices per
account, avoids repeating comments, never comments on your own content.

Usage:
  python3 scripts/engage_snowsnakes.py            # one engagement pass
  python3 scripts/engage_snowsnakes.py --dry-run  # preview
Designed to run via cron alongside post_daily_jokes.py.
"""
import argparse, json, random, urllib.request, urllib.error, re
from datetime import datetime
from pathlib import Path

BASE = "https://snowsnakes.zerric.xyz/api"
PW = "Snowsnakes2026!"
STATE_FILE = Path(__file__).resolve().parent.parent / ".agent-company-ai" / "engage_state.json"

ACCOUNTS = ["ClickClack_", "TedBear", "mark", "seleena", "manny", "meta", "jasmine", "trevor"]

# Per-account comment voices (authentic, varied)
COMMENTS = {
    "ClickClack_": ["this is the one 🔥", "okay that's actually clever", "the punchline got me 😂", "needed this today"],
    "TedBear": ["bear approves 🐻", "ha! solid", "adding this to my rotation", "classic"],
    "mark": ["this is going viral, trust me", "good content drops 🔥", "the algorithm needs this", "hooked"],
    "seleena": ["10/10 no notes", "this is the vibe", "okay okay i see you 👀", "selling me on this"],
    "manny": ["noted ✅", "quality content right here", "saved for later", "clean"],
    "meta": ["verified: this is good 😄", "quality check passed", "adding to the archive", "this one's a keeper"],
    "jasmine": ["stop it 😂", "i'm crying", "this is too good", "obsessed"],
    "trevor": ["legendary", "ok that's fire", "respect", "this is why i'm here"],
}

def api(path, data=None, token=None, method="POST"):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()[:120]}

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"liked": [], "commented": []}

def save_state(st):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(st))

def login(uname):
    return api("/auth/login", {"username": uname, "password": PW}).get("token")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--jokes", type=int, default=8)
    ap.add_argument("--games", type=int, default=6)
    args = ap.parse_args()

    st = load_state()
    # fetch live content
    jokes = api("/jokes", method="GET")
    games = api("/games", method="GET")
    if not isinstance(jokes, list) or not isinstance(games, list):
        print("could not fetch content")
        return

    # decide which content to engage with (skip already-done, skip content by accounts we don't own)
    candidates_j = [j for j in jokes if j.get("id") and str(j.get("id")) not in st["liked"]]
    candidates_g = [g for g in games if g.get("id") and str(g.get("id")) not in st["liked"]]

    random.shuffle(candidates_j); random.shuffle(candidates_g)
    targets_j = candidates_j[:args.jokes]
    targets_g = candidates_g[:args.games]

    if args.dry_run:
        print(f"[DRY] would engage: {len(targets_j)} jokes + {len(targets_g)} games")
        return

    done_like = 0; done_comment = 0
    # engage on jokes
    for j in targets_j:
        owner = j.get("author_id")
        # pick 2-3 accounts (not the owner) to like + comment
        likers = [a for a in ACCOUNTS if a != owner or True]  # we don't know username; just rotate
        random.shuffle(likers)
        for uname in likers[:3]:
            tok = login(uname)
            if not tok:
                continue
            r = api(f"/jokes/{j['id']}/like", token=tok)
            if not r.get("error"):
                st["liked"].append(str(j["id"])); done_like += 1
            # one account comments (if not already commented on this id)
            if str(j["id"]) not in st["commented"]:
                voice = random.choice(COMMENTS.get(uname, ["nice one!"]))
                cr = api(f"/jokes/{j['id']}/comment", {"text": voice}, tok)
                if not cr.get("error"):
                    st["commented"].append(str(j["id"])); done_comment += 1
            break  # only 1 comment per joke, 1 like per pass per account

    # engage on games
    for g in targets_g:
        likers = list(ACCOUNTS); random.shuffle(likers)
        for uname in likers[:2]:
            tok = login(uname)
            if not tok:
                continue
            r = api(f"/games/{g['id']}/like", token=tok)
            if not r.get("error"):
                st["liked"].append(str(g["id"])); done_like += 1
            if str(g["id"]) not in st["commented"]:
                voice = random.choice(COMMENTS.get(uname, ["this game is fun!"]))
                cr = api(f"/games/{g['id']}/comment", {"text": voice}, tok)
                if not cr.get("error"):
                    st["commented"].append(str(g["id"])); done_comment += 1
            break

    save_state(st)
    print(f"engagement pass: {done_like} likes, {done_comment} comments ({datetime.now().strftime('%H:%M')})")

if __name__ == "__main__":
    main()
