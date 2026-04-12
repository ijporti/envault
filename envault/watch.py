"""Watch an environment for changes and trigger a callback."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from envault.store import load_vault, _vault_path


class WatchError(Exception):
    """Raised when a watch operation fails."""


@dataclass
class WatchEvent:
    environment: str
    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, tuple] = field(default_factory=dict)  # key -> (old, new)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.changed:
            parts.append(f"~{len(self.changed)} changed")
        return ", ".join(parts) if parts else "no changes"


def _snapshot(vault_dir: str, environment: str, password: str) -> Dict[str, str]:
    """Return current key/value mapping for an environment."""
    try:
        data = load_vault(vault_dir, environment, password)
        return dict(data)
    except FileNotFoundError:
        raise WatchError(f"Environment '{environment}' not found in '{vault_dir}'")


def _diff_snapshots(
    environment: str,
    before: Dict[str, str],
    after: Dict[str, str],
) -> WatchEvent:
    event = WatchEvent(environment=environment)
    before_keys = set(before)
    after_keys = set(after)
    event.added = {k: after[k] for k in after_keys - before_keys}
    event.removed = {k: before[k] for k in before_keys - after_keys}
    for k in before_keys & after_keys:
        if before[k] != after[k]:
            event.changed[k] = (before[k], after[k])
    return event


def watch_env(
    vault_dir: str,
    environment: str,
    password: str,
    callback: Callable[[WatchEvent], None],
    interval: float = 2.0,
    max_polls: Optional[int] = None,
) -> int:
    """Poll an environment for changes and invoke *callback* on each change.

    Returns the total number of change events emitted.
    """
    if interval <= 0:
        raise WatchError("interval must be a positive number")

    current = _snapshot(vault_dir, environment, password)
    events_emitted = 0
    polls = 0

    while max_polls is None or polls < max_polls:
        time.sleep(interval)
        polls += 1
        try:
            updated = _snapshot(vault_dir, environment, password)
        except WatchError:
            updated = {}
        event = _diff_snapshots(environment, current, updated)
        if event.has_changes:
            callback(event)
            events_emitted += 1
            current = updated

    return events_emitted
