"""Tests for envault.transform."""

from __future__ import annotations

import base64
import os
import pytest

from envault.store import save_vault
from envault.transform import (
    TransformError,
    TransformResult,
    apply_transform,
    available_transforms,
    transform_env,
)

PASSWORD = "test-secret"


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _seed(vault_dir, env, secrets):
    save_vault(vault_dir, env, PASSWORD, secrets)


# ---------------------------------------------------------------------------
# apply_transform unit tests
# ---------------------------------------------------------------------------

def test_available_transforms_returns_list():
    names = available_transforms()
    assert isinstance(names, list)
    assert "upper" in names
    assert "lower" in names
    assert "base64_encode" in names


def test_apply_transform_upper():
    assert apply_transform("hello", "upper") == "HELLO"


def test_apply_transform_lower():
    assert apply_transform("WORLD", "lower") == "world"


def test_apply_transform_strip():
    assert apply_transform("  hi  ", "strip") == "hi"


def test_apply_transform_reverse():
    assert apply_transform("abc", "reverse") == "cba"


def test_apply_transform_base64_roundtrip():
    original = "my-secret-value"
    encoded = apply_transform(original, "base64_encode")
    decoded = apply_transform(encoded, "base64_decode")
    assert decoded == original


def test_apply_transform_trim_quotes():
    assert apply_transform('"hello"', "trim_quotes") == "hello"
    assert apply_transform("'world'", "trim_quotes") == "world"


def test_apply_transform_unknown_raises():
    with pytest.raises(TransformError, match="Unknown transform"):
        apply_transform("value", "nonexistent_transform")


def test_apply_transform_base64_decode_invalid_raises():
    with pytest.raises(TransformError, match="failed"):
        apply_transform("not-valid-base64!!!", "base64_decode")


# ---------------------------------------------------------------------------
# transform_env integration tests
# ---------------------------------------------------------------------------

def test_transform_env_returns_transform_result(vault_dir):
    _seed(vault_dir, "dev", {"KEY": "hello"})
    result = transform_env(vault_dir, "dev", PASSWORD, "upper")
    assert isinstance(result, TransformResult)


def test_transform_env_changes_values(vault_dir):
    _seed(vault_dir, "dev", {"KEY": "hello"})
    result = transform_env(vault_dir, "dev", PASSWORD, "upper")
    assert "KEY" in result.changed
    assert result.changed["KEY"] == "HELLO"


def test_transform_env_persists_changes(vault_dir):
    from envault.store import load_vault
    _seed(vault_dir, "dev", {"KEY": "hello"})
    transform_env(vault_dir, "dev", PASSWORD, "upper")
    secrets = load_vault(vault_dir, "dev", PASSWORD)
    assert secrets["KEY"] == "HELLO"


def test_transform_env_skips_missing_keys(vault_dir):
    _seed(vault_dir, "dev", {"KEY": "hello"})
    result = transform_env(vault_dir, "dev", PASSWORD, "upper", keys=["KEY", "MISSING"])
    assert "MISSING" in result.skipped
    assert "KEY" in result.changed


def test_transform_env_no_change_not_counted(vault_dir):
    _seed(vault_dir, "dev", {"KEY": "ALREADY_UPPER"})
    result = transform_env(vault_dir, "dev", PASSWORD, "upper")
    assert result.total_changed == 0
    assert "KEY" not in result.changed


def test_transform_env_subset_of_keys(vault_dir):
    _seed(vault_dir, "dev", {"A": "hello", "B": "world"})
    result = transform_env(vault_dir, "dev", PASSWORD, "upper", keys=["A"])
    assert "A" in result.changed
    assert "B" not in result.changed
