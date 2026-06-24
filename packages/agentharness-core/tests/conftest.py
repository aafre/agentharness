"""Shared fixtures and helpers for the agentharness-core contract tests."""

from __future__ import annotations

from agentharness_core import ToolResult


class Adder:
    """A minimal deterministic Tool implementation used across tests.

    Satisfies the ``agentharness_core.Tool`` protocol structurally:
    ``name: str``, ``schema: dict``, and ``call(arguments: dict) -> ToolResult``.
    """

    name = "add"
    schema = {
        "type": "object",
        "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
        "required": ["a", "b"],
    }

    def call(self, arguments: dict) -> ToolResult:
        return ToolResult(content=str(arguments["a"] + arguments["b"]))


class Boom:
    """A Tool that always errors, to exercise the error path."""

    name = "boom"
    schema = {"type": "object", "properties": {}}

    def call(self, arguments: dict) -> ToolResult:
        return ToolResult(content="kaboom", is_error=True)
