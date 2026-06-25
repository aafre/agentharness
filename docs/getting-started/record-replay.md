# Record & replay

Every model call and tool call is recorded in a `Trace`. Replay feeds the recorded results
back into the pure kernel, so it performs no model or tool I/O.

```python exec="on"
from pathlib import Path
from tempfile import TemporaryDirectory

from agentharness_core import Message, State, Trace, replay, run
from agentharness_core.testing import FakeModel

start = State.start([Message("user", "Answer deterministically")])
live = run(start, model=FakeModel([Message("assistant", "recorded")]))
live.run_to_completion()

with TemporaryDirectory() as tmp:
    path = Path(tmp) / "run.jsonl"
    live.trace.save(path)
    again = replay(start, trace=Trace.load(path))
    again.run_to_completion()

assert again.state == live.state
print(again.result)
```

`DivergenceError` is the alarm: replay raises it when the current policy requests a
different effect than the next recorded trace item.

??? example "Full core example"
    ```python
    --8<-- "examples/quickstart.py"
    ```

