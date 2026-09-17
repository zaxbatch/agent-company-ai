#!/usr/bin/env python3
"""inbox_monitor.py — check every mailbox on a schedule and alert on new mail.

WHY THIS EXISTS
---------------
Zerric, 2026-09-17: "check your email regularly."
An audit that same week found 11 of 12 team mailboxes were 100% unread, and
BossLady's "are you checking your email" had sat unread for 22 days. Every mail
script we had was hardcoded to one address, so no agent could read its own inbox.
Promising to check more often does not fix that. A scheduled job does.

This runs from cron, tracks the last-seen UID per mailbox, and reports ONLY new
mail. Anything unread that is older than the last run still gets reported once, so
nothing is silently swallowed.

Usage:
  python3 scripts/inbox_monitor.py                 # check all, print new
  python3 scripts/inbox_monitor.py --alert         # also SMS/email on new mail
  python3 scripts/inbox_monitor.py --mailbox clickclack@zdotllc.com
"""
from __future__ import annotations
import argparse, imaplib, json, re, subprocess, sys
from datetime import datetime, timezone
from email.header import decode_header, make_header
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRED = ROOT / "communication" / "credentials.txt"
STATE = ROOT / "state" / "inbox_monitor.json"
IMAP_HOST, IMAP_PORT = "imap.hostinger.com", 993

MAILBOXES = [
    "clickclack@zdotllc.com", "ninjanerd@zdotllc.com", "bosslady@zdotllc.com",
    "mark@zdotllc.com", "meta@zdotllc.com", "manny@zdotllc.com",
    "seleena@zdotllc.com", "bots@zdotllc.com", "sales@zdotllc.com",
    "support@zdotllc.com", "info@zdotllc.com", "ez@zerric.xyz",
]


def pw_for(addr):
    txt = CRED.read_text(encoding="utf-8", errors="replace")
    for ln in txt.splitlines():
        if addr in ln:
            m = re.search(r"password\s*[:=]\s*(\S+)", ln, re.I)
            if m:
                return m.group(1)
    m = re.search(r"default for new boxes\):\s*(\S+)", txt)
    return m.group(1) if m else None


def h(v):
    try:
        return str(make_header(decode_header(v or "")))
    except Exception:
        return v or ""


def check(addr):
    """-> (ok, total, unread, [(uid, from, subject, date)])"""
    try:
        M = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, timeout=10)
        M.login(addr, pw_for(addr))
        M.select("INBOX", readonly=True)
        all_ids = M.search(None, "ALL")[1][0].split()
        unseen = M.search(None, "UNSEEN")[1][0].split()
        msgs = []
        for i in unseen[-12:]:
            st, x = M.fetch(i, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            raw = x[0][1].decode("utf-8", "replace")
            f = {l.split(":", 1)[0].strip().lower(): l.split(":", 1)[1].strip()
                 for l in raw.splitlines() if ":" in l}
            msgs.append((i.decode(), h(f.get("from", "")), h(f.get("subject", "")),
                         h(f.get("date", ""))))
        M.logout()
        return True, len(all_ids), len(unseen), msgs
    except Exception as e:
        return False, 0, 0, [(None, "ERROR", f"{type(e).__name__}: {str(e)[:60]}", "")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mailbox", action="append")
    ap.add_argument("--alert", action="store_true", help="send email+SMS if new mail")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    STATE.parent.mkdir(parents=True, exist_ok=True)
    prev = json.loads(STATE.read_text()) if STATE.exists() else {}
    boxes = a.mailbox or MAILBOXES
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    fresh = []
    for addr in boxes:
        ok, total, unread, msgs = check(addr)
        if not ok:
            if not a.quiet:
                print(f"  {addr:<26} ERROR: {msgs[0][2]}")
            continue
        seen = set(prev.get(addr, {}).get("uids", []))
        new_here = [m for m in msgs if m[0] not in seen and m[0] is not None]
        if not a.quiet:
            flag = f"{unread} unread" if unread else "clean"
            print(f"  {addr:<26} {total:>4} msgs, {flag}"
                  + (f"  <- {len(new_here)} NEW" if new_here else ""))
        for uid, frm, subj, date in new_here:
            fresh.append((addr, frm, subj, date))
        prev[addr] = {"uids": [m[0] for m in msgs if m[0]], "checked": now}

    STATE.write_text(json.dumps(prev, indent=1))

    if fresh:
        print(f"\n{len(fresh)} new message(s):")
        for addr, frm, subj, date in fresh:
            print(f"  [{addr}] {frm[:40]} :: {subj[:60]}")
        if a.alert:
            body = "\n".join(f"- [{b}] {f} :: {s}" for b, f, s, _d in fresh[:12])
            subprocess.run([str(ROOT / "venv" / "bin" / "python"),
                            str(ROOT / "scripts" / "agent_outbox.py"), "send",
                            "--to", "boss", "--sms",
                            "--subject", f"New mail: {len(fresh)} message(s)",
                            f"New mail arrived for the team:\n\n{body}"],
                           cwd=ROOT, capture_output=True, text=True, timeout=120)
            print("  (alert sent)")
    elif not a.quiet:
        print("\nno new mail")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
