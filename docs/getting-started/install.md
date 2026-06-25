# Install

AgentHarness is not published to PyPI yet. The package names are stable, so docs show the
target install commands and the source workflow that works today.

## From PyPI

```bash
pip install agentharness-core
pip install agentharness
```

Provider packages stay optional. Anthropic support lives behind the contrib extra:

```bash
pip install "agentharness-contrib[anthropic]"
```

## From source

```bash
git clone https://github.com/aafre/agentharness.git
cd agentharness
uv sync
uv run python examples/quickstart.py
uv run python examples/agent_quickstart.py
```

`agentharness-core` has no third-party runtime dependencies. The root workspace owns docs,
tests, and provider SDK tooling.

