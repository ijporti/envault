"""Tests for envault.rotate — key rotation."""

from __future__ import annotations

import pytest

from envault.rotate import rotate_key, rotate_all_keys, RotationError
from envault.store import save_vault, load_vault, list_environments


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def vault_dir(tmp_path):
    return tmp_path


SECRETS = {"API_KEY": "abc123", "DB_URL": "postgres://localhost/mydb"}
OLD_PASS = "old-s3cr3t"
NEW_PASS = "new-s3cr3t"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_rotate_key_returns_secret_count(vault_dir):
    save_vault("prod", SECRETS, OLD_PASS, vault_dir=vault_dir)
    count = rotate_key("prod", OLD_PASS, NEW_PASS, vault_dir=vault_dir)
    assert count == len(SECRETS)


def test_rotate_key_new_password_decrypts(vault_dir):
    save_vault("prod", SECRETS, OLD_PASS, vault_dir=vault_dir)
    rotate_key("prod", OLD_PASS, NEW_PASS, vault_dir=vault_dir)
    loaded = load_vault("prod", NEW_PASS, vault_dir=vault_dir)
    assert loaded == SECRETS


def test_rotate_key_old_password_no_longer_works(vault_dir):
    save_vault("prod", SECRETS, OLD_PASS, vault_dir=vault_dir)
    rotate_key("prod", OLD_PASS, NEW_PASS, vault_dir=vault_dir)
    with pytest.raises(Exception):
        load_vault("prod", OLD_PASS, vault_dir=vault_dir)


def test_rotate_key_wrong_old_password_raises(vault_dir):
    save_vault("prod", SECRETS, OLD_PASS, vault_dir=vault_dir)
    with pytest.raises(RotationError):
        rotate_key("prod", "totally-wrong", NEW_PASS, vault_dir=vault_dir)


def test_rotate_key_missing_env_raises(vault_dir):
    with pytest.raises(RotationError):
        rotate_key("nonexistent", OLD_PASS, NEW_PASS, vault_dir=vault_dir)


def test_rotate_all_keys_covers_all_envs(vault_dir):
    for env in ("dev", "staging", "prod"):
        save_vault(env, SECRETS, OLD_PASS, vault_dir=vault_dir)

    results = rotate_all_keys(OLD_PASS, NEW_PASS, vault_dir=vault_dir)

    assert set(results.keys()) == {"dev", "staging", "prod"}
    for count in results.values():
        assert count == len(SECRETS)


def test_rotate_all_keys_new_password_works_for_all(vault_dir):
    envs = ["dev", "prod"]
    for env in envs:
        save_vault(env, SECRETS, OLD_PASS, vault_dir=vault_dir)

    rotate_all_keys(OLD_PASS, NEW_PASS, vault_dir=vault_dir)

    for env in envs:
        loaded = load_vault(env, NEW_PASS, vault_dir=vault_dir)
        assert loaded == SECRETS


def test_rotate_all_keys_empty_vault_dir(vault_dir):
    results = rotate_all_keys(OLD_PASS, NEW_PASS, vault_dir=vault_dir)
    assert results == {}
