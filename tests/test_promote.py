"""Tests for envault.promote."""

import pytest

from envault.promote import PromoteError, PromoteResult, promote_env
from envault.store import load_vault, save_vault


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _seed(vault_dir, env, password, data):
    save_vault(vault_dir, env, password, data)


# ---------------------------------------------------------------------------
# Basic promotion
# ---------------------------------------------------------------------------

def test_promote_returns_promote_result(vault_dir):
    _seed(vault_dir, "staging", "pass", {"KEY": "val"})
    result = promote_env(vault_dir, "staging", "production", "pass")
    assert isinstance(result, PromoteResult)


def test_promote_all_keys(vault_dir):
    _seed(vault_dir, "staging", "pass", {"A": "1", "B": "2"})
    result = promote_env(vault_dir, "staging", "production", "pass")
    assert set(result.promoted) == {"A", "B"}
    assert result.total_promoted == 2


def test_promote_creates_target_environment(vault_dir):
    _seed(vault_dir, "staging", "pass", {"X": "hello"})
    promote_env(vault_dir, "staging", "production", "pass")
    secrets = load_vault(vault_dir, "production", "pass")
    assert secrets["X"] == "hello"


def test_promote_partial_keys(vault_dir):
    _seed(vault_dir, "staging", "pass", {"A": "1", "B": "2", "C": "3"})
    result = promote_env(vault_dir, "staging", "production", "pass", keys=["A", "C"])
    assert set(result.promoted) == {"A", "C"}
    secrets = load_vault(vault_dir, "production", "pass")
    assert "B" not in secrets


def test_promote_skips_missing_key_in_source(vault_dir):
    _seed(vault_dir, "staging", "pass", {"A": "1"})
    result = promote_env(vault_dir, "staging", "production", "pass", keys=["A", "MISSING"])
    assert "MISSING" in result.skipped
    assert result.total_promoted == 1


# ---------------------------------------------------------------------------
# Overwrite behaviour
# ---------------------------------------------------------------------------

def test_promote_skips_existing_by_default(vault_dir):
    _seed(vault_dir, "staging", "pass", {"KEY": "new"})
    _seed(vault_dir, "production", "pass", {"KEY": "old"})
    result = promote_env(vault_dir, "staging", "production", "pass")
    assert "KEY" in result.skipped
    secrets = load_vault(vault_dir, "production", "pass")
    assert secrets["KEY"] == "old"


def test_promote_overwrites_when_flag_set(vault_dir):
    _seed(vault_dir, "staging", "pass", {"KEY": "new"})
    _seed(vault_dir, "production", "pass", {"KEY": "old"})
    result = promote_env(vault_dir, "staging", "production", "pass", overwrite=True)
    assert "KEY" in result.overwritten
    secrets = load_vault(vault_dir, "production", "pass")
    assert secrets["KEY"] == "new"


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_promote_same_env_raises(vault_dir):
    _seed(vault_dir, "staging", "pass", {"A": "1"})
    with pytest.raises(PromoteError, match="must differ"):
        promote_env(vault_dir, "staging", "staging", "pass")


def test_promote_missing_source_raises(vault_dir):
    with pytest.raises(PromoteError, match="does not exist"):
        promote_env(vault_dir, "ghost", "production", "pass")


def test_total_promoted_counts_both_new_and_overwritten(vault_dir):
    _seed(vault_dir, "staging", "pass", {"A": "1", "B": "2"})
    _seed(vault_dir, "production", "pass", {"A": "old"})
    result = promote_env(vault_dir, "staging", "production", "pass", overwrite=True)
    assert result.total_promoted == 2
    assert len(result.overwritten) == 1
    assert len(result.promoted) == 1
