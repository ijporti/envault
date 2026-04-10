"""Search across environments and keys within a vault."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from envault.store import load_vault


@dataclass
class SearchResult:
    environment: str
    key: str
    value: str

    def __str__(self) -> str:
        return f"{self.environment}  {self.key}={self.value}"


def search_keys(
    vault_dir: str,
    password: str,
    pattern: str,
    environment: Optional[str] = None,
    case_sensitive: bool = False,
) -> List[SearchResult]:
    """Search for keys matching *pattern* across all (or one) environment.

    Parameters
    ----------
    vault_dir:      Root directory of the vault.
    password:       Master password used to decrypt the vault.
    pattern:        Substring to match against key names.
    environment:    If given, restrict search to this environment only.
    case_sensitive: When False (default) matching ignores case.

    Returns a list of :class:`SearchResult` sorted by environment then key.
    """
    secrets = load_vault(vault_dir, password)

    needle = pattern if case_sensitive else pattern.lower()

    results: List[SearchResult] = []
    for env, kvs in secrets.items():
        if environment is not None and env != environment:
            continue
        for key, value in kvs.items():
            haystack = key if case_sensitive else key.lower()
            if needle in haystack:
                results.append(SearchResult(environment=env, key=key, value=value))

    results.sort(key=lambda r: (r.environment, r.key))
    return results


def search_values(
    vault_dir: str,
    password: str,
    pattern: str,
    environment: Optional[str] = None,
    case_sensitive: bool = False,
) -> List[SearchResult]:
    """Search for keys whose *values* contain *pattern*."""
    secrets = load_vault(vault_dir, password)

    needle = pattern if case_sensitive else pattern.lower()

    results: List[SearchResult] = []
    for env, kvs in secrets.items():
        if environment is not None and env != environment:
            continue
        for key, value in kvs.items():
            haystack = value if case_sensitive else value.lower()
            if needle in haystack:
                results.append(SearchResult(environment=env, key=key, value=value))

    results.sort(key=lambda r: (r.environment, r.key))
    return results
