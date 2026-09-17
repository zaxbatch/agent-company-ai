"""SMS sending tool.

IMPORTANT — READ BEFORE TRUSTING THIS:
The previous SMS path used the T-Mobile email-to-SMS gateway (tmomail.net).
T-Mobile SHUT THAT DOWN in December 2024. Messages to it are accepted upstream
and then silently dropped: no delivery, no bounce. Every "SMS sent" log from
that era was a false positive.

This tool therefore requires a real carrier API. Set in .env:

    TWILIO_ACCOUNT_SID=...
    TWILIO_AUTH_TOKEN=...
    TWILIO_FROM_NUMBER=+1...

If those are absent the tool returns an explicit error rather than pretending
to send. That distinction matters: silent success is how we lost months.
"""
from __future__ import annotations

import base64
import os
import urllib.error
import urllib.parse
import urllib.request

from agent_company_ai.tools.registry import tool

_account_sid: str = ""
_auth_token: str = ""
_from_number: str = ""
_default_to: str = ""

# Legacy gateway. Kept for carriers that still support email-to-SMS, but it is
# known-dead for T-Mobile and must never be presented as a working default.
_LEGACY_GATEWAYS = {"tmobile": "tmomail.net", "att": "txt.att.net", "verizon": "vtext.com"}


def set_sms_config(account_sid: str = "", auth_token: str = "",
                   from_number: str = "", default_to: str = "") -> None:
    global _account_sid, _auth_token, _from_number, _default_to
    _account_sid, _auth_token, _from_number, _default_to = (
        account_sid, auth_token, from_number, default_to)


def set_sms_agent(name: str) -> None:
    global _current_agent
    _current_agent = name


_current_agent: str = "unknown"


def _configured() -> bool:
    return bool(_account_sid and _auth_token and _from_number)


@tool(
    "send_sms",
    (
        "Send a real SMS text message to a phone number. Requires a carrier API "
        "(Twilio) configured in .env; returns an explicit error if it is not, "
        "rather than reporting a false success."
    ),
    {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Recipient phone number in E.164 format, e.g. +15025551234"},
            "body": {"type": "string", "description": "Message text (keep under 320 characters)"},
        },
        "required": ["to", "body"],
    },
)
def send_sms(to: str, body: str) -> str:
    to = (to or _default_to).strip()
    body = (body or "").strip()
    if not to:
        return "Error: no recipient. Pass `to` in E.164 format (e.g. +15025551234)."
    if not body:
        return "Error: message body is empty."
    if len(body) > 320:
        body = body[:317] + "..."

    if not _configured():
        return (
            "Error: SMS is NOT configured, so nothing was sent.\n"
            "  A real carrier API is required. The old tmomail.net email-to-SMS "
            "gateway was shut down by T-Mobile in Dec 2024 and silently drops "
            "mail — it must not be used.\n"
            "  To enable SMS, set in .env:\n"
            "    TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER\n"
            f"  Deliverable would have been: to={to!r} ({len(body)} chars)"
        )

    url = f"https://api.twilio.com/2010-04-01/Accounts/{_account_sid}/Messages.json"
    data = urllib.parse.urlencode(
        {"To": to, "From": _from_number, "Body": body}).encode()
    auth = base64.b64encode(f"{_account_sid}:{_auth_token}".encode()).decode()
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            import json
            j = json.loads(r.read().decode())
        return f"SMS sent. sid={j.get('sid')} status={j.get('status')} to={to}"
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:200]
        return f"Error: Twilio rejected the message (HTTP {e.code}): {detail}"
    except Exception as e:
        return f"Error sending SMS: {type(e).__name__}: {e}"
