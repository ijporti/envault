"""Tests for envault.ttl module."""

import time
from pathlib import Path

import pytest

from envault.store import save_vault
from envault.ttl import (
    TTLEntry,
    list_ttl,
    purge_expired,
    set_ttl,
    _ttl_path,
)

PASSWORD = "test-password"


@pytest.fixture
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def _seed(vault_dir: Path, env: str, secrets: dict) -> None:
    save_vault(vault_dir, env, secrets, PASSWORD)


# ---------------------------------------------------------------------------
# set_ttl
# ---------------------------------------------------------------------------

def test_set_ttl_returns_entry(vault_dir):
    _seed(vault_dir, "prod", {"API_KEY": "abc"})
    entry = set_ttl(vault_dir, "prod", "API_KEY", ttl_seconds=300)
    assert isinstance(entry, TTLEntry)
    assert entry.key == "API_KEY"
    assert entry.environment == "prod"


def test_set_ttl_creates_registry_file(vault_dir):
    _seed(vault_dir, "prod", {"API_KEY": "abc"})
    set_ttl(vault_dir, "prod", "API_KEY", ttl_seconds=300)
    assert _ttl_path(vault_dir).exists()


def test_set_ttl_overwrites_existing_entry(vault_dir):
    _seed(vault_dir, "prod", {"API_KEY": "abc"})
    set_ttl(vault_dir, "prod", "API_KEY", ttl_seconds=300)
    entry2 = set_ttl(vault_dir, "prod", "API_KEY", ttl_seconds=600)
    entries = list_ttl(vault_dir, "prod")
    assert len(entries) == 1
    assert entries[0].expires_at == pytest.approx(entry2.expires_at, abs=1)


def test_ttl_entry_not_expired_when_fresh(vault_dir):
    _seed(vault_dir, "prod", {"TOKEN": "xyz"})
    entry = set_ttl(vault_dir, "prod", "TOKEN", ttl_seconds=3600)
    assert not entry.is_expired()
    assert entry.seconds_remaining() > 0


def test_ttl_entry_is_expired_when_past(vault_dir):
    _seed(vault_dir, "prod", {"TOKEN": "xyz"})
    entry = set_ttl(vault_dir, "prod", "TOKEN", ttl_seconds=-1)
    assert entry.is_expired()
    assert entry.seconds_remaining() == 0.0


# ---------------------------------------------------------------------------
# list_ttl
# ---------------------------------------------------------------------------

def test_list_ttl_returns_all_entries(vault_dir):
    _seed(vault_dir, "prod", {"A": "1", "B": "2"})
    _seed(vault_dir, "staging", {"C": "3"})
    set_ttl(vault_dir, "prod", "A", ttl_seconds=300)
    set_ttl(vault_dir, "prod", "B", ttl_seconds=300)
    set_ttl(vault_dir, "staging", "C", ttl_seconds=300)
    assert len(list_ttl(vault_dir)) == 3


def test_list_ttl_filtered_by_environment(vault_dir):
    _seed(vault_dir, "prod", {"A": "1"})
    _seed(vault_dir, "staging", {"B": "2"})
    set_ttl(vault_dir, "prod", "A", ttl_seconds=300)
    set_ttl(vault_dir, "staging", "B", ttl_seconds=300)
    result = list_ttl(vault_dir, environment="prod")
    assert len(result) == 1
    assert result[0].environment == "prod"


def test_list_ttl_empty_when_no_registry(vault_dir):
    assert list_ttl(vault_dir) == []


# ---------------------------------------------------------------------------
# purge_expired
# ---------------------------------------------------------------------------

def test_purge_expired_removes_expired_key(vault_dir):
    _seed(vault_dir, "prod", {"OLD_KEY": "val", "KEEP": "keep"})
    set_ttl(vault_dir, "prod", "OLD_KEY", ttl_seconds=-1)  # already expired
    removed = purge_expired(vault_dir, PASSWORD)
    assert "prod/OLD_KEY" in removed


def test_purge_expired_preserves_non_expired_key(vault_dir):
    from envault.store import load_vault
    _seed(vault_dir, "prod", {"OLD_KEY": "val", "KEEP": "keep"})
    set_ttl(vault_dir, "prod", "OLD_KEY", ttl_seconds=-1)
    purge_expired(vault_dir, PASSWORD)
    secrets = load_vault(vault_dir, "prod", PASSWORD)
    assert "KEEP" in secrets
    assert "OLD_KEY" not in secrets


def test_purge_expired_cleans_ttl_registry(vault_dir):
    _seed(vault_dir, "prod", {"OLD_KEY": "val"})
    set_ttl(vault_dir, "prod", "OLD_KEY", ttl_seconds=-1)
    purge_expired(vault_dir, PASSWORD)
    remaining = list_ttl(vault_dir)
    assert all(not e.is_expired() for e in remaining)


def test_purge_expired_returns_empty_when_nothing_expired(vault_dir):
    _seed(vault_dir, "prod", {"KEY": "val"})
    set_ttl(vault_dir, "prod", "KEY", ttl_seconds=3600)
    removed = purge_expired(vault_dir, PASSWORD)
    assert removed == []
