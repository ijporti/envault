"""mask.py — Bulk masking/unmasking of environment variable keys in a vault."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envault.store import load_vault, save_vault


class MaskError(Exception):
    """Raised when a masking operation fails."""


@dataclass
class MaskResult:
    environment: str
    masked: List[str] = field(default_factory=list)
    unmasked: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def total_masked(self) -> int:
        return len(self.masked)

    @property
    def total_unmasked(self) -> int:
        return len(self.unmasked)


_MASK_PREFIX = "__masked__"


def mask_keys(
    vault_dir: str,
    environment: str,
    password: str,
    keys: Optional[List[str]] = None,
) -> MaskResult:
    """Mark the given keys (or all keys) in *environment* as masked.

    Masking is stored as a metadata prefix in the encrypted value so that
    export / redact tooling can honour it without re-encrypting.
    """
    vault = load_vault(vault_dir, environment, password)
    result = MaskResult(environment=environment)

    target_keys = keys if keys is not None else list(vault.keys())

    for key in target_keys:
        if key not in vault:
            result.skipped.append(key)
            continue
        value = vault[key]
        if value.startswith(_MASK_PREFIX):
            result.skipped.append(key)
        else:
            vault[key] = _MASK_PREFIX + value
            result.masked.append(key)

    save_vault(vault_dir, environment, password, vault)
    return result


def unmask_keys(
    vault_dir: str,
    environment: str,
    password: str,
    keys: Optional[List[str]] = None,
) -> MaskResult:
    """Remove the masked marker from the given keys (or all keys)."""
    vault = load_vault(vault_dir, environment, password)
    result = MaskResult(environment=environment)

    target_keys = keys if keys is not None else list(vault.keys())

    for key in target_keys:
        if key not in vault:
            result.skipped.append(key)
            continue
        value = vault[key]
        if value.startswith(_MASK_PREFIX):
            vault[key] = value[len(_MASK_PREFIX):]
            result.unmasked.append(key)
        else:
            result.skipped.append(key)

    save_vault(vault_dir, environment, password, vault)
    return result


def is_masked(value: str) -> bool:
    """Return True if *value* carries the masked marker."""
    return value.startswith(_MASK_PREFIX)
