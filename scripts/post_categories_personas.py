#!/usr/bin/env python3
"""post_categories_personas.py — seed one dad joke into every canonical category.

Posted as the 8 sanctioned SnowSnakes personas (ids 72-79), rotating authorship
so no single account looks like a spam source.

CATEGORY SOURCE: tags are FREE TEXT on this platform (the submit form says
"comma separated"), so there is no server-side category list. The 11 categories
below are the clean, canonical tags actually in use on the live site. Excluded
deliberately: sprawl duplicates ("food (general, NOT food truck)", "travel &
vehicles", "home & everyday") and junk test tags ("qa", "test", "verification").

REVERSIBILITY: every joke is created by a persona we control, so any post here
can be reverted with DELETE /api/jokes/{id} (author-only; verified).
NOTE: comments are NOT reversible on this platform — do not add comments.

Usage:
  python3 scripts/post_categories_personas.py --dry-run
  python3 scripts/post_categories_personas.py
"""
from __future__ import annotations
import argparse, json, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://snowsnakes.zerric.xyz/api"
ROOT = Path(__file__).resolve().parent.parent
USERS = ROOT / ".snowsnakes_real_users.json"
EVID = ROOT / ".agent-company-ai" / "category_posts_state.json"

# (category tag, setup, punchline)
CONTENT = [
    ("dad-joke", "Why don't eggs tell jokes?", "They'd crack each other up."),
    ("music",    "Why did the singer need a ladder?", "To reach the high notes."),
    ("tech",     "Why did the developer go broke?", "He used up all his cache."),
    ("food",     "Why did the tomato turn red?", "Because it saw the salad dressing."),
    ("animals",  "What do you call a bear with no teeth?", "A gummy bear."),
    ("health",   "Why did the doctor carry a red pen?", "In case he needed to draw blood."),
    ("travel",   "Why did the traveller bring a ladder to the airport?", "He wanted a window seat on the way up."),
    ("weather",  "What did one raindrop say to the other?", "Two's company, three's a cloud."),
    ("gaming",   "Why did the gamer bring a ladder to the arcade?", "To reach the next level."),
    ("books",    "Why did the librarian slip on the floor?", "She was in the non-friction section."),
    ("snowsnakes", "Why did the snow snake bring a scarf to the party?", "He heard it was going to be a cold open."),
]


def api(path, data=None, token=None, method="GET"):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode()
            try:
                return r.status, json.loads(raw)
            except Exception:
                return r.status, {"_nonjson": raw[:100]}
    except urllib.error.HTTPError as e:
        return e.code, {"_err": e.read().decode()[:120]}
    except Exception as e:
        return None, {"_err": str(e)}


def likes_of(jid):
    st, d = api(f"/jokes/{jid}")
    return d.get("likes") if isinstance(d, dict) else None


def ensure_liked(jid, token):
    """End state = liked, without knowing prior state (POST /like is a toggle)."""
    b = likes_of(jid)
    st, d = api(f"/jokes/{jid}/like", token=token, method="POST")
    if st != 200:
        return "failed", False
    a = likes_of(jid)
    if a == b + 1:
        return "new_like", True
    if a == b - 1:                      # was already liked -> restore
        api(f"/jokes/{jid}/like", token=token, method="POST")
        return "restored", likes_of(jid) == b
    return "ambiguous", False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--likes-per-post", type=int, default=2)
    ap.add_argument("--pace", type=float, default=0.3)
    a = ap.parse_args()

    users = json.loads(USERS.read_text())
    names = [u["username"] for u in users]
    tok = {u["username"]: u["token"] for u in users}

    if a.dry_run:
        print(f"[DRY] {len(CONTENT)} categories, 1 joke each, rotating personas:")
        for i, (cat, setup, punch) in enumerate(CONTENT):
            print(f"   {cat:<11} by {names[i % len(names)]:<11} | {setup}")
        print(f"[DRY] then {a.likes_per_post} likes/post from other personas. No writes.")
        return

    created, results = [], []
    for i, (cat, setup, punch) in enumerate(CONTENT):
        author = names[i % len(names)]
        st, d = api("/jokes", {"content": setup, "punchline": punch, "tags": [cat]}, tok[author], "POST")
        jid = d.get("id") if isinstance(d, dict) else None
        ok = st == 201 and jid
        print(f"  {'ok ' if ok else '!! '}POST /jokes [{cat:<11}] as {author:<11} -> HTTP {st} id={jid}")
        if ok:
            created.append({"id": jid, "category": cat, "author": author, "content": setup, "punchline": punch})
            # engage from OTHER personas (never the author)
            others = [n for n in names if n != author]
            for k in range(a.likes_per_post):
                who = others[(i + k * 3) % len(others)]
                act, good = ensure_liked(jid, tok[who])
                results.append({"joke": jid, "category": cat, "liker": who, "action": act, "ok": good})
                print(f"       {'ok ' if good else '!! '}like by {who:<11} {act}")
                time.sleep(a.pace)
        time.sleep(a.pace)

    # verify live
    st, all_j = api("/jokes")
    live = {j["id"]: j for j in all_j}
    print(f"\nfeed total: {len(all_j)} jokes")
    verified = 0
    for c in created:
        j = live.get(c["id"])
        if j:
            verified += 1
            print(f"  VERIFIED id={c['id']:<4} [{c['category']:<11}] author={j.get('author_id')} "
                  f"tags={j.get('tags')} likes={j.get('likes')}")
        else:
            print(f"  MISSING id={c['id']} [{c['category']}]")
    like_ok = sum(1 for r in results if r["ok"])
    out = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "categories": len(CONTENT), "created": created,
        "verified_live": verified, "like_attempts": len(results), "like_ok": like_ok,
        "likes": results,
        "rollback": "DELETE /api/jokes/{id} as the author persona (author-only). Do NOT comment.",
    }
    EVID.parent.mkdir(parents=True, exist_ok=True)
    EVID.write_text(json.dumps(out, indent=1))
    print(f"\ncreated+live: {verified}/{len(CONTENT)} | likes ok: {like_ok}/{len(results)}")
    print(f"evidence: {EVID}")


if __name__ == "__main__":
    main()
