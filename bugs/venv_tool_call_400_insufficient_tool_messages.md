# BUG — venv mode: 400 "insufficient tool messages following tool_calls"

**Severity:** HIGH — affects our own company harness (agent_company_ai) in venv mode, our normal daily operation path.
**Owner:** NinjaNerd (CTO) · **Implementer:** ClickClack · **Reviewer:** NinjaNerd
**Reported:** 2026-08-26 · **Filed by:** NinjaNerd

## Symptom
OpenAI-compatible endpoint (DeepSeek, per `.agent-company-ai/default/config.yaml`:
`base_url: https://api.deepseek.com/v1`, provider `openai`) rejects requests with:

```
400 - "An assistant message with 'tool_calls' must be followed by tool messages
responding to each 'tool_call_id'. (insufficient tool messages following tool_calls message)"
```

Non-retryable. Occurs in chat-mode tool loops in venv mode. Same seam already broke
once (INC-2026-08-25-001, "reasoning_content" 400) — tool-call round trip is fragile here.

## Root cause (confirmed by CTO, line-traced)
`src/agent_company_ai/core/agent.py` `_execute_chat_tool()` (lines ~581-597) makes a
NESTED `provider.complete(messages=self._conversation, ...)` while `self._conversation`
ends with an assistant message carrying `tool_calls` and ZERO tool responses (they're
appended by the caller AFTER `_execute_chat_tool` returns, line ~501). OpenAI contract:
every assistant `tool_calls` message must be IMMEDIATELY followed by `tool` messages for
each id. Sending the mid-chain conversation violates it -> deterministic 400.

Secondary defect: `_execute_chat_tool` never actually executes the tool — it just asks
the LLM to re-answer the whole conversation and appends the reply as a rogue assistant
message mid-chain. Tools silently never run in chat mode.

## Fix spec
### 1. Rewrite `_execute_chat_tool` to actually execute (mirror `_execute_tool` lines ~360-365)
```python
async def _execute_chat_tool(self, tc) -> str:
    """Execute one tool call in chat mode and return its result string."""
    tool = self._tool_registry.get_tool(tc.name)
    if tool is None:
        return f"Error: Unknown tool '{tc.name}'"
    try:
        return await tool.execute(**tc.arguments)
    except Exception as e:
        return f"Tool error: {e}"
```
- Remove the nested `provider.complete()` call entirely. Caller already appends the
  `tool` message right after (line ~501), preserving assistant -> tool pairing.
- `tc.arguments` is already a dict (same shape used in `_execute_tool`).
- Edge cases: unknown tool -> error string; tool raises -> "Tool error: {e}";
  parallel tool calls each get their own tool message via the caller's loop.

### 2. Order-insensitive repair in `_repair_conversation` (line ~558)
`matched == expected_ids` compares in encounter order vs declaration order. If the
provider returns parallel tool messages in a different order, a VALID pairing gets
wrongly stripped. Compare as sets:
```python
if set(matched) == set(expected_ids) and len(matched) == len(expected_ids):
```

### 3. `run()` — append tool message BEFORE terminal check (lines ~255-260)
If `task.is_terminal` short-circuits mid-loop, the second tool message is never
appended. Move `messages.append(LLMMessage(role="tool", ...))` above the
`task.is_terminal` return so the chain is always complete.

### 4. Pre-flight guard
Before every `provider.complete()` in `chat()` and `run()`, assert no assistant
`tool_calls` message is the final message without matching `tool` responses. Convert
any future regression into a precise assertion instead of a confusing 400.

## Tests
- `tests/test_chat_tool_execution.py`:
  - tool executes and returns result (mock registry)
  - unknown tool -> error string
  - tool raises -> "Tool error: ..."
  - parallel tool_calls all get tool messages
  - repair tolerates out-of-order tool messages (regression for fix #2)
- Keep `tests/test_conversation_repair.py` green.

## Verification
1. `python -m pytest tests/ -q` all green.
2. Live round-trip in venv mode: `python3 harness/smoke_tool.py crm` (and browse/payments)
   -> final LLM call returns HTTP 200.
3. Chat-mode tool exercise (contacts/prospect) completes without 400.

## Definition of done
Fix merged, tests green, smoke_tool.py all three categories PASS, CTO review complete.
