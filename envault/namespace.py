"""Namespace support: logical grouping of keys under a dotted prefix."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.store import load_vault, save_vault


class NamespaceError(Exception):
    """Raised when a namespace operation fails."""


@dataclass
class NamespaceResult:
    namespace: str
    environment: str
    keys: List[str] = field(default_factory=list)

    @property
    def total_keys(self) -> int:
        return len(self.keys)


def _prefix(namespace: str) -> str:
    ns = namespace.strip().rstrip(".")
    if not ns:
        raise NamespaceError("Namespace must not be empty.")
    return ns + "."


def set_namespace_key(
    vault_dir: str,
    environment: str,
    namespace: str,
    key: str,
    value: str,
    password: str,
) -> str:
    """Store *value* under ``<namespace>.<key>`` and return the full key name."""
    full_key = _prefix(namespace) + key
    secrets = load_vault(vault_dir, environment, password)
    secrets[full_key] = value
    save_vault(vault_dir, environment, secrets, password)
    return full_key


def list_namespace_keys(
    vault_dir: str,
    environment: str,
    namespace: str,
    password: str,
) -> NamespaceResult:
    """Return all keys that belong to *namespace* in *environment*."""
    prefix = _prefix(namespace)
    secrets = load_vault(vault_dir, environment, password)
    matching = [k for k in secrets if k.startswith(prefix)]
    return NamespaceResult(namespace=namespace, environment=environment, keys=sorted(matching))


def delete_namespace(
    vault_dir: str,
    environment: str,
    namespace: str,
    password: str,
) -> NamespaceResult:
    """Remove every key that belongs to *namespace* and return the result."""
    prefix = _prefix(namespace)
    secrets = load_vault(vault_dir, environment, password)
    to_remove = [k for k in secrets if k.startswith(prefix)]
    if not to_remove:
        raise NamespaceError(
            f"Namespace '{namespace}' has no keys in environment '{environment}'."
        )
    for k in to_remove:
        del secrets[k]
    save_vault(vault_dir, environment, secrets, password)
    return NamespaceResult(namespace=namespace, environment=environment, keys=sorted(to_remove))


def get_namespace_values(
    vault_dir: str,
    environment: str,
    namespace: str,
    password: str,
) -> Dict[str, str]:
    """Return a mapping of ``key -> value`` for all keys in *namespace*."""
    prefix = _prefix(namespace)
    secrets = load_vault(vault_dir, environment, password)
    return {k: v for k, v in secrets.items() if k.startswith(prefix)}
