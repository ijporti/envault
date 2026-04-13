"""Dependency tracking between environment variable keys."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envault.store import load_vault, _vault_path


class DependencyError(Exception):
    """Raised when a dependency operation fails."""


def _dep_path(vault_dir: Path, environment: str) -> Path:
    return vault_dir / f"{environment}.deps.json"


def _load_deps(vault_dir: Path, environment: str) -> Dict[str, List[str]]:
    path = _dep_path(vault_dir, environment)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_deps(vault_dir: Path, environment: str, deps: Dict[str, List[str]]) -> None:
    _dep_path(vault_dir, environment).write_text(json.dumps(deps, indent=2))


def add_dependency(vault_dir: Path, environment: str, key: str, depends_on: str, password: str) -> List[str]:
    """Record that *key* depends on *depends_on* within *environment*.

    Returns the updated dependency list for *key*.
    """
    vault = load_vault(vault_dir, environment, password)
    if key not in vault:
        raise DependencyError(f"Key '{key}' not found in environment '{environment}'.")
    if depends_on not in vault:
        raise DependencyError(f"Dependency key '{depends_on}' not found in environment '{environment}'.")
    if key == depends_on:
        raise DependencyError("A key cannot depend on itself.")

    deps = _load_deps(vault_dir, environment)
    current = deps.get(key, [])
    if depends_on not in current:
        current.append(depends_on)
        current.sort()
    deps[key] = current
    _save_deps(vault_dir, environment, deps)
    return list(current)


def remove_dependency(vault_dir: Path, environment: str, key: str, depends_on: str) -> List[str]:
    """Remove a dependency edge from *key* -> *depends_on*. Returns remaining deps."""
    deps = _load_deps(vault_dir, environment)
    current = deps.get(key, [])
    if depends_on not in current:
        return list(current)
    current.remove(depends_on)
    deps[key] = current
    _save_deps(vault_dir, environment, deps)
    return list(current)


def get_dependencies(vault_dir: Path, environment: str, key: str) -> List[str]:
    """Return the list of keys that *key* depends on."""
    return list(_load_deps(vault_dir, environment).get(key, []))


def get_dependents(vault_dir: Path, environment: str, key: str) -> List[str]:
    """Return the list of keys that depend on *key* (reverse lookup)."""
    deps = _load_deps(vault_dir, environment)
    return sorted(k for k, v in deps.items() if key in v)


def dependency_order(vault_dir: Path, environment: str) -> List[str]:
    """Return keys in topological (dependency-first) order using Kahn's algorithm."""
    deps = _load_deps(vault_dir, environment)
    all_keys: set = set(deps.keys())
    for v in deps.values():
        all_keys.update(v)

    in_degree: Dict[str, int] = {k: 0 for k in all_keys}
    for k, parents in deps.items():
        for p in parents:
            in_degree[k] = in_degree.get(k, 0) + 1

    queue = sorted(k for k, d in in_degree.items() if d == 0)
    order: List[str] = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        for dependent in get_dependents(vault_dir, environment, node):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
                queue.sort()
    if len(order) != len(all_keys):
        raise DependencyError("Cycle detected in dependency graph.")
    return order
