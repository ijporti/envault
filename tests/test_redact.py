"""Tests for envault.redact."""

import pytest

from envault.redact import (
    RedactError,
    RedactResult,
    is_sensitive_key,
    mask_value,
    redact_dict,
)


# ---------------------------------------------------------------------------
# is_sensitive_key
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", [
    "PASSWORD", "db_password", "API_KEY", "api-key",
    "SECRET", "auth_token", "PRIVATE_KEY", "credential",
])
def test_is_sensitive_key_returns_true_for_known_patterns(key):
    assert is_sensitive_key(key) is True


@pytest.mark.parametrize("key", ["USERNAME", "HOST", "PORT", "DATABASE_URL", "TIMEOUT"])
def test_is_sensitive_key_returns_false_for_non_sensitive(key):
    assert is_sensitive_key(key) is False


# ---------------------------------------------------------------------------
# mask_value
# ---------------------------------------------------------------------------

def test_mask_value_default_returns_mask_only():
    assert mask_value("supersecret") == "********"


def test_mask_value_visible_chars_preserves_suffix():
    result = mask_value("supersecret", visible_chars=4)
    assert result.endswith("cret")
    assert result.startswith("****")


def test_mask_value_visible_chars_exceeds_length_returns_mask_only():
    assert mask_value("hi", visible_chars=10) == "********"


def test_mask_value_custom_mask():
    assert mask_value("value", mask="REDACTED") == "REDACTED"


def test_mask_value_negative_visible_chars_raises():
    with pytest.raises(RedactError):
        mask_value("value", visible_chars=-1)


# ---------------------------------------------------------------------------
# redact_dict
# ---------------------------------------------------------------------------

def test_redact_dict_returns_redact_result():
    result = redact_dict({"API_KEY": "abc123", "HOST": "localhost"})
    assert isinstance(result, RedactResult)


def test_redact_dict_auto_detects_sensitive_keys():
    result = redact_dict({"DB_PASSWORD": "s3cr3t", "HOST": "localhost"})
    assert result.data["DB_PASSWORD"] == "********"
    assert result.data["HOST"] == "localhost"


def test_redact_dict_explicit_keys_are_redacted():
    result = redact_dict({"FOO": "bar", "BAZ": "qux"}, keys=["FOO"], auto_detect=False)
    assert result.data["FOO"] == "********"
    assert result.data["BAZ"] == "qux"


def test_redact_dict_counts_are_correct():
    secrets = {"API_KEY": "k", "SECRET": "s", "HOST": "h"}
    result = redact_dict(secrets)
    assert result.original_count == 3
    assert result.redacted_count == 2
    assert result.total_visible == 1


def test_redact_dict_auto_detect_disabled_skips_patterns():
    result = redact_dict({"API_KEY": "abc"}, auto_detect=False)
    assert result.data["API_KEY"] == "abc"
    assert result.redacted_count == 0


def test_redact_dict_visible_chars_propagated():
    result = redact_dict({"TOKEN": "abcdef"}, visible_chars=2)
    assert result.data["TOKEN"].endswith("ef")


def test_redact_dict_empty_secrets_returns_empty_result():
    result = redact_dict({})
    assert result.original_count == 0
    assert result.redacted_count == 0
    assert result.data == {}
