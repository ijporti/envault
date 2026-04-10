"""Tests for envault.audit — append-only audit log."""

from __future__ import annotations

import json

import pytest

from envault.audit import record, read_log, _log_path


@pytest.fixture()
def vault_dir(tmp_path):
    return tmp_path


def test_record_creates_log_file(vault_dir):
    record("set", "prod", key="API_KEY", vault_dir=vault_dir)
    assert _log_path(vault_dir).exists()


def test_record_entry_is_valid_json(vault_dir):
    record("set", "prod", key="API_KEY", vault_dir=vault_dir)
    raw = _log_path(vault_dir).read_text(encoding="utf-8").strip()
    entry = json.loads(raw)
    assert isinstance(entry, dict)


def test_record_contains_required_fields(vault_dir):
    record("get", "staging", key="SECRET", vault_dir=vault_dir)
    entries = read_log(vault_dir=vault_dir)
    assert len(entries) == 1
    entry = entries[0]
    assert entry["action"] == "get"
    assert entry["env"] == "staging"
    assert entry["key"] == "SECRET"
    assert "timestamp" in entry


def test_record_without_key(vault_dir):
    record("rotate", "prod", vault_dir=vault_dir)
    entries = read_log(vault_dir=vault_dir)
    assert entries[0]["action"] == "rotate"
    assert "key" not in entries[0]


def test_record_extra_metadata(vault_dir):
    record("set", "dev", key="X", extra={"user": "alice"}, vault_dir=vault_dir)
    entry = read_log(vault_dir=vault_dir)[0]
    assert entry["user"] == "alice"


def test_multiple_records_appended_in_order(vault_dir):
    actions = ["set", "get", "rotate"]
    for action in actions:
        record(action, "prod", vault_dir=vault_dir)
    entries = read_log(vault_dir=vault_dir)
    assert [e["action"] for e in entries] == actions


def test_read_log_returns_empty_list_when_no_log(vault_dir):
    entries = read_log(vault_dir=vault_dir)
    assert entries == []


def test_timestamp_is_iso_format(vault_dir):
    from datetime import datetime
    record("set", "prod", vault_dir=vault_dir)
    entry = read_log(vault_dir=vault_dir)[0]
    # Should parse without raising
    dt = datetime.fromisoformat(entry["timestamp"])
    assert dt.tzinfo is not None  # UTC-aware
