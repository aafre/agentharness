# Tools with `@tool`

The `@tool` decorator converts a typed Python function into a core-compatible `Tool`.
The JSON schema is derived from type hints, and the original function remains callable.

```python exec="on"
from agentharness import FunctionTool, tool
from agentharness_core import Message, Tool
from agentharness_core.testing import FakeModel

_model = FakeModel([Message("assistant", "unused")])

@tool
def multiply(a: int, b: int, label: str = "product") -> str:
    """Multiply two integers."""
    return f"{label}: {a * b}"

assert isinstance(multiply, FunctionTool)
assert isinstance(multiply, Tool)
assert multiply.schema["required"] == ["a", "b"]
assert multiply(3, 4) == "product: 12"
print(multiply.schema["properties"]["label"]["type"])
```

Defaults make parameters optional in the schema; required parameters are those without
defaults.

