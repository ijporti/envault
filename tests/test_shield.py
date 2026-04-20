"""Tests for envault.shield."""

import pytest

from envault.shield import (
    ShieldError,
    ShieldResult,
    is_shielded,
    list_shields,
    shield_keys,
    unshield_keys,
)
from envault.store import save_vault

PASSWORD = "hunter2"


@pytest.fixture()
def vault_dir(tmp_path):
    return tmp_path


def _seed(vault_dir, env="production", secrets=None):
    if secrets is None:
        secrets = {"DB_URL": "postgres://localhost", "API_KEY": "abc123", "SECRET": "s3cr3t"}
    save_vault(vault_dir, env, secrets, PASSWORD)
    return secrets


def test_shield_keys_returns_shield_result(vault_dir):
    _seed(vault_dir)
    result = shield_keys(vault_dir, "production", ["DB_URL"], PASSWORD)
    assert isinstance(result, ShieldResult)


def test_shield_keys_new_keys_in_shielded_keys(vault_dir):
    _seed(vault_dir)
    result = shield_keys(vault_dir, "production", ["DB_URL", "API_KEY"], PASSWORD)
    assert "DB_URL" in result.shielded_keys
    assert "API_KEY" in result.shielded_keys
    assert result.total_shielded == 2


def test_shield_keys_already_shielded_not_duplicated(vault_dir):
    _seed(vault_dir)
    shield_keys(vault_dir, "production", ["DB_URL"], PASSWORD)
    result = shield_keys(vault_dir, "production", ["DB_URL"], PASSWORD)
    assert "DB_URL" in result.already_shielded
    assert result.total_shielded == 0


def test_shield_keys_creates_registry_file(vault_dir):
    _seed(vault_dir)
    shield_keys(vault_dir, "production", ["SECRET"], PASSWORD)
    assert (vault_dir / ".shield_registry.json").exists()


def test_shield_keys_nonexistent_key_raises(vault_dir):
    _seed(vault_dir)
    with pytest.raises(ShieldError, match="MISSING_KEY"):
        shield_keys(vault_dir, "production", ["MISSING_KEY"], PASSWORD)


def test_is_shielded_returns_true_after_shield(vault_dir):
    _seed(vault_dir)
    shield_keys(vault_dir, "production", ["API_KEY"], PASSWORD)
    assert is_shielded(vault_dir, "production", "API_KEY") is True


def test_is_shielded_returns_false_before_shield(vault_dir):
    _seed(vault_dir)
    assert is_shielded(vault_dir, "production", "DB_URL") is False


def test_list_shields_returns_all_shielded_keys(vault_dir):
    _seed(vault_dir)
    shield_keys(vault_dir, "production", ["DB_URL", "SECRET"], PASSWORD)
    shields = list_shields(vault_dir, "production")
    assert sorted(shields) == ["DB_URL", "SECRET"]


def test_list_shields_empty_when_none_set(vault_dir):
    _seed(vault_dir)
    assert list_shields(vault_dir, "production") == []


def test_unshield_keys_returns_removed_list(vault_dir):
    _seed(vault_dir)
    shield_keys(vault_dir, "production", ["DB_URL", "API_KEY"], PASSWORD)
    removed = unshield_keys(vault_dir, "production", ["DB_URL"])
    assert removed == ["DB_URL"]


def test_unshield_keys_key_no_longer_shielded(vault_dir):
    _seed(vault_dir)
    shield_keys(vault_dir, "production", ["DB_URL"], PASSWORD)
    unshield_keys(vault_dir, "production", ["DB_URL"])
    assert is_shielded(vault_dir, "production", "DB_URL") is False


def test_unshield_keys_ignores_non_shielded_keys(vault_dir):
    _seed(vault_dir)
    shield_keys(vault_dir, "production", ["DB_URL"], PASSWORD)
    removed = unshield_keys(vault_dir, "production", ["API_KEY"])
    assert removed == []
