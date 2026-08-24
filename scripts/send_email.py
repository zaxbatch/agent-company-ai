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
SENDER = "ez@zerric.xyz"
SMTP_HOST, SMTP_PORT = "smtp.hostinger.com", 465

def load_password():
    """Find the pass= line for ez@zerric.xyz in credentials.txt."""
    text = CRED_FILE.read_text()
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.strip().lower() == "ez@zerric.xyz" or ln.strip().lower().startswith("ez@zerric.xyz"):
            # look ahead for pass= on next line(s)
            for nxt in lines[i+1:i+3]:
                m = re.match(r"pass\s*[=:]\s*(\S+)", nxt.strip(), re.I)
                if m:
                    return m.group(1)
    raise RuntimeError(f"ez@zerric.xyz password not found in {CRED_FILE}")

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
