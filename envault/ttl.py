"""TTL (time-to-live) support for environment variable secrets."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.store import _vault_path, load_vault, save_vault


class TTLError(Exception):
    """Raised when a TTL operation fails."""


@dataclass
class TTLEntry:
    key: str
    environment: str
    expires_at: float  # Unix timestamp
    created_at: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        return time.time() >= self.expires_at

    def seconds_remaining(self) -> float:
        return max(0.0, self.expires_at - time.time())

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "environment": self.environment,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TTLEntry":
        return cls(
            key=data["key"],
            environment=data["environment"],
            expires_at=data["expires_at"],
            created_at=data["created_at"],
        )


def _ttl_path(vault_dir: Path) -> Path:
    return vault_dir / ".ttl.json"


def set_ttl(vault_dir: Path, environment: str, key: str, ttl_seconds: float) -> TTLEntry:
    """Attach a TTL to an existing secret key."""
    entries = _load_ttl_entries(vault_dir)
    # Remove any existing TTL for this key/env pair
    entries = [e for e in entries if not (e.key == key and e.environment == environment)]
    entry = TTLEntry(key=key, environment=environment, expires_at=time.time() + ttl_seconds)
    entries.append(entry)
    _save_ttl_entries(vault_dir, entries)
    return entry


def purge_expired(vault_dir: Path, password: str) -> List[str]:
    """Remove all expired keys from the vault and TTL registry. Returns list of removed keys."""
    entries = _load_ttl_entries(vault_dir)
    expired = [e for e in entries if e.is_expired()]
    if not expired:
        return []

    removed: List[str] = []
    for entry in expired:
        try:
            secrets = load_vault(vault_dir, entry.environment, password)
        except Exception:
            continue
        if entry.key in secrets:
            del secrets[entry.key]
            save_vault(vault_dir, entry.environment, secrets, password)
            removed.append(f"{entry.environment}/{entry.key}")

    surviving = [e for e in entries if not e.is_expired()]
    _save_ttl_entries(vault_dir, surviving)
    return removed


def list_ttl(vault_dir: Path, environment: Optional[str] = None) -> List[TTLEntry]:
    """Return TTL entries, optionally filtered by environment."""
    entries = _load_ttl_entries(vault_dir)
    if environment:
        entries = [e for e in entries if e.environment == environment]
    return entries


def _load_ttl_entries(vault_dir: Path) -> List[TTLEntry]:
    path = _ttl_path(vault_dir)
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    return [TTLEntry.from_dict(d) for d in data]


def _save_ttl_entries(vault_dir: Path, entries: List[TTLEntry]) -> None:
    path = _ttl_path(vault_dir)
    path.write_text(json.dumps([e.to_dict() for e in entries], indent=2))
