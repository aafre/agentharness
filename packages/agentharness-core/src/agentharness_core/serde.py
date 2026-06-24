"""Type-driven JSON (de)serialization for the data algebra.

Encoding emits plain nested JSON (objects, arrays, primitives) with **no in-band type
tags**. Decoding is driven by the *expected* type: we walk a dataclass's field
annotations and reconstruct each field by its declared type. Tuples come back from lists,
nested dataclasses from objects, and any field typed ``dict[...]`` or ``Any`` (e.g. a
tool's ``arguments``) passes through as raw JSON.

Because no tags live inside user data, arbitrary tool payloads round-trip losslessly —
even a dict that happens to contain a key like ``"__type__"``. Union discriminators that
the data can't carry itself (e.g. "is this record's result a ModelResponse or a
ToolResult?") are supplied explicitly by the caller (see ``trace.py``).
"""

from __future__ import annotations

import dataclasses
import types as _pytypes
from typing import Any, Literal, TypeVar, Union, get_args, get_origin, get_type_hints

_PRIMITIVES = (str, int, float, bool)


def encode(obj: Any) -> Any:
    """Convert a value into JSON-serializable primitives (no type tags)."""
    if obj is None or isinstance(obj, _PRIMITIVES):
        return obj
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: encode(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, tuple | list):
        return [encode(x) for x in obj]
    if isinstance(obj, dict):
        return {k: encode(v) for k, v in obj.items()}
    raise TypeError(f"Cannot encode object of type {type(obj)!r}")


def decode_as(tp: Any, data: Any) -> Any:
    """Reconstruct ``data`` as the expected type ``tp``."""
    if tp is Any or isinstance(tp, TypeVar):
        return data

    origin = get_origin(tp)

    if origin is Literal:
        return data
    if origin is Union or origin is _pytypes.UnionType:
        args = get_args(tp)
        if data is None and type(None) in args:
            return None
        non_none = [a for a in args if a is not type(None)]
        return decode_as(non_none[0], data) if non_none else data
    if origin is tuple:
        elem = get_args(tp)[0]
        return tuple(decode_as(elem, x) for x in data)
    if origin is list:
        elem = get_args(tp)[0]
        return [decode_as(elem, x) for x in data]
    if origin is dict:
        return data  # raw JSON payload (e.g. tool arguments) — never reinterpreted

    if tp in _PRIMITIVES or tp is type(None):
        return data
    if dataclasses.is_dataclass(tp) and isinstance(tp, type):
        localns = {p.__name__: p for p in getattr(tp, "__type_params__", ())}
        hints = get_type_hints(tp, localns=localns)
        kwargs = {
            f.name: decode_as(hints[f.name], data[f.name])
            for f in dataclasses.fields(tp)
            if f.name in data
        }
        return tp(**kwargs)

    return data
