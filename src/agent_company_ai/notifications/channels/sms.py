"""SMS delivery channel — pluggable provider interface.

Providers:
  - ``console``  — logs the message (default; great for local dev/demos)
  - ``twilio``   — real SMS via Twilio when env keys are configured

To add a provider: subclass :class:`SmsProvider` and register it in
:meth:`SmsChannel._build_provider`.
"""

from __future__ import annotations

import logging

import httpx

from agent_company_ai.notifications.channels.base import ChannelAdapter, DeliveryResult
from agent_company_ai.notifications.models import Channel, Notification

logger = logging.getLogger("agent_company_ai.notifications.sms")


class SmsProvider:
    """Interface for SMS backends."""

    name = "base"

    async def send(self, to: str, message: str) -> DeliveryResult:
        raise NotImplementedError


class ConsoleSmsProvider(SmsProvider):
    """Logs the SMS to stdout — the demo-friendly default."""

    name = "console"

    def __init__(self, to: str = "+15550000000") -> None:
        self.to = to

    async def send(self, to: str, message: str) -> DeliveryResult:
        logger.info("[SMS:%s] %s", to, message)
        print(f"[SMS → {to}] {message}")
        return DeliveryResult(ok=True, detail={"provider": "console"})


class TwilioSmsProvider(SmsProvider):
    """Real SMS via the Twilio REST API."""

    name = "twilio"

    def __init__(self, account_sid: str, api_key: str, from_number: str) -> None:
        self.account_sid = account_sid
        self.api_key = api_key
        self.from_number = from_number

    async def send(self, to: str, message: str) -> DeliveryResult:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        data = {"To": to, "From": self.from_number, "Body": message}
        auth = (self.account_sid, self.api_key)
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, data=data, auth=auth)
        if resp.status_code in (200, 201):
            return DeliveryResult(ok=True, detail={"provider": "twilio", "sid": resp.json().get("sid", "")})
        return DeliveryResult(ok=False, error=f"twilio {resp.status_code}: {resp.text[:200]}")


class SmsChannel(ChannelAdapter):
    """Sends notification SMS messages."""

    channel = Channel.SMS

    def __init__(self, config) -> None:
        self.cfg = config.sms
        self._provider: SmsProvider | None = None

    @property
    def configured(self) -> bool:
        return bool(self.cfg.enabled)

    def _build_provider(self) -> SmsProvider:
        if self.cfg.provider == "twilio" and self.cfg.account_sid and self.cfg.api_key and self.cfg.from_number:
            return TwilioSmsProvider(self.cfg.account_sid, self.cfg.api_key, self.cfg.from_number)
        return ConsoleSmsProvider()

    async def send(self, notification: Notification, user_id: str, prefs: dict) -> DeliveryResult:
        if not self.configured:
            return DeliveryResult(ok=False, error="SMS_NOT_CONFIGURED: set integrations.notifications.sms.enabled")
        if self._provider is None:
            self._provider = self._build_provider()
        to = self.cfg.from_number or "+15550000000"
        message = f"{notification.title}\n{notification.body or ''}".strip()
        return await self._provider.send(to, message)
