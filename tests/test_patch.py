"""Tests for envault.patch."""

import pytest

from envault.patch import PatchError, PatchResult, patch_env
from envault.store import load_vault, save_vault


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _seed(vault_dir, env, password, data):
    save_vault(vault_dir, env, password, data)


# ---------------------------------------------------------------------------
# PatchResult helpers
# ---------------------------------------------------------------------------

def test_patch_result_total_changed():
    r = PatchResult(environment="dev", updated=["A"], added=["B", "C"])
    assert r.total_changed == 3


def test_patch_result_total_changed_empty():
    r = PatchResult(environment="dev")
    assert r.total_changed == 0


# ---------------------------------------------------------------------------
# patch_env — basic behaviour
# ---------------------------------------------------------------------------

def test_patch_env_returns_patch_result(vault_dir):
    _seed(vault_dir, "dev", "pw", {"KEY": "old"})
    result = patch_env(vault_dir, "dev", "pw", {"KEY": "new"})
    assert isinstance(result, PatchResult)


def test_patch_env_updates_existing_key(vault_dir):
    _seed(vault_dir, "dev", "pw", {"KEY": "old"})
    result = patch_env(vault_dir, "dev", "pw", {"KEY": "new"})
    assert "KEY" in result.updated
    assert load_vault(vault_dir, "dev", "pw")["KEY"] == "new"


def test_patch_env_adds_new_key_by_default(vault_dir):
    _seed(vault_dir, "dev", "pw", {})
    result = patch_env(vault_dir, "dev", "pw", {"FRESH": "val"})
    assert "FRESH" in result.added
    assert load_vault(vault_dir, "dev", "pw")["FRESH"] == "val"


def test_patch_env_skips_new_key_when_add_new_false(vault_dir):
    _seed(vault_dir, "dev", "pw", {})
    result = patch_env(vault_dir, "dev", "pw", {"GHOST": "val"}, add_new=False)
    assert "GHOST" in result.skipped
    assert "GHOST" not in load_vault(vault_dir, "dev", "pw")


def test_patch_env_respects_keys_filter(vault_dir):
    _seed(vault_dir, "dev", "pw", {"A": "1", "B": "2"})
    result = patch_env(vault_dir, "dev", "pw", {"A": "X", "B": "Y"}, keys=["A"])
    assert "A" in result.updated
    assert "B" not in result.updated
    data = load_vault(vault_dir, "dev", "pw")
    assert data["A"] == "X"
    assert data["B"] == "2"


def test_patch_env_missing_environment_raises(vault_dir):
    with pytest.raises(PatchError, match="does not exist"):
        patch_env(vault_dir, "ghost", "pw", {"K": "v"})


def test_patch_env_multiple_keys(vault_dir):
    _seed(vault_dir, "prod", "secret", {"X": "1", "Y": "2"})
    result = patch_env(vault_dir, "prod", "secret", {"X": "10", "Y": "20", "Z": "30"})
    assert result.total_changed == 3
    data = load_vault(vault_dir, "prod", "secret")
    assert data == {"X": "10", "Y": "20", "Z": "30"}
