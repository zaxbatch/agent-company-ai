"""Sliding-window rate limiter for out-of-band notification delivery.

Prevents alert spam (email storms, SMS floods). Each (channel, user) pair
gets an hourly and a daily budget, configurable in
``integrations.notifications.rate_limits``.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field

from agent_company_ai.notifications.models import Channel


@dataclass
class _WindowCounter:
    """Rolling window of timestamps + a hard cap."""

    hourly_limit: int
    daily_limit: int
    hourly: deque[float] = field(default_factory=deque)
    daily: deque[float] = field(default_factory=deque)

    def _prune(self, now: float) -> None:
        while self.hourly and now - self.hourly[0] >= 3600:
            self.hourly.popleft()
        while self.daily and now - self.daily[0] >= 86400:
            self.daily.popleft()

    def allow(self, now: float | None = None) -> bool:
        now = now if now is not None else time.time()
        self._prune(now)
        if len(self.hourly) >= self.hourly_limit:
            return False
        if len(self.daily) >= self.daily_limit:
            return False
        return True

    def record(self, now: float | None = None) -> None:
        now = now if now is not None else time.time()
        self._prune(now)
        self.hourly.append(now)
        self.daily.append(now)

    def remaining(self, now: float | None = None) -> int:
        now = now if now is not None else time.time()
        self._prune(now)
        return max(0, min(self.hourly_limit - len(self.hourly),
                         self.daily_limit - len(self.daily)))

    def next_window_seconds(self, now: float | None = None) -> int:
        """Seconds until the hourly window frees up (for retry scheduling)."""
        now = now if now is not None else time.time()
        self._prune(now)
        if not self.hourly:
            return 0
        return max(1, int(3600 - (now - self.hourly[0])))


class RateLimiter:
    """Thread-safe-ish (asyncio single loop) rate limiter keyed by channel+user."""

    def __init__(self, config) -> None:
        self._limits: dict[Channel, tuple[int, int]] = {
            Channel.EMAIL: (config.rate_limits.emails_per_hour, config.rate_limits.emails_per_day),
            Channel.SMS: (config.rate_limits.sms_per_hour, config.rate_limits.sms_per_day),
            Channel.PUSH: (config.rate_limits.pushes_per_hour, config.rate_limits.pushes_per_day),
            Channel.INAPP: (10_000, 100_000),  # in-app is unbounded in practice
        }
        self._counters: dict[tuple[Channel, str], _WindowCounter] = defaultdict(
            lambda: _WindowCounter(0, 0)
        )

    def _counter(self, channel: Channel, user_id: str) -> _WindowCounter:
        limits = self._limits.get(channel, (100, 1000))
        key = (channel, user_id)
        c = self._counters[key]
        if c.hourly_limit != limits[0]:  # lazy init with current config
            c.hourly_limit, c.daily_limit = limits
        return c

    def allow(self, channel: Channel, user_id: str) -> bool:
        return self._counter(channel, user_id).allow()

    def record(self, channel: Channel, user_id: str) -> None:
        self._counter(channel, user_id).record()

    def remaining(self, channel: Channel, user_id: str) -> int:
        return self._counter(channel, user_id).remaining()

    def next_window_seconds(self, channel: Channel, user_id: str) -> int:
        return self._counter(channel, user_id).next_window_seconds()
