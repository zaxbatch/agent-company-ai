"""Channel adapter interface for notification delivery."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_company_ai.notifications.models import Channel, Notification


@dataclass
class DeliveryResult:
    """Outcome of one channel delivery attempt."""

    ok: bool
    error: str = ""
    # For rate-limited deliveries: seconds until we may retry.
    retry_after: int = 0
    # Extra info surfaced in the delivery log (e.g. provider message id).
    detail: dict[str, Any] = field(default_factory=dict)


class ChannelAdapter:
    """Base class for all delivery channels."""

    channel: Channel = Channel.INAPP

    async def send(self, notification: Notification, user_id: str, prefs: dict) -> DeliveryResult:
        """Deliver ``notification`` to the user via this channel.

        ``prefs`` is the resolved preference row for the notification category
        (may be used by channels to format digests differently).
        """
        raise NotImplementedError

    def describe(self) -> str:
        return self.channel.value
