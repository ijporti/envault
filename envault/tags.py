"""Tag management for envault secrets.

Allows assigning arbitrary string tags to keys within an environment,
enabling grouping, filtering, and bulk operations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class TagError(Exception):
    """Raised when a tagging operation fails."""


def _tag_path(vault_dir: Path, environment: str) -> Path:
    """Return the path to the tag registry for *environment*."""
    return vault_dir / environment / ".tags.json"


def _load_registry(vault_dir: Path, environment: str) -> Dict[str, List[str]]:
    """Load the tag registry for *environment*, returning an empty dict if absent."""
    path = _tag_path(vault_dir, environment)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise TagError(f"Failed to read tag registry: {exc}") from exc


def _save_registry(
    vault_dir: Path, environment: str, registry: Dict[str, List[str]]
) -> None:
    """Persist *registry* to disk."""
    path = _tag_path(vault_dir, environment)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2, sort_keys=True), encoding="utf-8")


def add_tags(
    vault_dir: Path, environment: str, key: str, tags: List[str]
) -> List[str]:
    """Add *tags* to *key* in *environment*. Returns the updated tag list."""
    if not tags:
        raise TagError("At least one tag must be provided.")
    registry = _load_registry(vault_dir, environment)
    existing = set(registry.get(key, []))
    existing.update(tags)
    registry[key] = sorted(existing)
    _save_registry(vault_dir, environment, registry)
    return registry[key]


def remove_tags(
    vault_dir: Path, environment: str, key: str, tags: List[str]
) -> List[str]:
    """Remove *tags* from *key* in *environment*. Returns the updated tag list."""
    registry = _load_registry(vault_dir, environment)
    existing = set(registry.get(key, []))
    existing.difference_update(tags)
    if existing:
        registry[key] = sorted(existing)
    else:
        registry.pop(key, None)
    _save_registry(vault_dir, environment, registry)
    return sorted(existing)


def get_tags(vault_dir: Path, environment: str, key: str) -> List[str]:
    """Return the tags assigned to *key* in *environment*."""
    registry = _load_registry(vault_dir, environment)
    return registry.get(key, [])


def find_by_tag(
    vault_dir: Path, environment: str, tag: str
) -> List[str]:
    """Return all keys in *environment* that carry *tag*."""
    registry = _load_registry(vault_dir, environment)
    return sorted(k for k, tags in registry.items() if tag in tags)


def list_all_tags(vault_dir: Path, environment: str) -> Dict[str, List[str]]:
    """Return a copy of the full tag registry for *environment*."""
    return dict(_load_registry(vault_dir, environment))
