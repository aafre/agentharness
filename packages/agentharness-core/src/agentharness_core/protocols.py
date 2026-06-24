"""The two structural contracts the world implements: Model and Tool.

These are the entire provider surface. Anything that satisfies ``Model`` can drive a
run; anything that satisfies ``Tool`` can be called. Structural (Protocol) typing means
implementers never import or subclass anything from this package.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .effects import ModelRequest
from .types import ModelResponse, ToolResult


@runtime_checkable
class Model(Protocol):
    """A source of assistant messages. One method is the whole contract."""

    def respond(self, request: ModelRequest) -> ModelResponse: ...


@runtime_checkable
class Tool(Protocol):
    """A callable the agent can invoke."""

    name: str
    schema: dict[str, Any]

    def call(self, arguments: dict[str, Any]) -> ToolResult: ...
