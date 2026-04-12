"""Tests for envault.sanitize."""

import pytest

from envault.sanitize import (
    SanitizeError,
    SanitizeResult,
    sanitize_key,
    sanitize_value,
    sanitize_env,
)


# ---------------------------------------------------------------------------
# sanitize_key
# ---------------------------------------------------------------------------

def test_sanitize_key_uppercase():
    key, warnings = sanitize_key("my_key")
    assert key == "MY_KEY"
    assert any("uppercased" in w for w in warnings)


def test_sanitize_key_strips_whitespace():
    key, warnings = sanitize_key("  DB_HOST  ")
    assert key == "DB_HOST"
    assert any("whitespace" in w for w in warnings)


def test_sanitize_key_replaces_hyphens_with_underscores():
    key, _ = sanitize_key("MY-KEY")
    assert key == "MY_KEY"


def test_sanitize_key_removes_invalid_chars():
    key, _ = sanitize_key("MY!KEY@NAME")
    assert key == "MYKEYNAME"


def test_sanitize_key_leading_digit_gets_prefix():
    key, warnings = sanitize_key("1SECRET")
    assert key == "_1SECRET"
    assert any("digit" in w for w in warnings)


def test_sanitize_key_already_valid_no_warnings():
    key, warnings = sanitize_key("VALID_KEY_123")
    assert key == "VALID_KEY_123"
    assert warnings == []


def test_sanitize_key_empty_after_sanitization_raises():
    with pytest.raises(SanitizeError):
        sanitize_key("!!!")


# ---------------------------------------------------------------------------
# sanitize_value
# ---------------------------------------------------------------------------

def test_sanitize_value_removes_null_bytes():
    value, warnings = sanitize_value("hello\x00world")
    assert value == "helloworld"
    assert any("null" in w for w in warnings)


def test_sanitize_value_strips_trailing_whitespace():
    value, warnings = sanitize_value("my_value   ")
    assert value == "my_value"
    assert any("trailing" in w for w in warnings)


def test_sanitize_value_preserves_leading_whitespace():
    value, _ = sanitize_value("  leading")
    assert value == "  leading"


def test_sanitize_value_clean_value_no_warnings():
    value, warnings = sanitize_value("clean")
    assert value == "clean"
    assert warnings == []


# ---------------------------------------------------------------------------
# sanitize_env
# ---------------------------------------------------------------------------

def test_sanitize_env_returns_results_list():
    results = sanitize_env({"my_key": "value", "OTHER": "val2"})
    assert len(results) == 2
    assert all(isinstance(r, SanitizeResult) for r in results)


def test_sanitize_env_any_changed_true_when_key_modified():
    results = sanitize_env({"lower": "value"})
    assert results[0].any_changed is True
    assert results[0].key_changed is True


def test_sanitize_env_any_changed_false_when_nothing_modified():
    results = sanitize_env({"CLEAN_KEY": "clean_value"})
    assert results[0].any_changed is False


def test_sanitize_env_raises_on_unrecoverable_key():
    with pytest.raises(SanitizeError):
        sanitize_env({"@@@": "value"})
