"""Diff utilities for comparing vault environments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class DiffEntry:
    key: str
    status: str  # 'added', 'removed', 'changed', 'unchanged'
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def __str__(self) -> str:
        if self.status == "added":
            return f"+ {self.key}={self.new_value}"
        elif self.status == "removed":
            return f"- {self.key}={self.old_value}"
        elif self.status == "changed":
            return f"~ {self.key}: {self.old_value!r} -> {self.new_value!r}"
        else:
            return f"  {self.key}={self.new_value}"


def diff_envs(
    old: Dict[str, str],
    new: Dict[str, str],
    show_unchanged: bool = False,
) -> List[DiffEntry]:
    """Compare two environment variable dicts and return a list of DiffEntry."""
    entries: List[DiffEntry] = []
    all_keys = sorted(set(old) | set(new))

    for key in all_keys:
        if key in old and key not in new:
            entries.append(DiffEntry(key=key, status="removed", old_value=old[key]))
        elif key not in old and key in new:
            entries.append(DiffEntry(key=key, status="added", new_value=new[key]))
        elif old[key] != new[key]:
            entries.append(
                DiffEntry(key=key, status="changed", old_value=old[key], new_value=new[key])
            )
        elif show_unchanged:
            entries.append(DiffEntry(key=key, status="unchanged", new_value=new[key]))

    return entries


def format_diff(entries: List[DiffEntry], use_color: bool = False) -> str:
    """Render diff entries as a human-readable string."""
    if not entries:
        return "(no differences)"

    _COLOR = {
        "added": "\033[32m",
        "removed": "\033[31m",
        "changed": "\033[33m",
        "unchanged": "",
        "reset": "\033[0m",
    }

    lines = []
    for entry in entries:
        line = str(entry)
        if use_color and entry.status in _COLOR:
            line = f"{_COLOR[entry.status]}{line}{_COLOR['reset']}"
        lines.append(line)

    return "\n".join(lines)
