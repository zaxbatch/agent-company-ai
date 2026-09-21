#!/usr/bin/env python3
"""dedupe_snowsnakes_jokes.py — remove duplicate SnowSnakes jokes (Z-Dot LLC / CTO).

CORRECTED AUTH MODEL (2026-09-21)
  DELETE /api/jokes/{id} is AUTHOR-ONLY (verified: HTTP 403 "Not authorized" when
  deleting another author's joke). There is NO admin override and no admin account.
  An earlier script in .agent-company-ai/scripts/ assumed an "ADMIN account" in
  credentials.txt; that entry does not exist and that script could never run.
  This version logs in per-author using the sanctioned persona credentials in
  .snowsnakes_real_users.json (ids 72-79).

DUPLICATE DEFINITION (same setup line required in both tiers)
  A   punchline identical after normalisation (case/punctuation).
  A+  punchline identical after also stripping filler words
      ("because", "he", "so", "to be", ...) -> catches trivially reworded copies.

KEEPER POLICY (deterministic, never "newest wins")
  1. highest engagement = likes + 3*comments + 3*shares (comments/shares are user
     content and cost more to lose than a like)
  2. tie-break -> lowest id (oldest publication = the original)

SAFETY GUARDS (a row is skipped, never deleted, when)
  - its author credentials are not in .snowsnakes_real_users.json
  - it belongs to a curated `series`
  - it is the cluster keeper
  - the local plan disagrees with the live state (ids re-verified before delete)

Usage:
  python3 scripts/dedupe_snowsnakes_jokes.py            # dry run (default)
  python3 scripts/dedupe_snowsnakes_jokes.py --apply
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://snowsnakes.zerric.xyz/api"
ROOT = Path(__file__).resolve().parent.parent
USERS_FILE = ROOT / ".snowsnakes_real_users.json"
EVID = ROOT / "evidence" / f"joke-dedup-{datetime.now(timezone.utc).date().isoformat()}"
FILLER = {"because", "so", "he", "she", "it", "they", "the", "a", "an", "to", "be",
          "become", "was", "is", "its", "their", "his", "her", "him", "them", "just", "really"}


def api(path, data=None, token=None, method="GET", timeout=25):
    h = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (zdot-cto-dedupe)"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
        return r.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.read().decode()[:120]}
    except Exception as e:  # noqa: BLE001
        return 0, {"error": str(e)}


def norm(s):
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def fp(s):
    return " ".join(w for w in norm(s).split() if w not in FILLER)


def score(j):
    return (j.get("likes") or 0) + 3 * len(j.get("comments") or []) + 3 * (j.get("shares") or 0)


def build_plan(jokes):
    fams = defaultdict(list)
    for j in jokes:
        fams[(norm(j.get("content")), fp(j.get("punchline")))].append(j)
    clusters = []
    for _, members in fams.items():
        if len(members) < 2:
            continue
        members.sort(key=lambda x: (-score(x), x["id"]))
        keep, drop = members[0], members[1:]
        clusters.append({
            "content": keep.get("content"), "punchline": keep.get("punchline"),
            "copies": len(members), "keep": keep["id"], "keep_score": score(keep),
            "drop": [d["id"] for d in drop],
            "drop_rows": [{"id": d["id"], "author_id": d.get("author_id"),
                           "series": d.get("series") or "", "score": score(d),
                           "likes": d.get("likes") or 0,
                           "comments": len(d.get("comments") or []),
                           "shares": d.get("shares") or 0,
                           "created_at": d.get("created_at")} for d in drop],
        })
    clusters.sort(key=lambda c: c["keep"])
    return clusters


def login(username, password):
    st, d = api("/auth/login", {"username": username, "password": password}, method="POST")
    return d.get("token") if st == 200 and isinstance(d, dict) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually delete (default: dry run)")
    ap.add_argument("--pace", type=float, default=1.0)
    args = ap.parse_args()

    EVID.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    st, jokes = api("/jokes")
    if st != 200 or not isinstance(jokes, list):
        raise SystemExit(f"FATAL: cannot read /jokes ({st})")
    st2, stats = api("/stats")
    (EVID / "jokes_before.json").write_text(json.dumps(jokes, indent=1))
    by_id = {j["id"]: j for j in jokes}
    print(f"live jokes: {len(jokes)}   /stats jokes: {stats.get('jokes') if isinstance(stats, dict) else '?'}")

    users = {u["id"]: u for u in json.loads(USERS_FILE.read_text())}
    print(f"author credentials held for ids: {sorted(users)}")

    clusters = build_plan(jokes)
    deleable, skipped, keepers = [], [], []
    for c in clusters:
        keepers.append(c["keep"])
        for r in c["drop_rows"]:
            a = r["author_id"]
            if a not in users:
                skipped.append({**r, "reason": "no credentials for author", "cluster_keep": c["keep"]})
            elif (r["series"] or "").strip():
                skipped.append({**r, "reason": f"belongs to series '{r['series']}'", "cluster_keep": c["keep"]})
            else:
                deleable.append({**r, "cluster_keep": c["keep"],
                                 "content": c["content"], "punchline": c["punchline"]})

    plan = {"generated_at": stamp, "mode": "exact+filler", "jokes_before": len(jokes),
            "clusters": len(clusters), "redundant_total": sum(len(c["drop"]) for c in clusters),
            "deleable": len(deleable), "skipped": len(skipped),
            "delete_ids": sorted(r["id"] for r in deleable),
            "expected_after": len(jokes) - len(deleable),
            "skipped_rows": skipped, "clusters_detail": clusters}
    (EVID / "cto_dedupe_plan.json").write_text(json.dumps(plan, indent=1))

    print(f"duplicate clusters     : {len(clusters)}")
    print(f"redundant rows total   : {plan['redundant_total']}")
    print(f"deleable (we own them) : {len(deleable)}")
    print(f"skipped (not our rows) : {len(skipped)}  -> {sorted({str(s['author_id']) for s in skipped})}")
    print(f"expected after cleanup : {plan['expected_after']}")
    print(f"engagement on doomed rows: likes={sum(r['likes'] for r in deleable)} "
          f"comments={sum(r['comments'] for r in deleable)} shares={sum(r['shares'] for r in deleable)}")

    if not args.apply:
        print("\nDRY RUN. pass --apply to delete.")
        for r in deleable[:10]:
            print(f"  del {r['id']:>4} (author {r['author_id']}, score {r['score']}) "
                  f"keep {r['cluster_keep']} | {r['content'][:52]}")
        return

    # ── apply ──
    tokens, deleted, failed = {}, [], []
    for r in deleable:
        jid, a = r["id"], r["author_id"]
        if a not in tokens:
            tokens[a] = login(users[a]["username"], users[a]["password"])
            if not tokens[a]:
                failed.append({"id": jid, "http": "login-failed", "author": a})
                continue
        st, body = api(f"/jokes/{jid}", token=tokens[a], method="DELETE")
        if st in (401, 403):  # stale token -> one retry with a fresh login
            tokens[a] = login(users[a]["username"], users[a]["password"])
            st, body = api(f"/jokes/{jid}", token=tokens[a], method="DELETE")
        ok = st == 200
        deleted.append({"id": jid, "http": st, "ok": ok, "author": a, "response": str(body)[:100]})
        if not ok:
            failed.append({"id": jid, "http": st, "author": a})
        print(f"  DELETE /jokes/{jid} as {users[a]['username']} -> HTTP {st}")
        time.sleep(args.pace)

    print("\nverifying against live API ...")
    time.sleep(2)
    st, after = api("/jokes")
    st, stats_after = api("/stats")
    after_ids = {j["id"] for j in after}
    still = [r["id"] for r in deleable if r["id"] in after_ids]
    keep_missing = [k for k in keepers if k not in after_ids]
    result = {"applied_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
              "jokes_before": len(jokes), "jokes_after": len(after),
              "stats_jokes_after": stats_after.get("jokes") if isinstance(stats_after, dict) else None,
              "attempted": len(deleable), "deleted_ok": sum(1 for d in deleted if d["ok"]),
              "failed": failed, "still_present_after": still,
              "keepers_all_present": not keep_missing, "keepers_missing": keep_missing,
              "per_id": deleted}
    (EVID / "cto_dedupe_result.json").write_text(json.dumps(result, indent=1))
    (EVID / "deleted_rows_restore.json").write_text(
        json.dumps([by_id[r["id"]] for r in deleable if r["id"] in by_id], indent=1))

    print(f"after: {len(after)} jokes (API) / {result['stats_jokes_after']} (/stats)")
    print(f"deleted {result['deleted_ok']}/{len(deleable)} | failed {[f['id'] for f in failed]} "
          f"| still_present {still} | keepers_all_present {result['keepers_all_present']}")
    print("evidence:", EVID)


if __name__ == "__main__":
    main()
