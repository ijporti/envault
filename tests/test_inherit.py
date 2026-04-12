"""Tests for envault.inherit."""

from __future__ import annotations

import pytest

from envault.store import save_vault, load_vault
from envault.inherit import InheritError, InheritResult, apply_inheritance, resolve_env


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _seed(vault_dir, env, secrets, password="pw"):
    save_vault(vault_dir, env, secrets, password)


# ---------------------------------------------------------------------------
# apply_inheritance
# ---------------------------------------------------------------------------

def test_apply_inheritance_returns_inherit_result(vault_dir):
    _seed(vault_dir, "base", {"A": "1", "B": "2"})
    _seed(vault_dir, "dev", {"C": "3"})
    result = apply_inheritance(vault_dir, "dev", "base", "pw")
    assert isinstance(result, InheritResult)


def test_apply_inheritance_adds_missing_keys(vault_dir):
    _seed(vault_dir, "base", {"A": "1", "B": "2"})
    _seed(vault_dir, "dev", {"C": "3"})
    apply_inheritance(vault_dir, "dev", "base", "pw")
    data = load_vault(vault_dir, "dev", "pw")
    assert data["A"] == "1"
    assert data["B"] == "2"
    assert data["C"] == "3"


def test_apply_inheritance_skips_existing_keys_by_default(vault_dir):
    _seed(vault_dir, "base", {"A": "base_val"})
    _seed(vault_dir, "dev", {"A": "dev_val"})
    result = apply_inheritance(vault_dir, "dev", "base", "pw")
    data = load_vault(vault_dir, "dev", "pw")
    assert data["A"] == "dev_val"
    assert "A" in result.keys_skipped


def test_apply_inheritance_overwrites_when_flag_set(vault_dir):
    _seed(vault_dir, "base", {"A": "base_val"})
    _seed(vault_dir, "dev", {"A": "dev_val"})
    apply_inheritance(vault_dir, "dev", "base", "pw", overwrite=True)
    data = load_vault(vault_dir, "dev", "pw")
    assert data["A"] == "base_val"


def test_apply_inheritance_creates_child_if_missing(vault_dir):
    _seed(vault_dir, "base", {"X": "10"})
    result = apply_inheritance(vault_dir, "newenv", "base", "pw")
    data = load_vault(vault_dir, "newenv", "pw")
    assert data["X"] == "10"
    assert result.total_inherited == 1


def test_apply_inheritance_same_env_raises(vault_dir):
    _seed(vault_dir, "base", {"A": "1"})
    with pytest.raises(InheritError):
        apply_inheritance(vault_dir, "base", "base", "pw")


def test_apply_inheritance_counts_are_correct(vault_dir):
    _seed(vault_dir, "base", {"A": "1", "B": "2", "C": "3"})
    _seed(vault_dir, "dev", {"A": "own"})
    result = apply_inheritance(vault_dir, "dev", "base", "pw")
    assert result.total_inherited == 2   # B and C
    assert result.total_skipped == 1     # A


# ---------------------------------------------------------------------------
# resolve_env
# ---------------------------------------------------------------------------

def test_resolve_env_merges_without_persisting(vault_dir):
    _seed(vault_dir, "base", {"A": "1", "B": "2"})
    _seed(vault_dir, "dev", {"B": "override", "C": "3"})
    merged = resolve_env(vault_dir, "dev", "base", "pw")
    assert merged["A"] == "1"
    assert merged["B"] == "override"   # child wins
    assert merged["C"] == "3"
    # vault on disk must NOT be changed
    on_disk = load_vault(vault_dir, "dev", "pw")
    assert "A" not in on_disk
