"""Compare two environments and report value-level differences."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .store import load_vault


class CompareError(Exception):
    """Raised when a comparison cannot be completed."""


@dataclass
class CompareResult:
    source_env: str
    target_env: str
    only_in_source: List[str] = field(default_factory=list)
    only_in_target: List[str] = field(default_factory=list)
    same_value: List[str] = field(default_factory=list)
    different_value: List[str] = field(default_factory=list)

    @property
    def is_identical(self) -> bool:
        return (
            not self.only_in_source
            and not self.only_in_target
            and not self.different_value
        )

    @property
    def total_keys(self) -> int:
        return (
            len(self.only_in_source)
            + len(self.only_in_target)
            + len(self.same_value)
            + len(self.different_value)
        )


def compare_envs(
    vault_dir: str,
    source_env: str,
    target_env: str,
    password: str,
    keys: Optional[List[str]] = None,
) -> CompareResult:
    """Compare secrets between *source_env* and *target_env*.

    Parameters
    ----------
    vault_dir:
        Directory that contains the vault files.
    source_env:
        Name of the reference environment.
    target_env:
        Name of the environment to compare against.
    password:
        Master password used to decrypt both vaults.
    keys:
        Optional explicit list of keys to restrict the comparison to.

    Returns
    -------
    CompareResult
    """
    src_vault: Dict[str, str] = load_vault(vault_dir, source_env, password)
    tgt_vault: Dict[str, str] = load_vault(vault_dir, target_env, password)

    if keys is not None:
        src_vault = {k: v for k, v in src_vault.items() if k in keys}
        tgt_vault = {k: v for k, v in tgt_vault.items() if k in keys}

    src_keys = set(src_vault)
    tgt_keys = set(tgt_vault)
    common = src_keys & tgt_keys

    result = CompareResult(source_env=source_env, target_env=target_env)
    result.only_in_source = sorted(src_keys - tgt_keys)
    result.only_in_target = sorted(tgt_keys - src_keys)

    for key in sorted(common):
        if src_vault[key] == tgt_vault[key]:
            result.same_value.append(key)
        else:
            result.different_value.append(key)

    return result
