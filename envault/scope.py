"""Scope management: restrict key visibility to a defined set of environments."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.store import load_vault, _vault_path


class ScopeError(Exception):
    """Raised when a scope operation fails."""


def _scope_path(vault_dir: Path) -> Path:
    return vault_dir / ".scope_registry.json"


def _load_scopes(vault_dir: Path) -> Dict[str, List[str]]:
    p = _scope_path(vault_dir)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_scopes(vault_dir: Path, data: Dict[str, List[str]]) -> None:
    _scope_path(vault_dir).write_text(json.dumps(data, indent=2))


@dataclass
class ScopeResult:
    scope: str
    environments: List[str] = field(default_factory=list)
    keys_visible: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def total_keys(self) -> int:
        return sum(len(v) for v in self.keys_visible.values())


def set_scope(vault_dir: Path, scope: str, environments: List[str]) -> List[str]:
    """Define or overwrite the environment list for a named scope."""
    if not scope:
        raise ScopeError("Scope name must not be empty.")
    if not environments:
        raise ScopeError("Scope must include at least one environment.")
    data = _load_scopes(vault_dir)
    data[scope] = sorted(set(environments))
    _save_scopes(vault_dir, data)
    return data[scope]


def delete_scope(vault_dir: Path, scope: str) -> bool:
    """Remove a scope definition. Returns True if it existed."""
    data = _load_scopes(vault_dir)
    if scope not in data:
        return False
    del data[scope]
    _save_scopes(vault True


def list_scopes(vault_dir: Path) -> Dict[str, List[str]]:
    """Return all defined scopes and their environment lists."""
    return _load_scopes(vault_dir)


def resolve_scope(
    vault_dir: Path,
    scope: str,
    password: str,
    keys: Optional[List[str]] = None,
) -> ScopeResult:
    """Return the visible keys for every environment in *scope*."""
    data = _load_scopes(vault_dir)
    if scope not in data:
        raise ScopeError(f"Scope '{scope}' does not exist.")
    envs = data[scope]
    result = ScopeResult(scope=scope, environments=envs)
    for env in envs:
        vault_file = _vault_path(vault_dir, env)
        if not vault_file.exists():
            result.keys_visible[env] = []
            continue
        from envault.store import load_vault
        secrets = load_vault(vault_dir, env, password)
        visible = list(secrets.keys()) if keys is None else [k for k in keys if k in secrets]
        result.keys_visible[env] = sorted(visible)
    return result
