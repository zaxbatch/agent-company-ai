"""Email delivery channel (Resend or SendGrid).

Pluggable provider selection via ``integrations.notifications.email.provider``.
If no API key is configured the channel reports a clear blocker error so the
delivery log shows exactly what is missing.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from agent_company_ai.notifications.channels.base import ChannelAdapter, DeliveryResult
from agent_company_ai.notifications.models import Channel, Notification

logger = logging.getLogger("agent_company_ai.notifications.email")

RESEND_URL = "https://api.resend.com/emails"
SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"


class EmailChannel(ChannelAdapter):
    """Sends notification emails through Resend or SendGrid."""

    channel = Channel.EMAIL

    def __init__(self, config) -> None:
        self.cfg = config.email
        self._client: httpx.AsyncClient | None = None

    @property
    def configured(self) -> bool:
        return bool(self.cfg.enabled and self.cfg.api_key and self.cfg.from_address)

    async def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    def _build_payload(self, notification: Notification) -> dict[str, Any]:
        html = (
            f"<div style='font-family:sans-serif;max-width:560px;margin:auto'>"
            f"<h2 style='color:#111'>{notification.title}</h2>"
            f"<p style='color:#333;font-size:15px;line-height:1.5'>{notification.body or ''}</p>"
            f"<hr style='border:none;border-top:1px solid #eee'/>"
            f"<p style='color:#888;font-size:12px'>Z-Dot LLC · Mission Control notification "
            f"({notification.type}) · <a href='https://dashboard.zdot.app/notifications'>Open dashboard</a></p>"
            f"</div>"
        )
        if self.cfg.provider == "sendgrid":
            return {
                "personalizations": [{"to": [{"email": self.cfg.from_address}]}],
                "from": {"email": self.cfg.from_address, "name": self.cfg.from_name or "Z-Dot Notifications"},
                "subject": notification.title,
                "content": [{"type": "text/html", "value": html}],
            }
        return {
            "from": f"{self.cfg.from_name or 'Z-Dot Notifications'} <{self.cfg.from_address}>",
            "to": [self.cfg.from_address],
            "reply_to": self.cfg.reply_to or self.cfg.from_address,
            "subject": notification.title,
            "html": html,
            "text": f"{notification.title}\n\n{notification.body or ''}",
        }

    # ------------------------------------------------------------------
    async def send(self, notification: Notification, user_id: str, prefs: dict) -> DeliveryResult:
        if not self.configured:
            return DeliveryResult(
                ok=False,
                error="EMAIL_NOT_CONFIGURED: set integrations.notifications.email.enabled, "
                      "api_key (RESEND_API_KEY/SENDGRID_API_KEY) and from_address",
            )
        try:
            client = await self._http()
            if self.cfg.provider == "sendgrid":
                headers = {"Authorization": f"Bearer {self.cfg.api_key}"}
                url = SENDGRID_URL
            else:
                headers = {"Authorization": f"Bearer {self.cfg.api_key}"}
                url = RESEND_URL
            resp = await client.post(url, json=self._build_payload(notification), headers=headers)
            if resp.status_code in (200, 201, 202):
                body = resp.json() if resp.content else {}
                msg_id = body.get("id") or body.get("message_id") or ""
                logger.info("Email sent for notification %s (%s)", notification.id, self.cfg.provider)
                return DeliveryResult(ok=True, detail={"provider": self.cfg.provider, "message_id": msg_id})
            logger.warning("Email provider returned %s: %s", resp.status_code, resp.text[:300])
            return DeliveryResult(ok=False, error=f"email provider {resp.status_code}: {resp.text[:200]}")
        except Exception as exc:  # network errors, timeouts
            logger.exception("Email delivery failed for notification %s", notification.id)
            return DeliveryResult(ok=False, error=f"email exception: {exc}")
