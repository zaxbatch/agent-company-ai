#!/usr/bin/env python3
"""
send_message.py — Reach BossLady (and the team) from ez@zerric.xyz
=================================================================
Email:    ez@zerric.xyz  ->  zdotconnect@gmail.com   (BossLady's inbox)
SMS:      T-Mobile email gateway -> 5022995252        (BossLady's phone, real text)

Usage:
  python3 scripts/send_message.py email "Subject here" "Message body"
  python3 scripts/send_message.py sms   "Message text (<=150 chars)"
  python3 scripts/send_message.py both  "Subject" "Message body"

The SMTP password is read from communication/credentials.txt — never hardcode it,
never print it, never commit it.
"""
import re, sys, smtplib, ssl
from email.mime.text import MIMEText
from email.utils import formatdate

SENDER = "ez@zerric.xyz"
SMTP_HOST = "smtp.hostinger.com"
SMTP_PORT = 465
BOSS_EMAIL = "zdotconnect@gmail.com"
BOSS_SMS_GATEWAY = "5022995252@tmomail.net"   # T-Mobile

def load_password():
    """Return the candidate password that actually authenticates (credentials.txt
    holds several accounts; only the Hostinger/ez@ one works for SMTP)."""
    creds = open("communication/credentials.txt", encoding="utf-8", errors="replace").read()
    candidates = []
    for m in re.finditer(r"(?i)(password|pass|pwd|hostinger)\s*[:=]\s*([A-Za-z0-9@._#\-]{6,})", creds):
        candidates.append(m.group(2))
    # dedupe, keep order
    seen = set(); uniq = []
    for c in candidates:
        if c not in seen:
            seen.add(c); uniq.append(c)
    ctx = ssl.create_default_context()
    for pw in uniq:
        try:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=15) as s:
                s.login(SENDER, pw)
            return pw  # this one authenticates
        except Exception:
            continue
    raise RuntimeError("None of the credentials.txt passwords authenticate for ez@zerric.xyz SMTP")

def send(subject, body, to_addr):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = f"Z-Dot Team <{SENDER}>"
    msg["To"] = to_addr
    msg["Date"] = formatdate(localtime=True)
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=25) as s:
        s.login(SENDER, load_password())
        s.sendmail(SENDER, [to_addr], msg.as_string())
    print(f"sent: {to_addr}")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "email"
    if mode == "email" and len(sys.argv) >= 4:
        send(sys.argv[2], sys.argv[3], BOSS_EMAIL)
    elif mode == "sms" and len(sys.argv) >= 3:
        body = sys.argv[2]
        if len(body) > 150: body = body[:150]  # keep SMS short
        send("SMS", body, BOSS_SMS_GATEWAY)
    elif mode == "both" and len(sys.argv) >= 4:
        subj, body = sys.argv[2], sys.argv[3]
        send(subj, body, BOSS_EMAIL)
        send("SMS", subj + " - " + body, BOSS_SMS_GATEWAY)
    else:
        print(__doc__)
