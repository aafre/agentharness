# agentharness-core

The zero-dependency deterministic core of **AgentHarness**.

> An agent run is a deterministic, inspectable, replayable state machine — not a
> black box you pray over.

This package is the durable spec layer: an `Event`/`State`/`Effect` algebra, two pure
functions (`decide`, `reduce`), a sync/async-agnostic driver loop, the `Model`/`Tool`
protocols, and a record/replay engine. It has **no third-party runtime dependencies**
and targets API stability measured in years.

```python
from agentharness_core import run, replay, State, Message
from agentharness_core.testing import FakeModel

model = FakeModel([...])           # deterministic, no network
r = run(State.start([Message("user", "add 1 and 2")]), model=model, tools=[adder])
print(r.result)                    # final answer
r.trace.save("run.jsonl")          # the whole run is just data

r2 = replay(State.start([Message("user", "add 1 and 2")]), trace=Trace.load("run.jsonl"))
assert r2.state == r.state         # byte-identical replay, no model/tools needed
```

See `docs/superpowers/specs/2026-06-24-agentharness-core-design.md` for the full design.
