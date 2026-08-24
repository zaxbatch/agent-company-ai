"""Preference-aware routing: which channels, and how urgently.

Rules
-----
1. In-app is ALWAYS delivered immediately (it is the dashboard's purpose).
2. HIGH priority (payments, hot leads, cancellations, bookings) → out-of-band
   channels deliver immediately regardless of the user's frequency setting.
3. LOW priority (system/operational, digests) → out-of-band channels respect
   the user's frequency: ``instant`` delivers now, ``digest`` batches into the
   daily digest.
4. A channel is used only if the user has an enabled preference row for the
   notification's category (falling back to the ``*`` wildcard row).
"""

from __future__ import annotations

import logging

from agent_company_ai.notifications.models import (
    CATEGORY_WILDCARD,
    Channel,
    Frequency,
    Notification,
    Priority,
    UserPreference,
)

logger = logging.getLogger("agent_company_ai.notifications.router")

DEFAULT_PREFERENCES: list[dict] = [
    # category, channel, frequency
    ("payment", Channel.EMAIL.value, Frequency.INSTANT.value),
    ("payment", Channel.SMS.value, Frequency.INSTANT.value),
    ("lead", Channel.EMAIL.value, Frequency.INSTANT.value),
    ("booking", Channel.EMAIL.value, Frequency.DIGEST.value),
    ("system", Channel.EMAIL.value, Frequency.DIGEST.value),
    ("*", Channel.INAPP.value, Frequency.INSTANT.value),
]


def resolve_preference(
    prefs: list[UserPreference],
    category: str,
    channel: Channel,
) -> UserPreference | None:
    """Find the best-matching enabled preference for (category, channel).

    Exact category match wins; otherwise the ``*`` wildcard applies.
    """
    exact = next((p for p in prefs if p.category == category and p.channel == channel.value), None)
    if exact is not None:
        return exact if exact.enabled else None
    wild = next((p for p in prefs if p.category == CATEGORY_WILDCARD and p.channel == channel.value), None)
    return wild if wild is not None and wild.enabled else None


def plan_deliveries(notification: Notification, prefs: list[UserPreference]) -> dict[Channel, bool]:
    """Return {channel: deliver_now} for the notification.

    ``deliver_now`` True → enqueue immediately; False → hold for digest.
    """
    plan: dict[Channel, bool] = {}
    # In-app always (wildcard default covers it, but be explicit & safe).
    plan[Channel.INAPP] = True

    high = notification.priority == Priority.HIGH
    for ch in Channel.out_of_band():
        pref = resolve_preference(prefs, notification.category, ch)
        if pref is None:
            continue
        if high:
            plan[ch] = True                       # HIGH → always immediate
        else:
            plan[ch] = pref.frequency == Frequency.INSTANT
    return plan
