"""Build-time hook that writes site/llms-full.txt from Markdown sources."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any


def _flatten_nav(items: Any) -> Iterable[str]:
    if isinstance(items, str):
        yield items
        return
    if isinstance(items, dict):
        for value in items.values():
            yield from _flatten_nav(value)
        return
    if isinstance(items, list | tuple):
        for item in items:
            yield from _flatten_nav(item)


def build_llms_full(docs_dir: Path, site_dir: Path, nav: Any) -> Path:
    output = site_dir / "llms-full.txt"
    parts = [
        "# AgentHarness full documentation",
        "> Generated from the MkDocs navigation order at build time.",
    ]
    seen: set[Path] = set()
    for rel in _flatten_nav(nav):
        if not rel.endswith(".md"):
            continue
        source = docs_dir / rel
        if source in seen or not source.exists():
            continue
        seen.add(source)
        text = source.read_text(encoding="utf-8").strip()
        parts.append(f"<!-- Source: {rel} -->\n\n{text}")

    output.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    return output


def on_post_build(config: Any) -> None:
    build_llms_full(
        docs_dir=Path(config["docs_dir"]),
        site_dir=Path(config["site_dir"]),
        nav=config["nav"],
    )
