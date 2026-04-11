"""Tests for envault.compare."""

from __future__ import annotations

import pytest

from envault.compare import CompareResult, compare_envs
from envault.store import save_vault


PASSWORD = "test-password"


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _seed(vault_dir, env, secrets):
    save_vault(vault_dir, env, secrets, PASSWORD)


# ---------------------------------------------------------------------------
# compare_envs
# ---------------------------------------------------------------------------

def test_compare_returns_compare_result(vault_dir):
    _seed(vault_dir, "dev", {"KEY": "val"})
    _seed(vault_dir, "prod", {"KEY": "val"})
    result = compare_envs(vault_dir, "dev", "prod", PASSWORD)
    assert isinstance(result, CompareResult)


def test_compare_identical_envs(vault_dir):
    secrets = {"A": "1", "B": "2"}
    _seed(vault_dir, "dev", secrets)
    _seed(vault_dir, "prod", secrets)
    result = compare_envs(vault_dir, "dev", "prod", PASSWORD)
    assert result.is_identical
    assert result.same_value == ["A", "B"]


def test_compare_detects_only_in_source(vault_dir):
    _seed(vault_dir, "dev", {"A": "1", "B": "2"})
    _seed(vault_dir, "prod", {"A": "1"})
    result = compare_envs(vault_dir, "dev", "prod", PASSWORD)
    assert "B" in result.only_in_source
    assert result.only_in_target == []


def test_compare_detects_only_in_target(vault_dir):
    _seed(vault_dir, "dev", {"A": "1"})
    _seed(vault_dir, "prod", {"A": "1", "C": "3"})
    result = compare_envs(vault_dir, "dev", "prod", PASSWORD)
    assert "C" in result.only_in_target
    assert result.only_in_source == []


def test_compare_detects_different_values(vault_dir):
    _seed(vault_dir, "dev", {"DB_URL": "localhost"})
    _seed(vault_dir, "prod", {"DB_URL": "prod-host"})
    result = compare_envs(vault_dir, "dev", "prod", PASSWORD)
    assert "DB_URL" in result.different_value
    assert not result.is_identical


def test_compare_total_keys(vault_dir):
    _seed(vault_dir, "dev", {"A": "1", "B": "2", "C": "3"})
    _seed(vault_dir, "prod", {"A": "1", "B": "changed", "D": "4"})
    result = compare_envs(vault_dir, "dev", "prod", PASSWORD)
    # A=same, B=different, C=only_src, D=only_tgt
    assert result.total_keys == 4


def test_compare_with_key_filter(vault_dir):
    _seed(vault_dir, "dev", {"A": "1", "B": "2", "C": "3"})
    _seed(vault_dir, "prod", {"A": "1", "B": "changed", "C": "3"})
    result = compare_envs(vault_dir, "dev", "prod", PASSWORD, keys=["A", "B"])
    assert result.same_value == ["A"]
    assert result.different_value == ["B"]
    assert "C" not in result.same_value


def test_compare_source_env_and_target_env_stored(vault_dir):
    _seed(vault_dir, "staging", {"X": "1"})
    _seed(vault_dir, "prod", {"X": "1"})
    result = compare_envs(vault_dir, "staging", "prod", PASSWORD)
    assert result.source_env == "staging"
    assert result.target_env == "prod"
