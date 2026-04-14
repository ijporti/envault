"""Tests for envault.scope."""
import pytest
from pathlib import Path

from envault.scope import (
    ScopeError,
    set_scope,
    delete_scope,
    list_scopes,
    resolve_scope,
    ScopeResult,
)
from envault.store import save_vault

PASSWORD = "test-password"


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def _seed(vault_dir: Path, env: str, secrets: dict) -> None:
    save_vault(vault_dir, env, secrets, PASSWORD)


# --- set_scope ---

def test_set_scope_returns_sorted_envs(vault_dir):
    result = set_scope(vault_dir, "prod", ["production", "staging"])
    assert result == ["production", "staging"]


def test_set_scope_deduplicates(vault_dir):
    result = set_scope(vault_dir, "prod", ["production", "production", "staging"])
    assert result.count("production") == 1


def test_set_scope_creates_registry_file(vault_dir):
    set_scope(vault_dir, "prod", ["production"])
    assert (vault_dir / ".scope_registry.json").exists()


def test_set_scope_empty_name_raises(vault_dir):
    with pytest.raises(ScopeError):
        set_scope(vault_dir, "", ["production"])


def test_set_scope_empty_environments_raises(vault_dir):
    with pytest.raises(ScopeError):
        set_scope(vault_dir, "prod", [])


# --- delete_scope ---

def test_delete_scope_returns_true_when_exists(vault_dir):
    set_scope(vault_dir, "prod", ["production"])
    assert delete_scope(vault_dir, "prod") is True


def test_delete_scope_returns_false_when_missing(vault_dir):
    assert delete_scope(vault_dir, "nonexistent") is False


def test_delete_scope_removes_from_registry(vault_dir):
    set_scope(vault_dir, "prod", ["production"])
    delete_scope(vault_dir, "prod")
    assert "prod" not in list_scopes(vault_dir)


# --- list_scopes ---

def test_list_scopes_returns_all(vault_dir):
    set_scope(vault_dir, "prod", ["production"])
    set_scope(vault_dir, "dev", ["development", "local"])
    scopes = list_scopes(vault_dir)
    assert set(scopes.keys()) == {"prod", "dev"}


def test_list_scopes_empty_when_no_registry(vault_dir):
    assert list_scopes(vault_dir) == {}


# --- resolve_scope ---

def test_resolve_scope_returns_scope_result(vault_dir):
    _seed(vault_dir, "production", {"DB": "prod-db"})
    set_scope(vault_dir, "prod", ["production"])
    result = resolve_scope(vault_dir, "prod", PASSWORD)
    assert isinstance(result, ScopeResult)


def test_resolve_scope_contains_keys(vault_dir):
    _seed(vault_dir, "production", {"DB": "prod-db", "API": "key"})
    set_scope(vault_dir, "prod", ["production"])
    result = resolve_scope(vault_dir, "prod", PASSWORD)
    assert "DB" in result.keys_visible["production"]
    assert "API" in result.keys_visible["production"]


def test_resolve_scope_filters_keys(vault_dir):
    _seed(vault_dir, "production", {"DB": "prod-db", "API": "key"})
    set_scope(vault_dir, "prod", ["production"])
    result = resolve_scope(vault_dir, "prod", PASSWORD, keys=["DB"])
    assert result.keys_visible["production"] == ["DB"]


def test_resolve_scope_missing_env_returns_empty_list(vault_dir):
    set_scope(vault_dir, "prod", ["ghost-env"])
    result = resolve_scope(vault_dir, "prod", PASSWORD)
    assert result.keys_visible["ghost-env"] == []


def test_resolve_scope_unknown_scope_raises(vault_dir):
    with pytest.raises(ScopeError):
        resolve_scope(vault_dir, "unknown", PASSWORD)


def test_resolve_scope_total_keys(vault_dir):
    _seed(vault_dir, "production", {"A": "1", "B": "2"})
    _seed(vault_dir, "staging", {"A": "1"})
    set_scope(vault_dir, "multi", ["production", "staging"])
    result = resolve_scope(vault_dir, "multi", PASSWORD)
    assert result.total_keys == 3
