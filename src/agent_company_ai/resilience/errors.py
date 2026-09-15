"""Error taxonomy + classification.

Six classes (deliverable 1):
  auth      - credential rejected/expired            -> NOT retryable, alert now
  transport - network/TLS/5xx/429/timeout            -> retryable (backoff)
  config    - integration unset/misconfigured        -> NOT retryable, degrade gracefully
  edge      - WAF/CDN bot challenge or block         -> NOT retryable (retry worsens ban)
  data      - 4xx validation / bad payload           -> NOT retryable, caller bug
  app       - our own bug / unexpected state         -> NOT retryable, page engineer
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ErrorClass(str, Enum):
    AUTH = "auth"
    TRANSPORT = "transport"
    CONFIG = "config"
    EDGE = "edge"
    DATA = "data"
    APP = "app"


# --- Vendor-specific hard-auth error codes -----------------------------------
_AUTH_CODES = {
    "api_key_expired", "invalid_api_key", "api_key_invalid", "unauthorized",
    "authentication_required", "invalid_token", "token_expired", "account_invalid",
    "expired_api_key", "key_revoked", "invalid_access_token",
}

# --- Body fingerprints of a WAF / CDN bot challenge --------------------------
_CHALLENGE_MARKERS = (
    "just a moment",
    "checking your browser before accessing",
    "attention required! | cloudflare",
    "cf-mitigated",
    "enable javascript and cookies to continue",
    "ddos protection by",
    "__cf_chl_",
    "hcdn-challenge",
    "imunify",
    "bot-protection",
)
_CHALLENGE_HEADERS = ("cf-mitigated", "x-hcdn-challenge", "x-imunify-captcha")

_CF_EDGE_STATUS = {520, 521, 522, 523, 524, 525, 526, 527}  # Cloudflare origin errors
_RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504} | _CF_EDGE_STATUS


def detect_edge_challenge(headers: dict | None, body: str | None) -> str | None:
    """Return the matched marker if the response is a bot challenge, else None."""
    for h in (headers or {}):
        if str(h).lower() in _CHALLENGE_HEADERS:
            return f"header:{str(h).lower()}"
    low = (body or "")[:20000].lower()
    for m in _CHALLENGE_MARKERS:
        if m in low:
            return f"body:{m}"
    return None


@dataclass
class IntegrationError(Exception):
    """A classified, structured integration failure."""

    integration: str
    operation: str
    error_class: ErrorClass
    message: str
    status: int | None = None
    code: str | None = None
    retryable: bool = False
    degraded: bool = False          # True => caller got a safe fallback value
    retry_after: float | None = None
    attempts: int = 1
    marker: str | None = None       # what matched, for edge/config class
    context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__init__(f"[{self.error_class.value}] {self.integration}.{self.operation}: {self.message}")

    def to_log(self) -> dict[str, Any]:
        """Structured log record. The single shape every integration emits."""
        d = asdict(self)
        d["error_class"] = self.error_class.value
        d["ts"] = datetime.now(timezone.utc).isoformat()
        d["event"] = "integration_error"
        d["severity"] = "critical" if self.error_class in (ErrorClass.AUTH, ErrorClass.EDGE) else (
            "error" if self.error_class in (ErrorClass.APP, ErrorClass.TRANSPORT) else "warning")
        d["alert"] = self.error_class in (ErrorClass.AUTH, ErrorClass.EDGE) or not self.retryable
        return d


def _redact(text: str) -> str:
    """Never let a credential reach a log line."""
    text = re.sub(r"(sk_live_|sk_test_|pk_live_|ghp_|Bearer\s+)\w+", r"\1<REDACTED>", text)
    text = re.sub(r"(?i)(api[_-]?key|access[_-]?token|secret|password)\"?\s*[:=]\s*\"?[A-Za-z0-9_\-]{12,}", r"\1=<REDACTED>", text)
    return text


def classify(
    *,
    integration: str,
    operation: str,
    status: int | None = None,
    code: str | None = None,
    body: str | None = None,
    headers: dict | None = None,
    exception: BaseException | None = None,
    retry_after: float | None = None,
    context: dict | None = None,
) -> IntegrationError:
    """Turn any raw failure into exactly one ErrorClass, with a retry verdict."""
    ctx = context or {}
    body_l = (body or "")[:4000]
    exc_name = type(exception).__name__ if exception else None

    # 1. EDGE first: a challenge/block is never fixed by retrying.
    marker = detect_edge_challenge(headers, body)
    if marker and status in (403, 429, 503, None):
        return IntegrationError(integration, operation, ErrorClass.EDGE,
                                f"edge block/challenge detected ({marker})",
                                status=status, code=code, retryable=False, marker=marker, context=ctx)

    # 2. AUTH: vendor explicitly rejects the credential.
    c_low = (code or "").lower()
    if status in (401, 403) and (c_low in _AUTH_CODES or not code):
        return IntegrationError(integration, operation, ErrorClass.AUTH,
                                _redact(f"credential rejected by vendor ({code or 'no code'})"),
                                status=status, code=code, retryable=False, context=ctx)
    if c_low in _AUTH_CODES:
        return IntegrationError(integration, operation, ErrorClass.AUTH,
                                _redact(f"credential rejected by vendor ({code})"),
                                status=status, code=code, retryable=False, context=ctx)

    # 3. CONFIG: unset/placeholder credentials or missing setting.
    if c_low in ("not_configured", "config_missing", "missing_credential") or (
            exc_name in ("KeyError", "ConfigError") and "not configured" in str(exception or "").lower()):
        return IntegrationError(integration, operation, ErrorClass.CONFIG,
                                "integration not configured", code=code, retryable=False, context=ctx)

    # 4. TRANSPORT: retryable network / upstream fault.
    transient_exc = exc_name in ("ConnectError", "ConnectTimeout", "ReadTimeout", "TimeoutException",
                                 "RemoteProtocolError", "NetworkError", "SSLError", "ConnectionResetError",
                                 "ConnectError", "PoolTimeout", "WriteTimeout", "ReadError")
    if transient_exc or (status in _RETRYABLE_STATUS) or (status is None and exception is not None):
        return IntegrationError(integration, operation, ErrorClass.TRANSPORT,
                                _redact(f"upstream/network failure: {exc_name or ''} {body_l[:200]}".strip()),
                                status=status, code=code, retryable=True,
                                retry_after=retry_after, context=ctx)

    # 5. DATA: caller sent something the vendor refuses (our input bug).
    if status in (400, 404, 405, 409, 413, 415, 422):
        return IntegrationError(integration, operation, ErrorClass.DATA,
                                _redact(f"rejected request payload: {body_l[:300]}"),
                                status=status, code=code, retryable=False, context=ctx)

    # 6. APP: anything else is ours.
    return IntegrationError(integration, operation, ErrorClass.APP,
                            _redact(f"unclassified failure: {body_l[:300] or exc_name}"),
                            status=status, code=code, retryable=False, context=ctx)
