"""Events: outcomes that already happened.

Where an Effect is a request, an Event is a fact. The runner performs an Effect and
turns its result into an Event; ``reduce`` folds the Event into the next State. The
ordered stream of Events is the inspectable history of a run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .types import Message, State, Usage


@dataclass(frozen=True, slots=True)
class RunStarted:
    """Emitted once at the beginning of a run."""

    state: State[Any]


@dataclass(frozen=True, slots=True)
class ModelResponded:
    """The model produced an assistant message."""

    message: Message
    usage: Usage = field(default_factory=Usage)


@dataclass(frozen=True, slots=True)
class ToolResulted:
    """A tool call resolved."""

    call_id: str
    content: str
    is_error: bool = False


@dataclass(frozen=True, slots=True)
class StepFinished:
    """Emitted after each effect is applied, carrying the new state."""

    state: State[Any]


@dataclass(frozen=True, slots=True)
class RunFinished:
    """Emitted once when the run completes successfully."""

    state: State[Any]


@dataclass(frozen=True, slots=True)
class RunFailed:
    """Emitted once when the run terminates in failure."""

    state: State[Any]
    error: str


Event = RunStarted | ModelResponded | ToolResulted | StepFinished | RunFinished | RunFailed
