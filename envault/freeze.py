"""freeze.py – snapshot an environment into a read-only frozen copy.

A frozen environment is stored as a separate vault entry whose name is
prefixed with ``frozen/`` and whose keys can be read but not overwritten
by normal ``set`` operations without explicitly thawing it first.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.store import load_vault, save_vault


class FreezeError(Exception):
    """Raised when a freeze/thaw operation cannot be completed."""


@dataclass
class FreezeResult:
    source_env: str
    frozen_env: str
    keys_frozen: List[str] = field(default_factory=list)

    @property
    def total_frozen(self) -> int:
        return len(self.keys_frozen)


def _frozen_name(env: str) -> str:
    """Return the canonical frozen-environment name for *env*."""
    if env.startswith("frozen/"):
        return env
    return f"frozen/{env}"


def freeze_env(
    vault_dir: str,
    env: str,
    password: str,
    *,
    overwrite: bool = False,
) -> FreezeResult:
    """Copy *env* into a frozen snapshot.  Raises if frozen copy exists and
    *overwrite* is False."""
    data = load_vault(vault_dir, password)
    if env not in data:
        raise FreezeError(f"Environment '{env}' does not exist.")

    frozen_name = _frozen_name(env)
    if frozen_name in data and not overwrite:
        raise FreezeError(
            f"Frozen environment '{frozen_name}' already exists. "
            "Pass overwrite=True to replace it."
        )

    source_secrets: Dict[str, str] = data[env]
    data[frozen_name] = dict(source_secrets)
    save_vault(vault_dir, data, password)

    return FreezeResult(
        source_env=env,
        frozen_env=frozen_name,
        keys_frozen=sorted(source_secrets.keys()),
    )


def thaw_env(
    vault_dir: str,
    env: str,
    password: str,
) -> List[str]:
    """Delete the frozen snapshot for *env* and return the keys that were thawed."""
    data = load_vault(vault_dir, password)
    frozen_name = _frozen_name(env)
    if frozen_name not in data:
        raise FreezeError(f"No frozen environment found for '{env}'.")

    keys = sorted(data[frozen_name].keys())
    del data[frozen_name]
    save_vault(vault_dir, data, password)
    return keys


def is_frozen(vault_dir: str, env: str, password: str) -> bool:
    """Return True if a frozen snapshot exists for *env*."""
    data = load_vault(vault_dir, password)
    return _frozen_name(env) in data
