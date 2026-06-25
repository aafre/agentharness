# The thesis

An agent loop is easier to trust when the impure parts are isolated.

```text
decide(state) -> Effect         # pure: what should happen next?
runner performs the Effect      # impure: model call or tool call
reduce(state, Event) -> State   # pure: fold the outcome into data
```

Because `decide` and `reduce` are pure functions over serializable data, AgentHarness gets
four production properties:

| You get | Because |
| --- | --- |
| Inspection | Every step is a plain `Event`. |
| Determinism | Same events produce the same states. |
| Replay | Recorded effects can be re-fed with no model or tools. |
| Sync and async | Only the runner owns I/O. |

```python exec="on"
from agentharness_core import Message, ModelResponded, State, Usage, reduce
from agentharness_core.testing import FakeModel

_model = FakeModel([Message("assistant", "unused")])
start = State.start([Message("user", "hello")])
next_state = reduce(
    start,
    ModelResponded(message=Message("assistant", "hi"), usage=Usage()),
)

assert next_state.messages[-1].content == "hi"
print(next_state.status)
```

The `FakeModel` is not needed by `reduce`; it is included here to keep every executed docs
snippet network-free and aligned with the docs gate.

