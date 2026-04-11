"""Clone an environment to a new vault directory (project)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from envault.store import load_vault, save_vault


class CloneError(Exception):
    """Raised when a clone operation fails."""


def clone_env(
    src_vault_dir: Path,
    src_env: str,
    src_password: str,
    dst_vault_dir: Path,
    dst_env: Optional[str],
    dst_password: str,
    *,
    overwrite: bool = False,
) -> int:
    """Clone *src_env* from *src_vault_dir* into *dst_vault_dir*.

    Parameters
    ----------
    src_vault_dir:  Directory that contains the source vault file.
    src_env:        Name of the environment to clone.
    src_password:   Master password for the source vault.
    dst_vault_dir:  Directory that will contain the destination vault file.
    dst_env:        Name of the environment in the destination vault.
                    Defaults to *src_env* when ``None``.
    dst_password:   Master password for the destination vault.
    overwrite:      When ``True``, existing keys in *dst_env* are replaced.

    Returns
    -------
    int
        Number of secrets written.

    Raises
    ------
    CloneError
        If *src_env* does not exist in the source vault, or if *dst_env*
        already exists and *overwrite* is ``False``.
    """
    src_data = load_vault(src_vault_dir, src_password)

    if src_env not in src_data:
        raise CloneError(f"Source environment '{src_env}' not found.")

    target_env = dst_env if dst_env is not None else src_env

    # Load or initialise destination vault.
    try:
        dst_data = load_vault(dst_vault_dir, dst_password)
    except FileNotFoundError:
        dst_data = {}

    if target_env in dst_data and not overwrite:
        raise CloneError(
            f"Destination environment '{target_env}' already exists. "
            "Pass overwrite=True to replace it."
        )

    dst_data[target_env] = dict(src_data[src_env])
    save_vault(dst_vault_dir, dst_password, dst_data)
    return len(dst_data[target_env])
