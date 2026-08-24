"""Event-type registry: type → category, severity, priority, and copy templates.

Adding a new notification type = add one entry here (see the runbook).
Titles/bodies support ``{placeholder}`` substitution from the event metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_company_ai.notifications.models import (
    CATEGORY_BOOKING,
    CATEGORY_LEAD,
    CATEGORY_PAYMENT,
    CATEGORY_SYSTEM,
    Priority,
    Severity,
)


@dataclass(frozen=True)
class EventTemplate:
    """Presentation + routing rules for one event type."""

    category: str
    severity: Severity
    priority: Priority
    title: str
    body: str = ""
    icon: str = "🔔"

    def render(self, metadata: dict[str, Any]) -> tuple[str, str]:
        """Substitute ``{key}`` placeholders from event metadata."""
        ctx = {k: (v if v is not None else "") for k, v in metadata.items()}
        try:
            title = self.title.format(**ctx)
        except (KeyError, IndexError):
            title = self.title
        try:
            body = self.body.format(**ctx)
        except (KeyError, IndexError):
            body = self.body
        return title, body


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

TEMPLATES: dict[str, EventTemplate] = {
    # ── Payments (HIGH → immediate) ─────────────────────────────────────
    "payment.received": EventTemplate(
        category=CATEGORY_PAYMENT,
        severity=Severity.HIGH,
        priority=Priority.HIGH,
        title="💰 Payment received — {amount}",
        body="{customer} paid {amount} for {product} ({method}).",
        icon="💰",
    ),
    "payment.cancelled": EventTemplate(
        category=CATEGORY_PAYMENT,
        severity=Severity.HIGH,
        priority=Priority.HIGH,
        title="⚠️ Payment cancelled — {customer}",
        body="{customer} cancelled {product} ({method}). Follow up within 24h.",
        icon="⚠️",
    ),
    # ── Leads (HIGH → immediate) ────────────────────────────────────────
    "lead.new": EventTemplate(
        category=CATEGORY_LEAD,
        severity=Severity.HIGH,
        priority=Priority.HIGH,
        title="🔥 New hot lead — {name}",
        body="{name} ({company}) via {source}. {email}",
        icon="🔥",
    ),
    # ── Bookings (HIGH → immediate) ─────────────────────────────────────
    "booking.scheduled": EventTemplate(
        category=CATEGORY_BOOKING,
        severity=Severity.HIGH,
        priority=Priority.HIGH,
        title="📅 Booking scheduled — {name}",
        body="{name} booked {title} at {start_time} ({duration} min).",
        icon="📅",
    ),
    # ── System / operational (LOW → batched) ────────────────────────────
    "system.alert": EventTemplate(
        category=CATEGORY_SYSTEM,
        severity=Severity.LOW,
        priority=Priority.LOW,
        title="🛠 {subject}",
        body="{detail}",
        icon="🛠",
    ),
    "system.test": EventTemplate(
        category=CATEGORY_SYSTEM,
        severity=Severity.MEDIUM,
        priority=Priority.HIGH,   # test notifications should appear instantly
        title="🧪 Test notification — {channel}",
        body="This is a manual test of the {channel} channel. If you can read this, the pipeline works.",
        icon="🧪",
    ),
    "digest.daily": EventTemplate(
        category=CATEGORY_SYSTEM,
        severity=Severity.LOW,
        priority=Priority.LOW,
        title="📬 Daily digest — {count} item(s)",
        body="Summary of low-priority updates: {summary}",
        icon="📬",
    ),
}

# Alias: CRM lead capture may post under a different event name.
TEMPLATES["crm.lead.new"] = TEMPLATES["lead.new"]


def get_template(event_type: str) -> EventTemplate | None:
    return TEMPLATES.get(event_type)


def known_event_types() -> list[str]:
    return sorted(TEMPLATES.keys())
