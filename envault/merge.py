"""Merge environment variables from one or more source environments into a target."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.store import load_vault, save_vault


class MergeError(Exception):
    """Raised when a merge operation cannot be completed."""


@dataclass
class MergeResult:
    target_env: str
    sources: List[str]
    added: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def total_applied(self) -> int:
        return len(self.added) + len(self.overwritten)


def merge_envs(
    vault_dir: str,
    password: str,
    sources: List[str],
    target: str,
    overwrite: bool = False,
    keys: Optional[List[str]] = None,
) -> MergeResult:
    """Merge variables from *sources* into *target*.

    Args:
        vault_dir: Directory that contains the vault files.
        password: Master password used to decrypt/encrypt vaults.
        sources: Ordered list of source environment names (later entries win).
        target: Destination environment name.
        overwrite: When *True*, existing keys in *target* are overwritten.
        keys: Optional allowlist of keys to merge; all keys merged when *None*.

    Returns:
        A :class:`MergeResult` describing what changed.
    """
    if not sources:
        raise MergeError("At least one source environment must be provided.")

    vault = load_vault(vault_dir, password)

    for src in sources:
        if src not in vault:
            raise MergeError(f"Source environment '{src}' does not exist.")

    if target not in vault:
        vault[target] = {}

    result = MergeResult(target_env=target, sources=list(sources))
    target_data: Dict[str, str] = vault[target]

    # Build merged view from sources (last source wins for duplicate keys)
    merged: Dict[str, str] = {}
    for src in sources:
        merged.update(vault[src])

    if keys is not None:
        merged = {k: v for k, v in merged.items() if k in keys}

    for key, value in merged.items():
        if key in target_data:
            if overwrite:
                target_data[key] = value
                result.overwritten.append(key)
            else:
                result.skipped.append(key)
        else:
            target_data[key] = value
            result.added.append(key)

    vault[target] = target_data
    save_vault(vault_dir, password, vault)
    return result
