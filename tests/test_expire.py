"""Tests for envault.expire."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from envault.store import save_vault, load_vault
from envault.ttl import set_ttl, _ttl_path
from envault.expire import expire_env, ExpireResult


@pytest.fixture()
def vault_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def _seed(vault_dir: str, env: str, secrets: dict, password: str = "pw") -> None:
    save_vault(vault_dir, env, secrets, password)


# ---------------------------------------------------------------------------
# expire_env
# ---------------------------------------------------------------------------

def test_expire_env_returns_expire_result(vault_dir):
    _seed(vault_dir, "dev", {"KEY": "val"}, "pw")
    result = expire_env(vault_dir, "dev", "pw")
    assert isinstance(result, ExpireResult)


def test_expire_env_no_ttl_file_returns_empty(vault_dir):
    _seed(vault_dir, "dev", {"KEY": "val"}, "pw")
    result = expire_env(vault_dir, "dev", "pw")
    assert result.total_removed == 0
    assert result.removed_keys == []


def test_expire_env_removes_expired_key(vault_dir):
    _seed(vault_dir, "dev", {"OLD": "gone", "NEW": "keep"}, "pw")
    # set TTL that is already expired (1 second, then sleep)
    set_ttl(vault_dir, "dev", "OLD", 1)
    time.sleep(1.1)

    result = expire_env(vault_dir, "dev", "pw")
    assert "OLD" in result.removed_keys
    assert result.total_removed == 1


def test_expire_env_keeps_non_expired_key(vault_dir):
    _seed(vault_dir, "dev", {"FRESH": "here"}, "pw")
    set_ttl(vault_dir, "dev", "FRESH", 9999)

    result = expire_env(vault_dir, "dev", "pw")
    assert "FRESH" not in result.removed_keys
    assert result.total_removed == 0


def test_expire_env_secret_no_longer_readable_after_expiry(vault_dir):
    _seed(vault_dir, "dev", {"GONE": "bye"}, "pw")
    set_ttl(vault_dir, "dev", "GONE", 1)
    time.sleep(1.1)

    expire_env(vault_dir, "dev", "pw")
    secrets = load_vault(vault_dir, "dev", "pw")
    assert "GONE" not in secrets


def test_expire_env_dry_run_does_not_modify_vault(vault_dir):
    _seed(vault_dir, "dev", {"TMP": "val"}, "pw")
    set_ttl(vault_dir, "dev", "TMP", 1)
    time.sleep(1.1)

    result = expire_env(vault_dir, "dev", "pw", dry_run=True)
    assert "TMP" in result.removed_keys

    # vault must be untouched
    secrets = load_vault(vault_dir, "dev", "pw")
    assert "TMP" in secrets


def test_expire_env_dry_run_does_not_modify_ttl_registry(vault_dir):
    _seed(vault_dir, "dev", {"TMP": "val"}, "pw")
    set_ttl(vault_dir, "dev", "TMP", 1)
    time.sleep(1.1)

    ttl_file = Path(_ttl_path(vault_dir, "dev"))
    before = json.loads(ttl_file.read_text())

    expire_env(vault_dir, "dev", "pw", dry_run=True)

    after = json.loads(ttl_file.read_text())
    assert before == after


def test_expire_env_cleans_ttl_entry_after_removal(vault_dir):
    _seed(vault_dir, "dev", {"STALE": "x"}, "pw")
    set_ttl(vault_dir, "dev", "STALE", 1)
    time.sleep(1.1)

    expire_env(vault_dir, "dev", "pw")

    ttl_file = Path(_ttl_path(vault_dir, "dev"))
    registry = json.loads(ttl_file.read_text())
    assert "STALE" not in registry
