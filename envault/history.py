"""Track per-key change history within an environment."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class HistoryError(Exception):
    """Raised when a history operation fails."""


@dataclass
class HistoryEntry:
    key: str
    value: str
    timestamp: float
    actor: str = "envault"

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "actor": self.actor,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryEntry":
        return cls(
            key=data["key"],
            value=data["value"],
            timestamp=data["timestamp"],
            actor=data.get("actor", "envault"),
        )

    def __str__(self) -> str:
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.timestamp))
        return f"[{ts}] {self.key}={self.value!r} (by {self.actor})"


def _history_path(vault_dir: Path, environment: str) -> Path:
    return vault_dir / f".history_{environment}.json"


def _load_history(vault_dir: Path, environment: str) -> dict:
    path = _history_path(vault_dir, environment)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def _save_history(vault_dir: Path, environment: str, data: dict) -> None:
    path = _history_path(vault_dir, environment)
    with path.open("w") as fh:
        json.dump(data, fh, indent=2)


def record_change(
    vault_dir: Path,
    environment: str,
    key: str,
    value: str,
    actor: str = "envault",
) -> HistoryEntry:
    """Append a change entry for *key* in *environment*."""
    data = _load_history(vault_dir, environment)
    entry = HistoryEntry(key=key, value=value, timestamp=time.time(), actor=actor)
    data.setdefault(key, []).append(entry.to_dict())
    _save_history(vault_dir, environment, data)
    return entry


def get_history(
    vault_dir: Path,
    environment: str,
    key: str,
    limit: Optional[int] = None,
) -> List[HistoryEntry]:
    """Return recorded history for *key*, newest first."""
    data = _load_history(vault_dir, environment)
    raw = data.get(key, [])
    entries = [HistoryEntry.from_dict(r) for r in reversed(raw)]
    return entries[:limit] if limit is not None else entries


def clear_history(vault_dir: Path, environment: str, key: str) -> int:
    """Remove all history for *key*. Returns number of entries removed."""
    data = _load_history(vault_dir, environment)
    removed = len(data.pop(key, []))
    _save_history(vault_dir, environment, data)
    return removed
