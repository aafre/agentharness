"""Contract for the OpenAI provider — translation + a full run, all without network.

We drive ``OpenAIModel`` with a fake client that returns OpenAI-shaped objects, so these
tests need neither the ``openai`` SDK nor an API key. ``OllamaModel`` is the same provider
with Ollama-friendly defaults (it speaks the OpenAI Chat Completions API), so it's covered
by the same fake client.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

from agentharness import Agent, tool
from agentharness_contrib import OllamaModel, OpenAIModel
from agentharness_contrib.openai_provider import (
    _to_model_response,
    _to_openai_messages,
    _to_openai_tool,
)
from agentharness_core import Message, ModelRequest, ToolCall


# --- Fake OpenAI client ----------------------------------------------------------
def _message(content: str | None, tool_calls: list | None = None) -> SimpleNamespace:
    return SimpleNamespace(content=content, tool_calls=tool_calls)


def _tool_call(id: str, name: str, arguments: dict) -> SimpleNamespace:
    return SimpleNamespace(
        id=id,
        type="function",
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
    )


def _response(
    content: str | None,
    tool_calls: list | None = None,
    prompt_tokens: int = 7,
    completion_tokens: int = 3,
) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=_message(content, tool_calls))],
        usage=SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
    )


class FakeCompletions:
    def __init__(self, scripted: list) -> None:
        self._scripted = list(scripted)
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self._scripted.pop(0)


class FakeClient:
    def __init__(self, scripted: list, **init_kwargs: Any) -> None:
        self.init_kwargs = init_kwargs
        self.chat = SimpleNamespace(completions=FakeCompletions(scripted))

    @property
    def calls(self) -> list[dict[str, Any]]:
        return self.chat.completions.calls


# --- Translation unit tests ------------------------------------------------------
def test_to_openai_messages_round_trips_roles_and_tool_calls() -> None:
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
    out = _to_openai_messages(msgs)

    assert out[0] == {"role": "system", "content": "be terse"}
    assert out[1] == {"role": "user", "content": "add 1 and 2"}

    assistant = out[2]
    assert assistant["role"] == "assistant"
    call = assistant["tool_calls"][0]
    assert call["id"] == "c1"
    assert call["type"] == "function"
    assert call["function"]["name"] == "add"
    # The gotcha: OpenAI tool-call arguments are a JSON *string*, not a dict.
    assert isinstance(call["function"]["arguments"], str)
    assert json.loads(call["function"]["arguments"]) == {"a": 1, "b": 2}

    assert out[3] == {"role": "tool", "tool_call_id": "c1", "content": "3"}


def test_to_openai_messages_omits_tool_calls_when_none() -> None:
    out = _to_openai_messages((Message("assistant", "just text"),))
    assert "tool_calls" not in out[0]


def test_to_openai_tool_wraps_function_schema() -> None:
    neutral = {"name": "add", "description": "adds", "schema": {"type": "object"}}
    assert _to_openai_tool(neutral) == {
        "type": "function",
        "function": {
            "name": "add",
            "description": "adds",
            "parameters": {"type": "object"},
        },
    }


def test_to_model_response_parses_text_tool_use_and_usage() -> None:
    resp = _response(
        content="hi ",
        tool_calls=[_tool_call("c1", "add", {"a": 1, "b": 2})],
        prompt_tokens=5,
        completion_tokens=9,
    )
    out = _to_model_response(resp)
    assert out.message.content == "hi "
    # json.loads applied: arguments come back as a dict.
    assert out.message.tool_calls == (ToolCall(id="c1", name="add", arguments={"a": 1, "b": 2}),)
    assert out.usage.input_tokens == 5
    assert out.usage.output_tokens == 9


# --- respond() and full-loop tests ----------------------------------------------
def test_respond_passes_model_messages_and_tools_to_client() -> None:
    client = FakeClient([_response("ok")])
    model = OpenAIModel("gpt-4o", client=client, max_tokens=128, system="S")
    request = ModelRequest(
        messages=(Message("user", "hi"),),
        tools=({"name": "add", "description": "adds", "schema": {"type": "object"}},),
    )
    model.respond(request)

    call = client.calls[0]
    assert call["model"] == "gpt-4o"
    # System prompt is prepended as a system message.
    assert call["messages"][0] == {"role": "system", "content": "S"}
    assert call["tools"][0]["function"]["name"] == "add"
    assert call["tools"][0]["function"]["parameters"] == {"type": "object"}


def test_full_run_through_core_loop_with_fake_client() -> None:
    @tool
    def add(a: int, b: int) -> str:
        """Add two numbers."""
        return str(a + b)

    client = FakeClient(
        [
            _response(content=None, tool_calls=[_tool_call("c1", "add", {"a": 2, "b": 3})]),
            _response(content="2 + 3 = 5."),
        ]
    )
    agent = Agent(model=OpenAIModel(client=client), tools=[add])
    run = agent.run("What is 2 + 3?")

    assert run.result == "2 + 3 = 5."
    assert run.state.status == "done"
    # The tool actually ran in the core loop, and the result was fed back to the model.
    assert any(m.role == "tool" and m.content == "5" for m in run.state.messages)
    # The model saw the tool schema on the first call.
    assert client.calls[0]["tools"][0]["function"]["name"] == "add"


def test_ollama_model_defaults_to_local_openai_compatible_endpoint() -> None:
    captured: dict[str, Any] = {}

    def fake_factory(**kwargs: Any) -> FakeClient:
        captured.update(kwargs)
        return FakeClient([_response("pong")])

    model = OllamaModel(client_factory=fake_factory)
    model.respond(ModelRequest(messages=(Message("user", "ping"),), tools=()))

    assert captured["base_url"].endswith(":11434/v1")
    # Ollama ignores the key but the SDK requires a non-empty one.
    assert captured["api_key"]
