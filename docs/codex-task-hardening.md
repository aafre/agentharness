# Codex task: harden agentharness-core (fixes from adversarial review)

Fix the 7 findings below in `packages/agentharness-core`. **TDD:** for each finding, first
add a failing test to a NEW file `packages/agentharness-core/tests/test_hardening.py`, then
implement the minimal fix. Do **not** modify the existing contract test files. Keep the
green gate passing at the end: `uv run ruff check && uv run mypy && uv run pytest -q`.

The decisions below are made — implement them as specified, don't redesign.

## 1. (Critical) Tools must not be able to mutate recorded state/trace
`ToolCall.arguments` is a mutable dict shared by reference with tools.
- In `ToolCall.__post_init__`, store a deep copy of `arguments` (`copy.deepcopy`) so the
  frozen dataclass owns isolated data.
- In `_LivePerformer.perform` for `ToolInvocation`, pass `copy.deepcopy(call.arguments)` to
  `tool.call(...)`.
- Test: a tool that mutates its `arguments` argument must NOT change the recorded
  `ToolInvocation` in `run.trace` nor the message in `run.state`.

## 2. (High) `max_steps` must not fail a run that finishes exactly at the limit
Reorder `Run._drive`: each iteration, call `decide(state)` FIRST. If it returns `Done`,
finish (emit `RunFinished`) regardless of step count. Only if an effect must be performed,
enforce the budget: if `step >= max_steps`, emit `RunFailed`. (`max_steps` bounds effects
performed.) Verify the existing `test_max_steps_guard_fails_gracefully` still passes.
- Test: a model that gives a final answer in one model call with `max_steps=1` finishes
  `done`, not `failed`.

## 3. (High) Replay must reject leftover trace records
Add a `finalize()` method to the performer interface:
- `_LivePerformer.finalize()` → no-op.
- `_ReplayPerformer.finalize()` → raise `DivergenceError` if `self._cursor != len(self._records)`.
Call `performer.finalize()` in `Run._drive` right before emitting `RunFinished` (and before
`RunFailed`). Update the `_Performer` Protocol accordingly.
- Test: take a valid recorded trace, append one extra `TraceRecord`, then `replay(...)` must
  raise `DivergenceError` (not finish `done`).

## 4. (High) Serialization must not collide with legal tool JSON
Today any plain dict containing `"__type__"` (e.g. tool `arguments={"__type__": "x"}`) is
mis-decoded. Fix the format so **plain dicts round-trip losslessly even if they contain keys
like `__type__`**, while dataclasses still reconstruct.
Required approach (type-driven decoding — no in-band tags inside user data):
- Encoding: keep dataclasses as JSON objects, but the Trace record envelope carries the
  discriminator explicitly. Serialize each record as
  `{"effect_kind": "<ModelRequest|ToolInvocation>", "effect": <fields>, "result_kind":
  "<ModelResponse|ToolResult>", "result": <fields>}`.
- Decoding is driven by the EXPECTED type (use `typing.get_type_hints` on the dataclass and
  recurse by field type): tuples decode from lists, nested dataclasses decode by their field
  type, and any field typed `dict[...]`/`Any` (e.g. `ToolCall.arguments`, `State.context`,
  `ModelRequest.tools` entries) is passed through as raw JSON with NO tag interpretation.
- `State.to_dict()` / `State.from_dict()` keep working (decode `from_dict` as type `State`).
- Test: `ToolCall(arguments={"__type__": "NotARealType", "a": [1, {"b": 2}]})` survives a
  trace save/load AND a `State.to_dict()/from_dict()` round-trip unchanged.

## 5. (Medium) Duplicate `tool_call.id` must not drop calls
In `reduce` for `ToolResulted`, remove only the FIRST pending call whose `id == call_id`
(by position), not all matching ids.
- Test: two pending calls sharing id `"dup"` both get resolved across two `ToolResulted`
  events (two tool messages appended), deterministically.

## 6. (Medium) Trace bytes must be canonical
In `Trace.save` (and anywhere JSON is emitted for traces), use
`json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)` so logically
equal traces serialize to identical bytes regardless of dict construction order.
- Test: two traces built with differently-ordered argument dicts that are logically equal
  serialize to byte-identical files.

## 7. (Low) Make the `Run` iterator contract explicit
Make `Run` a proper one-shot `Iterator`: `__iter__` returns `self`, add `__next__` that
delegates to the internal generator. Document in the docstring that a `Run` is consumed once
(stepping and iterating share progress; it is not restartable). Apply the analogous contract
note to `AsyncRun`.
- Test: `next(r)` then `list(r)` continues from where stepping left off (no duplication, no reset).

## Definition of done
Show green output for `uv run ruff check && uv run mypy && uv run pytest -q`, report the new
test count, and summarize each fix with file:line. Do not change the existing contract tests.
