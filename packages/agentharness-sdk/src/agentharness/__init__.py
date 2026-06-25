"""AgentHarness: the ergonomic, batteries-included layer over ``agentharness-core``.

    from agentharness import Agent, tool

    @tool
    def add(a: int, b: int) -> str:
        '''Add two numbers.'''
        return str(a + b)

    agent = Agent(model=my_model, tools=[add])
    print(agent.run("What is 2 + 3?").result)

Everything here is built on the deterministic, replayable core, so any agent you build is
inspectable and replayable for free.
"""

from __future__ import annotations

# Re-export the core essentials so most users need only ``import agentharness``.
from agentharness_core import (
    AsyncRun,
    DivergenceError,
    Message,
    Model,
    Run,
    State,
    Tool,
    ToolCall,
    ToolResult,
    Trace,
    arun,
    replay,
    run,
)

from .agent import Agent
from .tools import FunctionTool, tool

__version__ = "0.1.0"

__all__ = [  # noqa: RUF022 - grouped by concept
    # ergonomic layer
    "Agent",
    "tool",
    "FunctionTool",
    # core re-exports
    "run",
    "arun",
    "replay",
    "Run",
    "AsyncRun",
    "State",
    "Message",
    "ToolCall",
    "ToolResult",
    "Trace",
    "Model",
    "Tool",
    "DivergenceError",
    "__version__",
]
