"""Daily digest builder — batches LOW-priority out-of-band notifications.

At the configured digest time the service calls :meth:`build` to collect
LOW-priority notifications from the last 24h that were held for digest
delivery, and produces a single summary email notification
(``digest.daily``) that goes through the normal pipeline.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from agent_company_ai.storage.database import Database

logger = logging.getLogger("agent_company_ai.notifications.digest")


async def collect_digest_items(db: Database, user_id: str, since_hours: int = 24) -> list[dict]:
    """Unread LOW-priority notifications created in the last ``since_hours``."""
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).strftime("%Y-%m-%d %H:%M:%S")
    rows = await db.fetch_all(
        """SELECT id, type, title, body, severity, category, created_at
           FROM notifications
           WHERE user_id = ? AND severity = 'LOW' AND read_at IS NULL AND created_at >= ?
           ORDER BY created_at DESC LIMIT 50""",
        (user_id, cutoff),
    )
    return rows


def build_summary(items: list[dict]) -> tuple[str, str]:
    """Build (title, body) for the digest notification."""
    if not items:
        return "📬 Daily digest — no low-priority updates", "You're all caught up. Nothing batched today."
    lines = []
    for it in items:
        ts = (it.get("created_at") or "")[:16]
        lines.append(f"- [{ts}] {it.get('title', '')}")
    body = "Your batched low-priority updates:\n\n" + "\n".join(lines)
    return f"📬 Daily digest — {len(items)} item(s)", body


def parse_digest_time(hhmm: str) -> tuple[int, int]:
    """Parse 'HH:MM' → (hour, minute); falls back to 08:00."""
    try:
        h, m = hhmm.split(":")
        return int(h), int(m)
    except (ValueError, AttributeError):
        return 8, 0


def seconds_until_next(hhmm: str, now: datetime | None = None) -> int:
    """Seconds until the next occurrence of ``hhmm`` (UTC)."""
    now = now or datetime.now(timezone.utc)
    h, m = parse_digest_time(hhmm)
    target = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return int((target - now).total_seconds())
