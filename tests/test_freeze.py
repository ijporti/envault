"""Tests for envault.freeze."""
from __future__ import annotations

import pytest

from envault.freeze import (
    FreezeError,
    FreezeResult,
    freeze_env,
    is_frozen,
    thaw_env,
)
from envault.store import load_vault, save_vault

PASSWORD = "s3cr3t"


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _seed(vault_dir: str, env: str, secrets: dict) -> None:
    try:
        data = load_vault(vault_dir, PASSWORD)
    except FileNotFoundError:
        data = {}
    data[env] = secrets
    save_vault(vault_dir, data, PASSWORD)


# ---------------------------------------------------------------------------
# freeze_env
# ---------------------------------------------------------------------------

def test_freeze_env_returns_freeze_result(vault_dir):
    _seed(vault_dir, "production", {"DB_URL": "postgres://prod", "API_KEY": "abc"})
    result = freeze_env(vault_dir, "production", PASSWORD)
    assert isinstance(result, FreezeResult)


def test_freeze_env_source_and_frozen_names(vault_dir):
    _seed(vault_dir, "production", {"DB_URL": "postgres://prod"})
    result = freeze_env(vault_dir, "production", PASSWORD)
    assert result.source_env == "production"
    assert result.frozen_env == "frozen/production"


def test_freeze_env_keys_frozen_sorted(vault_dir):
    _seed(vault_dir, "staging", {"Z_KEY": "z", "A_KEY": "a", "M_KEY": "m"})
    result = freeze_env(vault_dir, "staging", PASSWORD)
    assert result.keys_frozen == ["A_KEY", "M_KEY", "Z_KEY"]
    assert result.total_frozen == 3


def test_freeze_env_persists_values(vault_dir):
    secrets = {"TOKEN": "tok123", "HOST": "localhost"}
    _seed(vault_dir, "dev", secrets)
    freeze_env(vault_dir, "dev", PASSWORD)
    data = load_vault(vault_dir, PASSWORD)
    assert data["frozen/dev"] == secrets


def test_freeze_env_nonexistent_raises(vault_dir):
    _seed(vault_dir, "dev", {"K": "v"})
    with pytest.raises(FreezeError, match="does not exist"):
        freeze_env(vault_dir, "ghost", PASSWORD)


def test_freeze_env_duplicate_raises_without_overwrite(vault_dir):
    _seed(vault_dir, "production", {"K": "v"})
    freeze_env(vault_dir, "production", PASSWORD)
    with pytest.raises(FreezeError, match="already exists"):
        freeze_env(vault_dir, "production", PASSWORD)


def test_freeze_env_overwrite_flag_replaces(vault_dir):
    _seed(vault_dir, "production", {"K": "v1"})
    freeze_env(vault_dir, "production", PASSWORD)
    # Update source and re-freeze with overwrite
    _seed(vault_dir, "production", {"K": "v2"})
    result = freeze_env(vault_dir, "production", PASSWORD, overwrite=True)
    data = load_vault(vault_dir, PASSWORD)
    assert data["frozen/production"]["K"] == "v2"
    assert result.total_frozen == 1


# ---------------------------------------------------------------------------
# thaw_env
# ---------------------------------------------------------------------------

def test_thaw_env_returns_keys(vault_dir):
    _seed(vault_dir, "dev", {"A": "1", "B": "2"})
    freeze_env(vault_dir, "dev", PASSWORD)
    keys = thaw_env(vault_dir, "dev", PASSWORD)
    assert sorted(keys) == ["A", "B"]


def test_thaw_env_removes_frozen_entry(vault_dir):
    _seed(vault_dir, "dev", {"A": "1"})
    freeze_env(vault_dir, "dev", PASSWORD)
    thaw_env(vault_dir, "dev", PASSWORD)
    data = load_vault(vault_dir, PASSWORD)
    assert "frozen/dev" not in data


def test_thaw_env_nonexistent_raises(vault_dir):
    _seed(vault_dir, "dev", {"A": "1"})
    with pytest.raises(FreezeError, match="No frozen environment"):
        thaw_env(vault_dir, "dev", PASSWORD)


# ---------------------------------------------------------------------------
# is_frozen
# ---------------------------------------------------------------------------

def test_is_frozen_returns_true_after_freeze(vault_dir):
    _seed(vault_dir, "staging", {"X": "y"})
    freeze_env(vault_dir, "staging", PASSWORD)
    assert is_frozen(vault_dir, "staging", PASSWORD) is True


def test_is_frozen_returns_false_before_freeze(vault_dir):
    _seed(vault_dir, "staging", {"X": "y"})
    assert is_frozen(vault_dir, "staging", PASSWORD) is False


def test_is_frozen_returns_false_after_thaw(vault_dir):
    _seed(vault_dir, "staging", {"X": "y"})
    freeze_env(vault_dir, "staging", PASSWORD)
    thaw_env(vault_dir, "staging", PASSWORD)
    assert is_frozen(vault_dir, "staging", PASSWORD) is False
