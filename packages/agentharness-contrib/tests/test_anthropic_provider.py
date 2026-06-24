"""Contract for the Anthropic provider — translation + a full run, all without network.

We drive ``AnthropicModel`` with a fake client that returns Anthropic-shaped objects, so
these tests need neither the ``anthropic`` SDK nor an API key.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from agentharness import Agent, tool
from agentharness_contrib import AnthropicModel
from agentharness_contrib.anthropic_provider import (
    _split_messages,
    _to_anthropic_tool,
    _to_model_response,
)
from agentharness_core import Message, ModelRequest, ToolCall


# --- Fake Anthropic client -------------------------------------------------------
def _text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def _tool_use_block(id: str, name: str, input: dict) -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=id, name=name, input=input)


def _response(content: list, input_tokens: int = 7, output_tokens: int = 3) -> SimpleNamespace:
    return SimpleNamespace(
        content=content,
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
    )


class FakeMessages:
    def __init__(self, scripted: list) -> None:
        self._scripted = list(scripted)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self._scripted.pop(0)


class FakeClient:
    def __init__(self, scripted: list) -> None:
        self.messages = FakeMessages(scripted)


# --- Translation unit tests ------------------------------------------------------
def test_split_messages_extracts_system_and_tool_results() -> None:
    msgs = (
        Message("system", "be terse"),
        Message("user", "add 1 and 2"),
        Message(
            role="assistant",
            content=None,
            tool_calls=(ToolCall(id="c1", name="add", arguments={"a": 1, "b": 2}),),
        ),
        Message(role="tool", content="3", tool_call_id="c1", name="add"),
    )
    system, out = _split_messages(msgs)

    assert system == "be terse"
    assert out[0] == {"role": "user", "content": "add 1 and 2"}
    assert out[1]["role"] == "assistant"
    assert out[1]["content"][0] == {
        "type": "tool_use",
        "id": "c1",
        "name": "add",
        "input": {"a": 1, "b": 2},
    }
    assert out[2] == {
        "role": "user",
        "content": [{"type": "tool_result", "tool_use_id": "c1", "content": "3"}],
    }


def test_to_anthropic_tool_uses_input_schema() -> None:
    neutral = {"name": "add", "description": "adds", "schema": {"type": "object"}}
    assert _to_anthropic_tool(neutral) == {
        "name": "add",
        "description": "adds",
        "input_schema": {"type": "object"},
    }


def test_to_model_response_parses_text_and_tool_use() -> None:
    resp = _response(
        [_text_block("hi "), _tool_use_block("c1", "add", {"a": 1, "b": 2})],
        input_tokens=5,
        output_tokens=9,
    )
    out = _to_model_response(resp)
    assert out.message.content == "hi "
    assert out.message.tool_calls == (ToolCall(id="c1", name="add", arguments={"a": 1, "b": 2}),)
    assert out.usage.input_tokens == 5
    assert out.usage.output_tokens == 9


# --- respond() and full-loop tests ----------------------------------------------
def test_respond_passes_system_and_tools_to_client() -> None:
    client = FakeClient([_response([_text_block("ok")])])
    model = AnthropicModel("claude-opus-4-8", client=client, max_tokens=128)
    request = ModelRequest(
        messages=(Message("system", "S"), Message("user", "hi")),
        tools=({"name": "add", "description": "adds", "schema": {"type": "object"}},),
    )
    model.respond(request)

    call = client.messages.calls[0]
    assert call["model"] == "claude-opus-4-8"
    assert call["max_tokens"] == 128
    assert call["system"] == "S"
    assert call["tools"][0]["input_schema"] == {"type": "object"}


def test_full_run_through_core_loop_with_fake_client() -> None:
    @tool
    def add(a: int, b: int) -> str:
        """Add two numbers."""
        return str(a + b)

    client = FakeClient(
        [
            _response([_tool_use_block("c1", "add", {"a": 2, "b": 3})]),
            _response([_text_block("2 + 3 = 5.")]),
        ]
    )
    agent = Agent(model=AnthropicModel(client=client), tools=[add])
    run = agent.run("What is 2 + 3?")

    assert run.result == "2 + 3 = 5."
    assert run.state.status == "done"
    # The tool actually ran in the core loop, and the result was fed back to the model.
    assert any(m.role == "tool" and m.content == "5" for m in run.state.messages)
    # The model saw the tool schema on the first call.
    assert client.messages.calls[0]["tools"][0]["name"] == "add"
