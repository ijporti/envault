"""Snapshot support: capture and restore full environment state."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from envault.store import _vault_path, load_vault, save_vault


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


@dataclass
class Snapshot:
    label: str
    created_at: str
    environments: Dict[str, Dict[str, str]]
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "created_at": self.created_at,
            "environments": self.environments,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            label=data["label"],
            created_at=data["created_at"],
            environments=data["environments"],
            tags=data.get("tags", []),
        )


def _snapshot_path(vault_dir: str) -> str:
    import os
    return os.path.join(vault_dir, "snapshots.json")


def create_snapshot(
    vault_dir: str,
    password: str,
    label: str,
    tags: Optional[List[str]] = None,
) -> Snapshot:
    """Capture the current state of all environments into a named snapshot."""
    from envault.store import list_environments

    envs = list_environments(vault_dir)
    environments: Dict[str, Dict[str, str]] = {}
    for env in envs:
        environments[env] = load_vault(vault_dir, env, password)

    snap = Snapshot(
        label=label,
        created_at=datetime.now(timezone.utc).isoformat(),
        environments=environments,
        tags=tags or [],
    )
    _save_snapshot(vault_dir, snap)
    return snap


def restore_snapshot(vault_dir: str, password: str, label: str) -> int:
    """Restore all environments from a named snapshot. Returns env count."""
    snap = get_snapshot(vault_dir, label)
    if snap is None:
        raise SnapshotError(f"Snapshot '{label}' not found.")
    for env, secrets in snap.environments.items():
        save_vault(vault_dir, env, password, secrets)
    return len(snap.environments)


def list_snapshots(vault_dir: str) -> List[Snapshot]:
    """Return all stored snapshots sorted by creation time (newest first)."""
    data = _load_all(vault_dir)
    snaps = [Snapshot.from_dict(d) for d in data]
    return sorted(snaps, key=lambda s: s.created_at, reverse=True)


def get_snapshot(vault_dir: str, label: str) -> Optional[Snapshot]:
    for snap in list_snapshots(vault_dir):
        if snap.label == label:
            return snap
    return None


def delete_snapshot(vault_dir: str, label: str) -> bool:
    """Delete a snapshot by label. Returns True if deleted, False if not found."""
    data = _load_all(vault_dir)
    new_data = [d for d in data if d["label"] != label]
    if len(new_data) == len(data):
        return False
    path = _snapshot_path(vault_dir)
    with open(path, "w") as fh:
        json.dump(new_data, fh, indent=2)
    return True


# ── internal helpers ──────────────────────────────────────────────────────────

def _load_all(vault_dir: str) -> list:
    import os
    path = _snapshot_path(vault_dir)
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        return json.load(fh)


def _save_snapshot(vault_dir: str, snap: Snapshot) -> None:
    data = _load_all(vault_dir)
    if any(d["label"] == snap.label for d in data):
        raise SnapshotError(f"A snapshot named '{snap.label}' already exists.")
    data.append(snap.to_dict())
    path = _snapshot_path(vault_dir)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)
