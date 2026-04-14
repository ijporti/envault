"""Tests for envault.copy_env."""

from __future__ import annotations

import pytest

from envault.copy_env import CopyError, copy_env
from envault.store import load_vault, save_vault

PASSWORD = "test-password"


@pytest.fixture()
def vault_dir(tmp_path):
    """Return a temp directory pre-populated with two environments."""
    initial: dict[str, dict[str, str]] = {
        "production": {"DB_URL": "postgres://prod", "API_KEY": "prod-key"},
        "staging": {"DB_URL": "postgres://staging"},
    }
    save_vault(str(tmp_path), initial, PASSWORD)
    return str(tmp_path)


def test_copy_env_returns_count(vault_dir):
    count = copy_env(vault_dir, "production", "development", PASSWORD)
    assert count == 2


def test_copy_env_creates_new_environment(vault_dir):
    copy_env(vault_dir, "production", "development", PASSWORD)
    vault = load_vault(vault_dir, PASSWORD)
    assert "development" in vault


def test_copy_env_values_match_source(vault_dir):
    copy_env(vault_dir, "production", "development", PASSWORD)
    vault = load_vault(vault_dir, PASSWORD)
    assert vault["development"]["DB_URL"] == "postgres://prod"
    assert vault["development"]["API_KEY"] == "prod-key"


def test_copy_env_partial_keys(vault_dir):
    count = copy_env(
        vault_dir, "production", "development", PASSWORD, keys=["API_KEY"]
    )
    assert count == 1
    vault = load_vault(vault_dir, PASSWORD)
    assert "API_KEY" in vault["development"]
    assert "DB_URL" not in vault["development"]


def test_copy_env_conflict_raises_without_overwrite(vault_dir):
    """Copying to an env that already has the key should raise by default."""
    with pytest.raises(CopyError, match="already exist"):
        copy_env(vault_dir, "production", "staging", PASSWORD)


def test_copy_env_conflict_resolved_with_overwrite(vault_dir):
    copy_env(vault_dir, "production", "staging", PASSWORD, overwrite=True)
    vault = load_vault(vault_dir, PASSWORD)
    assert vault["staging"]["DB_URL"] == "postgres://prod"


def test_copy_env_missing_source_raises(vault_dir):
    with pytest.raises(CopyError, match="does not exist"):
        copy_env(vault_dir, "nonexistent", "development", PASSWORD)


def test_copy_env_missing_keys_raises(vault_dir):
    with pytest.raises(CopyError, match="Keys not found"):
        copy_env(
            vault_dir, "production", "development", PASSWORD, keys=["MISSING_KEY"]
        )


def test_copy_env_source_unchanged(vault_dir):
    copy_env(vault_dir, "production", "development", PASSWORD)
    vault = load_vault(vault_dir, PASSWORD)
    # Source environment must remain intact.
    assert vault["production"]["DB_URL"] == "postgres://prod"
    assert vault["production"]["API_KEY"] == "prod-key"


def test_copy_env_does_not_affect_other_environments(vault_dir):
    """Copying between two environments must not modify unrelated environments."""
    copy_env(vault_dir, "production", "development", PASSWORD)
    vault = load_vault(vault_dir, PASSWORD)
    # Staging should be completely unmodified.
    assert vault["staging"] == {"DB_URL": "postgres://staging"}
