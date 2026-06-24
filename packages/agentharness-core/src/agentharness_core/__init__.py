"""AgentHarness core: an agent run as a deterministic, inspectable, replayable state machine.

The public surface is intentionally tiny and meant to stay stable for years.

    from agentharness_core import run, replay, State, Message
    from agentharness_core.testing import FakeModel

See ``docs/superpowers/specs/2026-06-24-agentharness-core-design.md`` for the design.
"""

from __future__ import annotations

from .effects import (
    Done,
    Effect,
    GenId,
    ModelRequest,
    Now,
    RandomBytes,
    ToolInvocation,
)
from .events import (
    Event,
    ModelResponded,
    RunFailed,
    RunFinished,
    RunStarted,
    StepFinished,
    ToolResulted,
)
from .kernel import decide, reduce
from .protocols import Model, Tool
from .run import AsyncRun, Run, arun, replay, run
from .trace import DivergenceError, Trace, TraceRecord
from .types import (
    Message,
    ModelResponse,
    Role,
    State,
    Status,
    ToolCall,
    ToolResult,
    Usage,
)

__version__ = "0.0.1"

__all__ = [  # noqa: RUF022 - grouped by concept for readability, not alphabetized
    # driver
    "run",
    "arun",
    "replay",
    "Run",
    "AsyncRun",
    # kernel
    "decide",
    "reduce",
    # state & messages
    "State",
    "Message",
    "ToolCall",
    "Usage",
    "ToolResult",
    "ModelResponse",
    "Role",
    "Status",
    # effects
    "Effect",
    "ModelRequest",
    "ToolInvocation",
    "Now",
    "GenId",
    "RandomBytes",
    "Done",
    # events
    "Event",
    "RunStarted",
    "ModelResponded",
    "ToolResulted",
    "StepFinished",
    "RunFinished",
    "RunFailed",
    # protocols
    "Model",
    "Tool",
    # determinism
    "Trace",
    "TraceRecord",
    "DivergenceError",
    "__version__",
]
