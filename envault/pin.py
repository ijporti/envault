"""Pin a secret to a specific value, preventing accidental overwrites."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.store import _vault_path


class PinError(Exception):
    """Raised when a pin operation fails."""


def _pin_path(vault_dir: str) -> Path:
    return Path(vault_dir) / ".pins.json"


def _load_pins(vault_dir: str) -> Dict[str, Dict[str, List[str]]]:
    """Load pin registry: {env: {key: [pinned_value_hash, ...]}}"""
    path = _pin_path(vault_dir)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_pins(vault_dir: str, data: Dict[str, Dict[str, List[str]]]) -> None:
    path = _pin_path(vault_dir)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def pin_key(vault_dir: str, environment: str, key: str) -> bool:
    """Mark *key* in *environment* as pinned.

    Returns True if the pin was newly added, False if it already existed.
    Raises PinError if the vault file for the environment does not exist.
    """
    vault_file = _vault_path(vault_dir, environment)
    if not vault_file.exists():
        raise PinError(f"Environment '{environment}' does not exist.")

    pins = _load_pins(vault_dir)
    env_pins = pins.setdefault(environment, [])
    if key in env_pins:
        return False
    env_pins.append(key)
    env_pins.sort()
    _save_pins(vault_dir, pins)
    return True


def unpin_key(vault_dir: str, environment: str, key: str) -> bool:
    """Remove a pin from *key* in *environment*.

    Returns True if the pin was removed, False if it was not pinned.
    """
    pins = _load_pins(vault_dir)
    env_pins = pins.get(environment, [])
    if key not in env_pins:
        return False
    env_pins.remove(key)
    if not env_pins:
        pins.pop(environment, None)
    _save_pins(vault_dir, pins)
    return True


def is_pinned(vault_dir: str, environment: str, key: str) -> bool:
    """Return True if *key* is pinned in *environment*."""
    pins = _load_pins(vault_dir)
    return key in pins.get(environment, [])


def list_pins(vault_dir: str, environment: Optional[str] = None) -> Dict[str, List[str]]:
    """Return all pinned keys, optionally filtered to a single environment."""
    pins = _load_pins(vault_dir)
    if environment is not None:
        return {environment: pins.get(environment, [])}
    return {env: keys for env, keys in pins.items() if keys}
