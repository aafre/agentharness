# Catch a regression

When behavior changes, replay raises `DivergenceError` at the first mismatched effect.

```python exec="on"
from agentharness_core import DivergenceError, Message, State, replay, run
from agentharness_core.testing import FakeModel

original = State.start([Message("user", "answer yes")])
live = run(original, model=FakeModel([Message("assistant", "yes")]))
live.run_to_completion()

changed = State.start([Message("user", "answer no")])
try:
    replay(changed, trace=live.trace).run_to_completion()
except DivergenceError:
    print("regression caught")
else:
    raise AssertionError("replay should diverge")
```

Why it works: the recorded `ModelRequest` includes the messages. A changed prompt requests
a different effect.

