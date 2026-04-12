"""Tests for envault/mask.py"""
import pytest

from envault.store import save_vault, load_vault
from envault.mask import (
    MaskResult,
    MaskError,
    mask_keys,
    unmask_keys,
    is_masked,
    _MASK_PREFIX,
)


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


PASSWORD = "test-password"
ENV = "production"


def _seed(vault_dir, data=None):
    data = data or {"API_KEY": "abc123", "DB_PASS": "secret", "PORT": "8080"}
    save_vault(vault_dir, ENV, PASSWORD, data)
    return data


# ---------------------------------------------------------------------------
# is_masked
# ---------------------------------------------------------------------------

def test_is_masked_returns_true_for_prefixed_value():
    assert is_masked(_MASK_PREFIX + "hello") is True


def test_is_masked_returns_false_for_plain_value():
    assert is_masked("hello") is False


def test_is_masked_returns_false_for_empty_string():
    assert is_masked("") is False


# ---------------------------------------------------------------------------
# mask_keys
# ---------------------------------------------------------------------------

def test_mask_keys_returns_mask_result(vault_dir):
    _seed(vault_dir)
    result = mask_keys(vault_dir, ENV, PASSWORD, ["API_KEY"])
    assert isinstance(result, MaskResult)


def test_mask_keys_records_masked_key(vault_dir):
    _seed(vault_dir)
    result = mask_keys(vault_dir, ENV, PASSWORD, ["API_KEY"])
    assert "API_KEY" in result.masked


def test_mask_keys_value_has_prefix(vault_dir):
    _seed(vault_dir)
    mask_keys(vault_dir, ENV, PASSWORD, ["API_KEY"])
    vault = load_vault(vault_dir, ENV, PASSWORD)
    assert vault["API_KEY"].startswith(_MASK_PREFIX)


def test_mask_keys_all_keys_when_none_specified(vault_dir):
    data = _seed(vault_dir)
    result = mask_keys(vault_dir, ENV, PASSWORD)
    assert result.total_masked == len(data)


def test_mask_keys_skips_already_masked(vault_dir):
    _seed(vault_dir)
    mask_keys(vault_dir, ENV, PASSWORD, ["DB_PASS"])
    result = mask_keys(vault_dir, ENV, PASSWORD, ["DB_PASS"])
    assert "DB_PASS" in result.skipped
    assert result.total_masked == 0


def test_mask_keys_skips_missing_key(vault_dir):
    _seed(vault_dir)
    result = mask_keys(vault_dir, ENV, PASSWORD, ["NONEXISTENT"])
    assert "NONEXISTENT" in result.skipped


# ---------------------------------------------------------------------------
# unmask_keys
# ---------------------------------------------------------------------------

def test_unmask_keys_removes_prefix(vault_dir):
    _seed(vault_dir)
    mask_keys(vault_dir, ENV, PASSWORD, ["API_KEY"])
    unmask_keys(vault_dir, ENV, PASSWORD, ["API_KEY"])
    vault = load_vault(vault_dir, ENV, PASSWORD)
    assert not vault["API_KEY"].startswith(_MASK_PREFIX)
    assert vault["API_KEY"] == "abc123"


def test_unmask_keys_records_unmasked_key(vault_dir):
    _seed(vault_dir)
    mask_keys(vault_dir, ENV, PASSWORD, ["PORT"])
    result = unmask_keys(vault_dir, ENV, PASSWORD, ["PORT"])
    assert "PORT" in result.unmasked


def test_unmask_keys_skips_non_masked_key(vault_dir):
    _seed(vault_dir)
    result = unmask_keys(vault_dir, ENV, PASSWORD, ["API_KEY"])
    assert "API_KEY" in result.skipped
    assert result.total_unmasked == 0


def test_unmask_keys_skips_missing_key(vault_dir):
    _seed(vault_dir)
    result = unmask_keys(vault_dir, ENV, PASSWORD, ["GHOST"])
    assert "GHOST" in result.skipped
