"""Resilience core: classification, retry, idempotency, dead-letter.

The Bot Mode lesson: nothing is "done" without an artifact and proof.
Every outbound integration call MUST go through `resilient_call`.
"""
from .errors import ErrorClass, IntegrationError, classify, detect_edge_challenge
from .retry import RetryPolicy, with_retry
from .idempotency import idempotency_key, IdempotencyStore
from .dlq import DeadLetterQueue
from .http import resilient_call

__all__ = [
    "ErrorClass", "IntegrationError", "classify", "detect_edge_challenge",
    "RetryPolicy", "with_retry",
    "idempotency_key", "IdempotencyStore",
    "DeadLetterQueue", "resilient_call",
]
