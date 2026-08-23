"""Regression tests for conversation repair (orphaned tool_calls).

Covers the OpenAI error 'An assistant message with tool_calls must be
followed by tool messages responding to each tool_call_id'.
"""
import sys
sys.path.insert(0, "src")

from agent_company_ai.core.agent import Agent
from agent_company_ai.llm.base import LLMMessage


def _agent():
    a = Agent.__new__(Agent)
    a.name = "T"
    return a


def test_trailing_dangling_tool_calls_removed():
    a = _agent()
    a._conversation = [
        LLMMessage(role="system", content="sys"),
        LLMMessage(role="user", content="hi"),
        LLMMessage(role="assistant", content="", tool_calls=[{"id": "a", "name": "web_search", "arguments": "{}"}]),
        LLMMessage(role="tool", content="result", tool_call_id="a"),
        LLMMessage(role="assistant", content="", tool_calls=[{"id": "b", "name": "x", "arguments": "{}"}]),
    ]
    a._repair_conversation()
    conv = a._conversation
    assert len(conv) == 4
    assert conv[-1].role == "tool" and conv[-1].tool_call_id == "a"


def test_mid_conversation_orphan_repaired_text_kept():
    a = _agent()
    a._conversation = [
        LLMMessage(role="system", content="sys"),
        LLMMessage(role="user", content="hi"),
        LLMMessage(role="assistant", content="thinking...", tool_calls=[{"id": "z", "name": "x", "arguments": "{}"}]),
        LLMMessage(role="user", content="next"),
        LLMMessage(role="assistant", content="final"),
    ]
    a._repair_conversation()
    conv = a._conversation
    assert len(conv) == 5
    assert conv[2].tool_calls is None and conv[2].content == "thinking..."


def test_partial_tool_responses_repaired():
    a = _agent()
    a._conversation = [
        LLMMessage(role="system", content="sys"),
        LLMMessage(role="assistant", content="", tool_calls=[
            {"id": "1", "name": "a", "arguments": "{}"},
            {"id": "2", "name": "b", "arguments": "{}"},
        ]),
        LLMMessage(role="tool", content="only one", tool_call_id="1"),
        LLMMessage(role="user", content="next"),
    ]
    a._repair_conversation()
    assert not any(m.tool_calls for m in a._conversation)
    assert not any(m.role == "tool" for m in a._conversation)


def test_empty_orphaned_assistant_dropped():
    a = _agent()
    a._conversation = [
        LLMMessage(role="system", content="sys"),
        LLMMessage(role="assistant", content="", tool_calls=[{"id": "q", "name": "x", "arguments": "{}"}]),
        LLMMessage(role="user", content="next"),
    ]
    a._repair_conversation()
    assert len(a._conversation) == 2


def test_valid_pairing_untouched():
    a = _agent()
    a._conversation = [
        LLMMessage(role="system", content="sys"),
        LLMMessage(role="assistant", content="", tool_calls=[{"id": "a", "name": "x", "arguments": "{}"}]),
        LLMMessage(role="tool", content="r", tool_call_id="a"),
        LLMMessage(role="assistant", content="done"),
    ]
    a._repair_conversation()
    assert len(a._conversation) == 4
    assert a._conversation[1].tool_calls == [{"id": "a", "name": "x", "arguments": "{}"}]
