"""Failover JSON-RPC client.

Fixes TRANSPORT class (deliverable 2B). Root cause was not "the chain is down":
it was that `chains.py` hardcoded exactly ONE rpc_url per chain, so a single
dead endpoint (525 TLS / 401 tenant-disabled) took the whole chain offline with
no failover. Fix: ordered endpoint list + per-endpoint classification + failover
on transport/edge class, and persist a health record so the monitor can see it.

Chain-level mistakes to avoid (learned the hard way):
  * Never fail over on AUTH - that endpoint is misconfigured, not flaky.
  * A 200 with a JSON-RPC `error` object is still a failure; check the envelope.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

from ..resilience.errors import ErrorClass, IntegrationError, classify
from .chains import endpoints_for

logger = logging.getLogger("agent_company_ai.wallet.rpc")

HEALTH_PATH = Path("logs/rpc_health.json")


def _record(endpoint: str, chain: str, ok: bool, detail: str, status: int | None = None) -> None:
    HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if HEALTH_PATH.exists():
        try:
            data = json.loads(HEALTH_PATH.read_text())
        except json.JSONDecodeError:
            data = {}
    data.setdefault(chain, {})[endpoint] = {
        "ok": ok, "detail": detail, "status": status,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    HEALTH_PATH.write_text(json.dumps(data, indent=2))


def call_endpoint(url: str, method: str, params: list, *, chain: str = "unknown",
                  timeout: float = 12.0) -> dict:
    """Single endpoint call. Raises IntegrationError (classified) on any failure."""
    try:
        r = httpx.post(url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                       timeout=timeout, follow_redirects=True)
    except Exception as exc:
        err = classify(integration="rpc", operation=method, exception=exc, body=str(exc),
                       context={"chain": chain, "endpoint": url})
        _record(url, chain, False, f"{type(exc).__name__}: {exc}")
        raise err from exc

    if r.status_code >= 400:
        err = classify(integration="rpc", operation=method, status=r.status_code,
                       body=r.text, headers=dict(r.headers),
                       context={"chain": chain, "endpoint": url})
        _record(url, chain, False, err.message, r.status_code)
        raise err

    body = r.json()
    if "error" in body:                      # HTTP 200 but the call failed
        code = str(body["error"].get("code"))
        err = classify(integration="rpc", operation=method, status=r.status_code,
                       code=code, body=json.dumps(body["error"]),
                       context={"chain": chain, "endpoint": url, "jsonrpc_error": True})
        # tenant disabled / unauthorized inside a 200 envelope -> AUTH
        if "unauthorized" in json.dumps(body["error"]).lower():
            err.error_class = ErrorClass.AUTH
            err.retryable = False
        _record(url, chain, False, err.message, r.status_code)
        raise err

    _record(url, chain, True, "ok", r.status_code)
    return body


def rpc_call(chain: str, method: str, params: list | None = None, *, timeout: float = 12.0) -> dict:
    """Call `method` on `chain`, failing over across endpoints. Returns the raw JSON-RPC body.

    Raises IntegrationError only if EVERY endpoint fails.
    """
    params = params or []
    errors: list[IntegrationError] = []
    for url in endpoints_for(chain):
        try:
            body = call_endpoint(url, method, params, chain=chain, timeout=timeout)
            if errors:
                logger.warning("rpc %s.%s recovered via failover endpoint %s (after %d failed)",
                               chain, method, url, len(errors))
            return body
        except IntegrationError as err:
            errors.append(err)
            if err.error_class is ErrorClass.AUTH and len(errors) == 1:
                # endpoint is misconfigured -> skip it, keep going. Do NOT retry it.
                logger.error("rpc endpoint auth-blocked, skipping: %s (%s)", url, err.message)
            continue
    detail = "; ".join(f"{e.context.get('endpoint')}:{e.error_class.value}:{e.message[:80]}"
                       for e in errors)
    raise IntegrationError("rpc", f"{chain}.{method}", ErrorClass.TRANSPORT,
                           f"all {len(errors)} endpoints failed: {detail}",
                           retryable=False, context={"chain": chain, "failures": len(errors)})


def block_number(chain: str) -> int:
    return int(rpc_call(chain, "eth_blockNumber")["result"], 16)
