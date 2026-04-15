"""Bookmark frequently accessed keys for quick retrieval."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.store import load_vault


class BookmarkError(Exception):
    """Raised when a bookmark operation fails."""


def _bookmark_path(vault_dir: Path) -> Path:
    return vault_dir / ".bookmarks.json"


def _load_bookmarks(vault_dir: Path) -> Dict[str, str]:
    p = _bookmark_path(vault_dir)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_bookmarks(vault_dir: Path, data: Dict[str, str]) -> None:
    _bookmark_path(vault_dir).write_text(json.dumps(data, indent=2))


@dataclass
class BookmarkEntry:
    alias: str
    environment: str
    key: str

    def __str__(self) -> str:
        return f"{self.alias} -> {self.environment}/{self.key}"


def add_bookmark(
    vault_dir: Path,
    alias: str,
    environment: str,
    key: str,
    password: str,
) -> BookmarkEntry:
    """Bookmark *key* in *environment* under *alias*."""
    if not alias:
        raise BookmarkError("Alias must not be empty.")
    vault = load_vault(vault_dir, environment, password)
    if key not in vault:
        raise BookmarkError(f"Key '{key}' not found in environment '{environment}'.")
    data = _load_bookmarks(vault_dir)
    data[alias] = f"{environment}/{key}"
    _save_bookmarks(vault_dir, data)
    return BookmarkEntry(alias=alias, environment=environment, key=key)


def remove_bookmark(vault_dir: Path, alias: str) -> bool:
    """Remove a bookmark by *alias*. Returns True if it existed."""
    data = _load_bookmarks(vault_dir)
    if alias not in data:
        return False
    del data[alias]
    _save_bookmarks(vault_dir, data)
    return True


def resolve_bookmark(
    vault_dir: Path, alias: str, password: str
) -> Optional[str]:
    """Return the secret value for *alias*, or None if alias unknown."""
    data = _load_bookmarks(vault_dir)
    if alias not in data:
        return None
    environment, key = data[alias].split("/", 1)
    vault = load_vault(vault_dir, environment, password)
    return vault.get(key)


def list_bookmarks(vault_dir: Path) -> List[BookmarkEntry]:
    """Return all registered bookmarks."""
    data = _load_bookmarks(vault_dir)
    entries: List[BookmarkEntry] = []
    for alias, ref in sorted(data.items()):
        environment, key = ref.split("/", 1)
        entries.append(BookmarkEntry(alias=alias, environment=environment, key=key))
    return entries
