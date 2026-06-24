"""Contract: the kernel is two pure functions over serializable data.

`decide(state) -> Effect | Done` answers "what impure thing should happen next?"
`reduce(state, event) -> State` folds an outcome into a new state.

Both must be pure: no I/O, no mutation of inputs, deterministic.
"""

from __future__ import annotations

from agentharness_core import (
    Done,
    Message,
    ModelRequest,
    ModelResponded,
    State,
    ToolCall,
    ToolInvocation,
    Usage,
    decide,
    reduce,
)


def test_decide_requests_model_when_user_spoke_last() -> None:
    s = State.start([Message("user", "hello")])
    effect = decide(s)
    assert isinstance(effect, ModelRequest)
    assert effect.messages[-1].content == "hello"


def test_decide_invokes_tool_when_assistant_requested_one() -> None:
    s = State.start([Message("user", "add")])
    assistant = Message(
        role="assistant",
        content=None,
        tool_calls=(ToolCall(id="c1", name="add", arguments={"a": 1, "b": 2}),),
    )
    s2 = reduce(s, ModelResponded(message=assistant, usage=Usage()))
    effect = decide(s2)
    assert isinstance(effect, ToolInvocation)
    assert effect.call.name == "add"


def test_decide_is_done_when_assistant_answers_plainly() -> None:
    s = State.start([Message("user", "hi")])
    s2 = reduce(s, ModelResponded(message=Message("assistant", "hello"), usage=Usage()))
    assert isinstance(decide(s2), Done)


def test_reduce_does_not_mutate_input_state() -> None:
    s = State.start([Message("user", "hi")])
    before = s.to_dict()
    reduce(s, ModelResponded(message=Message("assistant", "hello"), usage=Usage()))
    assert s.to_dict() == before  # input untouched


def test_reduce_accumulates_usage() -> None:
    s = State.start([Message("user", "hi")])
    s2 = reduce(
        s,
        ModelResponded(
            message=Message("assistant", "a"), usage=Usage(input_tokens=2, output_tokens=1)
        ),
    )
    assert s2.usage == Usage(input_tokens=2, output_tokens=1)


def test_decide_is_deterministic() -> None:
    s = State.start([Message("user", "hello")])
    assert decide(s) == decide(s)
