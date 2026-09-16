#!/usr/bin/env python3
"""BizzyBee Bots — outbound campaign sender (the campaign that never ran).

Task e9b05f95c9b7 ("Get with @Mark for zdot email campaign") FAILED on
2026-09-15 without sending anything, and email_log has 0 rows: no campaign
email has ever been sent. Root cause: integrations.email was hard-disabled
(api_key='' + from_address='' with provider=resend), so every send raised
"Email not configured". Fixed 2026-09-15 (provider=smtp).

CAN-SPAM compliance built in: real physical address, working unsubscribe,
honest subject, no deceptive headers. One send per contact, no re-sends.

Usage:
  python3 scripts/bizzybee_campaign.py --dry-run            # preview, no sends
  python3 scripts/bizzybee_campaign.py --test you@you.com   # send ONE sample to self
  python3 scripts/bizzybee_campaign.py --send --limit 5     # real send (small batch first)
  python3 scripts/bizzybee_campaign.py --report             # what's been sent so far
"""
from __future__ import annotations
import argparse, re, smtplib, ssl, sys, time
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRED = ROOT / "communication" / "credentials.txt"
ENV  = ROOT / ".env"
SENDER = "info@zdotllc.com"          # WORK domain (verified: SPF pass + DKIM signed)
SENDER_NAME = "Z-Dot LLC"

# --- CAN-SPAM required elements -------------------------------------------------
PHYSICAL_ADDRESS = "Z-Dot LLC, Louisville, KY 40201"
UNSUB_MAILTO = "info@zdotllc.com"
REPLY_TO = "info@zdotllc.com"

SUBJECT = "Quick question about {company}"
BODY = """Hi {first},

I run Z-Dot, a small shop in Louisville. We built a set of tools for service
businesses and I'm trying to find out if they're worth shipping properly.

We're NOT selling you anything in this email — I'm looking for five {trade}
owners who'll tell me if this is useful or a waste of time.

What it does: takes the repetitive stuff off your plate. Missed-call follow-up,
quote follow-through, and a simple CRM so jobs don't live in your phone.

If that's a problem you have, reply "tell me more" and I'll send a 2-minute video.
If not, reply "no thanks" and I won't contact you again.

Either answer helps me. Just hit reply — it comes straight to me.

- The Z-Dot team

--
{address}
Don't want any further email from us? Reply with "unsubscribe" and you're removed
immediately, no questions. Or email {unsub}.
"""

TRADE_WORDS = {
    "plumbing": "plumbing", "plumb": "plumbing",
    "lawn": "landscaping", "landscap": "landscaping",
    "paint": "painting", "clean": "cleaning",
    "hvac": "HVAC", "roof": "roofing", "electric": "electrical",
}


def load_password(sender: str = SENDER) -> str:
    """Find the password for `sender` in credentials.txt, verified by real login."""
    txt = CRED.read_text(errors="replace")
    cands = []
    m = re.search(rf'{re.escape(sender)}[^\n]*?pass(?:word)?\s*[:=]?\s*(\S+)', txt)
    if m:
        cands.append(m.group(1))
    d = re.search(r'(?i)default for new boxes\)?\s*[:=]\s*(\S+)', txt)
    if d:
        cands.append(d.group(1))
    for pw in cands:
        try:
            with smtplib.SMTP_SSL("smtp.hostinger.com", 465,
                                  context=ssl.create_default_context(), timeout=15) as s:
                s.login(sender, pw)
            return pw
        except Exception:
            continue
    sys.exit(f"FATAL: no authenticating password for {sender}")


def contacts():
    import sqlite3
    c = sqlite3.connect(ROOT / ".agent-company-ai/default/company.db")
    c.row_factory = sqlite3.Row
    return [dict(r) for r in c.execute(
        "SELECT id,name,company,email,phone,status,tags FROM contacts "
        "WHERE email IS NOT NULL AND email != '' ORDER BY id")]


