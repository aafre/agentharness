# Run async

When your application is async, use `arun` for eager completion or `astream` for event
streaming.

```python exec="on"
import asyncio

from agentharness import Agent
from agentharness.testing import FakeModel
from agentharness_core import Message

async def main() -> None:
    agent = Agent(model=FakeModel([Message("assistant", "async result")]))
    run = await agent.arun("work async")
    assert run.result == "async result"
    print(run.result)

asyncio.run(main())
```

Why it works: the async API wraps the same deterministic core. Provider packages can add
real async I/O without changing the state model.

