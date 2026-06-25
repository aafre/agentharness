# Determinism kit

The determinism kit is three pieces:

- `Trace`: append-only JSONL records of performed effects and results.
- `replay`: an offline runner that consumes a trace.
- `DivergenceError`: raised when behavior no longer matches the recording.

```python exec="on"
from agentharness_core import DivergenceError, Message, State, replay, run
from agentharness_core.testing import FakeModel

start = State.start([Message("user", "say yes")])
live = run(start, model=FakeModel([Message("assistant", "yes")]))
live.run_to_completion()

changed = State.start([Message("user", "say no")])
try:
    replay(changed, trace=live.trace).run_to_completion()
except DivergenceError as exc:
    print(type(exc).__name__)
else:
    raise AssertionError("expected replay divergence")
```

That failure is useful: it says a code or prompt change altered the next requested effect.

