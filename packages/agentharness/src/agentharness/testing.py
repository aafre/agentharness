"""Test helpers for agents: deterministic models and readable assertions."""

from __future__ import annotations

from agentharness_core import Run
from agentharness_core.testing import FakeModel, ScriptedModel

__all__ = ["FakeModel", "ScriptedModel", "assert_answer", "assert_used_tool"]


def assert_used_tool(run: Run, name: str) -> None:
    """Assert the agent invoked the named tool at least once during ``run``."""
    used = [m.name for m in run.state.messages if m.role == "tool"]
    assert name in used, f"expected tool {name!r} to be used; tools used: {used}"


def assert_answer(run: Run, expected: str) -> None:
    """Assert the agent's final answer equals ``expected``."""
    assert run.result == expected, f"expected final answer {expected!r}, got {run.result!r}"
