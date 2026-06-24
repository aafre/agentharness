# Codex task: implement `agentharness-core`

You are implementing the zero-dependency deterministic core of the AgentHarness library.

## Goal

Create the implementation modules under
`packages/agentharness-core/src/agentharness_core/` so that the **existing contract
tests** in `packages/agentharness-core/tests/` all pass, with `mypy --strict` and
`ruff` clean. Do NOT modify the tests except to fix an objively wrong test (if you
believe a test is wrong, explain why in your final message rather than silently
changing it).

## Read first

- `docs/superpowers/specs/2026-06-24-agentharness-core-design.md` — the full design.
- All files in `packages/agentharness-core/tests/` — the exact API contract.
- `pyproject.toml` (root) — ruff/mypy/pytest config.

## Hard constraints

- **Zero third-party runtime dependencies** in `agentharness-core`. Standard library only.
- Python **3.12+**. Use PEP 695 generics (`class State[CtxT]: ...`) where natural.
- All `State`, `Message`, `ToolCall`, `Usage`, every `Event`, and every `Effect` are
  **frozen dataclasses** and **JSON round-trippable**.
- The kernel (`decide`, `reduce`) is **pure**: no I/O, no input mutation, deterministic.
- All nondeterminism is funneled through effects performed by the runner. The default
  policy only performs `ModelRequest` and `ToolInvocation` effects; ambient effects
  (`Now`, `GenId`, `RandomBytes`) should exist in the type algebra but need not be used
  by the default loop.
- `mypy --strict` clean (run `uv run mypy`). `ruff check` clean (`uv run ruff check`).

## Modules to create (suggested layout — adjust if cleaner)

- `types.py` — `Role`, `Message`, `ToolCall`, `Usage`, `Status`, `State[CtxT]`
  (with `State.start(messages, context=None)`, `.to_dict()`, `.from_dict()`),
  `ModelResponse`, `ToolResult`.
- `effects.py` — `ModelRequest`, `ToolInvocation`, `Now`, `GenId`, `RandomBytes`, `Done`,
  and the `Effect` union.
- `events.py` — `RunStarted`, `ModelResponded`, `ToolResulted`, `StepFinished`,
  `RunFinished`, `RunFailed`, and the `Event` union.
- `protocols.py` — `Model` (one method `respond(ModelRequest) -> ModelResponse`),
  `Tool` (`name: str`, `schema: dict`, `call(arguments: dict) -> ToolResult`).
- `kernel.py` — `decide(state) -> Effect | Done`, `reduce(state, event) -> State`.
- `run.py` — `run(state, *, model, tools=(), max_steps=...) -> Run`, `arun(...)`,
  and the `Run` object (iterable of events; `.step() -> Event | None`; `.state`;
  `.result`; `.trace`). `run` records every performed effect into `run.trace`.
- `trace.py` — `Trace` (append-only `(effect, result)` log; `len()`, `==`,
  `.save(path)`, `.load(path)` JSON Lines), `replay(state, *, trace) -> Run`
  (answers effects from the trace, performs no I/O; raises `DivergenceError` on
  mismatch), `Recorder`/`Replayer` internals, `DivergenceError`.
- `testing.py` — `FakeModel(scripted_messages)`: deterministic `Model` that returns the
  next scripted `Message` on each `respond()` call. Also `ScriptedModel` alias.
- `__init__.py` — re-export the public surface used by the tests:
  `run, arun, replay, State, Message, ToolCall, Usage, ToolResult, ModelResponse,
  ModelRequest, ToolInvocation, Now, GenId, RandomBytes, Done,
  RunStarted, ModelResponded, ToolResulted, StepFinished, RunFinished, RunFailed,
  Model, Tool, decide, reduce, Trace, DivergenceError, Event, Effect`.
  Keep `FakeModel`/`ScriptedModel` importable from `agentharness_core.testing`.

## Behaviour notes (from the contract)

- `State.start(messages)` → status `"running"`, step 0, no result/error.
- Default loop: while running and step < max_steps:
  decide → if `ModelRequest`, call `model.respond` → `ModelResponded`;
  if `ToolInvocation`, find tool by name and `call` → `ToolResulted`
  (capture errors as `is_error=True`, never raise out of the loop);
  if `Done`, finish. Each performed effect is appended to the trace.
- Exceeding `max_steps` sets status `"failed"` with a non-None `error` (no infinite loop).
- Iterating a `Run` yields `Event`s; `Run.step()` advances one effect and returns the
  resulting `Event` (or `None` when finished). After completion `.result` holds the final
  assistant text and `.state.status == "done"`.
- `replay` reproduces an identical `State` sequence using only the trace — no model, no
  tools. A mismatch between a requested effect and the recorded one raises
  `DivergenceError`.

## Definition of done

Run and show green output for:

```
uv run pytest packages/agentharness-core
uv run mypy
uv run ruff check
```

Then summarize what you built and any deviations from the brief.
