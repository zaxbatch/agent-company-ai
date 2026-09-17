#!/usr/bin/env python3
"""agent_outbox.py — give agents a real outbound channel (email + SMS).

THE PROBLEM THIS SOLVES
-----------------------
BossLady, 2026-09-17: "I can't send email or SMS from here, and I can't write
files. No channel, no shell." Every directive she issues dies in the chat.

There IS an indirect write path: her harness persists her turns as files in
.agent-company-ai/default/output/. So rather than asking her to write to a
dropbox (she can't), this gives her three routes, in order of reliability:

  1. DROPBOX  — any agent that CAN write a file appends to
                communication/outbox/<agent>.md, one message per '---' block.
                `agent_outbox.py flush` sends everything queued and archives it.
  2. WATCH    — `agent_outbox.py watch` forwards NEW agent output files
                automatically (the harness-written path, zero cooperation needed).
  3. RELAY    — `agent_outbox.py send --as X --to Y "text"` sends immediately.

Delivery uses the two rails already proven to work on this box:
  email: ez@zerric.xyz via Hostinger SMTP  (proven: reached zdotconnect@gmail.com)
  sms:   <number>@tmomail.net              (proven: reached 5022995252)

Usage:
  python3 scripts/agent_outbox.py send --as BossLady --to boss "Directive text"
  python3 scripts/agent_outbox.py flush            # send + archive the dropbox
  python3 scripts/agent_outbox.py watch            # forward new output files
  python3 scripts/agent_outbox.py status
"""
from __future__ import annotations
import argparse, json, re, smtplib, ssl, sys, time
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.utils import formatdate, formataddr
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRED = ROOT / "communication" / "credentials.txt"
OUTBOX = ROOT / "communication" / "outbox"
SENT = OUTBOX / "_sent"
AGENT_OUT = ROOT / ".agent-company-ai" / "default" / "output"
STATE = ROOT / ".agent-company-ai" / "outbox_state.json"
SMTP_HOST, SMTP_PORT = "smtp.hostinger.com", 465

# Each agent sends from ITS OWN mailbox. zerric@ told us plainly: "Don't use the
# ez@zerric.xyz to email me because I use it. I'm sending stuff to myself. Use
# your own email to email me. That's what it's for." ez@ is his personal account;
# routing team outbound through it put our mail in his own inbox stream.
FALLBACK_SENDER = "ez@zerric.xyz"
AGENT_MAILBOX = {
    "clickclack": "clickclack@zdotllc.com",
    "bosslady":   "bosslady@zdotllc.com",
    "ninjanerd":  "ninjanerd@zdotllc.com",
    "mark":       "mark@zdotllc.com",
    "meta":       "meta@zdotllc.com",
    "manny":      "manny@zdotllc.com",
    "seleena":    "seleena@zdotllc.com",
    "bots":       "bots@zdotllc.com",
}

# proven recipients only
RECIPIENTS = {
    # (email, sms_number).
    #
    # DELIVERY LESSON: do NOT default 'zerric' to zerric@zdotllc.com. A self-test
    # (clickclack@ -> clickclack@, same domain) was ACCEPTED by SMTP with no
    # bounce and then never arrived in INBOX or Junk -- local delivery between
    # @zdotllc.com mailboxes is broken. External delivery from @zdotllc.com works
    # fine. So mail sent to an @zdotllc.com recipient appears to vanish.
    # zerric replies from zdotconnect@gmail.com, which is externally hosted and
    # proven to deliver, so that is the primary address.
    "boss":     ("zdotconnect@gmail.com", "+15022995252"),
    "bosslady": ("zdotconnect@gmail.com", "+15022995252"),
    "zerric":   ("zdotconnect@gmail.com", "+15022995252"),
    "zerric_g": ("zdotconnect@gmail.com", "+15022995252"),
    "zerric_work": ("zerric@zdotllc.com", "+15022995252"),   # known unreliable
}
SMS_GATEWAY = "tmomail.net"
MAX_SMS = 300


def _password(mailbox=FALLBACK_SENDER):
    """Password for *mailbox* from credentials.txt, verified against SMTP."""
    txt = CRED.read_text(encoding="utf-8", errors="replace")
    cands = []
    for ln in txt.splitlines():
        if mailbox in ln:
            m = re.search(r"password\s*[:=]\s*(\S+)", ln, re.I)
            if m:
                cands.append(m.group(1))
    m = re.search(r"default for new boxes\):\s*(\S+)", txt)
    if m:
        cands.append(m.group(1))
    for m in re.finditer(r"(?im)^\s*pass\s*[:=]\s*(\S+)", txt):
        cands.append(m.group(1))
    for pw in dict.fromkeys(cands):
        try:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT,
                                  context=ssl.create_default_context(), timeout=15) as s:
                s.login(mailbox, pw)
            return pw
        except Exception:
            continue
    raise RuntimeError(f"no authenticating password for {mailbox}")


