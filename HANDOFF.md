# HANDOFF — living state

> Read `CLAUDE.md` first (the working agreement), then this file (what's actually done
> and what's next). Update this file before every stop/handoff.

**Last updated:** 2026-06-24

## Current status: `agentharness-core` is implemented and green

All four sub-project success criteria are met:

- ✅ `uv run pytest` — **24 passed** (includes the headline record/replay property test)
- ✅ `uv run mypy` — strict, clean (10 library source files)
- ✅ `uv run ruff check` — clean
- ✅ `uv run python examples/quickstart.py` — record → save → replay reproduces identically
- ✅ Zero third-party runtime deps in `agentharness-core`

### What exists

```
packages/agentharness-core/src/agentharness_core/
  types.py       # Role, Message, ToolCall, Usage, ToolResult, ModelResponse, State[CtxT]
  effects.py     # ModelRequest, ToolInvocation, Now, GenId, RandomBytes, Done, Effect
  events.py      # RunStarted, ModelResponded, ToolResulted, StepFinished, Run(Finished|Failed)
  protocols.py   # Model, Tool (structural)
  kernel.py      # decide(), reduce()  — the pure core
  run.py         # Run, run(), arun()/AsyncRun, replay(), live + replay performers
  trace.py       # Trace, TraceRecord, DivergenceError (JSONL record/replay)
  serde.py       # tagged JSON encode/decode for the whole algebra
  testing.py     # FakeModel / ScriptedModel
packages/agentharness-core/tests/   # contract tests: types, kernel, run, replay
examples/quickstart.py
docs/superpowers/specs/2026-06-24-agentharness-core-design.md
.github/workflows/ci.yml, release.yml
```

## Next step (single most useful thing)

**Initial git commit of the working core**, then choose the next sub-project. The repo is
green and ready to commit.

## Roadmap / backlog (ordered)

1. **Commit** the current green state. *(immediate)*
2. **Docs + cookbook** — the user flagged docs/tutorials as make-or-break for adoption.
   Build a docs site (Mintlify or mkdocs-material), a cookbook of cases, and an `llms.txt`
   so agents can consume the docs. Spec it via brainstorming → writing-plans first.
3. **`agentharness` ergonomic layer** — `Agent` wrapper, `@tool` JSON-schema generation
   from type hints, a pytest plugin with assertion helpers (`assert_called_tool`, etc.).
4. **`agentharness-contrib`** — Anthropic, OpenAI, Ollama/OpenAI-compatible providers,
   each behind an optional extra; keep core dep-free.
5. **Launch / marketing** — confirm final package name with the user (currently
   `agentharness*`), publish to PyPI (Trusted Publishing already wired), write the launch
   post, seed examples.

## Open decisions for the user

- **Package name**: working name `agentharness-core` / `agentharness` / `agentharness-contrib`
  (all available on PyPI; `harness` itself is taken). Confirm before first publish.
- **Publishing moment**: user authorized publishing under their account. Do NOT publish
  until the user explicitly approves the release (PyPI names/versions are permanent).

## Gotchas / notes

- Tests use absolute imports (`from conftest import Adder`) — the tests dir is intentionally
  not a package, and pytest puts it on `sys.path`.
- `mypy` is scoped to `packages/agentharness-core/src` (library code is the strict-typed
  contract; tests are covered by pytest + ruff). See `pyproject.toml`.
- Recorded `ModelRequest` effects are stored WITHOUT tool schemas (the canonical decide()
  output), so replay matches; the live runner injects schemas only for the actual model call.
- Codex delegation must use the `/codex:*` plugin commands, not raw `codex exec` with
  bypass flags (the harness blocks autonomous bypass loops).
