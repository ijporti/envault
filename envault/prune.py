"""Prune stale or duplicate keys from a vault environment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from envault.store import load_vault, save_vault


class PruneError(Exception):
    """Raised when pruning cannot be completed."""


@dataclass
class PruneResult:
    environment: str
    removed_keys: list[str] = field(default_factory=list)
    kept_keys: list[str] = field(default_factory=list)

    @property
    def total_removed(self) -> int:
        return len(self.removed_keys)

    @property
    def total_kept(self) -> int:
        return len(self.kept_keys)


def prune_keys(
    vault_dir: str,
    environment: str,
    password: str,
    keys_to_remove: Iterable[str],
) -> PruneResult:
    """Remove a specific set of keys from *environment*.

    Returns a :class:`PruneResult` describing what was removed and what
    remained.  Raises :class:`PruneError` if the environment does not exist.
    """
    try:
        secrets = load_vault(vault_dir, environment, password)
    except FileNotFoundError:
        raise PruneError(f"Environment '{environment}' does not exist.")

    to_remove = set(keys_to_remove)
    result = PruneResult(environment=environment)

    updated: dict[str, str] = {}
    for key, value in secrets.items():
        if key in to_remove:
            result.removed_keys.append(key)
        else:
            updated[key] = value
            result.kept_keys.append(key)

    save_vault(vault_dir, environment, password, updated)
    return result


def prune_empty_values(
    vault_dir: str,
    environment: str,
    password: str,
) -> PruneResult:
    """Remove all keys whose decrypted value is an empty string."""
    try:
        secrets = load_vault(vault_dir, environment, password)
    except FileNotFoundError:
        raise PruneError(f"Environment '{environment}' does not exist.")

    empty_keys = [k for k, v in secrets.items() if v == ""]
    return prune_keys(vault_dir, environment, password, empty_keys)
