"""Tests for envault.clone."""

from __future__ import annotations

import pytest

from envault.clone import CloneError, clone_env
from envault.store import load_vault, save_vault


@pytest.fixture()
def vault_dir(tmp_path):
    """Provide a helper that creates a vault directory with seed data."""

    def _make(subdir: str, password: str, data: dict) -> object:
        d = tmp_path / subdir
        d.mkdir(parents=True, exist_ok=True)
        save_vault(d, password, data)
        return d

    return _make


def test_clone_env_returns_secret_count(vault_dir):
    src = vault_dir("src", "pass", {"prod": {"KEY": "val1", "OTHER": "val2"}})
    dst = vault_dir("dst", "pass", {})

    count = clone_env(src, "prod", "pass", dst, None, "pass")
    assert count == 2


def test_clone_env_creates_target_environment(vault_dir):
    src = vault_dir("src", "pass", {"prod": {"A": "1"}})
    dst = vault_dir("dst", "pass2", {})

    clone_env(src, "prod", "pass", dst, "staging", "pass2")
    data = load_vault(dst, "pass2")
    assert "staging" in data


def test_clone_env_values_match_source(vault_dir):
    src = vault_dir("src", "pw", {"dev": {"DB_URL": "sqlite:///dev.db", "DEBUG": "true"}})
    dst = vault_dir("dst", "pw", {})

    clone_env(src, "dev", "pw", dst, "dev", "pw")
    result = load_vault(dst, "pw")
    assert result["dev"]["DB_URL"] == "sqlite:///dev.db"
    assert result["dev"]["DEBUG"] == "true"


def test_clone_env_missing_src_env_raises(vault_dir):
    src = vault_dir("src", "pw", {"prod": {"X": "1"}})
    dst = vault_dir("dst", "pw", {})

    with pytest.raises(CloneError, match="not found"):
        clone_env(src, "nonexistent", "pw", dst, None, "pw")


def test_clone_env_existing_dst_without_overwrite_raises(vault_dir):
    src = vault_dir("src", "pw", {"prod": {"X": "1"}})
    dst = vault_dir("dst", "pw", {"prod": {"Y": "2"}})

    with pytest.raises(CloneError, match="already exists"):
        clone_env(src, "prod", "pw", dst, "prod", "pw", overwrite=False)


def test_clone_env_overwrite_replaces_values(vault_dir):
    src = vault_dir("src", "pw", {"prod": {"KEY": "new_val"}})
    dst = vault_dir("dst", "pw", {"prod": {"KEY": "old_val"}})

    clone_env(src, "prod", "pw", dst, "prod", "pw", overwrite=True)
    result = load_vault(dst, "pw")
    assert result["prod"]["KEY"] == "new_val"


def test_clone_env_dst_vault_created_when_missing(tmp_path, vault_dir):
    src = vault_dir("src", "pw", {"prod": {"A": "1"}})
    dst_dir = tmp_path / "brand_new"
    dst_dir.mkdir()

    count = clone_env(src, "prod", "pw", dst_dir, None, "newpass")
    assert count == 1
    result = load_vault(dst_dir, "newpass")
    assert "prod" in result
