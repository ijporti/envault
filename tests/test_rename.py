"""Tests for envault.rename."""

import pytest

from envault.store import save_vault, load_vault
from envault.rename import RenameError, rename_key, rename_key_all_envs


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


PASSWORD = "test-password"


def _seed(vault_dir, env, data):
    save_vault(vault_dir, env, data, PASSWORD)


def test_rename_key_returns_true_when_key_exists(vault_dir):
    _seed(vault_dir, "dev", {"OLD_KEY": "value"})
    result = rename_key(vault_dir, "dev", "OLD_KEY", "NEW_KEY", PASSWORD)
    assert result is True


def test_rename_key_returns_false_when_key_missing(vault_dir):
    _seed(vault_dir, "dev", {"OTHER": "value"})
    result = rename_key(vault_dir, "dev", "MISSING", "NEW_KEY", PASSWORD)
    assert result is False


def test_rename_key_new_key_readable(vault_dir):
    _seed(vault_dir, "dev", {"OLD_KEY": "secret"})
    rename_key(vault_dir, "dev", "OLD_KEY", "NEW_KEY", PASSWORD)
    vault = load_vault(vault_dir, "dev", PASSWORD)
    assert vault["NEW_KEY"] == "secret"


def test_rename_key_old_key_removed(vault_dir):
    _seed(vault_dir, "dev", {"OLD_KEY": "secret"})
    rename_key(vault_dir, "dev", "OLD_KEY", "NEW_KEY", PASSWORD)
    vault = load_vault(vault_dir, "dev", PASSWORD)
    assert "OLD_KEY" not in vault


def test_rename_key_raises_when_new_key_exists_no_overwrite(vault_dir):
    _seed(vault_dir, "dev", {"OLD_KEY": "v1", "NEW_KEY": "v2"})
    with pytest.raises(RenameError):
        rename_key(vault_dir, "dev", "OLD_KEY", "NEW_KEY", PASSWORD)


def test_rename_key_overwrites_when_flag_set(vault_dir):
    _seed(vault_dir, "dev", {"OLD_KEY": "v1", "NEW_KEY": "v2"})
    rename_key(vault_dir, "dev", "OLD_KEY", "NEW_KEY", PASSWORD, overwrite=True)
    vault = load_vault(vault_dir, "dev", PASSWORD)
    assert vault["NEW_KEY"] == "v1"
    assert "OLD_KEY" not in vault


def test_rename_key_all_envs_applies_to_matching_envs(vault_dir):
    _seed(vault_dir, "dev", {"OLD_KEY": "d"})
    _seed(vault_dir, "prod", {"OLD_KEY": "p"})
    _seed(vault_dir, "staging", {"OTHER": "s"})
    results = rename_key_all_envs(vault_dir, "OLD_KEY", "NEW_KEY", PASSWORD)
    assert results["dev"] is True
    assert results["prod"] is True
    assert results["staging"] is False


def test_rename_key_all_envs_values_preserved(vault_dir):
    _seed(vault_dir, "dev", {"OLD_KEY": "dev-value"})
    _seed(vault_dir, "prod", {"OLD_KEY": "prod-value"})
    rename_key_all_envs(vault_dir, "OLD_KEY", "NEW_KEY", PASSWORD)
    assert load_vault(vault_dir, "dev", PASSWORD)["NEW_KEY"] == "dev-value"
    assert load_vault(vault_dir, "prod", PASSWORD)["NEW_KEY"] == "prod-value"
