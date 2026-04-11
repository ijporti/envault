"""expire.py — bulk-expire secrets by environment or tag, removing TTL entries that have passed."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envault.store import load_vault, save_vault
from envault.ttl import _ttl_path, TTLEntry, is_expired


class ExpireError(Exception):
    """Raised when expiration cannot be completed."""


@dataclass
class ExpireResult:
    environment: str
    removed_keys: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)

    @property
    def total_removed(self) -> int:
        return len(self.removed_keys)


def expire_env(
    vault_dir: str,
    environment: str,
    password: str,
    *,
    dry_run: bool = False,
) -> ExpireResult:
    """Remove all secrets whose TTL has expired from *environment*.

    If *dry_run* is True the vault and TTL registry are left untouched and the
    result only reports what *would* be removed.
    """
    result = ExpireResult(environment=environment)

    ttl_file = Path(_ttl_path(vault_dir, environment))
    if not ttl_file.exists():
        return result

    import json

    raw = json.loads(ttl_file.read_text())
    entries: dict[str, TTLEntry] = {
        k: TTLEntry(**v) for k, v in raw.items()
    }

    expired_keys = [k for k, e in entries.items() if is_expired(e)]
    if not expired_keys:
        return result

    secrets = load_vault(vault_dir, environment, password)

    for key in expired_keys:
        if key in secrets:
            result.removed_keys.append(key)
            if not dry_run:
                del secrets[key]
        else:
            result.skipped_keys.append(key)

    if not dry_run:
        save_vault(vault_dir, environment, secrets, password)
        for key in expired_keys:
            entries.pop(key, None)
        updated = {k: v.__dict__ for k, v in entries.items()}
        ttl_file.write_text(json.dumps(updated, indent=2))

    return result
