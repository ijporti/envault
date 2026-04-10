"""Key rotation utilities for re-encrypting vault contents with a new password."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault.store import load_vault, save_vault, _vault_path


class RotationError(Exception):
    """Raised when key rotation fails."""


def rotate_key(
    env: str,
    old_password: str,
    new_password: str,
    vault_dir: Optional[Path] = None,
) -> int:
    """Re-encrypt all secrets in *env* with *new_password*.

    Returns the number of secrets that were re-encrypted.

    Raises
    ------
    RotationError
        If the old password is wrong or the vault cannot be read/written.
    """
    try:
        secrets = load_vault(env, old_password, vault_dir=vault_dir)
    except Exception as exc:
        raise RotationError(
            f"Could not decrypt vault '{env}' with the supplied old password: {exc}"
        ) from exc

    count = len(secrets)

    try:
        save_vault(env, secrets, new_password, vault_dir=vault_dir)
    except Exception as exc:
        raise RotationError(
            f"Could not save re-encrypted vault '{env}': {exc}"
        ) from exc

    return count


def rotate_all_keys(
    old_password: str,
    new_password: str,
    vault_dir: Optional[Path] = None,
) -> dict[str, int]:
    """Rotate the key for every environment found in *vault_dir*.

    Returns a mapping of environment name → number of secrets rotated.
    """
    from envault.store import list_environments  # local import to avoid cycles

    results: dict[str, int] = {}
    for env in list_environments(vault_dir=vault_dir):
        results[env] = rotate_key(
            env, old_password, new_password, vault_dir=vault_dir
        )
    return results
