"""Simple append-only audit log for envault operations."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_DEFAULT_LOG_NAME = "audit.log"


def _log_path(vault_dir: Optional[Path] = None) -> Path:
    base = vault_dir or Path(os.environ.get("ENVAULT_DIR", Path.home() / ".envault"))
    return base / _DEFAULT_LOG_NAME


def record(
    action: str,
    env: str,
    key: Optional[str] = None,
    extra: Optional[dict] = None,
    vault_dir: Optional[Path] = None,
) -> None:
    """Append a JSON audit entry to the log file.

    Parameters
    ----------
    action:
        Short verb describing the operation (e.g. 'set', 'get', 'rotate').
    env:
        The environment name that was affected.
    key:
        Optional secret key that was accessed or modified.
    extra:
        Any additional metadata to store alongside the entry.
    vault_dir:
        Override the directory that contains the audit log.
    """
    entry: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "env": env,
    }
    if key is not None:
        entry["key"] = key
    if extra:
        entry.update(extra)

    log_file = _log_path(vault_dir)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def read_log(vault_dir: Optional[Path] = None) -> list[dict]:
    """Return all audit entries as a list of dicts (oldest first)."""
    log_file = _log_path(vault_dir)
    if not log_file.exists():
        return []
    entries = []
    with log_file.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries
