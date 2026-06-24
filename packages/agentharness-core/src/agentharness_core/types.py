"""The data algebra: immutable, structural, JSON round-trippable.

These are the nouns of an agent run. Everything here is a frozen dataclass with no
behaviour beyond construction, equality, and (de)serialization, so a run is always
"just data" that can be inspected, stored, and replayed.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant", "tool"]
Status = Literal["running", "done", "failed"]


@dataclass(frozen=True, slots=True)
class ToolCall:
    """A request from the model to invoke a named tool with JSON arguments."""

    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Message:
    """A single conversation turn."""

    role: Role
    content: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: str | None = None
    name: str | None = None

    def __post_init__(self) -> None:
        # Coerce sequences (e.g. lists from deserialization) to tuples for immutability.
        object.__setattr__(self, "tool_calls", tuple(self.tool_calls))


@dataclass(frozen=True, slots=True)
class Usage:
    """Token accounting. Forms an additive monoid so usage can be folded over a run."""

    input_tokens: int = 0
    output_tokens: int = 0

    def __add__(self, other: Usage) -> Usage:
        return Usage(
            self.input_tokens + other.input_tokens,
            self.output_tokens + other.output_tokens,
        )


@dataclass(frozen=True, slots=True)
class ToolResult:
    """The outcome of running a tool."""

    content: str
    is_error: bool = False


@dataclass(frozen=True, slots=True)
class ModelResponse:
    """What a Model returns: one assistant message plus token usage."""

    message: Message
    usage: Usage = field(default_factory=Usage)


@dataclass(frozen=True, slots=True)
class State[CtxT]:
    """An immutable snapshot of an agent run.

    Generic over an opaque user context type ``CtxT`` so callers can thread their own
    state through a run without the core knowing anything about it.
    """

    messages: tuple[Message, ...]
    status: Status = "running"
    step: int = 0
    usage: Usage = field(default_factory=Usage)
    pending_calls: tuple[ToolCall, ...] = ()
    result: str | None = None
    error: str | None = None
    context: CtxT | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "messages", tuple(self.messages))
        object.__setattr__(self, "pending_calls", tuple(self.pending_calls))

    @classmethod
    def start(
        cls,
        messages: Iterable[Message],
        context: CtxT | None = None,
    ) -> State[CtxT]:
        """Begin a run from an initial list of messages."""
        return cls(messages=tuple(messages), status="running", context=context)

    def to_dict(self) -> dict[str, Any]:
        from typing import cast

        from . import serde

        return cast("dict[str, Any]", serde.encode(self))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> State[Any]:
        from . import serde

        obj = serde.decode(dict(data))
        assert isinstance(obj, State)
        return obj


def last_message(messages: Sequence[Message]) -> Message | None:
    return messages[-1] if messages else None
