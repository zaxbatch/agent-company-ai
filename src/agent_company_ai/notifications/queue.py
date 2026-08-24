"""Async delivery queue with retries, backoff, and crash recovery.

Deliveries are persisted in ``notification_deliveries`` before they are
attempted, so a restart can recover in-flight work (see
:meth:`DeliveryQueue.recover_pending`). Failed deliveries retry with
exponential backoff up to ``max_attempts``.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass

from agent_company_ai.notifications.channels.base import ChannelAdapter
from agent_company_ai.notifications.models import Channel, DeliveryStatus, Notification
from agent_company_ai.notifications.rate_limit import RateLimiter
from agent_company_ai.storage.database import Database

logger = logging.getLogger("agent_company_ai.notifications.queue")


@dataclass
class DeliveryJob:
    """A queued delivery attempt."""

    delivery_id: int
    notification_id: str
    notification: Notification
    channel: Channel
    user_id: str
    prefs: dict


class DeliveryQueue:
    """In-process queue + DB-backed retry bookkeeping."""

    def __init__(
        self,
        db: Database,
        channels: dict[Channel, ChannelAdapter],
        limiter: RateLimiter,
        max_retries: int = 3,
        retry_base_seconds: int = 5,
    ) -> None:
        self.db = db
        self.channels = channels
        self.limiter = limiter
        self.max_retries = max_retries
        self.retry_base = retry_base_seconds
        self._queue: asyncio.Queue[DeliveryJob] = asyncio.Queue()
        self._worker: asyncio.Task | None = None
        self._running = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._worker = asyncio.create_task(self._run(), name="notification-delivery-worker")

    async def stop(self) -> None:
        self._running = False
        if self._worker:
            self._worker.cancel()
            try:
                await self._worker
            except (asyncio.CancelledError, Exception):
                pass
            self._worker = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def enqueue(
        self,
        notification: Notification,
        channel: Channel,
        user_id: str,
        prefs: dict,
        *,
        max_attempts: int | None = None,
    ) -> int:
        """Persist a delivery row and enqueue it for immediate processing."""
        cursor = await self.db.execute(
            """INSERT INTO notification_deliveries
               (notification_id, channel, status, max_attempts, created_at)
               VALUES (?, ?, 'pending', ?, ?)""",
            (notification.id, channel.value, max_attempts or self.max_retries,
             time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())),
        )
        delivery_id = int(cursor.lastrowid)
        await self._queue.put(DeliveryJob(
            delivery_id=delivery_id,
            notification_id=notification.id,
            notification=notification,
            channel=channel,
            user_id=user_id,
            prefs=prefs,
        ))
        return delivery_id

    async def recover_pending(self) -> int:
        """Re-enqueue deliveries left pending/retrying after a restart."""
        rows = await self.db.fetch_all(
            """SELECT id, notification_id, channel, status FROM notification_deliveries
               WHERE status IN ('pending','retrying') AND attempts < max_attempts""",
        )
        recovered = 0
        for row in rows:
            nrow = await self.db.fetch_one(
                "SELECT * FROM notifications WHERE id = ?", (row["notification_id"],)
            )
            if not nrow:
                continue
            try:
                channel = Channel(row["channel"])
            except ValueError:
                continue
            notif = Notification(
                id=nrow["id"], user_id=nrow["user_id"], event_id=nrow["event_id"],
                type=nrow["type"], category=nrow["category"], source=nrow["source"],
                severity=nrow["severity"], priority=nrow["priority"], title=nrow["title"],
                body=nrow["body"] or "", metadata=nrow["metadata_json"] or {},
            )
            await self._queue.put(DeliveryJob(
                delivery_id=row["id"], notification_id=notif.id, notification=notif,
                channel=channel, user_id=nrow["user_id"], prefs={},
            ))
            recovered += 1
        if recovered:
            logger.info("Recovered %d pending delivery(ies) from the database", recovered)
        return recovered

    # ------------------------------------------------------------------
    # Worker
    # ------------------------------------------------------------------

    async def _run(self) -> None:
        while self._running:
            try:
                job = await self._queue.get()
            except asyncio.CancelledError:
                break
            try:
                await self._process(job)
            except Exception:
                logger.exception("Unhandled error processing delivery %s", job.delivery_id)
            finally:
                self._queue.task_done()

    async def _process(self, job: DeliveryJob) -> None:
        adapter = self.channels.get(job.channel)
        if adapter is None:
            await self._mark(job, DeliveryStatus.SKIPPED, "no adapter for channel")
            return

        # Rate limiting (anti-spam)
        if not self.limiter.allow(job.channel, job.user_id):
            await self.db.execute(
                """UPDATE notification_deliveries
                   SET status='rate_limited', last_error=?, next_attempt_at=?
                   WHERE id=?""",
                ("rate limit reached; will retry", 
                 time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + self.limiter.next_window_seconds(job.channel, job.user_id))),
                 job.delivery_id),
            )
            logger.info("Rate-limited %s delivery for notification %s", job.channel.value, job.notification_id)
            # schedule a retry inside the next window
            delay = self.limiter.next_window_seconds(job.channel, job.user_id)
            asyncio.get_running_loop().call_later(delay, lambda: asyncio.create_task(self._retry(job)))
            return

        await self.db.execute(
            """UPDATE notification_deliveries SET status='retrying', attempts=attempts+1 WHERE id=?""",
            (job.delivery_id,),
        )
        result = await adapter.send(job.notification, job.user_id, job.prefs)
        if result.ok:
            self.limiter.record(job.channel, job.user_id)
            await self.db.execute(
                """UPDATE notification_deliveries
                   SET status='sent', delivered_at=?, last_error=''
                   WHERE id=?""",
                (time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), job.delivery_id),
            )
            logger.info("Delivered notification %s via %s", job.notification_id, job.channel.value)
            return

        # Failure → retry with backoff until max_attempts
        row = await self.db.fetch_one(
            "SELECT attempts FROM notification_deliveries WHERE id=?", (job.delivery_id,)
        )
        attempts = (row or {}).get("attempts", 0)
        if attempts >= self.max_retries:
            await self.db.execute(
                """UPDATE notification_deliveries SET status='failed', last_error=? WHERE id=?""",
                (result.error[:500], job.delivery_id),
            )
            logger.error("Delivery %s failed permanently: %s", job.delivery_id, result.error)
            return
        backoff = self.retry_base * (2 ** (attempts - 1))
        await self.db.execute(
            """UPDATE notification_deliveries SET status='retrying', last_error=?,
               next_attempt_at=? WHERE id=?""",
            (result.error[:500],
             time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + backoff)),
             job.delivery_id),
        )
        logger.warning("Delivery %s failed (attempt %d/%d): %s — retrying in %ds",
                       job.delivery_id, attempts, self.max_retries, result.error, backoff)
        asyncio.get_running_loop().call_later(backoff, lambda: asyncio.create_task(self._retry(job)))

    async def _retry(self, job: DeliveryJob) -> None:
        """Re-enqueue a previously failed/rate-limited job if still retryable."""
        row = await self.db.fetch_one(
            """SELECT status, attempts, max_attempts FROM notification_deliveries WHERE id=?""",
            (job.delivery_id,),
        )
        if not row:
            return
        if row["status"] not in ("retrying", "rate_limited", "pending"):
            return
        if row["attempts"] >= row["max_attempts"] and row["status"] != "rate_limited":
            await self.db.execute(
                "UPDATE notification_deliveries SET status='failed' WHERE id=?",
                (job.delivery_id,),
            )
            return
        if not self._running:
            return
        await self._queue.put(job)

    async def _mark(self, job: DeliveryJob, status: DeliveryStatus, error: str = "") -> None:
        await self.db.execute(
            "UPDATE notification_deliveries SET status=?, last_error=? WHERE id=?",
            (status.value, error[:500], job.delivery_id),
        )
