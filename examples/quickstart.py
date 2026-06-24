"""AgentHarness quickstart: a run is data you can record and replay.

Run me:  uv run python examples/quickstart.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from agentharness_core import Message, State, ToolCall, ToolResult, Trace, replay, run
from agentharness_core.testing import FakeModel


# 1. A tool is anything with a name, a JSON schema, and a `call`.
class Add:
    name = "add"
    schema = {
        "type": "object",
        "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
        "required": ["a", "b"],
    }

    def call(self, arguments: dict) -> ToolResult:
        return ToolResult(content=str(arguments["a"] + arguments["b"]))


# 2. A model is anything with `respond`. FakeModel scripts the conversation so this
#    example needs no API key and is fully deterministic.
model = FakeModel(
    [
        Message(
            role="assistant",
            content=None,
            tool_calls=(ToolCall(id="c1", name="add", arguments={"a": 2, "b": 3}),),
        ),
        Message(role="assistant", content="2 + 3 = 5."),
    ]
)

start = State.start([Message("user", "What is 2 + 3?")])

# 3. Run it. Iterating yields the typed event stream; every effect is recorded.
live = run(start, model=model, tools=[Add()])
for event in live:
    print(f"  event: {type(event).__name__}")

print(f"\nresult : {live.result}")
print(f"status : {live.state.status}")
print(f"trace  : {len(live.trace)} recorded effects")

# 4. The whole run is just data. Save it...
path = Path(tempfile.gettempdir()) / "agentharness_quickstart.jsonl"
live.trace.save(path)

# 5. ...and replay it with NO model and NO tools. Byte-identical.
replayed = replay(start, trace=Trace.load(path))
replayed.run_to_completion()

assert replayed.state == live.state, "replay must reproduce the run exactly"
print("\n[OK] replay reproduced the run exactly")
