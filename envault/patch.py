"""Apply a partial update (patch) to an environment, modifying only specified keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.store import load_vault, save_vault


class PatchError(Exception):
    """Raised when a patch operation fails."""


@dataclass
class PatchResult:
    environment: str
    updated: List[str] = field(default_factory=list)
    added: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def total_changed(self) -> int:
        return len(self.updated) + len(self.added)


def patch_env(
    vault_dir: str,
    environment: str,
    password: str,
    patch: Dict[str, str],
    *,
    keys: Optional[List[str]] = None,
    add_new: bool = True,
) -> PatchResult:
    """Apply *patch* to *environment*, returning a PatchResult.

    Args:
        vault_dir:   Directory that contains the vault files.
        environment: Target environment name.
        password:    Vault password.
        patch:       Mapping of key -> new value to apply.
        keys:        If given, only these keys are considered from *patch*.
        add_new:     When True (default), keys absent from the environment are
                     added.  When False they are recorded in ``skipped``.
    """
    try:
        secrets = load_vault(vault_dir, environment, password)
    except FileNotFoundError:
        raise PatchError(f"Environment '{environment}' does not exist.")

    result = PatchResult(environment=environment)
    candidates = {k: v for k, v in patch.items() if keys is None or k in keys}

    for key, value in candidates.items():
        if key in secrets:
            secrets[key] = value
            result.updated.append(key)
        elif add_new:
            secrets[key] = value
            result.added.append(key)
        else:
            result.skipped.append(key)

    save_vault(vault_dir, environment, password, secrets)
    return result
