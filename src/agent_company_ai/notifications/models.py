"""Data models and constants for the notification system."""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    """How important a notification is (used for display and routing)."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Priority(str, Enum):
    """Urgency for delivery routing.

    HIGH  → delivered immediately on all enabled channels
    LOW   → in-app immediately; out-of-band batched into the daily digest
    """

    HIGH = "HIGH"
    LOW = "LOW"


class Frequency(str, Enum):
    """How often a user wants out-of-band delivery for a category."""

    INSTANT = "instant"
    DIGEST = "digest"


class DeliveryStatus(str, Enum):
    """Lifecycle of a channel delivery attempt."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"
    RATE_LIMITED = "rate_limited"
    RETRYING = "retrying"


class Channel(str, Enum):
    """Available delivery channels."""

    INAPP = "inapp"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

    @classmethod
    def out_of_band(cls) -> list["Channel"]:
        """Channels other than the in-app notification center."""
        return [cls.EMAIL, cls.SMS, cls.PUSH]


# ---------------------------------------------------------------------------
# Event categories (what Zerric can toggle in preferences)
# ---------------------------------------------------------------------------

CATEGORY_PAYMENT = "payment"
CATEGORY_LEAD = "lead"
CATEGORY_BOOKING = "booking"
CATEGORY_SYSTEM = "system"
CATEGORY_WILDCARD = "*"

CATEGORIES = [CATEGORY_PAYMENT, CATEGORY_LEAD, CATEGORY_BOOKING, CATEGORY_SYSTEM]


# ---------------------------------------------------------------------------
# Event envelope — the ingestion contract
# ---------------------------------------------------------------------------

class NotificationEvent(BaseModel):
    """An inbound business event that may produce notifications.

    ``event_id`` is the idempotency key — re-ingesting the same event is a
    no-op (the source webhook systems can retry safely).
    """

    event_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    type: str                                  # e.g. "payment.received"
    source: str = ""                           # stripe | gumroad | calcom | crm | manual | system
    user_id: str = "admin"
    severity: Optional[Severity] = None        # override template default
    title: Optional[str] = None                # override template default
    body: Optional[str] = None                 # override template default
    metadata: dict[str, Any] = Field(default_factory=dict)

    def dedupe_key(self) -> str:
        return self.event_id


# ---------------------------------------------------------------------------
# Notification record (as stored in the notifications table)
# ---------------------------------------------------------------------------

class Notification(BaseModel):
    """A persisted, user-facing notification."""

    id: str
    user_id: str = "admin"
    event_id: Optional[str] = None
    type: str
    category: str = CATEGORY_SYSTEM
    source: str = ""
    severity: Severity = Severity.LOW
    priority: Priority = Priority.LOW
    title: str
    body: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    read_at: Optional[str] = None
    created_at: Optional[str] = None

    @property
    def is_read(self) -> bool:
        return bool(self.read_at)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_id": self.event_id,
            "type": self.type,
            "category": self.category,
            "source": self.source,
            "severity": self.severity.value if isinstance(self.severity, Severity) else self.severity,
            "priority": self.priority.value if isinstance(self.priority, Priority) else self.priority,
            "title": self.title,
            "body": self.body,
            "metadata": self.metadata,
            "read_at": self.read_at,
            "created_at": self.created_at,
            "is_read": self.is_read,
        }


# ---------------------------------------------------------------------------
# Ingest result
# ---------------------------------------------------------------------------

class IngestResult(BaseModel):
    """Outcome of ingesting one event."""

    accepted: bool
    duplicate: bool = False
    notification_id: Optional[str] = None
    event_id: str = ""
    channels: list[str] = Field(default_factory=list)
    skipped_reason: str = ""


# ---------------------------------------------------------------------------
# User preference row
# ---------------------------------------------------------------------------

class UserPreference(BaseModel):
    """One (user, category, channel) delivery rule."""

    user_id: str = "admin"
    category: str = CATEGORY_WILDCARD
    channel: str = Channel.INAPP.value
    frequency: Frequency = Frequency.INSTANT
    enabled: bool = True


# ---------------------------------------------------------------------------
# Delivery row
# ---------------------------------------------------------------------------

class Delivery(BaseModel):
    """A single channel-delivery attempt (persisted in notification_deliveries)."""

    id: Optional[int] = None
    notification_id: str
    channel: str
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    last_error: str = ""
    next_attempt_at: Optional[str] = None
    delivered_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------

def now_iso() -> str:
    """Current UTC time as an ISO-8601 string (SQLite-friendly)."""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
