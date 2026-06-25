# Record and replay offline

When you want to prove a run can be reproduced without a model or tools, persist the trace
and replay it.

```python exec="on"
from pathlib import Path
from tempfile import TemporaryDirectory

from agentharness_core import Message, State, Trace, replay, run
from agentharness_core.testing import FakeModel

start = State.start([Message("user", "record this")])
live = run(start, model=FakeModel([Message("assistant", "done")]))
live.run_to_completion()

with TemporaryDirectory() as tmp:
    path = Path(tmp) / "trace.jsonl"
    live.trace.save(path)
    offline = replay(start, trace=Trace.load(path))
    offline.run_to_completion()

assert offline.state == live.state
print(offline.result)
```

Why it works: replay consumes the recorded effect results and performs no impure work.

