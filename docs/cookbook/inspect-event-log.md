# Inspect the event log

When you need observability, iterate the run. The stream contains typed events.

```python exec="on"
from agentharness import Agent
from agentharness.testing import FakeModel
from agentharness_core import Message

agent = Agent(model=FakeModel([Message("assistant", "streamed")]))
run = agent.stream("show events")

event_names = [type(event).__name__ for event in run]
assert run.result == "streamed"
print(" -> ".join(event_names))
```

Why it works: `Run` is the live event stream and the final run object.

