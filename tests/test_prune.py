"""Tests for envault.prune."""

import pytest

from envault.store import save_vault
from envault.prune import PruneError, PruneResult, prune_keys, prune_empty_values


PASSWORD = "test-password"


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _seed(vault_dir, env, data):
    save_vault(vault_dir, env, PASSWORD, data)


# ---------------------------------------------------------------------------
# PruneResult helpers
# ---------------------------------------------------------------------------

def test_prune_result_total_removed():
    r = PruneResult(environment="dev", removed_keys=["A", "B"], kept_keys=["C"])
    assert r.total_removed == 2


def test_prune_result_total_kept():
    r = PruneResult(environment="dev", removed_keys=["A"], kept_keys=["B", "C"])
    assert r.total_kept == 2


# ---------------------------------------------------------------------------
# prune_keys
# ---------------------------------------------------------------------------

def test_prune_keys_returns_prune_result(vault_dir):
    _seed(vault_dir, "dev", {"KEY": "val"})
    result = prune_keys(vault_dir, "dev", PASSWORD, ["KEY"])
    assert isinstance(result, PruneResult)


def test_prune_keys_removes_specified_keys(vault_dir):
    _seed(vault_dir, "dev", {"A": "1", "B": "2", "C": "3"})
    result = prune_keys(vault_dir, "dev", PASSWORD, ["A", "C"])
    assert "A" in result.removed_keys
    assert "C" in result.removed_keys
    assert "B" in result.kept_keys


def test_prune_keys_remaining_still_readable(vault_dir):
    from envault.store import load_vault
    _seed(vault_dir, "dev", {"KEEP": "yes", "DROP": "no"})
    prune_keys(vault_dir, "dev", PASSWORD, ["DROP"])
    secrets = load_vault(vault_dir, "dev", PASSWORD)
    assert "KEEP" in secrets
    assert "DROP" not in secrets


def test_prune_keys_nonexistent_key_is_ignored(vault_dir):
    _seed(vault_dir, "dev", {"A": "1"})
    result = prune_keys(vault_dir, "dev", PASSWORD, ["GHOST"])
    assert result.total_removed == 0
    assert "A" in result.kept_keys


def test_prune_keys_missing_environment_raises(vault_dir):
    with pytest.raises(PruneError, match="does not exist"):
        prune_keys(vault_dir, "ghost", PASSWORD, ["KEY"])


# ---------------------------------------------------------------------------
# prune_empty_values
# ---------------------------------------------------------------------------

def test_prune_empty_values_removes_empty(vault_dir):
    _seed(vault_dir, "dev", {"FULL": "value", "EMPTY": ""})
    result = prune_empty_values(vault_dir, "dev", PASSWORD)
    assert "EMPTY" in result.removed_keys
    assert "FULL" in result.kept_keys


def test_prune_empty_values_no_empty_keys(vault_dir):
    _seed(vault_dir, "dev", {"A": "x", "B": "y"})
    result = prune_empty_values(vault_dir, "dev", PASSWORD)
    assert result.total_removed == 0


def test_prune_empty_values_missing_environment_raises(vault_dir):
    with pytest.raises(PruneError):
        prune_empty_values(vault_dir, "no-such-env", PASSWORD)
