"""`resilient_call` - the ONE chokepoint every integration must use.

Fixes deliverable 3 (fail-loud):
  * structured JSON error log for every failure (logs/integration_errors.jsonl)
  * counters for the monitor (logs/resilience_metrics.json)
  * retry + backoff on transport class only
  * idempotency key on every mutating call, with response replay
  * dead-letter on give-up (success=False, dlq_pushed=True)
  * config-class failures DEGRADE GRACEFULLY when a fallback is supplied,
    instead of exploding in the caller's face
"""
from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import httpx

from .dlq import DeadLetterQueue
from .errors import ErrorClass, IntegrationError, classify
from .idempotency import IdempotencyStore, idempotency_key
from .retry import RetryPolicy, with_retry

logger = logging.getLogger("agent_company_ai.resilience.http")

LOG_DIR = Path("logs")
ERROR_LOG = LOG_DIR / "integration_errors.jsonl"
METRICS = LOG_DIR / "resilience_metrics.json"
_lock = threading.Lock()

_store: IdempotencyStore | None = None
_dlq: DeadLetterQueue | None = None


def store() -> IdempotencyStore:
    global _store
    if _store is None:
        _store = IdempotencyStore(LOG_DIR / "idempotency.db")
    return _store


def dlq() -> DeadLetterQueue:
    global _dlq
    if _dlq is None:
        _dlq = DeadLetterQueue(LOG_DIR / "dlq.jsonl")
    return _dlq


def _emit(err: IntegrationError) -> None:
    rec = err.to_log()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with _lock:
        with ERROR_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, default=str) + "\n")
        m: dict[str, Any] = {}
        if METRICS.exists():
            try:
                m = json.loads(METRICS.read_text())
            except json.JSONDecodeError:
                m = {}
        m["last_error"] = rec
        m["updated_at"] = rec["ts"]
        counts = m.setdefault("counts_by_class", {})
        counts[err.error_class.value] = counts.get(err.error_class.value, 0) + 1
        ic = m.setdefault("counts_by_integration", {})
        ic[f"{err.integration}.{err.operation}"] = ic.get(f"{err.integration}.{err.operation}", 0) + 1
        METRICS.write_text(json.dumps(m, indent=2, default=str))
    logger.error("integration_error %s.%s class=%s status=%s retryable=%s attempts=%d :: %s",
                 err.integration, err.operation, err.error_class.value, err.status,
                 err.retryable, err.attempts, err.message)
    if rec["alert"]:
        _alert(rec)


def _alert(rec: dict) -> None:
    """Fire an immediate alert for a non-retryable / auth / edge failure."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / "alerts.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, default=str) + "\n")


def resilient_call(
    *,
    integration: str,
    operation: str,
    method: str,
    url: str,
    headers: dict | None = None,
    params: dict | None = None,
    json_body: dict | None = None,
    data: dict | None = None,
    timeout: float = 20.0,
    policy: RetryPolicy | None = None,
    use_idempotency: bool = True,
    idempotency_bucket: str | None = None,
    fallback: Any = None,
    expect_json: bool = True,
    extra_headers: Callable[[], dict] | None = None,
    attempts_allowed: bool = False,
) -> Any:
    """Perform an HTTP call with full resilience. Returns parsed body, or `fallback`
    if a CONFIG-class problem occurs and a fallback was provided (graceful degradation).
    Raises IntegrationError otherwise."""
    policy = policy or RetryPolicy()
    key = idempotency_key(integration, operation, json_body or data, method, idempotency_bucket) \
        if use_idempotency else None

    if key:
        hit = store().get(key)
        if hit is not None:
            status, body = hit
            logger.info("idempotent replay %s.%s key=%s (status %s)", integration, operation, key, status)
            return json.loads(body) if expect_json and body else body

    def _once(**_kw: Any) -> Any:
        hdrs = dict(headers or {})
        if extra_headers:
            hdrs.update(extra_headers())
        if key:
            hdrs.setdefault("Idempotency-Key", key)
        try:
            r = httpx.request(method.upper(), url, headers=hdrs, params=params,
                              json=json_body, data=data, timeout=timeout,
                              follow_redirects=True)
        except Exception as exc:
            raise classify(integration=integration, operation=operation,
                           exception=exc, body=str(exc)) from exc

        if r.status_code >= 400:
            code = None
            if expect_json:
                try:
                    j = r.json()
                    err = j.get("error") if isinstance(j, dict) else None
                    if isinstance(err, dict):
                        code = err.get("code") or err.get("type")
                    elif isinstance(j, dict):
                        code = j.get("code") or j.get("error_code")
                except Exception:
                    pass
            ra = r.headers.get("retry-after")
            raise classify(integration=integration, operation=operation,
                           status=r.status_code, code=code, body=r.text,
                           headers=dict(r.headers),
                           retry_after=float(ra) if (ra or "").replace(".", "", 1).isdigit() else None)

        if key:
            store().put(key, integration, operation, r.status_code, r.text)
        if expect_json:
            try:
                return r.json()
            except Exception:
                return r.text
        return r.text

    try:
        return with_retry(_once, policy=policy)
    except IntegrationError as err:
        if err.error_class is ErrorClass.CONFIG and fallback is not None:
            err.degraded = True
            err.message = f"{err.message} -> degraded to fallback"
            _emit(err)
            return fallback
        if err.error_class is ErrorClass.TRANSPORT and fallback is not None:
            err.degraded = True
            _emit(err)
            return fallback
        dlq().push(kind="outbound", integration=integration, operation=operation,
                   error_class=err.error_class.value, message=err.message,
                   payload=json_body or data, attempts=err.attempts, status=err.status,
                   meta={"url": url, "method": method, "idempotency_key": key})
        err.context.setdefault("dlq_pushed", True)
        _emit(err)
        raise