def render(c: dict) -> tuple[str, str]:
    full = (c.get("name") or "").strip()
    first = full.split()[0] if full else "there"
    company = (c.get("company") or "").strip() or "your business"
    blob = f"{company} {full}".lower()
    trade = next((v for k, v in TRADE_WORDS.items() if k in blob), "local")
    return (
        SUBJECT.format(company=company),
        BODY.format(first=first, first_name=first, company=company,
                    trade=trade, address=PHYSICAL_ADDRESS, unsub=UNSUB_MAILTO),
    )


def already_sent() -> set:
    import sqlite3
    try:
        c = sqlite3.connect(ROOT / ".agent-company-ai/default/company.db")
        return {r[0] for r in c.execute(
            "SELECT DISTINCT to_address FROM email_log WHERE status='sent'")}
    except Exception:
        return set()


def send_one(pw: str, to: str, subject: str, body: str, log=True, sender: str = SENDER) -> bool:
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = f"{SENDER_NAME} <{sender}>"
    msg["To"] = to
    msg["Reply-To"] = REPLY_TO
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=sender.split("@")[-1])
    msg["List-Unsubscribe"] = f"<mailto:{UNSUB_MAILTO}?subject=unsubscribe>"
    try:
        with smtplib.SMTP_SSL("smtp.hostinger.com", 465,
                              context=ssl.create_default_context(), timeout=25) as s:
            s.login(sender, pw)
            s.sendmail(sender, [to], msg.as_string())
    except Exception as e:
        if log:
            _log(to, subject, body, "failed", sender)
        print(f"  FAIL {to}: {type(e).__name__}")
        return False
    if log:
        _log(to, subject, body, "sent", sender)
    return True


def _log(to: str, subject: str, body: str, status: str, sender: str = SENDER):
    import sqlite3
    try:
        c = sqlite3.connect(ROOT / ".agent-company-ai/default/company.db")
        c.execute("INSERT INTO email_log (to_address, from_address, subject, body_text, "
                  "status, sent_by, created_at) VALUES (?,?,?,?,?,?,datetime('now'))",
                  (to, sender, subject, body, status, "NinjaNerd"))
        c.commit()
    except Exception:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--test")
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--from", dest="sender", default=SENDER,
                    help="sending address (must be a real @zdotllc.com mailbox)")
    a = ap.parse_args()

    if a.report:
        import sqlite3
        c = sqlite3.connect(ROOT / ".agent-company-ai/default/company.db")
        print("email_log rows:", c.execute("SELECT count(*) FROM email_log").fetchone()[0])
        for r in c.execute("SELECT to_address,status,created_at FROM email_log "
                           "ORDER BY rowid DESC LIMIT 20"):
            print("  ", r)
        return 0

    cs = contacts()
    print(f"contacts with email: {len(cs)}")
    sent = already_sent()
    todo = [c for c in cs if c["email"].lower() not in sent]
    print(f"already emailed: {len(sent)}   remaining: {len(todo)}")
    if a.limit: todo = todo[:a.limit]

    if a.test:
        subj, body = render(todo[0] if todo else {"name": "Test", "company": "Test Co"})
        pw = load_password(a.sender)
        ok = send_one(pw, a.test, "[SAMPLE] " + subj, body, sender=a.sender)
        print("test send:", "OK" if ok else "FAILED")
        return 0 if ok else 1

    if a.dry_run:
        for c in todo[:5]:
            subj, body = render(c)
            print("=" * 70)
            print(f"TO: {c['name']} <{c['email']}>  [{c.get('company')}]")
            print(f"SUBJ: {subj}")
            print(body)
        print("=" * 70)
        print(f"[dry-run] {len(todo)} would send. Nothing was sent.")
        return 0

    if a.send:
        pw = load_password(a.sender)
        ok = bad = 0
        for i, c in enumerate(todo, 1):
            subj, body = render(c)
            if send_one(pw, c["email"], subj, body, sender=a.sender):
                ok += 1; print(f"  [{i}/{len(todo)}] sent -> {c['email']}")
            else:
                bad += 1
            time.sleep(2.5)          # polite pacing
        print(f"\nSENT {ok}  FAILED {bad}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
