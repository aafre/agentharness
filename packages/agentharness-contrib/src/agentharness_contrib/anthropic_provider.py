"""Anthropic (Claude) provider: maps the core ``Model`` protocol onto the Messages API.

The real ``anthropic`` SDK is an optional dependency, imported lazily, so installing
``agentharness-contrib`` does not require it unless you actually use this provider
(``pip install "agentharness-contrib[anthropic]"``).

The translation functions are pure and SDK-free, so they're unit-testable without any
network calls or even the SDK installed.
"""

from __future__ import annotations

from typing import Any

from agentharness_core import (
    Message,
    ModelRequest,
    ModelResponse,
    ToolCall,
    Usage,
)

DEFAULT_MODEL = "claude-opus-4-8"


def _split_messages(messages: tuple[Message, ...]) -> tuple[str | None, list[dict[str, Any]]]:
    """Split core messages into an Anthropic ``system`` string and a ``messages`` list."""
    system_parts: list[str] = []
    out: list[dict[str, Any]] = []
    for m in messages:
        if m.role == "system":
            if m.content:
                system_parts.append(m.content)
        elif m.role == "user":
            out.append({"role": "user", "content": m.content or ""})
        elif m.role == "assistant":
            blocks: list[dict[str, Any]] = []
            if m.content:
                blocks.append({"type": "text", "text": m.content})
            for call in m.tool_calls:
                blocks.append(
                    {"type": "tool_use", "id": call.id, "name": call.name, "input": call.arguments}
                )
            out.append({"role": "assistant", "content": blocks if blocks else (m.content or "")})
        elif m.role == "tool":
            out.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": m.tool_call_id or "",
                            "content": m.content or "",
                        }
                    ],
                }
            )
    system = "\n\n".join(system_parts) if system_parts else None
    return system, out


def _to_anthropic_tool(tool_def: dict[str, Any]) -> dict[str, Any]:
    """Map a neutral core tool descriptor to an Anthropic tool definition."""
    return {
        "name": tool_def["name"],
        "description": tool_def.get("description", "") or "",
        "input_schema": tool_def.get("schema", {}),
    }


def _to_model_response(resp: Any) -> ModelResponse:
    """Map an Anthropic ``Message`` response to a core ``ModelResponse``."""
    text_parts: list[str] = []
    tool_calls: list[ToolCall] = []
    for block in resp.content:
        block_type = getattr(block, "type", None)
        if block_type == "text":
            text_parts.append(block.text)
        elif block_type == "tool_use":
            tool_calls.append(ToolCall(id=block.id, name=block.name, arguments=dict(block.input)))
    content = "".join(text_parts) if text_parts else None
    usage = Usage(
        input_tokens=getattr(resp.usage, "input_tokens", 0) or 0,
        output_tokens=getattr(resp.usage, "output_tokens", 0) or 0,
    )
    message = Message(role="assistant", content=content, tool_calls=tuple(tool_calls))
    return ModelResponse(message=message, usage=usage)


class AnthropicModel:
    """A core ``Model`` backed by Anthropic's Messages API.

    >>> model = AnthropicModel("claude-opus-4-8")          # uses ANTHROPIC_API_KEY
    >>> agent = Agent(model=model, tools=[...])            # from agentharness

    Pass ``client=`` to inject a preconfigured ``anthropic.Anthropic`` (or a test double).
    Extra keyword arguments are forwarded to ``messages.create`` (e.g. ``thinking=...``).
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        client: Any | None = None,
        max_tokens: int = 4096,
        system: str | None = None,
        **create_kwargs: Any,
    ) -> None:
        if client is None:
            import anthropic  # lazy: optional dependency

            client = anthropic.Anthropic()
        self._client = client
        self._model = model
        self._max_tokens = max_tokens
        self._system = system
        self._create_kwargs = create_kwargs

    def respond(self, request: ModelRequest) -> ModelResponse:
        system, messages = _split_messages(request.messages)
        if self._system:
            system = self._system if not system else f"{self._system}\n\n{system}"
        tools = [_to_anthropic_tool(t) for t in request.tools]

        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "messages": messages,
            **self._create_kwargs,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = tools

        resp = self._client.messages.create(**kwargs)
        return _to_model_response(resp)
