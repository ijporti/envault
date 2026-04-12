"""Alias management for environment variable keys.

Allows creating short aliases that map to full key names within an environment.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.store import load_vault, _vault_path


class AliasError(Exception):
    """Raised when an alias operation fails."""


def _alias_path(vault_dir: Path) -> Path:
    return vault_dir / "aliases.json"


def _load_aliases(vault_dir: Path) -> Dict[str, Dict[str, str]]:
    """Load alias registry; returns {env: {alias: real_key}}."""
    path = _alias_path(vault_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_aliases(vault_dir: Path, registry: Dict[str, Dict[str, str]]) -> None:
    _alias_path(vault_dir).write_text(json.dumps(registry, indent=2))


def add_alias(
    vault_dir: Path,
    environment: str,
    alias: str,
    real_key: str,
    password: str,
) -> str:
    """Register *alias* -> *real_key* for *environment*.

    Returns the real key the alias points to.
    Raises AliasError if the environment or real_key does not exist.
    """
    vault = load_vault(vault_dir, environment, password)
    if real_key not in vault:
        raise AliasError(f"Key '{real_key}' not found in environment '{environment}'")

    registry = _load_aliases(vault_dir)
    registry.setdefault(environment, {})[alias] = real_key
    _save_aliases(vault_dir, registry)
    return real_key


def resolve_alias(
    vault_dir: Path,
    environment: str,
    alias: str,
) -> Optional[str]:
    """Return the real key for *alias*, or None if not registered."""
    registry = _load_aliases(vault_dir)
    return registry.get(environment, {}).get(alias)


def remove_alias(vault_dir: Path, environment: str, alias: str) -> bool:
    """Remove *alias* from *environment*. Returns True if it existed."""
    registry = _load_aliases(vault_dir)
    env_aliases = registry.get(environment, {})
    if alias not in env_aliases:
        return False
    del env_aliases[alias]
    if not env_aliases:
        registry.pop(environment, None)
    else:
        registry[environment] = env_aliases
    _save_aliases(vault_dir, registry)
    return True


def list_aliases(vault_dir: Path, environment: str) -> Dict[str, str]:
    """Return all aliases for *environment* as {alias: real_key}."""
    registry = _load_aliases(vault_dir)
    return dict(registry.get(environment, {}))
