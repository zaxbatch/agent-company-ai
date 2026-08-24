"""In-app delivery channel.

The in-app channel is implicit: the notification is already persisted and
pushed to the browser over SSE by the service at ingest time. This adapter
exists so the channel abstraction is uniform; ``send`` is a no-op success.
"""

from __future__ import annotations

from agent_company_ai.notifications.channels.base import ChannelAdapter, DeliveryResult
from agent_company_ai.notifications.models import Channel, Notification


class InAppChannel(ChannelAdapter):
    """Marker channel — delivery = DB row + SSE broadcast (done by service)."""

    channel = Channel.INAPP

    async def send(self, notification: Notification, user_id: str, prefs: dict) -> DeliveryResult:
        return DeliveryResult(ok=True, detail={"channel": "inapp"})
