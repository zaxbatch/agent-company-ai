"""Regression tests for the venv-mode 400 fix.

Root cause (INC-2026-08-26): ``_execute_chat_tool`` made a NESTED
``provider.complete()`` call while the conversation ended with an unanswered
assistant ``tool_calls`` message, which OpenAI-compatible APIs reject with
'An assistant message with tool_calls must be followed by tool messages
responding to each tool_call_id'.
"""
import sys
sys.path.insert(0, "src")

import pytest

from agent_company_ai.core.agent import Agent
from agent_company_ai.llm.base import LLMMessage, LLMResponse, ToolCall, ToolDefinition
from agent_company_ai.tools.registry import Tool, ToolRegistry


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeRegistry:
    def __init__(self, tool):
        self._tool = tool
        self._registry = ToolRegistry()
        self._registry.register(tool)

    def get_tool(self, name):
        return self._registry.get_tool(name)


class _FakeTool:
    def __init__(self, name="fake_tool", result="tool-ran", exc=None):
        self.name = name
        self._result = result
        self._exc = exc
        self.calls = []

    async def execute(self, **kwargs):
        self.calls.append(kwargs)
        if self._exc:
            raise self._exc
        return self._result


class FakeProvider:
    """Provider scripted to return tool_calls once, then a plain reply."""

    def __init__(self, tool_calls, final_reply="done"):
        self._tool_calls = tool_calls
        self._final_reply = final_reply
        self.complete_calls = 0
        self.last_messages = None

    async def complete(self, messages, tools=None):
        self.complete_calls += 1
        self.last_messages = list(messages)
        if self.complete_calls == 1:
            return LLMResponse(content="", tool_calls=self._tool_calls,
                               usage={"input_tokens": 1, "output_tokens": 1})
        return LLMResponse(content=self._final_reply, tool_calls=None,
                           usage={"input_tokens": 1, "output_tokens": 1})


def _agent_with(fake_provider, fake_tool):
    a = Agent.__new__(Agent)
    a.name = "T"
    a.provider = fake_provider
    a.tool_definitions = [
        ToolDefinition(name=fake_tool.name, description="d",
                       parameters={"type": "object", "properties": {}})
    ]
    a._conversation = []
    a._cost_tracker = None
    # Registry with the fake tool registered
    reg = ToolRegistry()
    reg.register(Tool(name=fake_tool.name, description="d",
                      parameters={"type": "object", "properties": {}},
                      func=fake_tool.execute, is_async=True))
    a._tool_registry = reg
    return a


# ---------------------------------------------------------------------------
# _execute_chat_tool: must EXECUTE the tool (no nested LLM call)
# ---------------------------------------------------------------------------

def test_execute_chat_tool_runs_tool_and_returns_result():
    tool = _FakeTool(name="fake_tool", result="ok-42")
    provider = FakeProvider(tool_calls=None)
    a = _agent_with(provider, tool)
    tc = ToolCall(id="c1", name="fake_tool", arguments={"x": 1})
    result = asyncio_run(a._execute_chat_tool(tc))
    assert result == "ok-42"
    assert tool.calls == [{"x": 1}]
    # The nested LLM call is GONE — provider must never be hit from here.
    assert provider.complete_calls == 0


def test_execute_chat_tool_unknown_tool_returns_error():
    provider = FakeProvider(tool_calls=None)
    a = _agent_with(provider, _FakeTool())
    tc = ToolCall(id="c1", name="nope", arguments={})
    result = asyncio_run(a._execute_chat_tool(tc))
    assert result == "Error: Unknown tool 'nope'"
    assert provider.complete_calls == 0


def test_execute_chat_tool_propagates_tool_exception_as_error():
    class Boom(Exception):
        pass
    tool = _FakeTool(exc=Boom("kaboom"))
    provider = FakeProvider(tool_calls=None)
    a = _agent_with(provider, tool)
    tc = ToolCall(id="c1", name="fake_tool", arguments={})
    result = asyncio_run(a._execute_chat_tool(tc))
    assert result == "Tool error: kaboom"
    assert provider.complete_calls == 0


