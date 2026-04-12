"""Tests for envault.rollback."""

from __future__ import annotations

import pytest

from envault.store import save_vault, load_vault
from envault.snapshot import create_snapshot
from envault.rollback import rollback_env, RollbackError, RollbackResult

PASSWORD = "test-secret"


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _seed(vault_dir, env, secrets):
    save_vault(vault_dir, env, secrets, PASSWORD)


def test_rollback_returns_rollback_result(vault_dir):
    _seed(vault_dir, "production", {"KEY": "val"})
    snap = create_snapshot(vault_dir, "production", PASSWORD)
    result = rollback_env(vault_dir, "production", snap.snapshot_id, PASSWORD)
    assert isinstance(result, RollbackResult)


def test_rollback_restores_keys(vault_dir):
    _seed(vault_dir, "production", {"A": "1", "B": "2"})
    snap = create_snapshot(vault_dir, "production", PASSWORD)
    # Overwrite with different data
    _seed(vault_dir, "production", {"A": "changed"})
    rollback_env(vault_dir, "production", snap.snapshot_id, PASSWORD)
    vault = load_vault(vault_dir, "production", PASSWORD)
    assert vault == {"A": "1", "B": "2"}


def test_rollback_result_keys_restored_count(vault_dir):
    _seed(vault_dir, "staging", {"X": "x", "Y": "y", "Z": "z"})
    snap = create_snapshot(vault_dir, "staging", PASSWORD)
    result = rollback_env(vault_dir, "staging", snap.snapshot_id, PASSWORD)
    assert result.keys_restored == 3


def test_rollback_result_previous_key_count(vault_dir):
    _seed(vault_dir, "staging", {"X": "x", "Y": "y"})
    snap = create_snapshot(vault_dir, "staging", PASSWORD)
    _seed(vault_dir, "staging", {"X": "x"})
    result = rollback_env(vault_dir, "staging", snap.snapshot_id, PASSWORD)
    assert result.previous_key_count == 1


def test_rollback_invalid_snapshot_id_raises(vault_dir):
    _seed(vault_dir, "production", {"K": "v"})
    with pytest.raises(RollbackError, match="not found"):
        rollback_env(vault_dir, "production", "nonexistent-id", PASSWORD)


def test_rollback_dry_run_does_not_change_vault(vault_dir):
    _seed(vault_dir, "production", {"A": "original"})
    snap = create_snapshot(vault_dir, "production", PASSWORD)
    _seed(vault_dir, "production", {"A": "modified"})
    rollback_env(vault_dir, "production", snap.snapshot_id, PASSWORD, dry_run=True)
    vault = load_vault(vault_dir, "production", PASSWORD)
    # dry_run should NOT restore; vault should still have modified value
    assert vault["A"] == "modified"


def test_rollback_net_change_positive(vault_dir):
    _seed(vault_dir, "dev", {"A": "1", "B": "2", "C": "3"})
    snap = create_snapshot(vault_dir, "dev", PASSWORD)
    _seed(vault_dir, "dev", {"A": "1"})
    result = rollback_env(vault_dir, "dev", snap.snapshot_id, PASSWORD)
    assert result.net_change == 2
