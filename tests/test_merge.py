"""Tests for envault.merge."""

import pytest

from envault.merge import MergeError, MergeResult, merge_envs
from envault.store import load_vault, save_vault


@pytest.fixture()
def vault_dir(tmp_path):
    """Return a temp directory pre-populated with two environments."""
    directory = str(tmp_path)
    vault = {
        "staging": {"DB_HOST": "staging-db", "DB_PORT": "5432", "SECRET": "s3cr3t"},
        "production": {"DB_HOST": "prod-db", "APP_ENV": "production"},
    }
    save_vault(directory, "pass", vault)
    return directory


def test_merge_returns_merge_result(vault_dir):
    result = merge_envs(vault_dir, "pass", sources=["staging"], target="production")
    assert isinstance(result, MergeResult)


def test_merge_adds_missing_keys(vault_dir):
    result = merge_envs(vault_dir, "pass", sources=["staging"], target="production")
    assert "DB_PORT" in result.added
    assert "SECRET" in result.added


def test_merge_skips_existing_keys_by_default(vault_dir):
    result = merge_envs(vault_dir, "pass", sources=["staging"], target="production")
    # DB_HOST already exists in production — should be skipped without overwrite
    assert "DB_HOST" in result.skipped
    vault = load_vault(vault_dir, "pass")
    assert vault["production"]["DB_HOST"] == "prod-db"


def test_merge_overwrites_when_flag_set(vault_dir):
    result = merge_envs(
        vault_dir, "pass", sources=["staging"], target="production", overwrite=True
    )
    assert "DB_HOST" in result.overwritten
    vault = load_vault(vault_dir, "pass")
    assert vault["production"]["DB_HOST"] == "staging-db"


def test_merge_creates_new_target_environment(vault_dir):
    result = merge_envs(vault_dir, "pass", sources=["staging"], target="dev")
    vault = load_vault(vault_dir, "pass")
    assert "dev" in vault
    assert vault["dev"]["DB_HOST"] == "staging-db"
    assert result.total_applied == len(vault["staging"])


def test_merge_respects_keys_allowlist(vault_dir):
    result = merge_envs(
        vault_dir, "pass", sources=["staging"], target="production", keys=["DB_PORT"]
    )
    assert result.added == ["DB_PORT"]
    assert "SECRET" not in result.added


def test_merge_later_source_wins(vault_dir):
    # Add a second source that overrides DB_HOST with a different value
    vault = load_vault(vault_dir, "pass")
    vault["override"] = {"DB_HOST": "override-db"}
    save_vault(vault_dir, "pass", vault)

    merge_envs(
        vault_dir,
        "pass",
        sources=["staging", "override"],
        target="dev",
        overwrite=True,
    )
    vault = load_vault(vault_dir, "pass")
    assert vault["dev"]["DB_HOST"] == "override-db"


def test_merge_missing_source_raises(vault_dir):
    with pytest.raises(MergeError, match="does not exist"):
        merge_envs(vault_dir, "pass", sources=["nonexistent"], target="production")


def test_merge_empty_sources_raises(vault_dir):
    with pytest.raises(MergeError, match="At least one source"):
        merge_envs(vault_dir, "pass", sources=[], target="production")
