# agentharness-contrib

Provider implementations and common tools for [AgentHarness](../../README.md). Each
provider lives behind an optional extra, so the core stays dependency-free.

```bash
pip install "agentharness-contrib[anthropic]"
```

```python
from agentharness import Agent, tool
from agentharness_contrib import AnthropicModel

@tool
def add(a: int, b: int) -> str:
    """Add two numbers."""
    return str(a + b)

agent = Agent(model=AnthropicModel("claude-opus-4-8"), tools=[add])
run = agent.run("What is 2 + 3?")
print(run.result)
run.trace.save("run.jsonl")   # real model call, fully recorded and replayable
```

`AnthropicModel` maps the core `Model` protocol onto Anthropic's Messages API. Pass
`client=` to inject a preconfigured `anthropic.Anthropic` (or a test double); extra
keyword arguments are forwarded to `messages.create` (e.g. `thinking=...`, `system=...`).

The Messages API translation is pure and SDK-free, so an agent's provider boundary is
unit-tested without network calls.

**Planned:** OpenAI (`[openai]`) and Ollama / OpenAI-compatible providers.
