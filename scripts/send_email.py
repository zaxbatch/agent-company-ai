#!/usr/bin/env python3
"""Send email from ez@zerric.xyz via Hostinger SMTP (Thunderbird-equivalent, scriptable).

Reads credentials from communication/credentials.txt (git-ignored). Never hardcode secrets.

Usage:
  python3 scripts/send_email.py --to "zdotconnect@gmail.com" --subject "Hi" --body "Hello"
  python3 scripts/send_email.py --to "5022995252@tmomail.net" --subject "PING" --body "TEST from ClickClack"
"""
import argparse, re, smtplib, ssl, sys
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRED_FILE = ROOT / "communication" / "credentials.txt"
SENDER = "ninjanerd@zdotllc.com"   # our own agent mailbox. ez@zerric.xyz is Zerric's PERSONAL inbox - never send from it.
SMTP_HOST, SMTP_PORT = "smtp.hostinger.com", 465

def load_password() -> str:
    """Password for SENDER from credentials.txt, verified by a real SMTP login."""
    import re as _re
    txt2 = CRED_FILE.read_text(errors="replace")
    cands = []
    m = _re.search(_re.escape(SENDER) + r"[^\n]*?pass(?:word)?\s*[:=]?\s*(\S+)", txt2)
    if m:
        cands.append(m.group(1))
    for ln in txt2.splitlines():
        mm = _re.match(r"\s*pass\s*[=:]\s*(\S+)", ln.strip(), _re.I)
        if mm:
            cands.append(mm.group(1))
    ctx = ssl.create_default_context()
    for pw in cands:
        try:
            with smtplib.SMTP_SSL("smtp.hostinger.com", 465, context=ctx, timeout=15) as s2:
                s2.login(SENDER, pw)
            return pw
        except Exception:
            continue
    raise RuntimeError("no authenticating password for " + SENDER + " in credentials.txt")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", required=True)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body", required=True)
    ap.add_argument("--from-name", default="Z-Dot Team")
    args = ap.parse_args()

    pw = load_password()
    msg = MIMEText(args.body, "plain", "utf-8")
    msg["Subject"] = args.subject
    msg["From"] = formataddr((args.from_name, SENDER))
    msg["To"] = args.to

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=30) as s:
        s.login(SENDER, pw)
        s.sendmail(SENDER, [args.to], msg.as_string())
    print(f"SENT from {SENDER} -> {args.to} | subject: {args.subject}")

if __name__ == "__main__":
    main()
