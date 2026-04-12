"""Environment inheritance — let one environment fall back to another for missing keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.store import load_vault, save_vault


class InheritError(Exception):
    """Raised when an inheritance operation fails."""


@dataclass
class InheritResult:
    environment: str
    parent: str
    keys_inherited: List[str] = field(default_factory=list)
    keys_skipped: List[str] = field(default_factory=list)

    @property
    def total_inherited(self) -> int:
        return len(self.keys_inherited)

    @property
    def total_skipped(self) -> int:
        return len(self.keys_skipped)


def resolve_env(
    vault_dir: str,
    environment: str,
    parent: str,
    password: str,
) -> Dict[str, str]:
    """Return a merged view of *environment* with missing keys filled from *parent*.

    Keys present in *environment* are never overwritten.  The result is an
    in-memory dict and the vault is **not** modified.
    """
    parent_data = load_vault(vault_dir, parent, password)
    child_data = load_vault(vault_dir, environment, password)

    merged: Dict[str, str] = {**parent_data}
    merged.update(child_data)          # child wins
    return merged


def apply_inheritance(
    vault_dir: str,
    environment: str,
    parent: str,
    password: str,
    overwrite: bool = False,
) -> InheritResult:
    """Copy missing keys from *parent* into *environment* and persist the vault.

    Parameters
    ----------
    overwrite:
        When *True*, parent values overwrite existing child values.
    """
    if environment == parent:
        raise InheritError("environment and parent must differ")

    parent_data = load_vault(vault_dir, parent, password)
    try:
        child_data = load_vault(vault_dir, environment, password)
    except FileNotFoundError:
        child_data = {}

    result = InheritResult(environment=environment, parent=parent)

    updated = dict(child_data)
    for key, value in parent_data.items():
        if key not in updated or overwrite:
            updated[key] = value
            result.keys_inherited.append(key)
        else:
            result.keys_skipped.append(key)

    save_vault(vault_dir, environment, updated, password)
    return result
