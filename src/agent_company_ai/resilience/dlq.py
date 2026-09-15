"""Dead-letter queue for webhooks and give-up-after-retries calls.

Two guarantees:
  1. A webhook that fails to process is NEVER dropped - it is persisted with its
     full body, headers, failure class and attempt count, then acked to the
     sender so the provider does not hammer us.
  2. Every give-up on an outbound call lands here, so "we silently lost 40
     registrations" is impossible.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger("agent_company_ai.resilience.dlq")


class DeadLetterQueue:
    def __init__(self, path: str | Path = "logs/dlq.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def push(self, *, kind: str, integration: str, operation: str, error_class: str,
             message: str, payload: Any = None, attempts: int = 1,
             status: int | None = None, meta: dict | None = None) -> dict:
        rec = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "kind": kind,                      # "outbound" | "webhook"
            "integration": integration,
            "operation": operation,
            "error_class": error_class,
            "message": message,
            "attempts": attempts,
            "status": status,
            "payload": payload,
            "meta": meta or {},
            "replayed": False,
        }
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, default=str) + "\n")
        logger.error("DLQ push kind=%s integration=%s op=%s class=%s attempts=%d",
                     kind, integration, operation, error_class, attempts)
        return rec

    def __iter__(self) -> Iterator[dict]:
        if not self.path.exists():
            return iter(())
        with self.path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue

    def depth(self) -> int:
        return sum(1 for _ in self)
