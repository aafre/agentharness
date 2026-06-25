# State & events

The core data algebra is immutable dataclasses: messages, tool calls, usage, tool results,
state, effects, events, and traces. They are structural and JSON round-trippable.

```python exec="on"
from agentharness_core import Message, State, ToolCall
from agentharness_core.testing import FakeModel

_model = FakeModel([Message("assistant", "unused")])
state = State.start(
    [
        Message(
            role="assistant",
            content=None,
            tool_calls=(ToolCall(id="c1", name="lookup", arguments={"q": "docs"}),),
        )
    ]
)

restored = State.from_dict(state.to_dict())
assert restored == state
print(restored.messages[0].tool_calls[0].arguments["q"])
```

Use `to_dict()` and `from_dict()` when you want stable storage without accepting an opaque
object graph.

