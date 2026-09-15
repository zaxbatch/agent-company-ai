"""Idempotency for outbound writes (charges, bookings, products, invoices).

A network timeout on a POST /v1/charges is ambiguous: the charge may have
succeeded. Without an idempotency key you double-bill the customer. This module
generates a deterministic, content-addressed key and stores the (key -> result)
mapping so a retry replays the ORIGINAL response instead of re-executing.
"""
from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("agent_company_ai.resilience.idempotency")

_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def idempotency_key(integration: str, operation: str, payload: dict | None = None,
                    method: str = "POST", bucket: str | None = None) -> str | None:
    """Deterministic key. Returns None for safe/idempotent-by-spec GETs.

    `bucket` lets a caller group a logical operation (e.g. one order id) so a
    retry of the same logical action reuses the key.
    """
    if method.upper() not in _MUTATING_METHODS:
        return None
    material = f"{integration}|{operation}|{bucket or ''}|{canon(payload or {})}"
    return f"zdot_{hashlib.sha256(material.encode()).hexdigest()[:40]}"


class IdempotencyStore:
    """SQLite-backed replay store. Safe for concurrent use (WAL + lock)."""

    def __init__(self, path: str | Path = "logs/idempotency.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS idem (
                key TEXT PRIMARY KEY, integration TEXT, operation TEXT,
                status INTEGER, response TEXT, created_at TEXT)""")

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.path, timeout=10)
        c.execute("PRAGMA journal_mode=WAL")
        return c

    def get(self, key: str) -> tuple[int, str] | None:
        with self._lock, self._conn() as c:
            row = c.execute("SELECT status, response FROM idem WHERE key=?", (key,)).fetchone()
        return (row[0], row[1]) if row else None

    def put(self, key: str, integration: str, operation: str, status: int, response: str) -> None:
        with self._lock, self._conn() as c:
            c.execute("INSERT OR IGNORE INTO idem VALUES (?,?,?,?,?,?)",
                      (key, integration, operation, status, response,
                       datetime.now(timezone.utc).isoformat()))

    def stats(self) -> dict[str, int]:
        with self._lock, self._conn() as c:
            n = c.execute("SELECT COUNT(*) FROM idem").fetchone()[0]
        return {"replay_keys_stored": n}
