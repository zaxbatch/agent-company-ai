"""Dashboard notification system for Agent Company AI.

Layers
------
- ``models``     — event / notification / preference data models
- ``templates``  — event-type → title/body/severity/priority registry
- ``rate_limit`` — sliding-window anti-spam counters per channel
- ``router``     — preference-aware channel + urgency routing
- ``queue``      — async delivery queue with retries and backoff
- ``channels``   — pluggable delivery adapters (in-app, email, sms, push)
- ``digest``     — batched daily digest for LOW-priority items
- ``service``    — orchestrator: ingest → route → enqueue → deliver → broadcast
- ``webhooks``   — FastAPI routes (Stripe/Gumroad/Cal.com + internal API + SSE)
"""

from agent_company_ai.notifications.service import NotificationService
from agent_company_ai.notifications.models import (
    NotificationEvent,
    Notification,
    IngestResult,
    DeliveryStatus,
    Severity,
    Priority,
    Frequency,
)

__all__ = [
    "NotificationService",
    "NotificationEvent",
    "Notification",
    "IngestResult",
    "DeliveryStatus",
    "Severity",
    "Priority",
    "Frequency",
]
