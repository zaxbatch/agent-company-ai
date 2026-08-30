#!/usr/bin/env python3
"""INC-2026-08-25-001 — smoke-test harness for the 3 incident tool categories.

Runs a REAL tool-call round trip through the shared LLM layer (the exact path
Agent.think() uses: complete() -> tool_calls -> execute tool -> complete() again)
for one of the incident categories (browse | crm | payments), and writes the
HTTP status + response body of EVERY LLM API call verbatim to a log file.

The final LLM call (the follow-up after the tool result) is the assertion point:
- Baseline (pre-fix):  HTTP 400 "reasoning_content ... must be passed back"
- Post-fix (expected): HTTP 200 with a valid response body

Usage:
    python3 harness/smoke_tool.py browse   [--log PATH]
    python3 harness/smoke_tool.py crm      [--log PATH]
    python3 harness/smoke_tool.py payments [--log PATH]

Exit codes:
    0  final LLM call returned HTTP 200 (PASS)
    1  final LLM call returned non-200 (FAIL — expected for baseline)
    2  harness / environment error (round trip could not complete)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Make the repo's src importable even if the package isn't pip-installed.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


# ---------------------------------------------------------------------------
# .env loader (mirrors start.sh: set -a; source .env; set +a)
# ---------------------------------------------------------------------------
def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


# ---------------------------------------------------------------------------
# Log writer
# ---------------------------------------------------------------------------
class _Log:
    def __init__(self, path: Path):
        self.path = path
        self._fh = open(path, "w", encoding="utf-8")
        self._fh.write(f"# INC-2026-08-25-001 smoke-test log — started {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
        self._fh.flush()

    def write(self, text: str) -> None:
        self._fh.write(text)
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


# ---------------------------------------------------------------------------
# Category configuration
# ---------------------------------------------------------------------------
CATEGORIES = {
    "browse": {
        "tool": "browse_page",
        "default_args": {"url": "https://example.com", "extract": "text"},
        "prompt": (
            "Use the browse_page tool to browse https://example.com and report "
            "the page title and the first 200 characters of extracted text."
        ),
    },
    "crm": {
        "tool": "add_contact",
        "default_args": {"email": "smoke.inc001@zdot-dummy.com", "name": "Smoke Test", "company": "Z-Dot LLC", "status": "lead", "source": "inc-2026-08-25-001-smoke"},
        "prompt": (
            "Use the add_contact tool to add a CRM contact with email "
            "smoke.inc001@zdot-dummy.com, name 'Smoke Test', company 'Z-Dot LLC', "
            "status 'lead', source 'inc-2026-08-25-001-smoke'."
        ),
    },
    "payments": {
        "tool": "check_payments",
        "default_args": {"limit": 1},
        "prompt": (
            "Use the check_payments tool to check the most recent Stripe charges "
            "and report how many charges exist."
        ),
    },
}

SYSTEM_PROMPT = (
    "You are a smoke-test agent for incident INC-2026-08-25-001. "
    "Complete the requested task by calling the provided tool. "
    "After the tool returns, answer with a short factual summary."
)


# ---------------------------------------------------------------------------
# Round trip
# ---------------------------------------------------------------------------
async def run_category(category: str, log: _Log) -> int:
    from agent_company_ai.config import load_config
    from agent_company_ai.llm.router import LLMRouter
    from agent_company_ai.llm.base import LLMMessage, ToolCall
    from agent_company_ai.tools.registry import ToolRegistry
    from agent_company_ai.storage.database import Database

    # 1) Load production config (same file the running platform uses).
    cfg_path = Path(".agent-company-ai/default/config.yaml")
    config = load_config(cfg_path)
    router = LLMRouter(config.llm)
    provider = router.get_provider()  # default_provider=openai -> DeepSeek endpoint

    log.write(f"# Category: {category}\n")
    log.write(f"# LLM config: model={provider.model} base_url={provider.base_url} key={provider.api_key[:8]}...\n")
    log.write(f"# Config file: {cfg_path.resolve()}\n\n")

    # 2) Wrap the provider's HTTP client so EVERY response (status + body) is
    #    captured verbatim to the log.
    import httpx
    import openai

    def _hook(response: httpx.Response) -> None:
        try:
            body = response.text
        except Exception:
            body = "<unreadable response body>"
        log.write(f"--- HTTP {response.status_code} ---\n{body}\n")

    http_client = httpx.AsyncClient(timeout=120.0, event_hooks={"response": [_hook]})
    provider._client = openai.AsyncOpenAI(
        api_key=provider.api_key,
        base_url=provider.base_url,
        http_client=http_client,
    )

    # 3) Load the REAL tool definition from the registry (same object the agent uses).
    import agent_company_ai.tools.browser_tool  # noqa: F401  (self-registers)
    import agent_company_ai.tools.contacts      # noqa: F401
    import agent_company_ai.tools.stripe_tools  # noqa: F401

    cat = CATEGORIES[category]
    tool_obj = ToolRegistry.get().get_tool(cat["tool"])
    if tool_obj is None:
        log.write(f"ERROR: tool '{cat['tool']}' not registered\n")
        return 2
    tool_def = tool_obj.to_definition()

    # 4) Wire the tool's runtime deps (temp SQLite DB + Stripe key from .env).
    db = Database(Path("/tmp/inc-2026-08-25-001-smoke.db"))
    await db.connect()
    from agent_company_ai.tools.contacts import set_contacts_db
    from agent_company_ai.tools.browser_tool import set_browser_db
    from agent_company_ai.tools.stripe_tools import set_stripe_config, set_stripe_db, set_stripe_rate_limits

    set_contacts_db(db)
    set_browser_db(db)
    set_stripe_db(db)
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
    set_stripe_config(stripe_key)
    set_stripe_rate_limits(500.0)
    log.write(f"# Stripe configured: {bool(stripe_key)} | temp DB: {db.db_path}\n\n")

    # 5) Round trip — mirrors Agent.think()'s message flow exactly.
    messages = [
        LLMMessage(role="system", content=SYSTEM_PROMPT),
        LLMMessage(role="user", content=cat["prompt"]),
    ]

    # ---- CALL 1: initial completion (model should emit a tool_call) ----
    log.write(f"===== LLM CALL 1 (initial, tools=[{cat['tool']}]) =====\n")
    try:
        resp1 = await provider.complete(messages=messages, tools=[tool_def])
    except Exception as exc:
        status = getattr(exc, "status_code", "?")
        log.write(f"RESULT-CALL1: EXCEPTION {type(exc).__name__} HTTP {status}\n")
        log.write(f"RESULT: FAIL — round trip aborted at CALL 1 (HTTP {status})\n")
        return 2
    log.write(f"RESULT-CALL1: OK — finish={resp1.stop_reason} content={resp1.content[:120]!r}\n\n")

    if resp1.tool_calls:
        tc: ToolCall = resp1.tool_calls[0]
        log.write(f"[CALL 1] model emitted tool_call: {tc.name}({json.dumps(tc.arguments)})\n")
    else:
        # Deterministic fallback (same approach as CTO pin_down repro):
        # build a valid tool_call against the real schema and execute it.
        tc = ToolCall(id="call_smoke_fabricated", name=cat["tool"], arguments=dict(cat["default_args"]))
        log.write(f"[CALL 1] model returned text only — FABRICATED valid tool_call {tc.name}({json.dumps(tc.arguments)}) for deterministic round trip\n")

    # ---- Execute the REAL tool ----
    log.write(f"\n===== TOOL EXECUTION: {tc.name}({json.dumps(tc.arguments)}) =====\n")
    try:
        tool_result = await tool_obj.execute(**tc.arguments)
    except Exception as exc:
        tool_result = f"Tool execution raised: {type(exc).__name__}: {exc}"
    log.write(f"TOOL RESULT: {tool_result[:300]}\n\n")

    # ---- Build the follow-up history EXACTLY as agent.py does (assistant w/
    # tool_calls + tool message). reasoning_content is NOT carried — this is
    # the buggy path under test. ----
    messages.append(LLMMessage(
        role="assistant",
        content=resp1.content or "",
        tool_calls=[{"id": tc.id, "name": tc.name, "arguments": tc.arguments}],
    ))
    messages.append(LLMMessage(role="tool", content=tool_result, tool_call_id=tc.id))

    # ---- CALL 2: the follow-up (ASSERTION POINT) ----
    log.write(f"===== LLM CALL 2 (follow-up after tool result, tools=[{cat['tool']}]) =====\n")
    try:
        resp2 = await provider.complete(messages=messages, tools=[tool_def])
        log.write(f"RESULT-CALL2: OK — HTTP 200 finish={resp2.stop_reason} content={resp2.content[:300]!r}\n")
        log.write("\nRESULT: PASS — final LLM call returned HTTP 200 with a valid response body\n")
        await db.close()
        return 0
    except Exception as exc:
        status = getattr(exc, "status_code", "?")
        body = getattr(getattr(exc, "response", None), "text", None)
        log.write(f"RESULT-CALL2: EXCEPTION {type(exc).__name__} HTTP {status}\n")
        if body:
            log.write(f"RESULT-CALL2 BODY: {body}\n")
        log.write(f"\nRESULT: FAIL — final LLM call returned HTTP {status} (non-200)\n")
        await db.close()
        return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="INC-2026-08-25-001 smoke-test harness")
    ap.add_argument("category", choices=sorted(CATEGORIES.keys()))
    ap.add_argument("--log", default=None, help="Log file path (default: logs/inc-2026-08-25-001/baseline-<category>.log)")
    args = ap.parse_args()

    _load_dotenv(Path(".env"))

    log_path = args.log or Path(f"logs/inc-2026-08-25-001/baseline-{args.category}.log")
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = _Log(log_path)

    try:
        rc = asyncio.run(run_category(args.category, log))
    except Exception as exc:  # pragma: no cover - safety net
        log.write(f"\nHARNESS ERROR: {type(exc).__name__}: {exc}\n")
        rc = 2
    finally:
        log.close()

    print(f"[smoke:{args.category}] log -> {log_path} (exit {rc})")
    return rc


if __name__ == "__main__":
    sys.exit(main())
