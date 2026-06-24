"""Contract: record/replay is the headline guarantee.

Recording a run produces a Trace (just data). Replaying that Trace reproduces an
identical state sequence WITHOUT any model or tools. If the policy asks for an effect
that does not match the recorded trace, replay raises DivergenceError.
"""

from __future__ import annotations

import pytest
from agentharness_core import (
    DivergenceError,
    Message,
    State,
    ToolCall,
    Trace,
    replay,
    run,
)
from agentharness_core.testing import FakeModel
from conftest import Adder
from hypothesis import given
from hypothesis import strategies as st


def _start() -> State:
    return State.start([Message("user", "add 1 and 2")])


def _model() -> FakeModel:
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


def test_run_exposes_a_trace() -> None:
    r = run(_start(), model=_model(), tools=[Adder()])
    list(r)
    assert isinstance(r.trace, Trace)
    assert len(r.trace) > 0


def test_replay_reproduces_identical_state_without_model_or_tools() -> None:
    original = run(_start(), model=_model(), tools=[Adder()])
    list(original)

    # Replay needs NEITHER model NOR tools — only the recorded trace.
    replayed = replay(_start(), trace=original.trace)
    list(replayed)

    assert replayed.state == original.state
    assert replayed.result == original.result


def test_trace_save_load_round_trip(tmp_path) -> None:
    original = run(_start(), model=_model(), tools=[Adder()])
    list(original)

    path = tmp_path / "run.jsonl"
    original.trace.save(path)
    loaded = Trace.load(path)
    assert loaded == original.trace

    replayed = replay(_start(), trace=loaded)
    list(replayed)
    assert replayed.state == original.state


def test_replay_detects_divergence() -> None:
    original = run(_start(), model=_model(), tools=[Adder()])
    list(original)

    # Replaying from a different starting state makes the policy request an effect
    # that does not match the recorded trace -> divergence.
    diverged = replay(State.start([Message("user", "completely different")]), trace=original.trace)
    with pytest.raises(DivergenceError):
        list(diverged)


# --- The headline property: record-then-replay is always identical. ---------------

_text = st.text(min_size=1, max_size=12)


@st.composite
def _scripts(draw: st.DrawFn) -> list[Message]:
    """Generate a valid scripted conversation: zero or more tool calls, then a final answer."""
    n_tool_turns = draw(st.integers(min_value=0, max_value=4))
    msgs: list[Message] = []
    for i in range(n_tool_turns):
        a = draw(st.integers(-50, 50))
        b = draw(st.integers(-50, 50))
        msgs.append(
            Message(
                role="assistant",
                content=None,
                tool_calls=(ToolCall(id=f"c{i}", name="add", arguments={"a": a, "b": b}),),
            )
        )
    msgs.append(Message(role="assistant", content=draw(_text)))
    return msgs


@given(script=_scripts(), prompt=_text)
def test_record_then_replay_is_always_identical(script: list[Message], prompt: str) -> None:
    start = State.start([Message("user", prompt)])

    original = run(start, model=FakeModel(script), tools=[Adder()])
    original_states = [ev_state for ev_state in _iter_states(original)]

    replayed = replay(start, trace=original.trace)
    replayed_states = [ev_state for ev_state in _iter_states(replayed)]

    assert replayed_states == original_states
    assert replayed.state == original.state


def _iter_states(r) -> list:
    """Collect the State after each event for sequence comparison."""
    states = []
    for _ in r:
        states.append(r.state)
    return states
