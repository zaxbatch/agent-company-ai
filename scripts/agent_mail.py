#!/usr/bin/env python3
"""agent_mail.py — read/send mail from ANY Z-Dot agent mailbox.

WHY THIS EXISTS
---------------
The team mailboxes (clickclack@, ninjanerd@, bosslady@, mark@, meta@, manny@,
seleena@, bots@, ...) were created 2026-08-25, but every existing mail script
(send_email.py, send_message.py, check_email.py) was hardcoded to ez@zerric.xyz.
No agent had a way to read its own inbox -- so nobody ever did. Verified
2026-09-15: every single mailbox had UNSEEN == total. Zerric's replies sat
unread for 21 days.

This script closes that gap: pass --as <mailbox> and it works for any agent.

USAGE
  python3 scripts/agent_mail.py read  --as clickclack@zdotllc.com [--unseen-only] [--limit 10]
  python3 scripts/agent_mail.py send  --as clickclack@zdotllc.com --to ninjanerd@zdotllc.com \
                                      --subject "..." --body "..."
  python3 scripts/agent_mail.py sweep            # every mailbox: unread counts (triage)

Secrets are read from communication/credentials.txt (git-ignored) and never printed.
"""
import argparse, email, imaplib, re, smtplib, ssl, sys
from email.header import decode_header, make_header
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRED = ROOT / "communication" / "credentials.txt"
IMAP_HOST, IMAP_PORT = "imap.hostinger.com", 993
SMTP_HOST, SMTP_PORT = "smtp.hostinger.com", 465
TEAM = ["zerric@zdotllc.com", "bosslady@zdotllc.com", "bots@zdotllc.com",
        "ninjanerd@zdotllc.com", "clickclack@zdotllc.com", "mark@zdotllc.com",
        "meta@zdotllc.com", "manny@zdotllc.com", "seleena@zdotllc.com",
        "sales@zdotllc.com", "support@zdotllc.com", "info@zdotllc.com"]


def cred_text():
    return CRED.read_text(encoding="utf-8", errors="replace")


def password_for(addr):
    """Return the password for *addr* from credentials.txt. Never logs the value."""
    for ln in cred_text().splitlines():
        if addr in ln:
            m = re.search(r"password\s*[:=]\s*(\S+)", ln, re.I)
            if m:
                return m.group(1)
    m = re.search(r"default for new boxes\):\s*(\S+)", cred_text())
    if m:
        return m.group(1)
    raise RuntimeError(f"no password found for {addr} in {CRED}")


def hdr(val):
    try:
        return str(make_header(decode_header(val or "")))
    except Exception:
        return val or ""


def connect_imap(addr, pw):
    M = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, timeout=25)
    M.login(addr, pw)
    return M


def cmd_read(args):
    M = connect_imap(args.as_addr, password_for(args.as_addr))
    M.select("INBOX", readonly=True)
    crit = "UNSEEN" if args.unseen_only else "ALL"
    st, d = M.search(None, crit)
    ids = d[0].split()
    print(f"{args.as_addr}: {len(ids)} message(s) [{'unseen only' if args.unseen_only else 'all'}]")
    for i in ids[-args.limit:]:
        st, x = M.fetch(i, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)] FLAGS)")
        raw = x[0][1].decode("utf-8", "replace")
        flags = re.search(r"FLAGS \(([^)]*)\)", x[0][0].decode() if isinstance(x[0], tuple) else "") \
            or re.search(r"FLAGS \(([^)]*)\)", raw)
        fields = {l.split(":", 1)[0].strip().lower(): l.split(":", 1)[1].strip()
                  for l in raw.splitlines() if ":" in l}
        print(f"  [{flags.group(1).strip() if flags else '?'}] {hdr(fields.get('date',''))}")
        print(f"      from: {hdr(fields.get('from',''))}")
        print(f"      subj: {hdr(fields.get('subject',''))}")
    M.logout()


def cmd_send(args):
    addr, pw = args.as_addr, password_for(args.as_addr)
    msg = MIMEText(args.body, "plain", "utf-8")
    msg["Subject"] = args.subject
    msg["From"] = formataddr((args.from_name, addr))
    msg["To"] = args.to
    if args.cc:
        msg["Cc"] = args.cc
    msg["Date"] = formatdate(localtime=True)
    rcpt = [r.strip() for r in ([args.to] + (args.cc.split(",") if args.cc else [])) if r.strip()]
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=25) as s:
        s.login(addr, pw)
        s.sendmail(addr, rcpt, msg.as_string())
    print(f"sent: {'/'.join(rcpt)} (from {addr})")


def cmd_sweep(args):
    """Triage every team mailbox: how much inbound has never been read?"""
    print(f"{'mailbox':<28} {'total':>6} {'unread':>7}  status")
    print("-" * 62)
    for addr in TEAM:
        try:
            M = connect_imap(addr, password_for(addr))
            M.select("INBOX", readonly=True)
            total = len(M.search(None, "ALL")[1][0].split())
            unseen = len(M.search(None, "UNSEEN")[1][0].split())
            flag = "NEVER READ" if total and unseen == total else ("has unread" if unseen else "ok")
            print(f"{addr:<28} {total:>6} {unseen:>7}  {flag}")
            M.logout()
        except Exception as e:
            print(f"{addr:<28} {'-':>6} {'-':>7}  ERR {type(e).__name__}")


def main():
    ap = argparse.ArgumentParser(description="Read/send mail from any Z-Dot agent mailbox")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("read"); r.add_argument("--as", dest="as_addr", required=True)
    r.add_argument("--limit", type=int, default=10); r.add_argument("--unseen-only", action="store_true")
    r.set_defaults(func=cmd_read)
    s = sub.add_parser("send"); s.add_argument("--as", dest="as_addr", required=True)
    s.add_argument("--to", required=True); s.add_argument("--subject", required=True)
    s.add_argument("--body", required=True); s.add_argument("--cc")
    s.add_argument("--from-name", default="Z-Dot Team")
    s.set_defaults(func=cmd_send)
    w = sub.add_parser("sweep"); w.set_defaults(func=cmd_sweep)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
