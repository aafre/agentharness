# Define a tool with `@tool`

When you want a Python function to become an agent tool, decorate it. The schema comes from
type hints.

```python exec="on"
from agentharness import tool
from agentharness_core import Message
from agentharness_core.testing import FakeModel

_model = FakeModel([Message("assistant", "unused")])

@tool
def add(a: int, b: int) -> str:
    """Add two integers."""
    return str(a + b)

assert add.schema["properties"]["a"] == {"type": "integer"}
assert add.schema["required"] == ["a", "b"]
assert add(2, 3) == "5"
print(add.name)
```

Why it works: the decorated object still calls the original function and also satisfies the
core `Tool` protocol.

