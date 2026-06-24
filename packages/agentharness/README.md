# agentharness

The ergonomic, batteries-included layer over [`agentharness-core`](../agentharness-core).

```python
from agentharness import Agent, tool

@tool
def add(a: int, b: int) -> str:
    """Add two numbers."""
    return str(a + b)

agent = Agent(model=my_model, tools=[add], system="You are helpful.")
run = agent.run("What is 2 + 3?")
print(run.result)          # "2 + 3 = 5."
run.trace.save("run.jsonl")  # the whole run is recorded and replayable
```

- **`@tool`** turns a typed Python function into a tool — the JSON schema is generated from
  type hints, no hand-written schemas.
- **`Agent`** wraps a model + tools + optional system prompt. `run()` executes to completion;
  `stream()` yields live events; `arun()`/`astream()` are the async variants.
- Built entirely on the deterministic core, so every agent you build is inspectable and
  replayable for free (`from agentharness_core import replay`).

Test agents like ordinary code, with no network:

```python
from agentharness.testing import FakeModel, assert_used_tool, assert_answer

agent = Agent(model=FakeModel([...]), tools=[add])
run = agent.run("What is 2 + 3?")
assert_used_tool(run, "add")
assert_answer(run, "2 + 3 = 5.")
```
