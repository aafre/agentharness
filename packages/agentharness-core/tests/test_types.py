"""Contract: the data algebra is immutable, structural, and JSON round-trippable."""

from __future__ import annotations

import dataclasses

import pytest
from agentharness_core import (
    Message,
    State,
    ToolCall,
    Usage,
)


def test_message_is_frozen() -> None:
    m = Message(role="user", content="hi")
    assert m.role == "user"
    assert m.content == "hi"
    assert m.tool_calls == ()
    with pytest.raises(dataclasses.FrozenInstanceError):
        m.content = "mutated"  # type: ignore[misc]


def test_toolcall_fields() -> None:
    tc = ToolCall(id="c1", name="add", arguments={"a": 1, "b": 2})
    assert tc.id == "c1"
    assert tc.name == "add"
    assert tc.arguments == {"a": 1, "b": 2}


def test_usage_is_additive() -> None:
    total = Usage(input_tokens=3, output_tokens=5) + Usage(input_tokens=1, output_tokens=2)
    assert total == Usage(input_tokens=4, output_tokens=7)


def test_state_start_constructor() -> None:
    s = State.start([Message("user", "hello")])
    assert s.status == "running"
    assert s.step == 0
    assert s.messages[0].content == "hello"
    assert s.result is None
    assert s.error is None


def test_state_is_immutable() -> None:
    s = State.start([Message("user", "hello")])
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.status = "done"  # type: ignore[misc]


def test_state_json_round_trip() -> None:
    s = State.start([Message("user", "add 1 and 2")])
    s2 = State.from_dict(s.to_dict())
    assert s2 == s


def test_message_with_tool_calls_round_trips_via_state() -> None:
    msg = Message(
        role="assistant",
        content=None,
        tool_calls=(ToolCall(id="c1", name="add", arguments={"a": 1, "b": 2}),),
    )
    s = dataclasses.replace(State.start([Message("user", "x")]), messages=(msg,))
    assert State.from_dict(s.to_dict()) == s
