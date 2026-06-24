"""The ``@tool`` decorator: a typed Python function becomes a core-compatible Tool.

The JSON schema is derived from type hints and the ``required`` set from which parameters
lack defaults, so a tool is declared once, in plain Python, with no hand-written schema.
"""

from __future__ import annotations

import inspect
import types as _pytypes
from collections.abc import Callable
from typing import Any, Union, get_args, get_origin, get_type_hints, overload

from agentharness_core import ToolResult

_JSON_SCALARS: dict[type, str] = {
    int: "integer",
    float: "number",
    str: "string",
    bool: "boolean",
}


def _type_to_schema(tp: Any) -> dict[str, Any]:
    if tp in _JSON_SCALARS:
        return {"type": _JSON_SCALARS[tp]}
    origin = get_origin(tp)
    if origin is list:
        args = get_args(tp)
        return {"type": "array", "items": _type_to_schema(args[0]) if args else {}}
    if origin is dict:
        return {"type": "object"}
    if origin is Union or origin is _pytypes.UnionType:
        non_none = [a for a in get_args(tp) if a is not type(None)]
        if len(non_none) == 1:
            return _type_to_schema(non_none[0])
    return {}  # unknown / unconstrained


def _build_schema(func: Callable[..., Any]) -> dict[str, Any]:
    signature = inspect.signature(func)
    hints = get_type_hints(func)
    properties: dict[str, Any] = {}
    required: list[str] = []
    for name, param in signature.parameters.items():
        if name == "self" or param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        properties[name] = _type_to_schema(hints.get(name, str))
        if param.default is inspect.Parameter.empty:
            required.append(name)
    return {"type": "object", "properties": properties, "required": required}


class FunctionTool:
    """Wraps a callable so it satisfies the core ``Tool`` protocol while staying callable."""

    def __init__(
        self,
        func: Callable[..., Any],
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        self._func = func
        self.name = name or func.__name__
        self.description = description or (inspect.getdoc(func) or "")
        self.schema = _build_schema(func)

    def call(self, arguments: dict[str, Any]) -> ToolResult:
        result = self._func(**arguments)
        if isinstance(result, ToolResult):
            return result
        return ToolResult(content=result if isinstance(result, str) else str(result))

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._func(*args, **kwargs)

    def __repr__(self) -> str:
        return f"FunctionTool(name={self.name!r})"


@overload
def tool(func: Callable[..., Any], /) -> FunctionTool: ...
@overload
def tool(
    *, name: str | None = ..., description: str | None = ...
) -> Callable[[Callable[..., Any]], FunctionTool]: ...


def tool(
    func: Callable[..., Any] | None = None,
    /,
    *,
    name: str | None = None,
    description: str | None = None,
) -> FunctionTool | Callable[[Callable[..., Any]], FunctionTool]:
    """Turn a function into a ``FunctionTool``. Usable as ``@tool`` or ``@tool(name=...)``."""

    def wrap(f: Callable[..., Any]) -> FunctionTool:
        return FunctionTool(f, name=name, description=description)

    return wrap(func) if func is not None else wrap
