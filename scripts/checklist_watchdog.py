#!/usr/bin/env python3
"""Checklist watchdog: flags stale tasks and who hasn't checked in.

Reads the LIVE portal (tasks.zdotllc.com) - the single source of truth.
Run by Manny (PM) regularly, or via cron. Exits 1 if anything is stale.
Usage: python scripts/checklist_watchdog.py [--portal URL] [--stale-hours N]
"""
import argparse
import http.cookiejar
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

PORTAL = "https://tasks.zdotllc.com"
API = PORTAL + "/api.php?action=list"
STALE_HOURS = 2
CRED_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "communication", "portal_credentials.txt")

def _load_creds(member="NinjaNerd"):
    try:
        for line in open(CRED_FILE):
            m = re.match(r"([A-Za-z]+): username=(\S+) password=(\S+)", line.strip())
            if m and m.group(1) == member:
                return m.group(2), m.group(3)
    except FileNotFoundError:
        pass
    return None, None

def _session():
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.addheaders = [("User-Agent", "Mozilla/5.0 (watchdog)"), ("Content-Type", "application/json")]
    return opener, jar

def fetch_tasks(url, opener):
    # Login first (portal requires a session)
    user, pw = _load_creds()
    if not user:
        raise RuntimeError(f"no credentials found in {CRED_FILE}")
    login = PORTAL + "/auth.php?action=login"
    body = json.dumps({"username": user, "password": pw}).encode()
    req = urllib.request.Request(login, data=body, method="POST")
    with opener.open(req, timeout=20) as r:
        resp = json.loads(r.read().decode())
    if "user" not in resp:
        raise RuntimeError("login failed")
    req = urllib.request.Request(url, method="GET")
    with opener.open(req, timeout=20) as r:
        return json.loads(r.read().decode())

def parse(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--portal", default=PORTAL)
    ap.add_argument("--stale-hours", type=float, default=STALE_HOURS)
    args = ap.parse_args()

    api_url = args.portal.rstrip("/") + "/api.php?action=list"
    try:
        opener, _jar = _session()
        tasks = fetch_tasks(api_url, opener)
    except Exception as e:
        print(f"ERROR: cannot reach portal at {api_url}: {e}")
        return 2

    now = datetime.now(timezone.utc)
    open_tasks = [t for t in tasks if t["status"] not in ("done", "failed", "cancelled")]
    by_assignee = {}
    for t in open_tasks:
        by_assignee.setdefault(t["assignee"] or "unassigned", []).append(t)

    print(f"CHECKLIST WATCHDOG - {now.strftime('%Y-%m-%d %H:%M UTC')} (source: {api_url})")
    print("=" * 60)
    stale_any = False
    for assignee, items in sorted(by_assignee.items()):
        parsed = [p for p in (parse(t["last_checked_at"]) for t in items) if p]
        last = max(parsed) if parsed else None
        since = (now - last).total_seconds() / 3600 if last else None
        flag = ""
        if since is None:
            flag = "  [STALE: never checked in]"
            stale_any = True
        elif since > args.stale_hours:
            flag = f"  [STALE: {since:.1f}h since check-in]"
            stale_any = True
        print(f"{assignee}: {len(items)} open task(s), last check-in {since if since is not None else 'never'}{flag}")
        for t in sorted(items, key=lambda x: x.get("priority", 0)):
            b = f"  BLOCKER: {t['blocker']}" if t.get("blocker") else ""
            print(f"  - {t['id']}: {t['description'][:70]}{b}")
    print("=" * 60)
    if stale_any:
        print("ACTION: stale check-ins found. PM follows up with assignees.")
        return 1
    print("All assignees checked in recently. All clear.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
