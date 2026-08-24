"""Push delivery channel — pluggable provider interface.

Providers:
  - ``console`` — logs the push (default; demo-friendly)
  - ``webpush`` — reserved for Web Push / VAPID integration (stub)

Add real providers by subclassing :class:`PushProvider`.
"""

from __future__ import annotations

import logging

from agent_company_ai.notifications.channels.base import ChannelAdapter, DeliveryResult
from agent_company_ai.notifications.models import Channel, Notification

logger = logging.getLogger("agent_company_ai.notifications.push")


class PushProvider:
    """Interface for push notification backends."""

    name = "base"

    async def send(self, title: str, body: str) -> DeliveryResult:
        raise NotImplementedError


class ConsolePushProvider(PushProvider):
    """Logs the push — the demo-friendly default."""

    name = "console"

    async def send(self, title: str, body: str) -> DeliveryResult:
        print(f"[PUSH] {title} — {body}")
        return DeliveryResult(ok=True, detail={"provider": "console"})


class WebPushProvider(PushProvider):
    """Web Push / VAPID stub — wire to pywebpush when ready."""

    name = "webpush"

    async def send(self, title: str, body: str) -> DeliveryResult:
        return DeliveryResult(
            ok=False,
            error="WEBPUSH_NOT_CONFIGURED: VAPID keys and a subscription registry are required",
        )


class PushChannel(ChannelAdapter):
    """Sends push notifications."""

    channel = Channel.PUSH

    def __init__(self, config) -> None:
        self.cfg = config.push
        self._provider: PushProvider | None = None

    @property
    def configured(self) -> bool:
        return bool(self.cfg.enabled)

    def _build_provider(self) -> PushProvider:
        if self.cfg.provider == "webpush":
            return WebPushProvider()
        return ConsolePushProvider()

    async def send(self, notification: Notification, user_id: str, prefs: dict) -> DeliveryResult:
        if not self.configured:
            return DeliveryResult(ok=False, error="PUSH_NOT_CONFIGURED: set integrations.notifications.push.enabled")
        if self._provider is None:
            self._provider = self._build_provider()
        return await self._provider.send(notification.title, notification.body or "")
