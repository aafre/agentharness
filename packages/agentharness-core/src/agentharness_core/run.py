"""The driver loop: ties decide -> perform -> reduce into an inspectable event stream.

``run`` performs effects for real and records them; ``replay`` answers effects from a
recorded Trace and performs nothing. Both produce a ``Run``: an iterable of events that
is also steppable, exposing the live ``state``, the final ``result``, and the ``trace``.
"""

from __future__ import annotations

import copy
from collections.abc import Iterator, Sequence
from dataclasses import replace
from typing import Any, Protocol

from .effects import Done, ModelRequest, ToolInvocation
from .events import (
    Event,
    ModelResponded,
    RunFailed,
    RunFinished,
    RunStarted,
    StepFinished,
    ToolResulted,
)
from .kernel import decide, reduce
from .protocols import Model, Tool
from .trace import DivergenceError, Trace
from .types import ModelResponse, State, ToolResult

DEFAULT_MAX_STEPS = 64


class _Performer(Protocol):
    trace: Trace

    def perform(self, effect: ModelRequest | ToolInvocation) -> Event: ...

    def finalize(self) -> None:
        """Called once when the run completes; lets replay assert the trace was fully used."""
        ...


class _LivePerformer:
    """Performs effects against a real model and real tools, recording each one."""

    def __init__(self, model: Model, tools: Sequence[Tool], trace: Trace) -> None:
        self._model = model
        self._tools: dict[str, Tool] = {t.name: t for t in tools}
        self.trace = trace

    def perform(self, effect: ModelRequest | ToolInvocation) -> Event:
        match effect:
            case ModelRequest():
                # Pass provider-neutral tool descriptors (name + description + schema);
                # each provider maps these to its own format. The recorded effect stays
                # schema-free so replay still matches decide().
                tool_defs = tuple(
                    {
                        "name": t.name,
                        "description": getattr(t, "description", "") or "",
                        "schema": dict(t.schema),
                    }
                    for t in self._tools.values()
                )
                call_request = replace(effect, tools=tool_defs) if tool_defs else effect
                response = self._model.respond(call_request)
                # Record the canonical (tools-free) effect so replay matches decide().
                self.trace.append(effect, response)
                return ModelResponded(response.message, response.usage)
            case ToolInvocation(call=call):
                tool = self._tools.get(call.name)
                if tool is None:
                    result = ToolResult(content=f"unknown tool: {call.name}", is_error=True)
                else:
                    try:
                        # Hand the tool a private copy so it cannot mutate recorded state.
                        result = tool.call(copy.deepcopy(call.arguments))
                    except Exception as exc:  # tools must never crash the loop
                        result = ToolResult(content=f"{type(exc).__name__}: {exc}", is_error=True)
                self.trace.append(effect, result)
                return ToolResulted(call.id, result.content, result.is_error)

    def finalize(self) -> None:
        return None


class _ReplayPerformer:
    """Answers effects from a recorded Trace, performing no I/O."""

    def __init__(self, trace: Trace) -> None:
        self.trace = trace
        self._records = list(trace.records)
        self._cursor = 0

    def perform(self, effect: ModelRequest | ToolInvocation) -> Event:
        if self._cursor >= len(self._records):
            raise DivergenceError("trace exhausted but the policy requested another effect")
        record = self._records[self._cursor]
        self._cursor += 1
        if record.effect != effect:
            raise DivergenceError(
                f"replay divergence at record {self._cursor - 1}:\n"
                f"  recorded: {record.effect!r}\n"
                f"  requested: {effect!r}"
            )
        result = record.result
        match effect:
            case ModelRequest():
                assert isinstance(result, ModelResponse)
                return ModelResponded(result.message, result.usage)
            case ToolInvocation(call=call):
                assert isinstance(result, ToolResult)
                return ToolResulted(call.id, result.content, result.is_error)

    def finalize(self) -> None:
        # If the policy stopped before consuming every recorded effect, behaviour changed.
        if self._cursor != len(self._records):
            raise DivergenceError(
                f"replay finished with {len(self._records) - self._cursor} unused trace "
                f"record(s): the policy requested fewer effects than were recorded"
            )


