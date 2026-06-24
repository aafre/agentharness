"""Contract: @tool turns a typed Python function into a core-compatible Tool."""

from __future__ import annotations

from agentharness import FunctionTool, tool
from agentharness_core import Tool, ToolResult


def test_tool_decorator_produces_a_core_tool() -> None:
    @tool
    def add(a: int, b: int) -> str:
        """Add two numbers."""
        return str(a + b)

    assert isinstance(add, FunctionTool)
    assert isinstance(add, Tool)  # satisfies the structural core protocol
    assert add.name == "add"
    assert add.description == "Add two numbers."


def test_schema_is_generated_from_type_hints() -> None:
    @tool
    def add(a: int, b: int) -> str:
        return str(a + b)

    assert add.schema == {
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
    }


def test_call_wraps_return_in_toolresult() -> None:
    @tool
    def add(a: int, b: int) -> str:
        return str(a + b)

    result = add.call({"a": 2, "b": 3})
    assert isinstance(result, ToolResult)
    assert result.content == "5"
    assert result.is_error is False


def test_tool_remains_directly_callable() -> None:
    @tool
    def add(a: int, b: int) -> str:
        return str(a + b)

    assert add(2, 3) == "5"  # the original function still works


def test_non_string_return_is_stringified() -> None:
    @tool
    def count(n: int) -> int:
        return n * 2

    assert count.call({"n": 4}).content == "8"


def test_toolresult_return_passes_through() -> None:
    @tool
    def risky(x: int) -> ToolResult:
        return ToolResult(content="boom", is_error=True)

    r = risky.call({"x": 1})
    assert r.is_error is True
    assert r.content == "boom"


def test_decorator_accepts_name_and_description_overrides() -> None:
    @tool(name="sum2", description="custom")
    def add(a: int, b: int) -> str:
        return str(a + b)

    assert add.name == "sum2"
    assert add.description == "custom"


def test_optional_and_defaulted_params_are_not_required() -> None:
    @tool
    def greet(name: str, greeting: str = "hello", times: int | None = None) -> str:
        return f"{greeting} {name}"

    assert greet.schema["required"] == ["name"]
    assert greet.schema["properties"]["greeting"] == {"type": "string"}
    assert greet.schema["properties"]["times"] == {"type": "integer"}


def test_list_param_schema() -> None:
    @tool
    def total(values: list[int]) -> str:
        return str(sum(values))

    assert total.schema["properties"]["values"] == {
        "type": "array",
        "items": {"type": "integer"},
    }
