"""Group management: organize environment variables into named groups."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.store import load_vault, save_vault, _vault_path


class GroupError(Exception):
    """Raised when a group operation fails."""


def _group_path(vault_dir: str) -> Path:
    return Path(vault_dir) / ".groups.json"


def _load_groups(vault_dir: str) -> Dict[str, List[str]]:
    path = _group_path(vault_dir)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def _save_groups(vault_dir: str, groups: Dict[str, List[str]]) -> None:
    path = _group_path(vault_dir)
    with path.open("w") as fh:
        json.dump(groups, fh, indent=2)


def add_to_group(
    vault_dir: str,
    environment: str,
    group: str,
    keys: List[str],
    password: str,
) -> List[str]:
    """Add keys to a group. Returns the updated sorted key list for the group."""
    vault = load_vault(vault_dir, environment, password)
    missing = [k for k in keys if k not in vault]
    if missing:
        raise GroupError(f"Keys not found in '{environment}': {missing}")

    groups = _load_groups(vault_dir)
    group_key = f"{environment}:{group}"
    existing = set(groups.get(group_key, []))
    existing.update(keys)
    groups[group_key] = sorted(existing)
    _save_groups(vault_dir, groups)
    return groups[group_key]


def remove_from_group(
    vault_dir: str, environment: str, group: str, keys: List[str]
) -> List[str]:
    """Remove keys from a group. Returns remaining keys."""
    groups = _load_groups(vault_dir)
    group_key = f"{environment}:{group}"
    if group_key not in groups:
        raise GroupError(f"Group '{group}' not found in environment '{environment}'")
    updated = [k for k in groups[group_key] if k not in keys]
    groups[group_key] = updated
    _save_groups(vault_dir, groups)
    return updated


def list_groups(vault_dir: str, environment: Optional[str] = None) -> Dict[str, List[str]]:
    """Return all groups, optionally filtered by environment."""
    groups = _load_groups(vault_dir)
    if environment is None:
        return groups
    prefix = f"{environment}:"
    return {k: v for k, v in groups.items() if k.startswith(prefix)}


def get_group_keys(
    vault_dir: str, environment: str, group: str
) -> List[str]:
    """Return the keys belonging to a group."""
    groups = _load_groups(vault_dir)
    group_key = f"{environment}:{group}"
    if group_key not in groups:
        raise GroupError(f"Group '{group}' not found in environment '{environment}'")
    return groups[group_key]
