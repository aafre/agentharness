# Testing agents

Use `FakeModel` for deterministic behavior and the assertion helpers for readable tests.

```python exec="on"
from agentharness import Agent, tool
from agentharness.testing import FakeModel, assert_answer, assert_used_tool
from agentharness_core import Message, ToolCall

@tool
def add(a: int, b: int) -> str:
    """Add two numbers."""
    return str(a + b)

def test_addition_agent() -> None:
    model = FakeModel(
        [
            Message(
                "assistant",
                tool_calls=(ToolCall(id="c1", name="add", arguments={"a": 1, "b": 2}),),
            ),
            Message("assistant", "1 + 2 = 3."),
        ]
    )
    run = Agent(model=model, tools=[add]).run("Add 1 and 2")

    assert_used_tool(run, "add")
    assert_answer(run, "1 + 2 = 3.")

test_addition_agent()
print("tested")
```

In a pytest suite, omit the final two lines and let pytest discover the test function.

