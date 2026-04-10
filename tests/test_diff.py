"""Tests for envault.diff module."""

import pytest

from envault.diff import DiffEntry, diff_envs, format_diff


OLD = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET": "old_secret"}
NEW = {"DB_HOST": "prod.db", "DB_PORT": "5432", "API_KEY": "abc123"}


def test_diff_detects_added_keys():
    entries = diff_envs(OLD, NEW)
    added = [e for e in entries if e.status == "added"]
    assert len(added) == 1
    assert added[0].key == "API_KEY"
    assert added[0].new_value == "abc123"


def test_diff_detects_removed_keys():
    entries = diff_envs(OLD, NEW)
    removed = [e for e in entries if e.status == "removed"]
    assert len(removed) == 1
    assert removed[0].key == "SECRET"
    assert removed[0].old_value == "old_secret"


def test_diff_detects_changed_keys():
    entries = diff_envs(OLD, NEW)
    changed = [e for e in entries if e.status == "changed"]
    assert len(changed) == 1
    assert changed[0].key == "DB_HOST"
    assert changed[0].old_value == "localhost"
    assert changed[0].new_value == "prod.db"


def test_diff_unchanged_excluded_by_default():
    entries = diff_envs(OLD, NEW)
    unchanged = [e for e in entries if e.status == "unchanged"]
    assert unchanged == []


def test_diff_unchanged_included_when_requested():
    entries = diff_envs(OLD, NEW, show_unchanged=True)
    unchanged = [e for e in entries if e.status == "unchanged"]
    assert len(unchanged) == 1
    assert unchanged[0].key == "DB_PORT"


def test_diff_identical_envs_empty_by_default():
    entries = diff_envs(OLD, OLD)
    assert entries == []


def test_diff_entries_are_sorted_by_key():
    entries = diff_envs(OLD, NEW)
    keys = [e.key for e in entries]
    assert keys == sorted(keys)


def test_format_diff_no_differences():
    result = format_diff([])
    assert result == "(no differences)"


def test_format_diff_contains_symbols():
    entries = diff_envs(OLD, NEW)
    output = format_diff(entries)
    assert "+" in output
    assert "-" in output
    assert "~" in output


def test_format_diff_with_color_contains_escape_codes():
    entries = diff_envs(OLD, NEW)
    output = format_diff(entries, use_color=True)
    assert "\033[" in output


def test_diff_entry_str_added():
    e = DiffEntry(key="FOO", status="added", new_value="bar")
    assert str(e) == "+ FOO=bar"


def test_diff_entry_str_removed():
    e = DiffEntry(key="FOO", status="removed", old_value="bar")
    assert str(e) == "- FOO=bar"


def test_diff_entry_str_changed():
    e = DiffEntry(key="FOO", status="changed", old_value="a", new_value="b")
    assert "~" in str(e)
    assert "FOO" in str(e)
