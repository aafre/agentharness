"""The ergonomic API: define tools with @tool, run an Agent, replay the run.

Run me:  uv run python examples/agent_quickstart.py
"""

from __future__ import annotations

from agentharness import Agent, tool
from agentharness.testing import FakeModel, assert_answer, assert_used_tool
from agentharness_core import Message, State, ToolCall, replay


@tool
def add(a: int, b: int) -> str:
    """Add two numbers."""
    return str(a + b)


# A scripted model so the example is deterministic and needs no API key.
model = FakeModel(
    [
        Message(
            role="assistant",
            content=None,
            tool_calls=(ToolCall(id="c1", name="add", arguments={"a": 2, "b": 3}),),
        ),
        Message(role="assistant", content="2 + 3 = 5."),
    ]
)

agent = Agent(model=model, tools=[add], system="You are a careful calculator.")
run = agent.run("What is 2 + 3?")

print(f"answer : {run.result}")
print(f"status : {run.state.status}")
print(f"tool schema: {add.schema}")

assert_used_tool(run, "add")
assert_answer(run, "2 + 3 = 5.")

# Everything is replayable, even through the ergonomic layer.
start = State.start(
    [Message("system", "You are a careful calculator."), Message("user", "What is 2 + 3?")]
)
replayed = replay(start, trace=run.trace)
replayed.run_to_completion()
assert replayed.result == run.result
print("\n[OK] agent run replayed identically")
