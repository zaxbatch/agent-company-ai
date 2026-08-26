#!/usr/bin/env python3
"""SnowSnakes team interaction tool — ONE authentic account, human-like pace.

Usage:
  python3 scripts/team_interact_snowsnakes.py like-game 85
  python3 scripts/team_interact_snowsnakes.py comment-game 85 "great beat maker, love the 8-bit vibe 🔥"
  python3 scripts/team_interact_snowsnakes.py like-joke 14
  python3 scripts/team_interact_snowsnakes.py comment-joke 14 "classic 😄"

Rules enforced by design:
  * ONE shared account (zdot_team) read from communication/credentials.txt — never hardcoded.
  * Rate limit: min interval between actions (default 45s, floor 30s). No bursts, no spam.
  * Every action prints BEFORE -> AFTER counts straight from the DB-backed API (proof, not claims).
  * Liking twice toggles UNLIKE — the script checks current like state first and refuses to double-like.

Requires: python3 stdlib only.
"""
import argparse, json, re, sys, time, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

BASE = "https://snowsnakes.zerric.xyz/api"
CREDS_FILE = Path(__file__).resolve().parent.parent / "communication" / "credentials.txt"
_last_action = 0.0

def read_creds():
    """Parse the team account entry from communication/credentials.txt (never commit it)."""
    txt = CREDS_FILE.read_text()
    m = re.search(r"- SnowSnakes team account: username: (\S+) \| email: \S+ \| password: (\S+) \| user_id: (\d+)", txt)
    if not m:
        sys.exit("FATAL: team account entry not found in communication/credentials.txt")
    return m.group(1), m.group(2), m.group(3)

def api(path, data=None, token=None, method="POST"):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {"error": "http " + str(e.code)}

def pace(interval):
    """Enforce human-like pacing: never fire two actions closer than `interval` seconds."""
    global _last_action
    wait = interval - (time.time() - _last_action)
    if wait > 0:
        print(f"  ...pacing: sleeping {wait:.0f}s (rate limit {interval}s) ...")
        time.sleep(wait)
    _last_action = time.time()

def get_state(kind, cid, token):
    """Return (likes, comments_len, is_liked) for a game/joke from the DB-backed API."""
    st, d = api(f"/{kind}s/{cid}", method="GET", token=token)
    if st != 200:
        sys.exit(f"FATAL: GET /{kind}s/{cid} -> {st} {d}")
    likes = d.get("likes", 0)
    comments = d.get("comments") or []
    is_liked = bool(d.get("isLiked") or d.get("liked_by"))
    return likes, len(comments), is_liked

def do_like(kind, cid, token, interval):
    before_likes, before_c, before_isl = get_state(kind, cid, token)
    if before_isl:
        print(f"SKIP {kind} {cid}: already liked by {kind[0]}_team — refusing to toggle-unlike.")
        return
    print(f"BEFORE: {kind} {cid} likes={before_likes} comments={before_c}")
    pace(interval)
    st, d = api(f"/{kind}s/{cid}/like", token=token)
    after_likes, after_c, _ = get_state(kind, cid, token)
    ok = (st == 200 and d.get("liked") is True and after_likes == before_likes + 1)
    print(f"POST /{kind}s/{cid}/like -> HTTP {st} {d}")
    print(f"AFTER:  {kind} {cid} likes={after_likes} comments={after_c}")
    print(("✅ VERIFIED +1 like, DB `likes` column incremented.") if ok else "❌ NOT VERIFIED — investigate!")
    return ok

def do_comment(kind, cid, text, token, interval):
    before_likes, before_c, _ = get_state(kind, cid, token)
    print(f"BEFORE: {kind} {cid} likes={before_likes} comments={before_c}")
    pace(interval)
    st, d = api(f"/{kind}s/{cid}/comment", {"text": text}, token)
    after_likes, after_c, _ = get_state(kind, cid, token)
    ok = (st == 201 and after_c == before_c + 1)
    print(f"POST /{kind}s/{cid}/comment -> HTTP {st}")
    print(f"AFTER:  {kind} {cid} likes={after_likes} comments={after_c}")
    st2, comments = api(f"/{kind}s/{cid}/comments", method="GET")
    mine = [c for c in (comments or []) if c.get("username") == "zdot_team"]
    if mine:
        print(f"  latest comment by zdot_team: \"{mine[0].get('text','')[:60]}\" (id {mine[0].get('id')})")
    print(("✅ VERIFIED +1 comment row in DB `comments` table.") if ok else "❌ NOT VERIFIED — investigate!")
    return ok

def main():
    ap = argparse.ArgumentParser(description="SnowSnakes team interaction (one account, human-like).")
    ap.add_argument("action", choices=["like-game", "comment-game", "like-joke", "comment-joke"])
    ap.add_argument("content_id", type=int)
    ap.add_argument("text", nargs="?", default=None, help="comment text (required for comment-*)")
    ap.add_argument("--interval", type=int, default=45, help="min seconds between actions (default 45, floor 30)")
    args = ap.parse_args()
    interval = max(30, args.interval)

    username, password, user_id = read_creds()
    st, d = api("/auth/login", {"username": username, "password": password})
    if st != 200 or "token" not in d:
        sys.exit(f"FATAL: login failed ({st}) — check credentials entry in communication/credentials.txt")
    token = d["token"]
    print(f"logged in as {username} (id {user_id}) @ {datetime.now().strftime('%H:%M:%S')}")

    ok = False
    if args.action == "like-game":
        ok = do_like("game", args.content_id, token, interval)
    elif args.action == "comment-game":
        if not args.text: sys.exit("comment-game requires TEXT (quote it)")
        ok = do_comment("game", args.content_id, args.text, token, interval)
    elif args.action == "like-joke":
        ok = do_like("joke", args.content_id, token, interval)
    elif args.action == "comment-joke":
        if not args.text: sys.exit("comment-joke requires TEXT (quote it)")
        ok = do_comment("joke", args.content_id, args.text, token, interval)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
