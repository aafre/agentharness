# CLAUDE.md — AgentHarness working agreement

This file is the contract every session (Claude, Codex, or a human) reads first. It
exists so work continues at full quality across context resets and handoffs. **Read this,
then read `HANDOFF.md` for the current state.**

## What we're building

The go-to Python agent-harness abstraction library for the next 20-30 years. One thesis:

> **An agent run is a deterministic, inspectable, replayable state machine — not a
> black box you pray over.**

Everything else (provider-agnosticism, observability, testability) falls out of getting
that abstraction right. Differentiator: engineers don't trust their agents; we make a run
fully deterministic, inspectable, and replayable.

## Architecture (layered for longevity)

| Package | Role | Status |
|---|---|---|
| `agentharness-core` | zero-dependency state machine, protocols, record/replay | **implemented** |
| `agentharness` | ergonomic layer: `Agent`, `@tool`, pytest helpers | planned |
| `agentharness-contrib` | real providers (Anthropic/OpenAI/Ollama) behind extras | planned |

The kernel is two pure functions over serializable data:
`decide(state) -> Effect | Done` and `reduce(state, event) -> State`. The **runner** is the
only impure part: it performs effects (model calls, tool calls) and records each one.
Replay re-feeds recorded results, so the pure core can't tell it isn't live.

Design spec: `docs/superpowers/specs/2026-06-24-agentharness-core-design.md`.

## Non-negotiable conventions

1. **`agentharness-core` has ZERO third-party runtime dependencies.** Standard library only.
2. **The kernel stays pure.** `decide`/`reduce` never do I/O, never mutate inputs, are
   deterministic. All nondeterminism goes through `Effect`s performed by the runner.
3. **Everything is a frozen dataclass and JSON round-trippable.** A run is always "just data."
4. **Python 3.12+**, PEP 695 generics (`class State[CtxT]`, `def reduce[CtxT](...)`).
5. **The public surface is tiny and stable.** Adding is fine; breaking is a last resort.
   New capabilities must be additive.
6. **TDD.** Write/extend the contract tests first, then implement to pass them.

## Dev workflow

The repo is a `uv` workspace. Always work from the repo root.

```bash
uv sync                                   # set up / refresh the env
uv run pytest -q                          # all tests
uv run pytest packages/agentharness-core  # just the core
uv run mypy                               # strict type check (library src only)
uv run ruff check                         # lint
uv run ruff format                        # format
uv run python examples/quickstart.py      # end-to-end smoke
```

**The green gate (run before every commit and every handoff):**

```bash
uv run ruff check && uv run mypy && uv run pytest -q
```

All three must pass. CI (`.github/workflows/ci.yml`) enforces this across
Python 3.12/3.13 on Linux/macOS/Windows. Releases go out via `release.yml` on a
`core-v*` tag using PyPI Trusted Publishing (no stored tokens).

## Delegating to Codex (plan → code → verify)

Codex (`gpt-5.5`, reasoning `xhigh`) writes code; Claude plans and verifies. Use the
installed Codex plugin commands — NOT raw `codex exec` (the harness blocks autonomous
bypass loops by design):

- `/codex:review` — read-only review of uncommitted changes.
- `/codex:adversarial-review` — skeptical pressure-test of design/edge cases.
- `/codex:rescue` — hand a tricky bug/implementation to Codex for a fresh attempt.
- `/codex:transfer` — hand the whole session to Codex to continue (context-handoff safety net).
- `/codex:status`, `/codex:result`, `/codex:cancel` — manage background runs.

Workflow: Claude writes the spec + the contract tests (the executable definition of done),
Codex implements to pass them, Claude runs the green gate and reviews. Never let either
side merge red.

## Handoff protocol (how we survive context limits)

The work lives in the repo, not in any session's context window. Before stopping:

1. Run the green gate. **Never hand off a red repo.**
2. Update `HANDOFF.md`: what changed, current status, the single most useful next step.
3. Commit with a clear message (and update the spec/docs if the design moved).
4. If mid-task and context is nearly full, either commit a WIP checkpoint with a `HANDOFF.md`
   note, or use `/codex:transfer` to continue.

A fresh session should be able to read `CLAUDE.md` + `HANDOFF.md`, run `uv sync`, run the
green gate, and immediately keep building at full quality.

## Roadmap (high level)

1. ✅ `agentharness-core`: kernel, effects/events, protocols, runner, record/replay, FakeModel.
2. Docs site + cookbook (human- and agent-readable; `llms.txt`).
3. `agentharness` ergonomic layer: `Agent`, `@tool` schema generation, pytest plugin.
4. `agentharness-contrib`: Anthropic, OpenAI, Ollama providers (optional extras).
5. Launch: PyPI publish, README/marketing, examples, community channels.

Keep `HANDOFF.md` authoritative for what's actually next.