# ---------------------------------------------------------------------------
# chat(): parallel tool calls all get tool messages, chain stays valid
# ---------------------------------------------------------------------------

def test_chat_parallel_tool_calls_all_answered_and_chain_valid():
    tool = _FakeTool(name="fake_tool", result="r")
    calls = [
        ToolCall(id="id-a", name="fake_tool", arguments={"n": 1}),
        ToolCall(id="id-b", name="fake_tool", arguments={"n": 2}),
    ]
    provider = FakeProvider(tool_calls=calls, final_reply="all done")
    a = _agent_with(provider, tool)
    # chat() also needs the "report_result"/"delegate_task" filter — fake_tool
    # isn't either, so tool_definitions stays as-is.
    reply = asyncio_run(a.chat("hello"))
    assert reply == "all done"
    # Two tool executions happened (one per tool_call).
    assert len(tool.calls) == 2
    # The conversation must end with the assistant's final reply, and every
    # assistant tool_calls block must be immediately answered by tool msgs.
    roles = [m.role for m in a._conversation]
    assert roles[-1] == "assistant"
    # Guard must pass on the final conversation.
    a._assert_tool_chain(a._conversation)
    # Every request the provider saw had a valid chain.
    assert provider.complete_calls == 2
    # Second call's message list: ... assistant(tool_calls) -> tool -> tool -> ...
    msgs = provider.last_messages
    idx = next(i for i, m in enumerate(msgs) if m.role == "assistant" and m.tool_calls)
    assert msgs[idx + 1].role == "tool" and msgs[idx + 1].tool_call_id == "id-a"
    assert msgs[idx + 2].role == "tool" and msgs[idx + 2].tool_call_id == "id-b"


# ---------------------------------------------------------------------------
# _assert_tool_chain: guards against regressions
# ---------------------------------------------------------------------------

def test_assert_tool_chain_rejects_unanswered_tool_calls():
    a = Agent.__new__(Agent)
    bad = [
        LLMMessage(role="user", content="hi"),
        LLMMessage(role="assistant", content="", tool_calls=[{"id": "x", "name": "t", "arguments": "{}"}]),
    ]
    with pytest.raises(RuntimeError):
        a._assert_tool_chain(bad)


def test_assert_tool_chain_accepts_valid_chain():
    a = Agent.__new__(Agent)
    good = [
        LLMMessage(role="user", content="hi"),
        LLMMessage(role="assistant", content="", tool_calls=[{"id": "x", "name": "t", "arguments": "{}"}]),
        LLMMessage(role="tool", content="r", tool_call_id="x"),
        LLMMessage(role="assistant", content="done"),
    ]
    a._assert_tool_chain(good)  # must not raise


# ---------------------------------------------------------------------------
# _repair_conversation: tolerates out-of-order tool messages (Fix C)
# ---------------------------------------------------------------------------

def test_repair_tolerates_out_of_order_tool_messages():
    a = Agent.__new__(Agent)
    a._conversation = [
        LLMMessage(role="system", content="sys"),
        LLMMessage(role="assistant", content="", tool_calls=[
            {"id": "1", "name": "a", "arguments": "{}"},
            {"id": "2", "name": "b", "arguments": "{}"},
        ]),
        # Valid pairing but tool messages arrive in reverse declaration order.
        LLMMessage(role="tool", content="r2", tool_call_id="2"),
        LLMMessage(role="tool", content="r1", tool_call_id="1"),
        LLMMessage(role="assistant", content="done"),
    ]
    a._repair_conversation()
    assert len(a._conversation) == 5
    assert a._conversation[1].tool_calls is not None  # pairing preserved


def asyncio_run(coro):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(coro)