class Run:
    """An in-progress or completed agent run, exposed as an event stream.

    A ``Run`` is a **one-shot iterator**: iterating and ``step()`` share the same
    progress, and it cannot be restarted. Iterate it once (``for event in run``,
    ``list(run)``, ``run.run_to_completion()``) or step it manually, not both ways
    expecting independent passes. To replay, build a new ``Run`` (e.g. via ``replay``).
    """

    def __init__(
        self,
        state: State[Any],
        performer: _Performer,
        max_steps: int = DEFAULT_MAX_STEPS,
    ) -> None:
        self._state = state
        self._performer = performer
        self._max_steps = max_steps
        self.trace = performer.trace
        self._gen = self._drive()

    @property
    def state(self) -> State[Any]:
        return self._state

    @property
    def result(self) -> str | None:
        return self._state.result

    def __iter__(self) -> Iterator[Event]:
        return self

    def __next__(self) -> Event:
        return next(self._gen)

    def step(self) -> Event | None:
        """Advance one event. Returns ``None`` when the run is complete."""
        try:
            return next(self._gen)
        except StopIteration:
            return None

    def run_to_completion(self) -> State[Any]:
        for _ in self._gen:
            pass
        return self._state

    def _drive(self) -> Iterator[Event]:
        yield RunStarted(self._state)
        while True:
            decision = decide(self._state)

            # Finishing takes priority over the budget: a run that reaches its final
            # answer exactly at max_steps still succeeds.
            if isinstance(decision, Done):
                self._performer.finalize()
                final = self._final_text()
                self._state = replace(self._state, status="done", result=final)
                yield RunFinished(self._state)
                return

            if not isinstance(decision, ModelRequest | ToolInvocation):
                raise TypeError(f"default loop cannot perform ambient effect {decision!r}")

            # An effect must be performed; enforce the budget here (max_steps bounds effects).
            if self._state.step >= self._max_steps:
                error = f"max_steps ({self._max_steps}) exceeded"
                self._state = replace(self._state, status="failed", error=error)
                yield RunFailed(self._state, error)
                return

            event = self._performer.perform(decision)
            self._state = reduce(self._state, event)
            yield event

            self._state = replace(self._state, step=self._state.step + 1)
            yield StepFinished(self._state)

    def _final_text(self) -> str | None:
        for message in reversed(self._state.messages):
            if message.role == "assistant" and message.content is not None:
                return message.content
        return None


def run(
    state: State[Any],
    *,
    model: Model,
    tools: Sequence[Tool] = (),
    max_steps: int = DEFAULT_MAX_STEPS,
) -> Run:
    """Run an agent to completion (lazily), recording every effect into ``run.trace``."""
    return Run(state, _LivePerformer(model, tools, Trace()), max_steps=max_steps)


def replay(
    state: State[Any],
    *,
    trace: Trace,
    max_steps: int = DEFAULT_MAX_STEPS,
) -> Run:
    """Replay a recorded trace from a starting state, using no model and no tools.

    Raises :class:`DivergenceError` if the policy requests an effect that does not
    match the recorded trace.
    """
    return Run(state, _ReplayPerformer(trace), max_steps=max_steps)


class AsyncRun:
    """An async view over a :class:`Run` for ``async for`` consumption.

    The reference core performs no real async I/O (that belongs to provider packages);
    this wrapper exists so user code written against the async API works unchanged when
    async providers arrive.
    """

    def __init__(self, run_obj: Run) -> None:
        self._run = run_obj

    @property
    def state(self) -> State[Any]:
        return self._run.state

    @property
    def result(self) -> str | None:
        return self._run.result

    @property
    def trace(self) -> Trace:
        return self._run.trace

    def __aiter__(self) -> AsyncRun:
        return self

    async def __anext__(self) -> Event:
        event = self._run.step()
        if event is None:
            raise StopAsyncIteration
        return event

    async def astep(self) -> Event | None:
        return self._run.step()


def arun(
    state: State[Any],
    *,
    model: Model,
    tools: Sequence[Tool] = (),
    max_steps: int = DEFAULT_MAX_STEPS,
) -> AsyncRun:
    """Async-iterable variant of :func:`run`."""
    return AsyncRun(run(state, model=model, tools=tools, max_steps=max_steps))
