# Anthropic

`agentharness-contrib` includes an Anthropic adapter behind an optional extra. The core and
ergonomic packages do not depend on the Anthropic SDK.

Install when you are ready to make real provider calls:

```bash
pip install "agentharness-contrib[anthropic]"
```

Illustrative usage:

```python
from agentharness import Agent, tool
from agentharness_contrib import AnthropicModel

@tool
def add(a: int, b: int) -> str:
    """Add two integers."""
    return str(a + b)

agent = Agent(model=AnthropicModel(), tools=[add])
run = agent.run("What is 2 + 3?")
run.trace.save("anthropic-run.jsonl")
print(run.result)
```

This block is not executed by the docs build because it would require network access and an
API key. Use `FakeModel` for tests and docs snippets; use `AnthropicModel` only at the
application boundary where real model I/O belongs.

OpenAI and Ollama/OpenAI-compatible providers are planned.

