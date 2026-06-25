"""The ``Agent`` ergonomic entry point over the core state machine."""

from __future__ import annotations

from collections.abc import Sequence

from agentharness_core import (
    AsyncRun,
    Message,
    Model,
    Run,
    State,
    Tool,
    arun,
    run,
)

DEFAULT_MAX_STEPS = 64


class Agent:
    """A model plus its tools and an optional system prompt.

    ``run`` is eager (executes to completion and returns the finished ``Run``, so
    ``.result``/``.state``/``.trace`` are immediately available). ``stream`` is lazy and
    yields the live event stream. Every run is recorded and therefore replayable.
    """

    def __init__(
        self,
        *,
        model: Model,
        tools: Sequence[Tool] = (),
        system: str | None = None,
        max_steps: int = DEFAULT_MAX_STEPS,
    ) -> None:
        self.model = model
        self.tools = list(tools)
        self.system = system
        self.max_steps = max_steps

    def _initial_state(self, prompt: str) -> State[None]:
        messages: list[Message] = []
        if self.system is not None:
            messages.append(Message("system", self.system))
        messages.append(Message("user", prompt))
        return State.start(messages)

    def stream(self, prompt: str) -> Run:
        """Return a lazy ``Run`` whose iteration yields live events."""
        return run(
            self._initial_state(prompt),
            model=self.model,
            tools=self.tools,
            max_steps=self.max_steps,
        )

    def run(self, prompt: str) -> Run:
        """Execute to completion and return the finished ``Run``."""
        r = self.stream(prompt)
        r.run_to_completion()
        return r

    def astream(self, prompt: str) -> AsyncRun:
        """Async-iterable variant of :meth:`stream`."""
        return arun(
            self._initial_state(prompt),
            model=self.model,
            tools=self.tools,
            max_steps=self.max_steps,
        )

    async def arun(self, prompt: str) -> AsyncRun:
        """Async variant of :meth:`run`: drain the run, then return it."""
        r = self.astream(prompt)
        async for _ in r:
            pass
        return r
