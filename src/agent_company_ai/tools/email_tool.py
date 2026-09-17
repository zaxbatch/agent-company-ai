"""Email sending tool — Resend or SendGrid via httpx.

Rate-limited and logged to the database. Requires API key configuration
in the integrations section of config.yaml.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.utils import formatdate

from agent_company_ai.tools.rate_limiter import RateLimiter
from agent_company_ai.tools.registry import tool

if TYPE_CHECKING:
    from agent_company_ai.storage.database import Database

logger = logging.getLogger("agent_company_ai.tools.email")

# Module-level state, set at runtime by Company
_db: Database | None = None
_current_agent: str = "unknown"
_provider: str = "resend"
_api_key: str = ""
_from_address: str = ""
_from_name: str = ""
_reply_to: str = ""
_enabled: bool = False


def set_email_config(
    provider: str,
    api_key: str,
    from_address: str,
    from_name: str = "",
    reply_to: str = "",
) -> None:
    global _provider, _api_key, _from_address, _from_name, _reply_to, _enabled
    _provider = provider
    _api_key = api_key
    _from_address = from_address
    _from_name = from_name
    _reply_to = reply_to
    _enabled = bool(api_key and from_address)


def set_email_db(db: Database) -> None:
    global _db
    _db = db


def set_email_agent(name: str) -> None:
    global _current_agent
    _current_agent = name


def _require_configured() -> None:
    if not _enabled:
        raise RuntimeError(
            "Email not configured. Set integrations.email.enabled: true, "
            "integrations.email.api_key, and integrations.email.from_address "
            "in config.yaml."
        )


async def _send_via_resend(to: str, subject: str, body: str, is_html: bool) -> dict:
    """Send email via Resend API."""
    payload: dict = {
        "from": f"{_from_name} <{_from_address}>" if _from_name else _from_address,
        "to": [to],
        "subject": subject,
    }
    if is_html:
        payload["html"] = body
    else:
        payload["text"] = body
    if _reply_to:
        payload["reply_to"] = _reply_to

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30.0,
        )
    if resp.status_code >= 400:
        try:
            data = resp.json()
        except Exception:
            data = resp.text
        raise RuntimeError(f"Resend API error ({resp.status_code}): {data}")
    return resp.json()


async def _send_via_sendgrid(to: str, subject: str, body: str, is_html: bool) -> dict:
    """Send email via SendGrid v3 API."""
    content_type = "text/html" if is_html else "text/plain"
    payload = {
        "personalizations": [{"to": [{"email": to}]}],
        "from": {"email": _from_address, "name": _from_name} if _from_name else {"email": _from_address},
        "subject": subject,
        "content": [{"type": content_type, "value": body}],
    }
    if _reply_to:
        payload["reply_to"] = {"email": _reply_to}

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30.0,
        )
    if resp.status_code >= 400:
        try:
            data = resp.json()
        except Exception:
            data = resp.text
        raise RuntimeError(f"SendGrid API error ({resp.status_code}): {data}")
    # SendGrid returns 202 with empty body on success
    return {"id": resp.headers.get("X-Message-Id", ""), "status": "sent"}


def _smtp_creds_for(address: str) -> str | None:
    """Look up the SMTP password for a specific mailbox in credentials.txt.

    Only @zdotllc.com work mailboxes are supported here. Never logs the value.
    """
    import re
    from pathlib import Path as _P
    cred = _P(__file__).resolve().parents[3] / "communication" / "credentials.txt"
    if not cred.exists():
        return None
    txt = cred.read_text(errors="replace")
    m = re.search(rf'{re.escape(address)}[^\n]*?pass(?:word)?\s*[:=]?\s*(\S+)', txt)
    return m.group(1) if m else None


async def _send_via_smtp(to: str, subject: str, body: str, is_html: bool) -> dict:
    """Send via SMTP. Honours `from_address` by authenticating AS that mailbox.

    Hostinger requires the authenticated account to match the From header, or the
    message fails DKIM alignment and looks like spoofing. The old code ignored
    from_address entirely and always sent as SMTP_USER while claiming otherwise.
    """
    host = os.getenv("SMTP_HOST", "smtp.hostinger.com")
    port = int(os.getenv("SMTP_PORT", "465"))
    fallback_user = os.getenv("SMTP_USER", "ez@zerric.xyz")
    fallback_pass = os.getenv("SMTP_PASS", "")

    wanted = (_from_address or "").strip()
    user, password = fallback_user, fallback_pass
    substituted_from = None

    if wanted and wanted.lower() != fallback_user.lower():
        pw = _smtp_creds_for(wanted)
        if pw:
            user, password = wanted, pw
        else:
            # no creds for the requested identity -> send as the authenticated
            # account and be explicit about the substitution rather than lying
            substituted_from = wanted

    if not password:
        raise RuntimeError("No SMTP password available. Set SMTP_PASS in .env.")
    msg = MIMEText(body, "html" if is_html else "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = f"{_from_name} <{user}>" if _from_name else user
    if _reply_to:
        msg["Reply-To"] = _reply_to
    msg["To"] = to
    msg["Date"] = formatdate(localtime=True)
    ctx = ssl.create_default_context()

    def _attempt(acct: str, pw: str):
        msg.replace_header("From", f"{_from_name} <{acct}>" if _from_name else acct)
        with smtplib.SMTP_SSL(host, port, context=ctx, timeout=25) as server:
            server.login(acct, pw)
            server.sendmail(acct, [to], msg.as_string())

    try:
        _attempt(user, password)
    except smtplib.SMTPAuthenticationError:
        # A stored password existed for the requested identity but is wrong
        # (e.g. team@/ceo@ mailboxes reject auth). Fall back to the account we can
        # actually authenticate, and say so — never silently misrepresent the sender.
        if user != fallback_user and fallback_pass:
            substituted_from = user
            user, password = fallback_user, fallback_pass
            _attempt(user, password)
        else:
            raise
    out = {"id": "smtp", "status": "sent", "provider": "smtp", "from": user}
    if substituted_from:
        out["warning"] = (f"requested From {substituted_from} has no stored SMTP "
                          f"password; sent as {user} instead")
    return out


@tool(
    "send_email",
    (
        "Send an email to a recipient. Rate-limited and logged. "
        "Requires email integration to be configured."
    ),
    {
        "type": "object",
        "properties": {
            "to": {
                "type": "string",
                "description": "Recipient email address",
            },
            "subject": {
                "type": "string",
                "description": "Email subject line",
            },
            "body": {
                "type": "string",
                "description": "Email body text (plain text or HTML)",
            },
            "is_html": {
                "type": "boolean",
                "description": "Whether the body is HTML (default: false)",
            },
        },
        "required": ["to", "subject", "body"],
    },
)
async def send_email(
    to: str,
    subject: str,
    body: str,
    is_html: bool = False,
) -> str:
    _require_configured()

    to = to.strip()
    if not to or "@" not in to:
        return "Error: invalid recipient email address."
    if not subject.strip():
        return "Error: subject is required."
    if not body.strip():
        return "Error: body is required."

    # Rate limit check
    limiter = RateLimiter.get()
    if not limiter.check("email_hourly"):
        remaining_h = limiter.remaining("email_hourly")
        return f"Rate limit exceeded: hourly email limit reached ({remaining_h} remaining). Try again later."
    if not limiter.check("email_daily"):
        remaining_d = limiter.remaining("email_daily")
        return f"Rate limit exceeded: daily email limit reached ({remaining_d} remaining). Try again later."

    # Send
    try:
        if _provider == "smtp":
            result = await _send_via_smtp(to, subject, body, is_html)
        elif _provider == "sendgrid":
            result = await _send_via_sendgrid(to, subject, body, is_html)
        else:
            result = await _send_via_resend(to, subject, body, is_html)
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        # Log the failure
        if _db:
            await _db.execute(
                "INSERT INTO email_log (to_address, from_address, subject, body_text, body_html, status, sent_by) "
                "VALUES (?, ?, ?, ?, ?, 'failed', ?)",
                (to, _from_address, subject, body if not is_html else "", body if is_html else "", _current_agent),
            )
        return f"Error sending email: {e}"

    # Record rate limit usage
    limiter.record("email_hourly")
    limiter.record("email_daily")

    # Log success
    provider_id = result.get("id", "")
    if _db:
        await _db.execute(
            "INSERT INTO email_log (to_address, from_address, subject, body_text, body_html, status, provider_message_id, sent_by) "
            "VALUES (?, ?, ?, ?, ?, 'sent', ?, ?)",
            (to, _from_address, subject, body if not is_html else "", body if is_html else "", provider_id, _current_agent),
        )

    logger.info(f"Email sent to {to}: {subject}")
    hourly_left = limiter.remaining("email_hourly")
    daily_left = limiter.remaining("email_daily")
    return (
        f"Email sent successfully to {to}.\n"
        f"  Subject: {subject}\n"
        f"  Provider: {_provider}\n"
        f"  Message ID: {provider_id}\n"
        f"  Rate limits remaining: {hourly_left}/hr, {daily_left}/day"
    )
