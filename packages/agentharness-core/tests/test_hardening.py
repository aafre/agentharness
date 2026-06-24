"""Hardening tests from the adversarial review (2026-06-24).

Each test pins a correctness guarantee that the first implementation got wrong. They are
kept separate from the original contract tests on purpose.
"""

from __future__ import annotations

import pytest
from agentharness_core import (
    DivergenceError,
    Message,
    State,
    ToolCall,
    ToolInvocation,
    ToolResult,
    ToolResulted,
    Trace,
    replay,
    run,
)
from agentharness_core.testing import FakeModel
from conftest import Adder


def _tool_records(trace: Trace) -> list:
    return [rec for rec in trace.records if isinstance(rec.effect, ToolInvocation)]


# --- Finding 1: a tool must not be able to mutate recorded state/trace ------------
class MutatingTool:
    name = "mut"
    schema = {"type": "object"}

    def call(self, arguments: dict) -> ToolResult:
        arguments["x"] = 999  # a badly-behaved tool mutates its input
        return ToolResult(content="ok")


def test_tool_cannot_mutate_recorded_arguments() -> None:
    model = FakeModel(
        [
            Message(
                role="assistant",
                content=None,
                tool_calls=(ToolCall(id="c1", name="mut", arguments={"x": 1}),),
            ),
            Message(role="assistant", content="done"),
        ]
    )
    r = run(State.start([Message("user", "go")]), model=model, tools=[MutatingTool()])
    list(r)

    assert _tool_records(r.trace)[0].effect.call.arguments == {"x": 1}, "recorded effect mutated"
    assert r.state.messages[1].tool_calls[0].arguments == {"x": 1}, "state message mutated"


# --- Finding 2: max_steps must allow a run that finishes exactly at the limit ------
def test_max_steps_one_allows_single_model_call_finish() -> None:
    r = run(
        State.start([Message("user", "hi")]),
        model=FakeModel([Message(role="assistant", content="hello")]),
        max_steps=1,
    )
    list(r)
    assert r.state.status == "done"
    assert r.result == "hello"


# --- Finding 3: replay must reject leftover (trailing) trace records ---------------
def test_replay_rejects_trailing_records() -> None:
    start = State.start([Message("user", "x")])
    original = run(start, model=FakeModel([Message(role="assistant", content="hi")]))
    list(original)

    padded = Trace(list(original.trace.records) + list(original.trace.records))
    diverged = replay(start, trace=padded)
    with pytest.raises(DivergenceError):
        list(diverged)


# --- Finding 4: serialization must not collide with legal tool JSON ----------------
def test_state_roundtrip_with_type_key_in_arguments() -> None:
    args = {"__type__": "NotARealType", "a": [1, {"b": 2}], "n": None, "flag": True}
    msg = Message(
        role="assistant",
        content=None,
        tool_calls=(ToolCall(id="c1", name="t", arguments=args),),
    )
    s = State.start([msg])
    s2 = State.from_dict(s.to_dict())
    assert s2.messages[0].tool_calls[0].arguments == args


def test_trace_roundtrip_with_type_key_in_arguments(tmp_path) -> None:
    weird = {"__type__": "x", "a": 1, "b": 2}
    model = FakeModel(
        [
            Message(
                role="assistant",
                content=None,
                tool_calls=(ToolCall(id="c1", name="add", arguments=weird),),
            ),
            Message(role="assistant", content="3"),
        ]
    )
    start = State.start([Message("user", "add")])
    r = run(start, model=model, tools=[Adder()])
    list(r)

    path = tmp_path / "t.jsonl"
    r.trace.save(path)
    loaded = Trace.load(path)
    assert loaded == r.trace
    assert _tool_records(loaded)[0].effect.call.arguments == weird


# --- Finding 5: duplicate tool_call ids must each resolve --------------------------
def test_duplicate_tool_call_ids_all_resolved() -> None:
    model = FakeModel(
        [
            Message(
                role="assistant",
                content=None,
                tool_calls=(
                    ToolCall(id="dup", name="add", arguments={"a": 1, "b": 1}),
                    ToolCall(id="dup", name="add", arguments={"a": 2, "b": 2}),
                ),
            ),
            Message(role="assistant", content="done"),
        ]
    )
    r = run(State.start([Message("user", "x")]), model=model, tools=[Adder()])
    events = list(r)

    assert sum(isinstance(e, ToolResulted) for e in events) == 2
    assert sum(m.role == "tool" for m in r.state.messages) == 2
    assert r.state.status == "done"


# --- Finding 6: trace bytes must be canonical -------------------------------------
def test_trace_bytes_are_canonical(tmp_path) -> None:
    def make_trace(args: dict) -> Trace:
        model = FakeModel(
            [
                Message(
                    role="assistant",
                    content=None,
                    tool_calls=(ToolCall(id="c1", name="add", arguments=args),),
                ),
                Message(role="assistant", content="3"),
            ]
        )
        r = run(State.start([Message("user", "x")]), model=model, tools=[Adder()])
        list(r)
        return r.trace

    t1 = make_trace({"a": 1, "b": 2})
    t2 = make_trace({"b": 2, "a": 1})  # same dict, different construction order
    p1, p2 = tmp_path / "1.jsonl", tmp_path / "2.jsonl"
    t1.save(p1)
    t2.save(p2)
    assert p1.read_bytes() == p2.read_bytes()


# --- Finding 7: Run is a one-shot iterator (explicit contract) ---------------------
def test_run_is_one_shot_iterator() -> None:
    start = State.start([Message("user", "x")])

    def make_run():
        return run(
            start,
            model=FakeModel(
                [
                    Message(
                        role="assistant",
                        content=None,
                        tool_calls=(ToolCall(id="c1", name="add", arguments={"a": 1, "b": 2}),),
                    ),
                    Message(role="assistant", content="3"),
                ]
            ),
            tools=[Adder()],
        )

    full = [type(e).__name__ for e in make_run()]

    r = make_run()
    first = next(r)
    rest = list(r)
    assert [type(first).__name__, *[type(e).__name__ for e in rest]] == full
