#!/usr/bin/env python3
"""Save current team state so we can resume after any disconnect/reboot.

Syncs: live portal tasks -> state/portal_snapshot.json
       snowsnakes content counts -> state/snowsnakes_snapshot.json
       stamps TEAM-STATE.md with last-updated + git commit.

Run:  python3 scripts/save_state.py        (snapshot + commit)
      python3 scripts/save_state.py --no-commit
"""
import argparse, json, os, re, subprocess, sys, urllib.request, http.cookiejar
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "state"
STATE_DIR.mkdir(exist_ok=True)


def log_chat(speaker, msg):
    """Append a chat message to persistent CHAT-LOG.md (immediate memory)."""
    from pathlib import Path
    import subprocess, sys
    log = Path(__file__).resolve().parent.parent / "state" / "CHAT-LOG.md"
    ts = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if not log.exists():
        log.write_text("# Z-Dot Team Chat Log (persistent memory)\n\n> Every chat message is appended here so nothing is lost.\n\n")
    with log.open("a") as f:
        f.write(f"### {ts} — {speaker}\n{msg}\n\n")
    return str(log)

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def get_portal_tasks():
    """Login to portal + fetch tasks. Best-effort; returns [] on failure."""
    cred_file = ROOT / "communication" / "portal_credentials.txt"
    try:
        user = pw = None
        for line in cred_file.read_text().splitlines():
            m = re.match(r"([A-Za-z]+): username=(\S+) password=(\S+)", line.strip())
            if m and m.group(1) == "ClickClack":
                user, pw = m.group(2), m.group(3)
        if not user:
            return []
        jar = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        opener.addheaders = [("User-Agent", "Mozilla/5.0 (save_state)"), ("Content-Type", "application/json")]
        req = urllib.request.Request("https://tasks.zdotllc.com/auth.php?action=login",
                                     data=json.dumps({"username": user, "password": pw}).encode(), method="POST")
        with opener.open(req, timeout=20) as r:
            json.loads(r.read().decode())
        with opener.open("https://tasks.zdotllc.com/api.php?action=list", timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print("portal snapshot failed:", e)
        return []

def get_snowsnakes_counts():
    counts = {}
    for ep in ["jokes", "games", "characters", "comics", "doodles", "episodes"]:
        try:
            with urllib.request.urlopen(f"https://snowsnakes.zerric.xyz/api/{ep}", timeout=15) as r:
                data = json.loads(r.read().decode())
                counts[ep] = len(data) if isinstance(data, list) else "n/a"
        except Exception as e:
            counts[ep] = f"err:{e}"
    return counts

def git_commit(msg):
    try:
        subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
        subprocess.run(["git", "commit", "-m", msg], cwd=ROOT, check=True)
        print("committed:", msg)
    except subprocess.CalledProcessError as e:
        print("commit skipped (nothing to commit or git error):", e)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-commit", action="store_true")
    args = ap.parse_args()

    stamp = now_iso()
    tasks = get_portal_tasks()
    counts = get_snowsnakes_counts()

    (STATE_DIR / "portal_snapshot.json").write_text(json.dumps(tasks, indent=2))
    (STATE_DIR / "snowsnakes_snapshot.json").write_text(json.dumps({**counts, "snapshot_at": stamp}, indent=2))

    # Update TEAM-STATE.md timestamp
    ts_file = ROOT / "TEAM-STATE.md"
    text = ts_file.read_text()
    text = re.sub(r"\*\*Last updated:\*\* .*", f"**Last updated:** {stamp}", text, count=1)
    ts_file.write_text(text)

    open_tasks = [t for t in tasks if t.get("status") not in ("done", "failed", "cancelled")]
    print(f"snapshot {stamp}: portal tasks={len(tasks)} open={len(open_tasks)} snowsnakes={counts}")

    if not args.no_commit:
        git_commit(f"state: snapshot {stamp}")

if __name__ == "__main__":
    main()
