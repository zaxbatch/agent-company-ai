"""Regression tests for the "went silent after a tool loop" bug (2026-09-13).

Root cause: ``Agent.chat()`` used a hardcoded ``for _ in range(10)`` tool loop
and returned the literal placeholder ``"(no response after tool loop)"`` when
the budget ran out. Any task needing more than 10 sequential tool rounds
(web_search -> fetch -> read -> verify) exited ON a tool round and handed the
caller a placeholder instead of prose.

Fix under test:
  1. cap is ``CHAT_MAX_TOOL_ROUNDS`` (40) and overridable via ``max_rounds``;
  2. on exhaustion, ONE final completion is forced with ``tools=None`` so the
     model must answer in prose;
  3. if that yields nothing, the longest assistant text seen is returned.
"""
import sys
sys.path.insert(0, "src")

import asyncio
import types

from agent_company_ai.core.agent import Agent, CHAT_MAX_TOOL_ROUNDS
from agent_company_ai.llm.base import LLMResponse, ToolCall
from agent_company_ai.tools.registry import Tool, ToolRegistry

PLACEHOLDER = "(no response after tool loop)"


def asyncio_run(coro):
    return asyncio.run(coro)


class _FakeTool:
    def __init__(self, name="fake_tool", result="tool-ran"):
        self.name = name
        self._result = result
        self.calls = []

    async def execute(self, **kwargs):
        self.calls.append(kwargs)
        return self._result


class ExhaustingProvider:
    """Never volunteers prose while tools are on offer.

    Models the real failure: every round it asks for another tool call, so the
    loop can only exit by running out of budget.
    """

    def __init__(self, final_prose="FINAL PROSE FROM FORCED PASS",
                 round_content="", final_content=None):
        self.complete_calls = 0
        self.final_prose = final_prose
        self.round_content = round_content
        self.final_content = final_prose if final_content is None else final_content
        self.tools_arg_seen = []

    async def complete(self, messages, tools=None):
        self.complete_calls += 1
        self.tools_arg_seen.append(tools)
        usage = {"input_tokens": 1, "output_tokens": 1}
        if tools is None:
            return LLMResponse(content=self.final_content, tool_calls=None,
                               usage=usage)
        return LLMResponse(
            content=self.round_content,
            tool_calls=[ToolCall(id=f"c{self.complete_calls}",
                                 name="fake_tool", arguments={"n": 1})],
            usage=usage,
        )


def _agent(provider, tool):
    a = Agent.__new__(Agent)
    a.name = "T"
    a.provider = provider
    a.role = types.SimpleNamespace(default_tools=[tool.name],
                                   can_delegate_to=False)
    a._conversation = []
    a._system_prompt = "system"
    a._cost_tracker = None
    reg = ToolRegistry()
    reg.register(Tool(name=tool.name, description="d",
                      parameters={"type": "object", "properties": {}},
                      func=tool.execute, is_async=True))
    a._tool_registry = reg
    return a


# ---------------------------------------------------------------------------
# The bug: exhaustion must NOT surface the placeholder
# ---------------------------------------------------------------------------

def test_exhausted_loop_returns_prose_not_placeholder():
    provider = ExhaustingProvider()
    a = _agent(provider, _FakeTool())
    reply = asyncio_run(a.chat("hello", max_rounds=3))

    assert reply != PLACEHOLDER, "regression: placeholder leaked to caller"
    assert reply == "FINAL PROSE FROM FORCED PASS"
    # 3 tool rounds + exactly 1 forced text-only pass
    assert provider.complete_calls == 4
    # the forced pass must offer NO tools
    assert provider.tools_arg_seen[-1] is None
    # every tool round did offer tools
    assert all(t is not None for t in provider.tools_arg_seen[:-1])


def test_default_cap_is_40_not_10():
    assert CHAT_MAX_TOOL_ROUNDS == 40
    provider = ExhaustingProvider()
    a = _agent(provider, _FakeTool())
    reply = asyncio_run(a.chat("hello"))
    assert reply == "FINAL PROSE FROM FORCED PASS"
    assert provider.complete_calls == CHAT_MAX_TOOL_ROUNDS + 1


def test_falls_back_to_longest_assistant_text_when_final_pass_empty():
    provider = ExhaustingProvider(
        round_content="Substantial partial deliverable text.",
        final_content="",
    )
    a = _agent(provider, _FakeTool())
    reply = asyncio_run(a.chat("hello", max_rounds=2))
    assert reply == "Substantial partial deliverable text."
    assert reply != PLACEHOLDER


def test_placeholder_only_when_nothing_at_all_was_produced():
    provider = ExhaustingProvider(round_content="", final_content="")
    a = _agent(provider, _FakeTool())
    reply = asyncio_run(a.chat("hello", max_rounds=2))
    assert reply == PLACEHOLDER


def test_normal_single_round_tool_use_unaffected():
    """A provider that answers after one round must still work normally."""

    class OneShotProvider:
        def __init__(self):
            self.calls = 0

        async def complete(self, messages, tools=None):
            self.calls += 1
            if self.calls == 1:
                return LLMResponse(content="", tool_calls=[
                    ToolCall(id="a", name="fake_tool", arguments={})], usage={})
            return LLMResponse(content="all done", tool_calls=None, usage={})

    provider = OneShotProvider()
    a = _agent(provider, _FakeTool())
    reply = asyncio_run(a.chat("hello", max_rounds=5))
    assert reply == "all done"
    assert provider.calls == 2
