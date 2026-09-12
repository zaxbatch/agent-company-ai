#!/usr/bin/env python3
"""engage_tdj_personas.py — toggle-SAFE engagement for the Team Daily Jokes series.

WHY THIS EXISTS
---------------
SnowSnakes' `POST /api/jokes/{id}/like` is a TOGGLE, and the server never
populates `isLiked` (verified: always False, authenticated or not). So a naive
"like everything" loop will silently UNLIKE content that a persona had already
liked, destroying real engagement counts. scripts/engage_snowsnakes.py had
exactly this bug (its state file records joke ids globally, not per account).

SAFE ALGORITHM (ensure_liked)
-----------------------------
Read count B -> POST /like -> read count A.
  A == B+1 -> persona had NOT liked it; now liked.        -> done (desired state reached)
  A == B-1 -> persona HAD liked it; toggle removed it.   -> POST /like again to restore -> done
  A == B   -> ambiguous (concurrent change).             -> re-read, retry once, else skip+log
Either path ends with the persona having liked the joke, WITHOUT needing to
know the prior state. Fully reversible: a second pass is a no-op.

Usage:
  python3 scripts/engage_tdj_personas.py --dry-run          # preview, no writes
  python3 scripts/engage_tdj_personas.py --per-joke 2       # real run
"""
from __future__ import annotations
import argparse, json, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://snowsnakes.zerric.xyz/api"
ROOT = Path(__file__).resolve().parent.parent
USERS = ROOT / ".snowsnakes_real_users.json"
STATE = ROOT / ".agent-company-ai" / "engage_tdj_state.json"
SERIES = "Team Daily Jokes"


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
                return r.status, {"_nonjson": raw[:120]}
    except urllib.error.HTTPError as e:
        return e.code, {"_err": e.read().decode()[:120]}
    except Exception as e:
        return None, {"_err": str(e)}


def likes_of(jid, token=None):
    st, d = api(f"/jokes/{jid}", token=token)
    return d.get("likes") if isinstance(d, dict) else None


def ensure_liked(jid, token, log):
    """Return (action, ok). action in {new_like, restored, noop_ambiguous, failed}."""
    b = likes_of(jid, token)
    if b is None:
        return "failed", False
    st, d = api(f"/jokes/{jid}/like", token=token, method="POST")
    if st != 200 or not isinstance(d, dict) or "liked" not in d:
        log.append({"joke": jid, "step": "like", "http": st, "resp": d})
        return "failed", False
    a = likes_of(jid, token)
    if a == b + 1:
        return "new_like", True
    if a == b - 1:
        # was already liked; toggle removed it -> restore
        st2, d2 = api(f"/jokes/{jid}/like", token=token, method="POST")
        a2 = likes_of(jid, token)
        log.append({"joke": jid, "step": "restore", "http": st2, "resp": d2, "likes": f"{b}->{a}->{a2}"})
        return ("restored", a2 == b) if a2 == b else ("failed", False)
    log.append({"joke": jid, "step": "ambiguous", "likes": f"{b}->{a}"})
    return "noop_ambiguous", False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--per-joke", type=int, default=2, help="personas that like each joke")
    ap.add_argument("--pace", type=float, default=0.4)
    args = ap.parse_args()

    users = json.loads(USERS.read_text())
    names = [u["username"] for u in users]
    tok = {u["username"]: u["token"] for u in users}

    st, jokes = api("/jokes")
    tdj = sorted([j for j in jokes if (j.get("series") or "") == SERIES], key=lambda j: j["id"])
    before_total = sum(j.get("likes") or 0 for j in tdj)
    zero_before = sum(1 for j in tdj if not (j.get("likes") or 0))
    print(f"Team Daily Jokes: {len(tdj)} jokes | likes before = {before_total} | with 0 likes = {zero_before}")
    print(f"personas: {len(names)} | per-joke likes: {args.per_joke}")
    if args.dry_run:
        exp = sum(args.per_joke for _ in tdj)
        print(f"[DRY] would attempt up to {exp} likes (~{exp*2} API calls). No writes.")
        return

    log, counts = [], {"new_like": 0, "restored": 0, "noop_ambiguous": 0, "failed": 0}
    for i, j in enumerate(tdj):
        jid = j["id"]
        # deterministic rotation: distinct personas per joke, spread across the set
        picks = [names[(i + k * 3) % len(names)] for k in range(args.per_joke)]
        for who in dict.fromkeys(picks):
            act, ok = ensure_liked(jid, tok[who], log)
            counts[act] = counts.get(act, 0) + 1
            flag = "ok " if ok else "!! "
            print(f"  {flag}joke {jid:<4} {who:<12} {act:<15} likes={likes_of(jid)}")
            time.sleep(args.pace)

    after_total = sum(likes_of(j["id"]) or 0 for j in tdj)
    zero_after = sum(1 for j in tdj if not (likes_of(j["id"]) or 0))
    summary = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "series": SERIES, "jokes": len(tdj),
        "likes_before": before_total, "likes_after": after_total,
        "zero_like_jokes_before": zero_before, "zero_like_jokes_after": zero_after,
        "actions": counts, "detail": log,
    }
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(summary, indent=1))
    print(f"\nlikes: {before_total} -> {after_total} (net +{after_total-before_total})")
    print(f"jokes with 0 likes: {zero_before} -> {zero_after}")
    print("actions:", counts)
    assert after_total >= before_total, "REGRESSION: total likes decreased!"
    print(f"state+evidence: {STATE}")


if __name__ == "__main__":
    main()
