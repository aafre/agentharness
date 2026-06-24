"""Deterministic test doubles. Build and test agents with zero network calls."""

from __future__ import annotations

from collections.abc import Iterable

from .effects import ModelRequest
from .types import Message, ModelResponse, Usage


class FakeModel:
    """A ``Model`` that returns a fixed script of messages, one per ``respond`` call.

    The whole point of the harness: you can unit-test an agent like ordinary code.
    """

    def __init__(self, messages: Iterable[Message], usage: Usage | None = None) -> None:
        self._messages = list(messages)
        self._usage = usage if usage is not None else Usage()
        self._cursor = 0

    def respond(self, request: ModelRequest) -> ModelResponse:
        if self._cursor >= len(self._messages):
            raise RuntimeError(
                "FakeModel ran out of scripted messages "
                f"(asked for #{self._cursor + 1}, have {len(self._messages)})"
            )
        message = self._messages[self._cursor]
        self._cursor += 1
        return ModelResponse(message=message, usage=self._usage)


# Alias for readability when the script is the salient point.
ScriptedModel = FakeModel
