<div align="center">

# AgentHarness

**Your AI agent is a deterministic, inspectable, replayable state machine — not a black box you pray over.**

[![CI](https://github.com/aafre/agentharness/actions/workflows/ci.yml/badge.svg)](https://github.com/aafre/agentharness/actions/workflows/ci.yml)
[![Docs](https://github.com/aafre/agentharness/actions/workflows/docs-deploy.yml/badge.svg)](https://aafre.github.io/agentharness/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)

[Documentation](https://aafre.github.io/agentharness/)

</div>

---

## The problem

Engineers don't trust their agents. Today's frameworks treat an agent run as a black
box: a prompt goes in, you pray, a result comes out. When it misbehaves in production
you can't see why, you can't reproduce it, and you can't prove that your "fix" actually
changed anything. Agents are some of the least testable code most teams have ever
shipped.

## The idea

AgentHarness models an agent run as a **state machine** built from three pure pieces:

```
  decide(state) -> Effect        "what impure thing should happen next?"   (pure)
  runner performs the Effect     call the model / run a tool                (impure, recorded)
  reduce(state, Event) -> State   "fold the outcome into the next state"    (pure)
```

Because `decide` and `reduce` are pure functions over serializable data, four things
that are normally hard become free:

| You get | Because |
|---|---|
| **Inspection** | every step is a plain `Event` you can read |
| **Determinism** | same events ⇒ same states, always |
| **Replay** | re-feed the recorded effects — no model, no tools, byte-identical |
| **Sync *and* async** | the core never does I/O; only the runner does |

## Quickstart

```python
from agentharness_core import run, replay, State, Message, Trace
from agentharness_core.testing import FakeModel

model = FakeModel([...])     # deterministic, no API key needed
start = State.start([Message("user", "What is 2 + 3?")])

# Run it — iterating yields a typed event stream; every effect is recorded.
live = run(start, model=model, tools=[Add()])
print(live.result)           # "2 + 3 = 5."

# The whole run is just data. Save it...
live.trace.save("run.jsonl")

# ...and replay it with NO model and NO tools. Identical, every time.
again = replay(start, trace=Trace.load("run.jsonl"))
again.run_to_completion()
assert again.state == live.state
```

See [`examples/quickstart.py`](examples/quickstart.py) for the full runnable version.

## Why this matters for production

- **Regression detection.** Re-run a recorded trace against your refactored agent. If
  behaviour changed, replay raises `DivergenceError` and tells you exactly where.
- **Unit-testable agents.** `FakeModel` scripts a conversation so you can assert on an
  agent's behaviour like any other code — zero network, zero flakiness.
- **Observability for free.** The event stream *is* your trace. Log it, store it, diff it.
- **No lock-in.** The core has **zero third-party dependencies** and a tiny, stable API.
  Anything with a `respond` method is a model; anything with `name`/`schema`/`call` is a tool.

## Architecture

AgentHarness is layered so the foundation can stay frozen for decades while the
ergonomic surface evolves:

- **`agentharness-core`** — the zero-dependency state machine, protocols, and record/replay. *(available)*
- **`agentharness`** — the ergonomic layer: `Agent`, `@tool` schema generation, test helpers. *(available)*
- **`agentharness-contrib`** — real providers behind optional extras: **Anthropic, OpenAI, and Ollama available**.

```python
from agentharness import Agent, tool

@tool
def add(a: int, b: int) -> str:
    """Add two numbers."""        # schema generated from type hints
    return str(a + b)

agent = Agent(model=my_model, tools=[add], system="You are helpful.")
print(agent.run("What is 2 + 3?").result)
```

## Status

Early but real. `agentharness-core` is fully implemented, type-checked (`mypy --strict`),
and tested — including a property test proving record-then-replay is always identical.
See [`docs/superpowers/specs/`](docs/superpowers/specs/) for the design and
[`HANDOFF.md`](HANDOFF.md) for current state and roadmap.

## License

Apache-2.0. See [LICENSE](LICENSE).
