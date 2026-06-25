# Unit-test an agent

When you want to test agent behavior with zero network, script the model and assert against
the finished run.

```python exec="on"
from agentharness import Agent, tool
from agentharness.testing import FakeModel, assert_answer, assert_used_tool
from agentharness_core import Message, ToolCall

@tool
def add(a: int, b: int) -> str:
    """Add two numbers."""
    return str(a + b)

model = FakeModel(
    [
        Message(
            "assistant",
            tool_calls=(ToolCall(id="c1", name="add", arguments={"a": 2, "b": 3}),),
        ),
        Message("assistant", "2 + 3 = 5."),
    ]
)
run = Agent(model=model, tools=[add]).run("What is 2 + 3?")

assert_used_tool(run, "add")
assert_answer(run, "2 + 3 = 5.")
print(run.result)
```

Why it works: the model script is ordinary data, and the assertion helpers read the recorded
event stream.

