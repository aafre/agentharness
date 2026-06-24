"""Tagged JSON (de)serialization for the data algebra.

Every dataclass round-trips through ``encode``/``decode`` using a ``__type__`` tag.
This is what lets a whole run be written to disk and reconstructed byte-identically,
which underpins record/replay. Plain dicts (e.g. tool ``arguments`` and JSON-Schema
``schema`` blobs) pass through untagged.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from . import effects, events, types

# Registry of every serializable dataclass, keyed by class name.
_CLASSES: tuple[type, ...] = (
    types.ToolCall,
    types.Message,
    types.Usage,
    types.ToolResult,
    types.ModelResponse,
    types.State,
    effects.ModelRequest,
    effects.ToolInvocation,
    effects.Now,
    effects.GenId,
    effects.RandomBytes,
    effects.Done,
    events.RunStarted,
    events.ModelResponded,
    events.ToolResulted,
    events.StepFinished,
    events.RunFinished,
    events.RunFailed,
)
_REGISTRY: dict[str, type] = {cls.__name__: cls for cls in _CLASSES}


def encode(obj: Any) -> Any:
    """Convert a value into JSON-serializable primitives with type tags."""
    if obj is None or isinstance(obj, str | int | float | bool):
        return obj
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        out: dict[str, Any] = {"__type__": type(obj).__name__}
        for f in dataclasses.fields(obj):
            out[f.name] = encode(getattr(obj, f.name))
        return out
    if isinstance(obj, tuple | list):
        return [encode(x) for x in obj]
    if isinstance(obj, dict):
        return {k: encode(v) for k, v in obj.items()}
    raise TypeError(f"Cannot encode object of type {type(obj)!r}")


def decode(data: Any) -> Any:
    """Inverse of :func:`encode`."""
    if isinstance(data, list):
        return [decode(x) for x in data]
    if isinstance(data, dict):
        type_name = data.get("__type__")
        if type_name is None:
            return {k: decode(v) for k, v in data.items()}
        cls = _REGISTRY.get(type_name)
        if cls is None:
            raise TypeError(f"Unknown __type__ tag {type_name!r}")
        kwargs = {k: decode(v) for k, v in data.items() if k != "__type__"}
        return cls(**kwargs)
    return data
