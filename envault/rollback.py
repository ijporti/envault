"""Rollback an environment to a previous snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from envault.snapshot import Snapshot, list_snapshots, restore_snapshot
from envault.store import load_vault, save_vault
from envault.audit import record


class RollbackError(Exception):
    """Raised when a rollback operation fails."""


@dataclass
class RollbackResult:
    environment: str
    snapshot_id: str
    keys_restored: int
    previous_key_count: int

    @property
    def net_change(self) -> int:
        return self.keys_restored - self.previous_key_count


def rollback_env(
    vault_dir: str,
    environment: str,
    snapshot_id: str,
    password: str,
    *,
    dry_run: bool = False,
) -> RollbackResult:
    """Restore *environment* to the state captured in *snapshot_id*.

    Parameters
    ----------
    vault_dir:    Root directory of the vault.
    environment:  Name of the environment to roll back.
    snapshot_id:  ID of the snapshot to restore from.
    password:     Master password used to encrypt/decrypt the vault.
    dry_run:      If True, compute the result without writing any files.
    """
    snapshots: List[Snapshot] = list_snapshots(vault_dir, environment)
    matching = [s for s in snapshots if s.snapshot_id == snapshot_id]
    if not matching:
        raise RollbackError(
            f"Snapshot '{snapshot_id}' not found for environment '{environment}'."
        )
    snapshot = matching[0]

    try:
        current_vault = load_vault(vault_dir, environment, password)
    except FileNotFoundError:
        current_vault = {}

    previous_key_count = len(current_vault)
    keys_restored = len(snapshot.secrets)

    if not dry_run:
        restore_snapshot(vault_dir, environment, snapshot_id, password)
        record(
            vault_dir,
            action="rollback",
            environment=environment,
            detail=f"snapshot={snapshot_id} keys_restored={keys_restored}",
        )

    return RollbackResult(
        environment=environment,
        snapshot_id=snapshot_id,
        keys_restored=keys_restored,
        previous_key_count=previous_key_count,
    )
