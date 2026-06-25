# Persist and diff traces

When you need auditability, traces are plain JSONL. Save them, inspect them, and diff them
like any other artifact.

```python exec="on"
from pathlib import Path
from tempfile import TemporaryDirectory

from agentharness_core import Message, State, run
from agentharness_core.testing import FakeModel

start = State.start([Message("user", "versioned answer")])

with TemporaryDirectory() as tmp:
    first = run(start, model=FakeModel([Message("assistant", "v1")]))
    second = run(start, model=FakeModel([Message("assistant", "v2")]))
    first.run_to_completion()
    second.run_to_completion()

    a = Path(tmp) / "a.jsonl"
    b = Path(tmp) / "b.jsonl"
    first.trace.save(a)
    second.trace.save(b)

    assert a.read_text() != b.read_text()
    print("trace changed")
```

Why it works: the trace file contains the requested effect plus the exact recorded result.

