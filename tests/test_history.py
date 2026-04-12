"""Tests for envault.history."""

import time
from pathlib import Path

import pytest

from envault.history import (
    HistoryEntry,
    clear_history,
    get_history,
    record_change,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_record_change_returns_history_entry(vault_dir):
    entry = record_change(vault_dir, "dev", "API_KEY", "secret123")
    assert isinstance(entry, HistoryEntry)
    assert entry.key == "API_KEY"
    assert entry.value == "secret123"


def test_record_change_creates_history_file(vault_dir):
    record_change(vault_dir, "dev", "DB_URL", "postgres://localhost")
    assert (vault_dir / ".history_dev.json").exists()


def test_record_change_timestamp_is_recent(vault_dir):
    before = time.time()
    entry = record_change(vault_dir, "dev", "TOKEN", "abc")
    after = time.time()
    assert before <= entry.timestamp <= after


def test_record_change_custom_actor(vault_dir):
    entry = record_change(vault_dir, "dev", "KEY", "val", actor="ci-bot")
    assert entry.actor == "ci-bot"


def test_get_history_returns_newest_first(vault_dir):
    record_change(vault_dir, "dev", "API_KEY", "first")
    record_change(vault_dir, "dev", "API_KEY", "second")
    record_change(vault_dir, "dev", "API_KEY", "third")
    history = get_history(vault_dir, "dev", "API_KEY")
    assert [e.value for e in history] == ["third", "second", "first"]


def test_get_history_limit(vault_dir):
    for i in range(5):
        record_change(vault_dir, "dev", "KEY", str(i))
    history = get_history(vault_dir, "dev", "KEY", limit=2)
    assert len(history) == 2
    assert history[0].value == "4"


def test_get_history_missing_key_returns_empty(vault_dir):
    history = get_history(vault_dir, "dev", "NONEXISTENT")
    assert history == []


def test_get_history_missing_environment_returns_empty(vault_dir):
    history = get_history(vault_dir, "staging", "ANY_KEY")
    assert history == []


def test_clear_history_returns_count(vault_dir):
    record_change(vault_dir, "dev", "FOO", "a")
    record_change(vault_dir, "dev", "FOO", "b")
    removed = clear_history(vault_dir, "dev", "FOO")
    assert removed == 2


def test_clear_history_removes_entries(vault_dir):
    record_change(vault_dir, "dev", "BAR", "x")
    clear_history(vault_dir, "dev", "BAR")
    assert get_history(vault_dir, "dev", "BAR") == []


def test_clear_history_missing_key_returns_zero(vault_dir):
    removed = clear_history(vault_dir, "dev", "GHOST")
    assert removed == 0


def test_history_entry_str_format(vault_dir):
    entry = record_change(vault_dir, "dev", "SECRET", "val")
    text = str(entry)
    assert "SECRET" in text
    assert "val" in text
    assert "envault" in text


def test_multiple_keys_stored_independently(vault_dir):
    record_change(vault_dir, "dev", "KEY_A", "a1")
    record_change(vault_dir, "dev", "KEY_B", "b1")
    record_change(vault_dir, "dev", "KEY_A", "a2")
    assert len(get_history(vault_dir, "dev", "KEY_A")) == 2
    assert len(get_history(vault_dir, "dev", "KEY_B")) == 1
