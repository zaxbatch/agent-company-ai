#!/usr/bin/env python3
"""Check ez@zerric.xyz inbox via IMAP and report recent unread mail (subjects only).

Usage: python3 scripts/check_email.py [--limit 10] [--unread-only]
Prints sender + subject + date (never bodies/attachments unless --show-body).
"""
import argparse, imaplib, re, sys
from email.header import decode_header
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRED_FILE = ROOT / "communication" / "credentials.txt"
IMAP_HOST, IMAP_PORT = "imap.hostinger.com", 993
SENDER = "ez@zerric.xyz"

def load_password():
    text = CRED_FILE.read_text()
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().lower().startswith("ez@zerric.xyz"):
            for nxt in lines[i+1:i+3]:
                m = re.match(r"pass\s*[=:]\s*(\S+)", nxt.strip(), re.I)
                if m:
                    return m.group(1)
    raise RuntimeError("ez@zerric.xyz password not found")

def dec(s):
    if not s: return ""
    parts = decode_header(s)
    out = ""
    for txt, enc in parts:
        if isinstance(txt, bytes):
            try: out += txt.decode(enc or "utf-8", "replace")
            except Exception: out += txt.decode("utf-8", "replace")
        else:
            out += txt
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--unread-only", action="store_true")
    args = ap.parse_args()

    pw = load_password()
    M = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    M.login(SENDER, pw)
    M.select("INBOX")

    status, data = M.search(None, "UNSEEN" if args.unread_only else "ALL")
    ids = data[0].split()
    ids = ids[-args.limit:] if ids else []
    print(f"Inbox: {len(ids)} {'unread' if args.unread_only else 'recent'} message(s)")
    for i in reversed(ids):
        try:
            status, msg = M.fetch(i, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            raw = msg[0][1].decode("utf-8", "replace")
            frm = dec(re.search(r"^From: (.*)$", raw, re.M).group(1)) if re.search(r"^From: (.*)$", raw, re.M) else "?"
            subj = dec(re.search(r"^Subject: (.*)$", raw, re.M).group(1)) if re.search(r"^Subject: (.*)$", raw, re.M) else "(no subject)"
            date = re.search(r"^Date: (.*)$", raw, re.M).group(1) if re.search(r"^Date: (.*)$", raw, re.M) else "?"
            print(f"  [{i.decode()}] {frm[:40]:42} | {subj[:55]:57} | {date[:22]}")
        except Exception as e:
            print(f"  [{i.decode()}] error reading: {e}")
    M.logout()

if __name__ == "__main__":
    main()
