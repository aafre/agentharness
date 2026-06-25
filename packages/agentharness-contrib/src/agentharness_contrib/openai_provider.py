"""OpenAI provider: maps the core ``Model`` protocol onto Chat Completions.

The real ``openai`` SDK is an optional dependency, imported lazily, so installing
``agentharness-contrib`` does not require it unless you actually use this provider.

The translation functions are pure and SDK-free, so they're unit-testable without any
network calls or even the SDK installed.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from agentharness_core import (
    Message,
    ModelRequest,
    ModelResponse,
    ToolCall,
    Usage,
)

DEFAULT_MODEL = "gpt-4o"


def _to_openai_messages(messages: tuple[Message, ...]) -> list[dict[str, Any]]:
    """Map core messages to OpenAI chat messages."""
    out: list[dict[str, Any]] = []
    for m in messages:
        if m.role in {"system", "user"}:
            out.append({"role": m.role, "content": m.content or ""})
        elif m.role == "assistant":
            message: dict[str, Any] = {"role": "assistant", "content": m.content}
            if m.tool_calls:
                message["tool_calls"] = [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.name,
                            "arguments": json.dumps(call.arguments),
                        },
                    }
                    for call in m.tool_calls
                ]
            out.append(message)
        elif m.role == "tool":
            out.append(
                {
                    "role": "tool",
                    "tool_call_id": m.tool_call_id or "",
                    "content": m.content or "",
                }
            )
    return out


def _to_openai_tool(tool_def: dict[str, Any]) -> dict[str, Any]:
    """Map a neutral core tool descriptor to an OpenAI function tool."""
    return {
        "type": "function",
        "function": {
            "name": tool_def["name"],
            "description": tool_def.get("description", "") or "",
            "parameters": tool_def.get("schema", {}),
        },
    }


def _to_model_response(resp: Any) -> ModelResponse:
    """Map an OpenAI chat completion response to a core ``ModelResponse``."""
    msg = resp.choices[0].message
    content = msg.content
    tool_calls: list[ToolCall] = []
    for tc in msg.tool_calls or []:
        tool_calls.append(
            ToolCall(
                id=tc.id,
                name=tc.function.name,
                arguments=json.loads(tc.function.arguments or "{}"),
            )
        )
    usage = Usage(
        input_tokens=getattr(resp.usage, "prompt_tokens", 0) or 0,
        output_tokens=getattr(resp.usage, "completion_tokens", 0) or 0,
    )
    message = Message(role="assistant", content=content, tool_calls=tuple(tool_calls))
    return ModelResponse(message=message, usage=usage)


def _default_client_factory(**kwargs: Any) -> Any:
    import openai  # lazy: optional dependency

    return openai.OpenAI(**{k: v for k, v in kwargs.items() if v is not None})


class OpenAIModel:
    """A core ``Model`` backed by OpenAI's Chat Completions API.

    >>> model = OpenAIModel("gpt-4o")                      # uses OPENAI_API_KEY
    >>> agent = Agent(model=model, tools=[...])            # from agentharness

    Pass ``client=`` to inject a preconfigured ``openai.OpenAI`` (or a test double).
    Extra keyword arguments are forwarded to ``chat.completions.create``.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        client: Any | None = None,
        client_factory: Callable[..., Any] | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        max_tokens: int = 4096,
        system: str | None = None,
        **create_kwargs: Any,
    ) -> None:
        if client is None:
            factory = client_factory or _default_client_factory
            client = factory(base_url=base_url, api_key=api_key)
        self._client = client
        self._model = model
        self._max_tokens = max_tokens
        self._system = system
        self._create_kwargs = create_kwargs

    def respond(self, request: ModelRequest) -> ModelResponse:
        messages = _to_openai_messages(request.messages)
        if self._system:
            messages = [{"role": "system", "content": self._system}, *messages]
        tools = [_to_openai_tool(t) for t in request.tools]

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "max_tokens": self._max_tokens,
            **self._create_kwargs,
        }
        if tools:
            kwargs["tools"] = tools

        resp = self._client.chat.completions.create(**kwargs)
        return _to_model_response(resp)


class OllamaModel(OpenAIModel):
    def __init__(
        self,
        model: str = "llama3.1",
        *,
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "ollama",
        **kwargs: Any,
    ) -> None:
        # ponytail: Ollama's /v1 shim reuses the OpenAI wire format, so just defaults.
        super().__init__(model, base_url=base_url, api_key=api_key, **kwargs)
