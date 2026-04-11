"""Tests for envault.lock."""

import pytest

from envault.lock import (
    LockError,
    assert_unlocked,
    is_locked,
    list_locked,
    lock_env,
    unlock_env,
)
from envault.store import save_vault


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _seed(vault_dir: str, env: str = "production") -> None:
    save_vault(vault_dir, env, {"API_KEY": "secret"}, password="pass")


def test_lock_env_returns_true_on_new_lock(vault_dir):
    _seed(vault_dir)
    assert lock_env(vault_dir, "production") is True


def test_lock_env_returns_false_when_already_locked(vault_dir):
    _seed(vault_dir)
    lock_env(vault_dir, "production")
    assert lock_env(vault_dir, "production") is False


def test_lock_env_nonexistent_raises(vault_dir):
    with pytest.raises(LockError, match="does not exist"):
        lock_env(vault_dir, "ghost")


def test_lock_env_creates_lock_file(vault_dir):
    _seed(vault_dir)
    lock_env(vault_dir, "production")
    from pathlib import Path
    assert (Path(vault_dir) / ".locks.json").exists()


def test_is_locked_true_after_lock(vault_dir):
    _seed(vault_dir)
    lock_env(vault_dir, "production")
    assert is_locked(vault_dir, "production") is True


def test_is_locked_false_before_lock(vault_dir):
    _seed(vault_dir)
    assert is_locked(vault_dir, "production") is False


def test_unlock_env_returns_true_when_locked(vault_dir):
    _seed(vault_dir)
    lock_env(vault_dir, "production")
    assert unlock_env(vault_dir, "production") is True


def test_unlock_env_returns_false_when_not_locked(vault_dir):
    _seed(vault_dir)
    assert unlock_env(vault_dir, "production") is False


def test_unlock_env_clears_lock(vault_dir):
    _seed(vault_dir)
    lock_env(vault_dir, "production")
    unlock_env(vault_dir, "production")
    assert is_locked(vault_dir, "production") is False


def test_list_locked_returns_sorted(vault_dir):
    for env in ("staging", "production", "dev"):
        _seed(vault_dir, env)
        lock_env(vault_dir, env)
    assert list_locked(vault_dir) == ["dev", "production", "staging"]


def test_list_locked_empty_when_none(vault_dir):
    assert list_locked(vault_dir) == []


def test_assert_unlocked_raises_when_locked(vault_dir):
    _seed(vault_dir)
    lock_env(vault_dir, "production")
    with pytest.raises(LockError, match="locked"):
        assert_unlocked(vault_dir, "production")


def test_assert_unlocked_passes_when_not_locked(vault_dir):
    _seed(vault_dir)
    assert_unlocked(vault_dir, "production")  # should not raise
