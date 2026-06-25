# Cookbook

Task-oriented recipes for common AgentHarness jobs. Each page keeps the runnable path small
and deterministic.

1. [Unit-test an agent](unit-test-agent.md): use `FakeModel`, `assert_used_tool`, and `assert_answer`.
2. [Record and replay offline](record-replay-offline.md): save a trace and replay with no I/O.
3. [Catch a regression](catch-regression.md): let `DivergenceError` flag changed behavior.
4. [Define a tool with `@tool`](define-tool.md): generate schema from type hints.
5. [Multi-step tool use](multi-step-tool-use.md): model calls a tool, sees the result, answers.
6. [Inspect the event log](inspect-event-log.md): iterate `Run` for typed events.
7. [Swap providers](swap-providers.md): keep agent code stable while changing models.
8. [Run async](run-async.md): use `arun` or `astream`.
9. [Persist and diff traces](persist-diff-traces.md): traces are plain JSONL.
10. [Bring your own model](bring-your-own-model.md): implement `respond`.

