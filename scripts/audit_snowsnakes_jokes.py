#!/usr/bin/env python3
"""CTO audit: read-only duplicate analysis of SnowSnakes jokes (no writes, no deletes)."""
import json
import re
import urllib.request
from collections import defaultdict

BASE = "https://snowsnakes.zerric.xyz/api"


def api(path, data=None, token=None, method="GET"):
    h = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (zdot-cto-audit)"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(BASE + path, data=body, method=method, headers=h)
    with urllib.request.urlopen(r, timeout=30) as resp:
        raw = resp.read().decode()
    return json.loads(raw) if raw.strip() else {}


def norm(s):
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def score(j):
    return (j.get("likes") or 0) + 3 * len(j.get("comments") or []) + 3 * (j.get("shares") or 0)


def main():
    jokes = api("/jokes")
    print(f"live jokes: {len(jokes)}  ids {min(j['id'] for j in jokes)}-{max(j['id'] for j in jokes)}")

    full = defaultdict(list)
    for j in jokes:
        full[(norm(j.get("content")), norm(j.get("punchline")))].append(j)
    exact = {k: v for k, v in full.items() if len(v) > 1}

    setup = defaultdict(list)
    for j in jokes:
        setup[norm(j.get("content"))].append(j)
    same_setup = {k: v for k, v in setup.items() if len(v) > 1}

    # same setup AND identical punchline after filler-strip (near-dupe tier)
    FILLER = {"because", "so", "he", "she", "it", "they", "the", "a", "an", "to", "be",
              "become", "was", "is", "its", "their", "his", "her", "him", "them", "just", "really"}

    def fp(s):
        return " ".join(w for w in norm(s).split() if w not in FILLER)

    near = defaultdict(list)
    for j in jokes:
        near[(norm(j.get("content")), fp(j.get("punchline")))].append(j)
    near_dupes = {k: v for k, v in near.items() if len(v) > 1}

    print(f"\nA  identical setup+punchline : {len(exact)} clusters / {sum(len(v)-1 for v in exact.values())} redundant rows")
    print(f"A+ identical setup + filler-stripped punchline (includes A): {len(near_dupes)} clusters / {sum(len(v)-1 for v in near_dupes.values())} redundant rows")
    print(f"B  same setup, different punchline: {len(same_setup)} groups / {sum(len(v) for v in same_setup.values())} rows (editorial - NOT deleable)")

    print("\n--- A+ clusters (keeper = highest engagement, tie -> oldest id) ---")
    rows = []
    for (c, p), members in sorted(near_dupes.items(), key=lambda kv: -len(kv[1])):
        members = sorted(members, key=lambda x: (-score(x), x["id"]))
        keep, drop = members[0], members[1:]
        rows.append({"keep": keep["id"], "drop": [d["id"] for d in drop],
                     "content": keep["content"], "punchline": keep["punchline"],
                     "keep_score": score(keep), "drop_scores": [score(d) for d in drop],
                     "drop_engagement": sum(score(d) for d in drop)})
        print(f"  keep {keep['id']:>4} (s={score(keep)})  drop {[d['id'] for d in drop]} (s={[score(d) for d in drop]})")
        print(f"       Q: {keep['content']}")
        print(f"       A: {keep['punchline']}")

    dropped = [i for r in rows for i in r["drop"]]
    print(f"\nTOTAL redundant rows to delete: {len(dropped)}  ->  {len(jokes)} - {len(dropped)} = {len(jokes)-len(dropped)}")
    print("engagement on doomed rows:", sum(r['drop_engagement'] for r in rows))

    out = {"live": len(jokes), "tierA_clusters": len(exact),
           "tierAplus_clusters": len(near_dupes), "tierB_groups": len(same_setup),
           "delete_ids": sorted(dropped), "plan": rows,
           "tierB": [{"content": v[0]["content"], "ids": sorted(x["id"] for x in v),
                      "punchlines": [x["punchline"] for x in v]}
                     for v in same_setup.values()]}
    with open("evidence/joke-dedup-20260921/cto_audit_plan.json", "w") as f:
        json.dump(out, f, indent=1)
    print("plan -> evidence/joke-dedup-20260921/cto_audit_plan.json")


if __name__ == "__main__":
    main()
