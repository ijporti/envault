"""Promote environment variables from one environment to another.

Typical usage: promote secrets from 'staging' to 'production'.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envault.store import load_vault, save_vault


class PromoteError(Exception):
    """Raised when a promotion operation fails."""


@dataclass
class PromoteResult:
    promoted: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)

    @property
    def total_promoted(self) -> int:
        return len(self.promoted) + len(self.overwritten)


def promote_env(
    vault_dir: str,
    source_env: str,
    target_env: str,
    password: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
) -> PromoteResult:
    """Copy secrets from *source_env* into *target_env*.

    Args:
        vault_dir:  Directory that contains the vault files.
        source_env: Name of the source environment.
        target_env: Name of the destination environment.
        password:   Master password (must be the same for both environments).
        keys:       Optional allow-list of keys to promote.  ``None`` means all.
        overwrite:  When *True*, existing keys in the target are overwritten.

    Returns:
        A :class:`PromoteResult` describing what happened.

    Raises:
        PromoteError: If *source_env* does not exist or *source_env* == *target_env*.
    """
    if source_env == target_env:
        raise PromoteError("Source and target environments must differ.")

    try:
        source_secrets = load_vault(vault_dir, source_env, password)
    except FileNotFoundError:
        raise PromoteError(f"Source environment '{source_env}' does not exist.")

    try:
        target_secrets = load_vault(vault_dir, target_env, password)
    except FileNotFoundError:
        target_secrets = {}

    candidates = keys if keys is not None else list(source_secrets.keys())

    result = PromoteResult()
    for key in candidates:
        if key not in source_secrets:
            result.skipped.append(key)
            continue
        if key in target_secrets and not overwrite:
            result.skipped.append(key)
            continue
        existed = key in target_secrets
        target_secrets[key] = source_secrets[key]
        if existed:
            result.overwritten.append(key)
        else:
            result.promoted.append(key)

    save_vault(vault_dir, target_env, password, target_secrets)
    return result
