"""Rename a key within an environment or across all environments."""

from __future__ import annotations

from typing import Optional

from .store import load_vault, save_vault


class RenameError(Exception):
    """Raised when a rename operation fails."""


def rename_key(
    vault_dir: str,
    environment: str,
    old_key: str,
    new_key: str,
    password: str,
    overwrite: bool = False,
) -> bool:
    """Rename *old_key* to *new_key* inside *environment*.

    Returns True if the key was renamed, False if *old_key* did not exist.
    Raises RenameError if *new_key* already exists and *overwrite* is False.
    """
    vault = load_vault(vault_dir, environment, password)

    if old_key not in vault:
        return False

    if new_key in vault and not overwrite:
        raise RenameError(
            f"Key '{new_key}' already exists in environment '{environment}'. "
            "Use overwrite=True to replace it."
        )

    vault[new_key] = vault.pop(old_key)
    save_vault(vault_dir, environment, vault, password)
    return True


def rename_key_all_envs(
    vault_dir: str,
    old_key: str,
    new_key: str,
    password: str,
    overwrite: bool = False,
) -> dict[str, bool]:
    """Rename *old_key* to *new_key* in every environment that contains it.

    Returns a mapping of environment name -> whether the rename was applied.
    """
    from .store import list_environments

    results: dict[str, bool] = {}
    for env in list_environments(vault_dir):
        results[env] = rename_key(
            vault_dir, env, old_key, new_key, password, overwrite=overwrite
        )
    return results
