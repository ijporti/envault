"""Tests for envault.validate."""

import pytest

from envault.validate import (
    ValidationError,
    ValidationResult,
    validate_env,
    _rule_not_empty,
    _rule_no_whitespace_only,
    _rule_max_length,
    _rule_key_uppercase,
)


# --- unit tests for individual rules ------------------------------------------

def test_rule_not_empty_passes_for_nonempty():
    assert _rule_not_empty("K", "hello") is None


def test_rule_not_empty_fails_for_empty_string():
    assert _rule_not_empty("K", "") is not None


def test_rule_no_whitespace_only_passes_for_normal_value():
    assert _rule_no_whitespace_only("K", "value") is None


def test_rule_no_whitespace_only_fails_for_spaces():
    assert _rule_no_whitespace_only("K", "   ") is not None


def test_rule_no_whitespace_only_passes_for_empty_string():
    # empty string is handled by not_empty rule, not this one
    assert _rule_no_whitespace_only("K", "") is None


def test_rule_max_length_passes_within_limit():
    assert _rule_max_length("K", "x" * 100) is None


def test_rule_max_length_fails_when_exceeded():
    assert _rule_max_length("K", "x" * 5000) is not None


def test_rule_max_length_custom_limit():
    assert _rule_max_length("K", "hello", max_len=3) is not None


def test_rule_key_uppercase_passes():
    assert _rule_key_uppercase("MY_KEY", "v") is None


def test_rule_key_uppercase_fails_for_lowercase():
    assert _rule_key_uppercase("my_key", "v") is not None


# --- integration tests for validate_env ---------------------------------------

def test_validate_env_returns_list_of_results():
    secrets = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    results = validate_env(secrets, "production")
    assert isinstance(results, list)
    assert all(isinstance(r, ValidationResult) for r in results)


def test_validate_env_all_pass_for_clean_secrets():
    secrets = {"API_KEY": "abc123", "DB_URL": "postgres://localhost/db"}
    results = validate_env(secrets, "staging")
    failures = [r for r in results if not r.passed]
    assert failures == []


def test_validate_env_detects_empty_value():
    secrets = {"SECRET": ""}
    results = validate_env(secrets, "dev", rules=["not_empty"])
    failures = [r for r in results if not r.passed]
    assert len(failures) == 1
    assert failures[0].key == "SECRET"
    assert failures[0].rule == "not_empty"


def test_validate_env_detects_lowercase_key():
    secrets = {"bad_key": "value"}
    results = validate_env(secrets, "dev", rules=["key_uppercase"])
    failures = [r for r in results if not r.passed]
    assert any(r.key == "bad_key" for r in failures)


def test_validate_env_multiple_rules_applied():
    secrets = {"GOOD": "ok", "BAD": ""}
    results = validate_env(secrets, "env", rules=["not_empty", "max_length"])
    # 2 keys × 2 rules = 4 results
    assert len(results) == 4


def test_validate_env_unknown_rule_raises():
    with pytest.raises(ValidationError, match="Unknown validation rules"):
        validate_env({"K": "v"}, "env", rules=["nonexistent_rule"])


def test_validation_result_str_pass():
    r = ValidationResult("MY_KEY", "prod", True, "not_empty", "ok")
    assert "PASS" in str(r)
    assert "MY_KEY" in str(r)


def test_validation_result_str_fail():
    r = ValidationResult("MY_KEY", "prod", False, "not_empty", "value is empty")
    assert "FAIL" in str(r)
    assert "value is empty" in str(r)
