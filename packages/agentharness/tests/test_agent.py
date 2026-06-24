"""Contract: Agent is the one-import ergonomic entry point over the core loop."""

from __future__ import annotations

from agentharness import Agent, tool
from agentharness.testing import FakeModel, assert_answer, assert_used_tool
from agentharness_core import Message, RunFinished, ToolCall


@tool
def add(a: int, b: int) -> str:
    """Add two numbers."""
    return str(a + b)


def _add_then_answer() -> FakeModel:
    return FakeModel(
        [
            Message(
                role="assistant",
                content=None,
                tool_calls=(ToolCall(id="c1", name="add", arguments={"a": 2, "b": 3}),),
            ),
            Message(role="assistant", content="2 + 3 = 5."),
        ]
    )


def test_agent_runs_to_completion_and_returns_result() -> None:
    agent = Agent(model=_add_then_answer(), tools=[add])
    run = agent.run("What is 2 + 3?")

    assert run.result == "2 + 3 = 5."
    assert run.state.status == "done"


def test_agent_uses_tools() -> None:
    agent = Agent(model=_add_then_answer(), tools=[add])
    run = agent.run("What is 2 + 3?")

    assert_used_tool(run, "add")
    assert_answer(run, "2 + 3 = 5.")


def test_agent_includes_system_prompt() -> None:
    agent = Agent(
        model=FakeModel([Message(role="assistant", content="hi")]),
        system="You are terse.",
    )
    run = agent.run("hello")
    assert run.state.messages[0].role == "system"
    assert run.state.messages[0].content == "You are terse."


def test_agent_stream_yields_live_events() -> None:
    agent = Agent(model=_add_then_answer(), tools=[add])
    events = list(agent.stream("What is 2 + 3?"))
    assert isinstance(events[-1], RunFinished)


def test_agent_run_is_replayable() -> None:
    from agentharness_core import State, replay

    agent = Agent(model=_add_then_answer(), tools=[add])
    run = agent.run("What is 2 + 3?")

    # The recorded run replays identically with no model and no tools.
    start = State.start([Message("user", "What is 2 + 3?")])
    replayed = replay(start, trace=run.trace)
    replayed.run_to_completion()
    assert replayed.result == run.result
