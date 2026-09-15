#!/usr/bin/env python3
"""sms.py — send a real text message to a team member's phone.

How it works: mobile carriers expose an email-to-SMS gateway. Sending a short
plain-text email to <number>@<carrier-gateway> arrives as a genuine SMS. No
third-party SMS API, no per-message cost.

Usage:
  python3 scripts/sms.py zerric   "message text"
  python3 scripts/sms.py bosslady "message text"
  python3 scripts/sms.py +1502... "message text"   # explicit E.164 number
  python3 scripts/sms.py --list

Rules: keep it under ~320 chars (longer texts get split or dropped by the
gateway). Never include credentials.
"""
import argparse
import re
import smtplib
import ssl
import sys
from email.mime.text import MIMEText
from email.utils import formatdate
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRED = ROOT / "communication" / "credentials.txt"
SMTP_HOST, SMTP_PORT = "smtp.hostinger.com", 465
SENDER = "ez@zerric.xyz"

# name -> (E.164 number, carrier SMS gateway)
RECIPIENTS = {
    "zerric":   ("+15022995252", "tmomail.net"),
    "bosslady": ("+15022995252", "tmomail.net"),
}
MAX = 320


def load_password():
    for m in re.finditer(r"(?im)^\s*pass\s*[:=]\s*(\S+)", CRED.read_text(encoding="utf-8", errors="replace")):
        pw = m.group(1)
        try:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT,
                                  context=ssl.create_default_context(), timeout=15) as s:
                s.login(SENDER, pw)
            return pw
        except Exception:
            continue
    raise RuntimeError("no authenticating password for ez@zerric.xyz in credentials.txt")


def resolve(who):
    if who in RECIPIENTS:
        num, gw = RECIPIENTS[who]
    elif re.fullmatch(r"\+?\d{7,15}", who):
        num, gw = who, "tmomail.net"
    else:
        raise SystemExit(f"unknown recipient {who!r}; try --list")
    digits = re.sub(r"\D", "", num)
    return f"{digits}@{gw}", num


def send(who, body, dry=False):
    gate, num = resolve(who)
    body = body.strip()
    if len(body) > MAX:
        print(f"warning: {len(body)} chars > {MAX}; gateway may split or drop")
    if dry:
        print(f"[dry-run] would send {len(body)} chars -> {who} ({num}) via {gate}")
        print(body)
        return
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = SENDER
    msg["To"] = gate
    msg["Date"] = formatdate(localtime=True)
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT,
                          context=ssl.create_default_context(), timeout=25) as s:
        s.login(SENDER, load_password())
        s.sendmail(SENDER, [gate], msg.as_string())
    print(f"sent {len(body)} chars -> {who} ({num})")


def main():
    ap = argparse.ArgumentParser(description="Send a real SMS via carrier email gateway")
    ap.add_argument("who", nargs="?", help="zerric | bosslady | +1XXXXXXXXXX")
    ap.add_argument("body", nargs="?", help="message text")
    ap.add_argument("--list", action="store_true", help="show known recipients")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.list or not a.who:
        print("known recipients:")
        for k, (n, g) in RECIPIENTS.items():
            print(f"  {k:<10} {n}  via {g}")
        return 0 if a.list else 1
    if not a.body:
        raise SystemExit("need a message body")
    send(a.who, a.body, dry=a.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
