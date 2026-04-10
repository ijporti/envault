"""Copy secrets from one environment to another within a vault."""

from __future__ import annotations

from typing import Optional

from envault.store import load_vault, save_vault


class CopyError(Exception):
    """Raised when a copy operation fails."""


def copy_env(
    vault_dir: str,
    src_env: str,
    dst_env: str,
    password: str,
    *,
    overwrite: bool = False,
    keys: Optional[list[str]] = None,
) -> int:
    """Copy secrets from *src_env* to *dst_env*.

    Parameters
    ----------
    vault_dir:
        Directory that contains the vault files.
    src_env:
        Source environment name.
    dst_env:
        Destination environment name.
    password:
        Master password used to decrypt/re-encrypt the vault.
    overwrite:
        When *True*, existing keys in *dst_env* are overwritten.
        When *False* (default), a :class:`CopyError` is raised on conflict.
    keys:
        Optional list of specific keys to copy.  When *None* all keys are
        copied.

    Returns
    -------
    int
        Number of secrets actually copied.
    """
    vault = load_vault(vault_dir, password)

    if src_env not in vault:
        raise CopyError(f"Source environment '{src_env}' does not exist.")

    src_secrets: dict[str, str] = vault[src_env]
    dst_secrets: dict[str, str] = vault.setdefault(dst_env, {})

    to_copy = keys if keys is not None else list(src_secrets.keys())

    # Validate requested keys exist in source.
    missing = [k for k in to_copy if k not in src_secrets]
    if missing:
        raise CopyError(
            f"Keys not found in '{src_env}': {', '.join(sorted(missing))}"
        )

    # Check for conflicts when overwrite is disabled.
    if not overwrite:
        conflicts = [k for k in to_copy if k in dst_secrets]
        if conflicts:
            raise CopyError(
                f"Keys already exist in '{dst_env}' (use overwrite=True to "
                f"force): {', '.join(sorted(conflicts))}"
            )

    for key in to_copy:
        dst_secrets[key] = src_secrets[key]

    save_vault(vault_dir, vault, password)
    return len(to_copy)
