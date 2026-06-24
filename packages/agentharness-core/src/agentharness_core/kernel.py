"""The pure kernel: two total functions that contain the entire agent-loop policy.

``decide`` answers "given this state, what impure thing should happen next?"
``reduce`` answers "given this state and an outcome, what is the next state?"

Neither performs I/O, neither mutates its inputs, and both are deterministic. That
purity is the whole game: it makes a run reproducible, inspectable, and replayable.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, assert_never

from .effects import Done, Effect, ModelRequest, ToolInvocation
from .events import (
    Event,
    ModelResponded,
    RunFailed,
    RunFinished,
    RunStarted,
    StepFinished,
    ToolResulted,
)
from .types import Message, State


def decide(state: State[Any]) -> Effect | Done:
    """Choose the next effect to perform, or signal the run is complete."""
    if state.status in ("done", "failed"):
        return Done()

    # Resolve any outstanding tool calls before asking the model again.
    if state.pending_calls:
        return ToolInvocation(state.pending_calls[0])

    if not state.messages:
        return Done()

    last = state.messages[-1]
    if last.role == "assistant":
        if last.tool_calls:
            return ToolInvocation(last.tool_calls[0])
        # The assistant produced a final answer with no tool calls: we're done.
        return Done()

    # The model's turn (user/tool/system spoke last).
    return ModelRequest(messages=state.messages)


def reduce[CtxT](state: State[CtxT], event: Event) -> State[CtxT]:
    """Fold an event into a new state. Total and pure."""
    match event:
        case RunStarted():
            return state
        case ModelResponded(message=message, usage=usage):
            return replace(
                state,
                messages=(*state.messages, message),
                usage=state.usage + usage,
                pending_calls=message.tool_calls,
            )
        case ToolResulted(call_id=call_id, content=content):
            tool_msg = Message(
                role="tool",
                content=content,
                tool_call_id=call_id,
                name=_tool_name_for(state, call_id),
            )
            # Resolve only the FIRST matching call, so duplicate ids each get handled.
            remaining = list(state.pending_calls)
            for index, pending in enumerate(remaining):
                if pending.id == call_id:
                    del remaining[index]
                    break
            return replace(
                state,
                messages=(*state.messages, tool_msg),
                pending_calls=tuple(remaining),
            )
        case StepFinished(state=snapshot):
            return snapshot
        case RunFinished(state=snapshot):
            return snapshot
        case RunFailed(state=snapshot):
            return snapshot
        case _:  # pragma: no cover - exhaustiveness guard
            assert_never(event)


def _tool_name_for(state: State[Any], call_id: str) -> str | None:
    for call in state.pending_calls:
        if call.id == call_id:
            return call.name
    return None
