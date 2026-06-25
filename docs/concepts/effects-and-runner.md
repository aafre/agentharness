# Effects & the runner

`Effect` values are requests for impure work. The current core effects are model requests
and tool invocations. The runner is the only layer that performs them.

```python exec="on"
from agentharness_core import Message, ModelRequest, State, decide, run
from agentharness_core.testing import FakeModel

start = State.start([Message("user", "What happens next?")])
effect = decide(start)
assert isinstance(effect, ModelRequest)

live = run(start, model=FakeModel([Message("assistant", "the runner records it")]))
live.run_to_completion()
assert len(live.trace.records) == 1
print(type(live.trace.records[0].effect).__name__)
```

The trace records the canonical effect and the result. During replay, the runner answers
from the trace instead of calling the model or a tool.

