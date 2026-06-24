"""The determinism engine: an append-only log of (effect, result) pairs.

A Trace is the recording of every impure thing that happened during a run. Because
the kernel is pure, re-feeding a Trace's results reproduces the run exactly — no model
and no tools required. A Trace is plain JSON-Lines data: inspect it, diff it, commit it.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import serde
from .effects import Effect
from .types import ModelResponse, ToolResult

EffectResult = ModelResponse | ToolResult


class DivergenceError(Exception):
    """Raised during replay when the policy requests an effect that does not match
    the next recorded effect. This is the "did my change alter agent behaviour?" alarm.
    """


@dataclass(frozen=True, slots=True)
class TraceRecord:
    """One performed effect and the result it produced."""

    effect: Effect
    result: EffectResult


class Trace:
    """An ordered, append-only log of effect/result records."""

    def __init__(self, records: Iterable[TraceRecord] | None = None) -> None:
        self._records: list[TraceRecord] = list(records or [])

    @property
    def records(self) -> tuple[TraceRecord, ...]:
        return tuple(self._records)

    def append(self, effect: Effect, result: EffectResult) -> None:
        self._records.append(TraceRecord(effect=effect, result=result))

    def __len__(self) -> int:
        return len(self._records)

    def __iter__(self) -> Any:
        return iter(self._records)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Trace):
            return NotImplemented
        return self._records == other._records

    def __repr__(self) -> str:
        return f"Trace({len(self._records)} records)"

    def save(self, path: str | Path) -> None:
        """Write the trace as JSON Lines (one record per line)."""
        import json

        lines = []
        for rec in self._records:
            lines.append(
                json.dumps(
                    {"effect": serde.encode(rec.effect), "result": serde.encode(rec.result)},
                    ensure_ascii=False,
                )
            )
        Path(path).write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> Trace:
        import json

        records: list[TraceRecord] = []
        text = Path(path).read_text(encoding="utf-8")
        for line in text.splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            effect = serde.decode(raw["effect"])
            result = serde.decode(raw["result"])
            records.append(TraceRecord(effect=effect, result=result))
        return cls(records)
