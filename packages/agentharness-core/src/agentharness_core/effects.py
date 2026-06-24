"""Effects: requests to do something impure.

The pure kernel never performs I/O. Instead ``decide`` returns an Effect describing
what the (impure) runner should do next. Funnelling *all* nondeterminism through
effects is what makes a run recordable and replayable: the runner logs every effect
and its result, and replay simply re-feeds those results.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .types import Message, ToolCall


@dataclass(frozen=True, slots=True)
class ModelRequest:
    """Ask the model for the next assistant message."""

    messages: tuple[Message, ...]
    tools: tuple[dict[str, Any], ...] = ()
    request_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "messages", tuple(self.messages))
        object.__setattr__(self, "tools", tuple(self.tools))


@dataclass(frozen=True, slots=True)
class ToolInvocation:
    """Run a single tool call."""

    call: ToolCall


@dataclass(frozen=True, slots=True)
class Now:
    """Ambient effect: request the current wall-clock time. Reserved; unused by the
    default policy but defined so deterministic clocks can be recorded later."""


@dataclass(frozen=True, slots=True)
class GenId:
    """Ambient effect: request a fresh unique id. Reserved."""


@dataclass(frozen=True, slots=True)
class RandomBytes:
    """Ambient effect: request `n` random bytes. Reserved."""

    n: int


@dataclass(frozen=True, slots=True)
class Done:
    """Sentinel returned by ``decide`` meaning the run is complete. Not performed."""


Effect = ModelRequest | ToolInvocation | Now | GenId | RandomBytes
