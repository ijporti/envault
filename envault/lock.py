"""Lock/unlock environments to prevent accidental writes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from envault.store import _vault_path


class LockError(Exception):
    """Raised when a lock operation fails."""


def _lock_path(vault_dir: str) -> Path:
    return Path(vault_dir) / ".locks.json"


def _load_locks(vault_dir: str) -> List[str]:
    p = _lock_path(vault_dir)
    if not p.exists():
        return []
    return json.loads(p.read_text())


def _save_locks(vault_dir: str, locked: List[str]) -> None:
    _lock_path(vault_dir).write_text(json.dumps(sorted(set(locked)), indent=2))


def lock_env(vault_dir: str, environment: str) -> bool:
    """Lock *environment*. Returns True if newly locked, False if already locked."""
    vault_file = _vault_path(vault_dir, environment)
    if not vault_file.exists():
        raise LockError(f"Environment '{environment}' does not exist.")
    locked = _load_locks(vault_dir)
    if environment in locked:
        return False
    locked.append(environment)
    _save_locks(vault_dir, locked)
    return True


def unlock_env(vault_dir: str, environment: str) -> bool:
    """Unlock *environment*. Returns True if unlocked, False if was not locked."""
    locked = _load_locks(vault_dir)
    if environment not in locked:
        return False
    locked.remove(environment)
    _save_locks(vault_dir, locked)
    return True


def is_locked(vault_dir: str, environment: str) -> bool:
    """Return True if *environment* is currently locked."""
    return environment in _load_locks(vault_dir)


def list_locked(vault_dir: str) -> List[str]:
    """Return a sorted list of all locked environments."""
    return sorted(_load_locks(vault_dir))


def assert_unlocked(vault_dir: str, environment: str) -> None:
    """Raise LockError if *environment* is locked."""
    if is_locked(vault_dir, environment):
        raise LockError(
            f"Environment '{environment}' is locked. Unlock it before making changes."
        )
