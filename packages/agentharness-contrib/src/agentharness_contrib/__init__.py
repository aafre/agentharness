"""agentharness-contrib: provider implementations for AgentHarness.

Each provider lives behind an optional extra so the core stays dependency-free:

    pip install "agentharness-contrib[anthropic]"

    from agentharness_contrib import AnthropicModel
    from agentharness import Agent

    agent = Agent(model=AnthropicModel("claude-opus-4-8"), tools=[...])
"""

from __future__ import annotations

from .anthropic_provider import AnthropicModel
from .openai_provider import OllamaModel, OpenAIModel

__version__ = "0.0.1"

__all__ = ["AnthropicModel", "OllamaModel", "OpenAIModel", "__version__"]