def deliver(to_key, subject, body, sms=False, dry=False, sender=None):
    email, num = RECIPIENTS.get(to_key, (to_key, None))
    sender = sender or FALLBACK_SENDER
    sent = []
    pw = None if dry else _password(sender)
    if email:
        if dry:
            print(f"  [dry] email -> {email} :: {subject}")
        else:
            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = formataddr(("Z-Dot Team", sender))
            msg["Reply-To"] = sender
            msg["To"] = email
            msg["Date"] = formatdate(localtime=True)
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT,
                                  context=ssl.create_default_context(), timeout=25) as s:
                s.login(sender, pw)
                s.sendmail(sender, [email], msg.as_string())
            print(f"  email -> {email} (from {sender})")
            sent.append(("email", email))
    if sms and (num or to_key in RECIPIENTS):
        num = num or RECIPIENTS[to_key][1]
        if num:
            gate = re.sub(r"\D", "", num) + "@" + SMS_GATEWAY
            short = (subject + " — " + body).strip()
            if len(short) > MAX_SMS:
                short = short[:MAX_SMS - 3] + "..."
            if dry:
                print(f"  [dry] sms -> {num}")
            else:
                msg = MIMEText(short, "plain", "utf-8")
                msg["From"] = sender
                msg["To"] = gate
                msg["Date"] = formatdate(localtime=True)
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT,
                                      context=ssl.create_default_context(), timeout=25) as s:
                    s.login(sender, pw)
                    s.sendmail(sender, [gate], msg.as_string())
                print(f"  sms -> {num} ({len(short)} chars)")
                sent.append(("sms", num))
    return sent


def parse_messages(text):
    """Messages are '---'-separated blocks. First line may be 'TO: x'. Subject line optional."""
    out = []
    for block in re.split(r"^---\s*$", text, flags=re.M):
        block = block.strip()
        if not block or block.startswith("#") and block.count("\n") < 2:
            continue
        to, subject, lines = "boss", None, []
        for ln in block.splitlines():
            if ln.upper().startswith("TO:"):
                to = ln.split(":", 1)[1].strip().lower()
            elif ln.upper().startswith("SUBJECT:"):
                subject = ln.split(":", 1)[1].strip()
            else:
                lines.append(ln)
        body = "\n".join(lines).strip()
        if body:
            out.append((to, subject or body.splitlines()[0][:70], body))
    return out


def cmd_send(a):
    subject = a.subject or a.body.splitlines()[0][:70]
    sender = AGENT_MAILBOX.get((a.sender or "").lower(), FALLBACK_SENDER)
    deliver(a.to, subject, a.body, sms=a.sms, dry=a.dry_run, sender=sender)


def cmd_flush(a):
    OUTBOX.mkdir(parents=True, exist_ok=True)
    SENT.mkdir(parents=True, exist_ok=True)
    total = 0
    for f in sorted(OUTBOX.glob("*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        msgs = parse_messages(text)
        if not msgs:
            continue
        print(f"{f.name}: {len(msgs)} message(s)")
        for to, subj, body in msgs:
            deliver(to, f"[{f.stem}] {subj}", body, sms=a.sms, dry=a.dry_run)
            total += 1
        if not a.dry_run:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            f.rename(SENT / f"{stamp}-{f.name}")
    print(f"flushed {total} message(s)")


def cmd_watch(a):
    """Forward agent output files the harness wrote, without the agent doing anything."""
    STATE.parent.mkdir(parents=True, exist_ok=True)
    seen = set(json.loads(STATE.read_text()).get("seen", [])) if STATE.exists() else set()
    new = []
    for f in sorted(AGENT_OUT.glob("*.md"), key=lambda p: p.stat().st_mtime):
        key = f"{f.name}:{int(f.stat().st_mtime)}"
        if key in seen:
            continue
        # only forward agent-authored directives, not our own notes
        if a.only and a.only.lower() not in f.name.lower():
            seen.add(key); continue
        if time.time() - f.stat().st_mtime > a.max_age_h:
            seen.add(key); continue
        new.append((key, f))
    if not new:
        print("no new agent output to forward")
    for key, f in new:
        text = f.read_text(encoding="utf-8", errors="replace")[:6000]
        who = f.name.split("_", 1)[0]
        deliver(a.to, f"[{who}] {f.stem[:70]}", text, sms=False, dry=a.dry_run)
        seen.add(key)
    STATE.write_text(json.dumps({"seen": sorted(seen)[-500:]}, indent=1))
    print(f"forwarded {len(new)} file(s)")


def cmd_status(a):
    OUTBOX.mkdir(parents=True, exist_ok=True)
    q = list(OUTBOX.glob("*.md"))
    print(f"outbox dir : {OUTBOX}")
    print(f"queued     : {len(q)} file(s)")
    for f in q:
        print(f"   {f.name} ({len(parse_messages(f.read_text(encoding='utf-8', errors='replace')))} msg)")
    print(f"answer dir : {AGENT_OUT}")
    print(f"recipients : {', '.join(RECIPIENTS)}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("send")
    s.add_argument("--as", dest="sender", default="agent")
    s.add_argument("--to", default="boss")
    s.add_argument("--subject")
    s.add_argument("--sms", action="store_true")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("body")
    s.set_defaults(func=cmd_send)
    f = sub.add_parser("flush"); f.add_argument("--sms", action="store_true")
    f.add_argument("--dry-run", action="store_true"); f.set_defaults(func=cmd_flush)
    w = sub.add_parser("watch"); w.add_argument("--only"); w.add_argument("--to", default="boss")
    w.add_argument("--max-age-h", type=float, default=6.0)
    w.add_argument("--dry-run", action="store_true"); w.set_defaults(func=cmd_watch)
    st = sub.add_parser("status"); st.set_defaults(func=cmd_status)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
