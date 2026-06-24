# agentharness-core — Design Spec

**Date:** 2026-06-24
**Status:** Approved (foundational decisions locked via brainstorming)
**Scope:** Sub-project #1 of the AgentHarness library — the zero-dependency deterministic core.

---

## 1. Vision

Build the open-source agent-harness abstraction library that becomes the Python
community's go-to for the next 20-30 years of AI development.

**Core thesis:** *An agent run is a deterministic, inspectable, replayable state
machine — not a black box you pray over.* Engineers don't trust their agents
because current frameworks treat a run as "prompt in, pray, result out." If a run
is a fully deterministic, inspectable, replayable state machine, you win the
production-engineering and enterprise market.

Everything else (provider-agnostic core, observability) falls out of getting that
one abstraction right.

## 2. Locked decisions

| Decision | Choice |
|---|---|
| Philosophy | Layered: `core` (spec) → `agentharness` (ergonomic) → `contrib` (providers/tools) |
| Differentiator | Determinism + inspectability + replay; provider-agnosticism and observability are consequences |
| Execution model | Event-stream / step-iterator state machine |
| Concurrency | Sync/async-agnostic **pure** core; all I/O is pluggable and lives in the runner |
| Python | 3.12+ (PEP 695 generics for clean generic `Protocol`s) |
| Naming | dists `agentharness-core` / `agentharness` / `agentharness-contrib`; imports `agentharness_core` etc. |
| Tooling | `uv` workspace, `hatchling`, `ruff`, `mypy --strict`, `pytest` + `hypothesis` |

## 3. The central idea: decide / perform / reduce

Separate **deciding** from **doing**, and make everything between pure.

```
  State ──▶ decide(state) ─▶ Effect | Done        (pure: "what next?")
                 │
                 ▼ Effect (data: ModelRequest, ToolInvocation, Now, GenId, RandomBytes)
            RUNNER performs the effect (sync OR async) ─▶ Event   (the only impure part)
                 │
                 ▼
  State ──▶ reduce(state, event) ─▶ State          (pure: "fold outcome in")
```

`decide` and `reduce` are **pure functions** over **serializable** data. Three hard
problems collapse into one mechanism:

- **Inspection** = read the event/effect log (it's just data).
- **Determinism** = same events ⇒ same states, always (pure reducer).
- **Replay** = re-feed recorded effect-results; the core cannot tell it isn't live.
- **Sync/async-agnostic** = the core never does I/O; only the runner does.

All nondeterminism (model output, tool side effects, clock, randomness, IDs) is
funneled through `Effect`s, so nothing leaks around the recorder.

## 4. Data algebra (`agentharness_core.types`)

All frozen dataclasses, all JSON round-trippable. Generic over a user context type
`CtxT` using PEP 695 syntax.

### Messages
- `Role` = `Literal["system", "user", "assistant", "tool"]`
- `ToolCall` — `id: str`, `name: str`, `arguments: dict`
- `Message` — `role: Role`, `content: str | None`, `tool_calls: tuple[ToolCall, ...] = ()`,
  `tool_call_id: str | None = None`, `name: str | None = None`
- `Usage` — `input_tokens: int = 0`, `output_tokens: int = 0` (additive monoid)

### State
- `Status` = `Literal["running", "awaiting_model", "awaiting_tools", "done", "failed"]`
- `State[CtxT]` — frozen:
  - `messages: tuple[Message, ...]`
  - `status: Status`
  - `step: int`
  - `usage: Usage`
  - `pending_calls: tuple[ToolCall, ...]` — tool calls decided but not yet resolved
  - `result: str | None` — final assistant text when `done`
  - `error: str | None`
  - `context: CtxT | None` — opaque user state slot
  - helper constructors: `State.start(messages, context=None)`

### Effects (requests to do something impure) — `Effect` union
- `ModelRequest` — `messages`, `tools` (schemas), `request_id`
- `ToolInvocation` — `call: ToolCall`
- `Now` — request wall-clock time
- `GenId` — request a fresh id
- `RandomBytes` — `n: int`
- `Done` — sentinel meaning the run is complete (returned by `decide`, not an effect to perform)

### Events (outcomes that already happened) — `Event` union
- `RunStarted` — `state`
- `ModelResponded` — `message: Message`, `usage: Usage`
- `ToolResulted` — `call_id: str`, `content: str`, `is_error: bool`
- `StepFinished` — `state`
- `RunFinished` — `state`
- `RunFailed` — `state`, `error: str`

## 5. The pure kernel (`agentharness_core.kernel`)

```python
def decide(state: State[CtxT]) -> Effect | Done: ...
def reduce(state: State[CtxT], event: Event) -> State[CtxT]: ...
```

`decide` logic (reference policy):
1. `status == done/failed` → `Done`.
2. `pending_calls` non-empty → `ToolInvocation` for the next unresolved call.
3. last message is `user`/`tool` (model's turn) → `ModelRequest`.
4. last assistant message has tool_calls → set `awaiting_tools`, emit first `ToolInvocation`.
5. last assistant message has no tool_calls → terminal; produce `RunFinished`/`Done`.

`reduce` is a total function: every `(state, event)` pair yields a valid next state;
it never performs I/O and never raises on valid input.

The decide policy is itself a small, swappable object (`Policy` protocol) so advanced
users can change loop behaviour without forking the kernel — but the default policy
is what 99% use.

## 6. Protocols (`agentharness_core.protocols`)

Structural, PEP 695 generics:

- `Model` — single method `respond(request: ModelRequest) -> ModelResponse`. This one
  method is the entire provider contract. (`ModelResponse` = `message` + `usage`.)
- `Tool` — `name: str`, `schema: dict` (JSON Schema for args), `call(arguments: dict) -> ToolResult`.
- `Clock` / `IdSource` / `Entropy` — ambient effect handlers (default real impls;
  deterministic impls used under record/replay).
- `Runner` — performs effects; `SyncRunner` and `AsyncRunner` reference implementations.

## 7. The driver loop (`agentharness_core.run`)

The loop ties decide → perform → reduce and yields events:

```python
def run(state, *, model, tools, ...) -> Run        # iterable of Event; .result, .state, .step()
async def arun(state, *, model, tools, ...) -> AsyncRun
```

`Run` is the step-iterator: iterating yields `Event`s; `.step()` advances one effect;
`.state` is the current `State`; `.result` is the final answer. Same object underlies
streaming, manual stepping, tracing, and replay.

## 8. Determinism kit (`agentharness_core.trace`)

- `Trace` — ordered, append-only log of `(Effect, Result)` pairs, serialized as JSON Lines.
- `Recorder` — wraps a runner; performs effects for real and appends each to the `Trace`.
- `Replayer` — wraps a runner; answers each effect from the `Trace` **without performing
  it**. If the core requests an effect that does not match the next logged effect, raises
  `DivergenceError` — the "did my refactor change agent behaviour?" superpower.
- Determinism contract: `replay(record(run)) == run` — byte-identical state sequence.

## 9. Test doubles (`agentharness_core.testing`)

- `FakeModel(scripted_responses)` / `ScriptedModel` — deterministic models, zero network.
- `tool_ok(name, ...)` helpers for building tools in tests.

## 10. Public surface (intentionally tiny)

`run`, `arun`, `step`, `State`, `Message`, `ToolCall`, the `Event`/`Effect` unions,
`Model`, `Tool`, `record`, `replay`, `Trace`, `FakeModel`. Learnable in an afternoon;
stable enough to never break. SemVer; the core targets API stability measured in years.

## 11. Testing strategy (TDD)

- Pure kernel → exhaustive unit tests of `decide`/`reduce` over hand-built states.
- Property test (hypothesis): **record-then-replay reproduces an identical state
  sequence** for arbitrary scripted model/tool interactions (the headline guarantee).
- Property test: `reduce` is total (never raises) over generated valid events.
- Serialization round-trip: every `State`/`Event`/`Effect` survives `to_json`/`from_json`.
- Zero runtime third-party dependencies in `agentharness-core`.

## 12. Out of scope (later sub-projects)

Real providers, `@tool` schema generation from type hints, pytest assertion plugin,
streaming token deltas, durable/distributed execution, human-in-the-loop pause/resume
persistence. The core is designed so these are additive, never breaking.

## 13. Success criteria for this sub-project

1. `uv run pytest` green, `mypy --strict` clean, `ruff` clean.
2. The record/replay property test passes.
3. A working end-to-end example: a `FakeModel` agent that calls a tool and finishes,
   recorded to a trace file and replayed identically.
4. Zero third-party runtime deps in the core distribution.
