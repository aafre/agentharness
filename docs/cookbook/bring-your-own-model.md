# Bring your own model

When you want a custom provider, implement `respond(request) -> ModelResponse`. This snippet
uses `FakeModel` internally to stay deterministic while showing the protocol shape.

```python exec="on"
from agentharness_core import Message, ModelRequest, ModelResponse, State, run
from agentharness_core.testing import FakeModel

class LocalModel:
    def __init__(self) -> None:
        self._script = FakeModel([Message("assistant", "local response")])

    def respond(self, request: ModelRequest) -> ModelResponse:
        return self._script.respond(request)

start = State.start([Message("user", "use local model")])
live = run(start, model=LocalModel())
live.run_to_completion()

assert live.result == "local response"
print(live.result)
```

Why it works: the core depends on the `Model` protocol. Provider SDK details belong inside
your adapter, not inside agent logic.

