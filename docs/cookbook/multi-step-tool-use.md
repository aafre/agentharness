# Multi-step tool use

When a model asks for a tool, AgentHarness records the request, runs the tool, records the
result, then sends the updated state back to the model.

```python exec="on"
from agentharness import Agent, tool
from agentharness.testing import FakeModel, assert_used_tool
from agentharness_core import Message, ToolCall

@tool
def add(a: int, b: int) -> str:
    """Add two integers."""
    return str(a + b)

model = FakeModel(
    [
        Message(
            role="assistant",
            content=None,
            tool_calls=(ToolCall(id="c1", name="add", arguments={"a": 4, "b": 6}),),
        ),
        Message("assistant", "4 + 6 = 10."),
    ]
)
run = Agent(model=model, tools=[add]).run("Add 4 and 6")

assert_used_tool(run, "add")
print(run.result)
```

Why it works: `decide` sees pending tool calls, the runner performs them, and `reduce` folds
tool results back into state.

