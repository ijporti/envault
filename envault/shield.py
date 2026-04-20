"""Shield: mark specific keys as immutable to prevent accidental overwrites."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envault.store import load_vault


class ShieldError(Exception):
    """Raised when a shield operation fails."""


@dataclass
class ShieldResult:
    environment: str
    shielded_keys: List[str] = field(default_factory=list)
    already_shielded: List[str] = field(default_factory=list)

    @property
    def total_shielded(self) -> int:
        return len(self.shielded_keys)


def _shield_path(vault_dir: Path) -> Path:
    return vault_dir / ".shield_registry.json"


def _load_shields(vault_dir: Path) -> dict:
    path = _shield_path(vault_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_shields(vault_dir: Path, data: dict) -> None:
    _shield_path(vault_dir).write_text(json.dumps(data, indent=2))


def shield_keys(
    vault_dir: Path, environment: str, keys: List[str], password: str
) -> ShieldResult:
    """Mark *keys* in *environment* as immutable."""
    vault = load_vault(vault_dir, environment, password)
    missing = [k for k in keys if k not in vault]
    if missing:
        raise ShieldError(
            f"Keys not found in '{environment}': {', '.join(missing)}"
        )

    registry = _load_shields(vault_dir)
    env_shields: List[str] = registry.get(environment, [])

    result = ShieldResult(environment=environment)
    for key in keys:
        if key in env_shields:
            result.already_shielded.append(key)
        else:
            env_shields.append(key)
            result.shielded_keys.append(key)

    registry[environment] = sorted(set(env_shields))
    _save_shields(vault_dir, registry)
    return result


def unshield_keys(
    vault_dir: Path, environment: str, keys: List[str]
) -> List[str]:
    """Remove shield from *keys* in *environment*. Returns unshielded keys."""
    registry = _load_shields(vault_dir)
    env_shields: List[str] = registry.get(environment, [])
    removed = [k for k in keys if k in env_shields]
    registry[environment] = sorted(set(env_shields) - set(keys))
    _save_shields(vault_dir, registry)
    return removed


def is_shielded(vault_dir: Path, environment: str, key: str) -> bool:
    """Return True if *key* is shielded in *environment*."""
    return key in _load_shields(vault_dir).get(environment, [])


def list_shields(vault_dir: Path, environment: str) -> List[str]:
    """Return all shielded keys for *environment*."""
    return list(_load_shields(vault_dir).get(environment, []))
