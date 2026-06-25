# Your first run

Start with `FakeModel`. It scripts the model response, so the run is deterministic and
needs no API key.

```python exec="on"
from agentharness_core import Message, State, run
from agentharness_core.testing import FakeModel

start = State.start([Message("user", "Say hello")])
model = FakeModel([Message("assistant", "hello")])

live = run(start, model=model)
events = [type(event).__name__ for event in live]

assert live.result == "hello"
print(", ".join(events))
```

The returned `Run` is both an iterator and the final run object. Iterating yields typed
events and leaves `.state`, `.result`, and `.trace` available for assertions.

??? example "Full ergonomic example"
    ```python
    --8<-- "examples/agent_quickstart.py"
    ```

