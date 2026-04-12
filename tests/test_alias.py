"""Tests for envault.alias."""
from __future__ import annotations

import pytest
from pathlib import Path

from envault.store import save_vault
from envault.alias import (
    AliasError,
    add_alias,
    resolve_alias,
    remove_alias,
    list_aliases,
    _alias_path,
)

PASSWORD = "test-secret"


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    save_vault(tmp_path, "production", {"DATABASE_URL": "postgres://localhost/db", "API_KEY": "abc123"}, PASSWORD)
    save_vault(tmp_path, "staging", {"DATABASE_URL": "postgres://localhost/staging"}, PASSWORD)
    return tmp_path


def test_add_alias_returns_real_key(vault_dir: Path) -> None:
    result = add_alias(vault_dir, "production", "db", "DATABASE_URL", PASSWORD)
    assert result == "DATABASE_URL"


def test_add_alias_creates_registry_file(vault_dir: Path) -> None:
    add_alias(vault_dir, "production", "db", "DATABASE_URL", PASSWORD)
    assert _alias_path(vault_dir).exists()


def test_add_alias_nonexistent_key_raises(vault_dir: Path) -> None:
    with pytest.raises(AliasError, match="MISSING_KEY"):
        add_alias(vault_dir, "production", "bad", "MISSING_KEY", PASSWORD)


def test_resolve_alias_returns_real_key(vault_dir: Path) -> None:
    add_alias(vault_dir, "production", "db", "DATABASE_URL", PASSWORD)
    assert resolve_alias(vault_dir, "production", "db") == "DATABASE_URL"


def test_resolve_alias_unknown_returns_none(vault_dir: Path) -> None:
    assert resolve_alias(vault_dir, "production", "no_such_alias") is None


def test_resolve_alias_unknown_environment_returns_none(vault_dir: Path) -> None:
    assert resolve_alias(vault_dir, "nonexistent", "db") is None


def test_remove_alias_returns_true_when_exists(vault_dir: Path) -> None:
    add_alias(vault_dir, "production", "db", "DATABASE_URL", PASSWORD)
    assert remove_alias(vault_dir, "production", "db") is True


def test_remove_alias_returns_false_when_missing(vault_dir: Path) -> None:
    assert remove_alias(vault_dir, "production", "ghost") is False


def test_remove_alias_no_longer_resolves(vault_dir: Path) -> None:
    add_alias(vault_dir, "production", "db", "DATABASE_URL", PASSWORD)
    remove_alias(vault_dir, "production", "db")
    assert resolve_alias(vault_dir, "production", "db") is None


def test_list_aliases_returns_dict(vault_dir: Path) -> None:
    add_alias(vault_dir, "production", "db", "DATABASE_URL", PASSWORD)
    add_alias(vault_dir, "production", "key", "API_KEY", PASSWORD)
    aliases = list_aliases(vault_dir, "production")
    assert aliases == {"db": "DATABASE_URL", "key": "API_KEY"}


def test_list_aliases_empty_for_unknown_env(vault_dir: Path) -> None:
    assert list_aliases(vault_dir, "unknown") == {}


def test_aliases_are_per_environment(vault_dir: Path) -> None:
    add_alias(vault_dir, "production", "db", "DATABASE_URL", PASSWORD)
    assert resolve_alias(vault_dir, "staging", "db") is None
