"""Contract: the driver loop runs an agent as an inspectable event stream."""

from __future__ import annotations

import asyncio

from agentharness_core import (
    Message,
    ModelResponded,
    RunFinished,
    State,
    ToolCall,
    ToolResulted,
    arun,
    run,
)
from agentharness_core.testing import FakeModel
from conftest import Adder, Boom


def _scripted_add_then_answer() -> FakeModel:
    """Model that first calls the `add` tool, then answers with the result."""
    return FakeModel(
        [
            Message(
                role="assistant",
                content=None,
                tool_calls=(ToolCall(id="c1", name="add", arguments={"a": 1, "b": 2}),),
            ),
            Message(role="assistant", content="The answer is 3."),
        ]
    )


def test_simple_tool_then_finish() -> None:
    r = run(
        State.start([Message("user", "add 1 and 2")]),
        model=_scripted_add_then_answer(),
        tools=[Adder()],
    )
    events = list(r)

    assert r.result == "The answer is 3."
    assert r.state.status == "done"
    # The conversation captured the tool round-trip.
    assert any(isinstance(e, ToolResulted) and e.content == "3" for e in events)
    assert any(isinstance(e, ModelResponded) for e in events)
    assert isinstance(events[-1], RunFinished)


def test_no_tool_immediate_answer() -> None:
    r = run(
        State.start([Message("user", "hi")]),
        model=FakeModel([Message(role="assistant", content="hello there")]),
    )
    list(r)
    assert r.result == "hello there"
    assert r.state.status == "done"


def test_manual_stepping_matches_iteration() -> None:
    r = run(
        State.start([Message("user", "add 1 and 2")]),
        model=_scripted_add_then_answer(),
        tools=[Adder()],
    )
    seen = []
    while True:
        ev = r.step()
        if ev is None:
            break
        seen.append(ev)
    assert r.state.status == "done"
    assert isinstance(seen[-1], RunFinished)


def test_tool_error_is_captured_not_raised() -> None:
    model = FakeModel(
        [
            Message(
                role="assistant",
                content=None,
                tool_calls=(ToolCall(id="c1", name="boom", arguments={}),),
            ),
            Message(role="assistant", content="handled the error"),
        ]
    )
    r = run(State.start([Message("user", "explode")]), model=model, tools=[Boom()])
    events = list(r)
    assert any(isinstance(e, ToolResulted) and e.is_error for e in events)
    assert r.state.status == "done"
    assert r.result == "handled the error"


def test_arun_async_iteration() -> None:
    async def go() -> str | None:
        r = arun(
            State.start([Message("user", "hi")]),
            model=FakeModel([Message(role="assistant", content="hello there")]),
        )
        async for _ in r:
            pass
        return r.result

    assert asyncio.run(go()) == "hello there"


def test_max_steps_guard_fails_gracefully() -> None:
    # A model that never stops calling tools must hit the guard and fail, not loop forever.
    looping = FakeModel(
        [
            Message(
                role="assistant",
                content=None,
                tool_calls=(ToolCall(id=f"c{i}", name="add", arguments={"a": 1, "b": 1}),),
            )
            for i in range(100)
        ]
    )
    r = run(
        State.start([Message("user", "loop")]),
        model=looping,
        tools=[Adder()],
        max_steps=3,
    )
    list(r)
    assert r.state.status == "failed"
    assert r.state.error is not None
