# Swap providers

When agent code depends only on the `Model` protocol, provider changes stay outside the
agent loop. This recipe uses two `FakeModel` instances as provider stand-ins.

```python exec="on"
from agentharness import Agent
from agentharness.testing import FakeModel
from agentharness_core import Message

def ask(model: FakeModel) -> str | None:
    return Agent(model=model).run("Status?").result

fake_provider_a = FakeModel([Message("assistant", "from provider A")])
fake_provider_b = FakeModel([Message("assistant", "from provider B")])

assert ask(fake_provider_a) == "from provider A"
assert ask(fake_provider_b) == "from provider B"
print("same agent code")
```

Why it works: the runner talks to the structural `Model` protocol, not a concrete SDK.

