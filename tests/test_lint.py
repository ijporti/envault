"""Tests for envault.lint."""

import pytest
from envault.lint import LintIssue, lint_keys, lint_values, lint_env, lint_all


# ---------------------------------------------------------------------------
# lint_keys
# ---------------------------------------------------------------------------

def test_lint_keys_valid_returns_empty():
    issues = lint_keys({"DATABASE_URL": "x", "API_KEY": "y"})
    assert issues == []


def test_lint_keys_lowercase_is_warning():
    issues = lint_keys({"database_url": "x"})
    assert len(issues) == 1
    assert issues[0].severity == "warning"
    assert issues[0].key == "database_url"


def test_lint_keys_invalid_chars_is_error():
    issues = lint_keys({"MY-KEY": "x"})
    assert len(issues) == 1
    assert issues[0].severity == "error"


def test_lint_keys_empty_key_is_error():
    issues = lint_keys({"": "x"})
    assert len(issues) == 1
    assert issues[0].severity == "error"


def test_lint_keys_attaches_environment():
    issues = lint_keys({"bad-key": "v"}, environment="production")
    assert issues[0].environment == "production"


# ---------------------------------------------------------------------------
# lint_values
# ---------------------------------------------------------------------------

def test_lint_values_valid_returns_empty():
    issues = lint_values({"KEY": "some_value"})
    assert issues == []


def test_lint_values_empty_value_is_warning():
    issues = lint_values({"KEY": ""})
    assert len(issues) == 1
    assert issues[0].severity == "warning"
    assert "empty" in issues[0].message.lower()


def test_lint_values_leading_whitespace_is_warning():
    issues = lint_values({"KEY": "  value"})
    assert len(issues) == 1
    assert "whitespace" in issues[0].message.lower()


def test_lint_values_trailing_whitespace_is_warning():
    issues = lint_values({"KEY": "value  "})
    assert len(issues) == 1


# ---------------------------------------------------------------------------
# lint_env
# ---------------------------------------------------------------------------

def test_lint_env_combines_key_and_value_issues():
    secrets = {"bad-key": "  spaced  ", "GOOD_KEY": ""}
    issues = lint_env(secrets)
    severities = {i.severity for i in issues}
    assert "error" in severities
    assert "warning" in severities


# ---------------------------------------------------------------------------
# lint_all
# ---------------------------------------------------------------------------

def test_lint_all_returns_issues_from_all_envs():
    vault = {
        "staging": {"GOOD": "ok"},
        "production": {"bad-key": "val", "EMPTY": ""},
    }
    issues = lint_all(vault)
    envs = {i.environment for i in issues}
    assert "production" in envs
    assert "staging" not in envs  # staging has no issues


def test_lint_all_empty_vault_returns_empty():
    assert lint_all({}) == []


# ---------------------------------------------------------------------------
# LintIssue.__str__
# ---------------------------------------------------------------------------

def test_lint_issue_str_with_environment():
    issue = LintIssue(key="X", severity="error", message="bad", environment="prod")
    text = str(issue)
    assert "ERROR" in text
    assert "[prod]" in text
    assert "X" in text


def test_lint_issue_str_without_environment():
    issue = LintIssue(key="X", severity="warning", message="hmm")
    text = str(issue)
    assert "[" not in text
