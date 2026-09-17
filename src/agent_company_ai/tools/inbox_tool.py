"""Inbox reading tool.

BossLady's point stands: an outbound channel is half a channel. Email is our only
live money channel and nobody could SEE it. This adds read_inbox.

Reads over IMAP. Never logs or returns credentials. Headers only by default so a
mailbox dump can't leak third-party content into a transcript.
"""
from __future__ import annotations

import email
import imaplib
import os
import re
from email.header import decode_header
from pathlib import Path

from agent_company_ai.tools.registry import tool

_current_agent: str = "unknown"
_account: str = ""
_password: str = ""
_host: str = "imap.hostinger.com"
_port: int = 993


def set_inbox_config(account: str = "", password: str = "",
                     host: str = "imap.hostinger.com", port: int = 993) -> None:
    global _account, _password, _host, _port
    _account, _password, _host, _port = account, password, host, port


def set_inbox_agent(name: str) -> None:
    global _current_agent
    _current_agent = name


def _creds_for(account: str) -> str | None:
    """Password for a mailbox from credentials.txt. Value is never logged."""
    cred = Path(__file__).resolve().parents[3] / "communication" / "credentials.txt"
    if not cred.exists():
        return None
    txt = cred.read_text(errors="replace")
    m = re.search(rf'{re.escape(account)}[^\n]*?pass(?:word)?\s*[:=]?\s*(\S+)', txt)
    return m.group(1) if m else None


def _dec(v) -> str:
    if not v:
        return ""
    out = ""
    for part, enc in decode_header(v):
        if isinstance(part, bytes):
            try:
                out += part.decode(enc or "utf-8", "replace")
            except Exception:
                out += part.decode("utf-8", "replace")
        else:
            out += part
    return out


@tool(
    "read_inbox",
    (
        "List recent messages in an email inbox: sender, subject, date, and whether "
        "it is unread. Header information only — use read_email for a body. "
        "Useful for spotting replies, orders and payment notifications."
    ),
    {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "description": "How many recent messages to list (default 10, max 50)"},
            "unread_only": {"type": "boolean", "description": "Only show unread messages"},
            "account": {"type": "string", "description": "Mailbox to read, e.g. ninjanerd@zdotllc.com (defaults to the configured account)"},
        },
    },
)
def read_inbox(limit: int = 10, unread_only: bool = False, account: str = "") -> str:
    acct = (account or _account).strip()
    pw = _password or (_creds_for(acct) if acct else None)
    if not acct or not pw:
        return ("Error: inbox not configured. Provide `account` for a mailbox with a "
                "password in credentials.txt, or set INBOX_ACCOUNT / INBOX_PASSWORD.")

    limit = max(1, min(50, int(limit or 10)))
    try:
        M = imaplib.IMAP4_SSL(_host, _port)
        M.login(acct, pw)
        M.select("INBOX")
        typ, data = M.search(None, "UNSEEN" if unread_only else "ALL")
        ids = data[0].split()[-limit:]
        if not ids:
            M.logout()
            return f"Inbox for {acct}: no messages."

        lines = [f"Inbox for {acct} — {len(ids)} most recent"
                 + (" (unread only)" if unread_only else "") + ":"]
        for i in reversed(ids):
            typ, raw = M.fetch(i, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            if not raw or not isinstance(raw[0], tuple):
                continue
            h = email.message_from_bytes(raw[0][1])
            from_ = _dec(h.get("From"))[:60]
            subj = _dec(h.get("Subject"))[:80] or "(no subject)"
            date = (h.get("Date") or "")[:31]
            lines.append(f"  · {from_} | {subj} | {date}")
        M.logout()
        return "\n".join(lines)
    except imaplib.IMAP4.error as e:
        return f"Error: IMAP rejected the login or command for {acct}: {str(e)[:160]}"
    except Exception as e:
        return f"Error reading inbox: {type(e).__name__}: {str(e)[:160]}"


@tool(
    "read_email",
    (
        "Read the full body of one message from the inbox, identified by its index "
        "in the most recent read_inbox listing (1 = newest)."
    ),
    {
        "type": "object",
        "properties": {
            "index": {"type": "integer", "description": "1 = newest message, 2 = next, etc."},
            "account": {"type": "string", "description": "Mailbox to read (defaults to configured)"},
        },
        "required": ["index"],
    },
)
def read_email(index: int = 1, account: str = "") -> str:
    acct = (account or _account).strip()
    pw = _password or (_creds_for(acct) if acct else None)
    if not acct or not pw:
        return "Error: inbox not configured."
    try:
        M = imaplib.IMAP4_SSL(_host, _port)
        M.login(acct, pw)
        M.select("INBOX")
        typ, data = M.search(None, "ALL")
        ids = data[0].split()
        if not ids:
            M.logout(); return "Inbox is empty."
        idx = max(1, min(len(ids), int(index)))
        target = ids[-idx]
        typ, raw = M.fetch(target, "(RFC822)")
        msg = email.message_from_bytes(raw[0][1])
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", "replace")
                    break
        else:
            body = msg.get_payload(decode=True).decode("utf-8", "replace")
        M.logout()
        body = re.sub(r"\n{3,}", "\n\n", body).strip()[:4000]
        return (f"From: {_dec(msg.get('From'))}\n"
                f"Subject: {_dec(msg.get('Subject'))}\n"
                f"Date: {msg.get('Date')}\n\n{body}")
    except Exception as e:
        return f"Error reading message: {type(e).__name__}: {str(e)[:160]}"
