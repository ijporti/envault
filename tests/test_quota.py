"""Tests for envault.quota."""

from __future__ import annotations

import pytest
from pathlib import Path

from envault.quota import (
    QuotaError,
    QuotaResult,
    check_quota,
    remove_quota,
    set_quota,
    _quota_path,
)
from envault.store import save_vault


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def _seed(vault_dir: Path, env: str, secrets: dict, password: str = "pw") -> None:
    save_vault(vault_dir, env, secrets, password)


# ---------------------------------------------------------------------------
# set_quota
# ---------------------------------------------------------------------------

def test_set_quota_returns_limit(vault_dir):
    result = set_quota(vault_dir, "production", 10)
    assert result == 10


def test_set_quota_creates_registry_file(vault_dir):
    set_quota(vault_dir, "staging", 5)
    assert _quota_path(vault_dir).exists()


def test_set_quota_persists_across_calls(vault_dir):
    set_quota(vault_dir, "dev", 3)
    set_quota(vault_dir, "prod", 20)
    # overwrite dev
    set_quota(vault_dir, "dev", 7)
    result = check_quota(vault_dir, "dev", "pw", default_limit=None)
    assert result.limit == 7


def test_set_quota_zero_raises(vault_dir):
    with pytest.raises(QuotaError):
        set_quota(vault_dir, "dev", 0)


def test_set_quota_negative_raises(vault_dir):
    with pytest.raises(QuotaError):
        set_quota(vault_dir, "dev", -5)


# ---------------------------------------------------------------------------
# remove_quota
# ---------------------------------------------------------------------------

def test_remove_quota_returns_true_when_exists(vault_dir):
    set_quota(vault_dir, "staging", 5)
    assert remove_quota(vault_dir, "staging") is True


def test_remove_quota_returns_false_when_missing(vault_dir):
    assert remove_quota(vault_dir, "nonexistent") is False


# ---------------------------------------------------------------------------
# check_quota
# ---------------------------------------------------------------------------

def test_check_quota_returns_quota_result(vault_dir):
    set_quota(vault_dir, "dev", 10)
    _seed(vault_dir, "dev", {"KEY": "val"}, "pw")
    result = check_quota(vault_dir, "dev", "pw")
    assert isinstance(result, QuotaResult)


def test_check_quota_correct_current_count(vault_dir):
    set_quota(vault_dir, "dev", 10)
    _seed(vault_dir, "dev", {"A": "1", "B": "2", "C": "3"}, "pw")
    result = check_quota(vault_dir, "dev", "pw")
    assert result.current == 3


def test_check_quota_not_exceeded(vault_dir):
    set_quota(vault_dir, "dev", 10)
    _seed(vault_dir, "dev", {"A": "1"}, "pw")
    result = check_quota(vault_dir, "dev", "pw")
    assert result.exceeded is False


def test_check_quota_exceeded(vault_dir):
    set_quota(vault_dir, "dev", 2)
    _seed(vault_dir, "dev", {"A": "1", "B": "2", "C": "3"}, "pw")
    result = check_quota(vault_dir, "dev", "pw")
    assert result.exceeded is True


def test_check_quota_remaining(vault_dir):
    set_quota(vault_dir, "dev", 5)
    _seed(vault_dir, "dev", {"A": "1", "B": "2"}, "pw")
    result = check_quota(vault_dir, "dev", "pw")
    assert result.remaining == 3


def test_check_quota_remaining_zero_when_exceeded(vault_dir):
    set_quota(vault_dir, "dev", 1)
    _seed(vault_dir, "dev", {"A": "1", "B": "2"}, "pw")
    result = check_quota(vault_dir, "dev", "pw")
    assert result.remaining == 0


def test_check_quota_no_env_file_returns_zero_current(vault_dir):
    set_quota(vault_dir, "empty", 5)
    result = check_quota(vault_dir, "empty", "pw")
    assert result.current == 0


def test_check_quota_no_quota_and_no_default_raises(vault_dir):
    with pytest.raises(QuotaError, match="No quota configured"):
        check_quota(vault_dir, "dev", "pw")


def test_check_quota_uses_default_limit_when_no_quota(vault_dir):
    _seed(vault_dir, "dev", {"A": "1"}, "pw")
    result = check_quota(vault_dir, "dev", "pw", default_limit=50)
    assert result.limit == 50
