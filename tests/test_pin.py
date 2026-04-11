"""Tests for envault.pin."""

import pytest

from envault.pin import (
    PinError,
    is_pinned,
    list_pins,
    pin_key,
    unpin_key,
    _pin_path,
)
from envault.store import save_vault


PASSWORD = "hunter2"


@pytest.fixture()
def vault_dir(tmp_path):
    save_vault(str(tmp_path), "dev", {"API_KEY": "abc", "DB_PASS": "secret"}, PASSWORD)
    save_vault(str(tmp_path), "prod", {"API_KEY": "xyz"}, PASSWORD)
    return str(tmp_path)


def test_pin_key_returns_true_on_new_pin(vault_dir):
    assert pin_key(vault_dir, "dev", "API_KEY") is True


def test_pin_key_returns_false_when_already_pinned(vault_dir):
    pin_key(vault_dir, "dev", "API_KEY")
    assert pin_key(vault_dir, "dev", "API_KEY") is False


def test_pin_key_creates_pin_file(vault_dir):
    pin_key(vault_dir, "dev", "API_KEY")
    assert _pin_path(vault_dir).exists()


def test_pin_key_nonexistent_environment_raises(vault_dir):
    with pytest.raises(PinError, match="staging"):
        pin_key(vault_dir, "staging", "API_KEY")


def test_is_pinned_true_after_pin(vault_dir):
    pin_key(vault_dir, "dev", "DB_PASS")
    assert is_pinned(vault_dir, "dev", "DB_PASS") is True


def test_is_pinned_false_before_pin(vault_dir):
    assert is_pinned(vault_dir, "dev", "DB_PASS") is False


def test_is_pinned_false_after_unpin(vault_dir):
    pin_key(vault_dir, "dev", "API_KEY")
    unpin_key(vault_dir, "dev", "API_KEY")
    assert is_pinned(vault_dir, "dev", "API_KEY") is False


def test_unpin_key_returns_true_when_removed(vault_dir):
    pin_key(vault_dir, "dev", "API_KEY")
    assert unpin_key(vault_dir, "dev", "API_KEY") is True


def test_unpin_key_returns_false_when_not_pinned(vault_dir):
    assert unpin_key(vault_dir, "dev", "MISSING") is False


def test_unpin_removes_empty_environment_entry(vault_dir):
    pin_key(vault_dir, "dev", "API_KEY")
    unpin_key(vault_dir, "dev", "API_KEY")
    pins = list_pins(vault_dir)
    assert "dev" not in pins


def test_list_pins_returns_all_environments(vault_dir):
    pin_key(vault_dir, "dev", "API_KEY")
    pin_key(vault_dir, "prod", "API_KEY")
    result = list_pins(vault_dir)
    assert "dev" in result
    assert "prod" in result


def test_list_pins_filtered_by_environment(vault_dir):
    pin_key(vault_dir, "dev", "API_KEY")
    pin_key(vault_dir, "prod", "API_KEY")
    result = list_pins(vault_dir, environment="dev")
    assert list(result.keys()) == ["dev"]


def test_pin_keys_are_sorted(vault_dir):
    pin_key(vault_dir, "dev", "DB_PASS")
    pin_key(vault_dir, "dev", "API_KEY")
    result = list_pins(vault_dir, environment="dev")
    assert result["dev"] == sorted(result["dev"])
