# AgentHarness

AgentHarness makes an agent run inspectable, deterministic, and replayable by treating it
as a state machine.

## Why in 30 seconds

Most agent frameworks mix policy, model calls, tool calls, and state mutation into one
loop. That makes failures hard to inspect and regressions hard to prove.

AgentHarness splits the loop into three parts:

- `decide(state) -> Effect`: choose the next impure operation.
- The runner performs the effect and records the result.
- `reduce(state, event) -> State`: fold the event into plain data.

The result is a typed event stream and a trace you can save, diff, and replay offline.

## Quickstart

```python exec="on"
from agentharness import Agent
from agentharness.testing import FakeModel
from agentharness_core import Message

agent = Agent(
    model=FakeModel([Message("assistant", "Use traces to make agents testable.")])
)
run = agent.run("Why AgentHarness?")

assert run.trace.records
print(run.result)
```

Next: [install AgentHarness](getting-started/install.md), then run your first deterministic
agent with no API key.

