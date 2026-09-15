"""Retry with exponential backoff + full jitter, honouring Retry-After.

Safety rules:
  * Only ErrorClass.TRANSPORT is retried. auth/config/edge/data/app are NEVER
    retried - retrying an expired key or a bot challenge is how you get banned.
  * Jitter is mandatory: synchronised retries cause thundering herds.
  * Every attempt is logged with attempt index so the DLQ has real context.
"""
from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from .errors import ErrorClass, IntegrationError

logger = logging.getLogger("agent_company_ai.resilience.retry")

T = TypeVar("T")


@dataclass
class RetryPolicy:
    max_attempts: int = 4
    base_seconds: float = 0.5
    max_seconds: float = 30.0
    jitter: bool = True
    retry_classes: tuple[ErrorClass, ...] = (ErrorClass.TRANSPORT,)

    def delay_for(self, attempt: int, retry_after: float | None = None) -> float:
        """attempt is 1-based. Server Retry-After always wins."""
        if retry_after is not None and retry_after >= 0:
            return min(float(retry_after), self.max_seconds)
        raw = self.base_seconds * (2 ** (attempt - 1))
        raw = min(raw, self.max_seconds)
        return random.uniform(0, raw) if self.jitter else raw


def with_retry(
    fn: Callable[..., T],
    *,
    policy: RetryPolicy | None = None,
    on_attempt: Callable[[int, float, IntegrationError], None] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    **kwargs: Any,
) -> T:
    """Call fn(**kwargs), retrying only retryable classes. Raises IntegrationError at the end."""
    policy = policy or RetryPolicy()
    last: IntegrationError | None = None

    for attempt in range(1, policy.max_attempts + 1):
        try:
            return fn(**kwargs)
        except IntegrationError as err:
            err.attempts = attempt
            if err.error_class not in policy.retry_classes or not err.retryable:
                logger.warning("non-retryable %s on %s.%s (attempt %d) - failing fast",
                               err.error_class.value, err.integration, err.operation, attempt)
                raise
            if attempt >= policy.max_attempts:
                last = err
                logger.error("exhausted %d attempts on %s.%s", attempt, err.integration, err.operation)
                break
            delay = policy.delay_for(attempt, err.retry_after)
            logger.warning("retryable %s on %s.%s attempt %d/%d - sleeping %.2fs",
                           err.error_class.value, err.integration, err.operation,
                           attempt, policy.max_attempts, delay)
            if on_attempt:
                on_attempt(attempt, delay, err)
            sleep(delay)
        except Exception as raw:  # never swallow: re-classify and keep taxonomy honest
            err = IntegrationError(getattr(fn, "__module__", "unknown"), getattr(fn, "__name__", "call"),
                                   ErrorClass.APP, str(raw), retryable=False)
            raise err from raw

    assert last is not None
    raise last
