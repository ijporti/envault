"""Tests for envault.tags module."""

import pytest
from pathlib import Path

from envault.tags import (
    TagError,
    add_tags,
    remove_tags,
    get_tags,
    find_by_tag,
    list_all_tags,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# add_tags
# ---------------------------------------------------------------------------

def test_add_tags_returns_sorted_list(vault_dir):
    result = add_tags(vault_dir, "prod", "DB_PASSWORD", ["secret", "db"])
    assert result == ["db", "secret"]


def test_add_tags_creates_registry_file(vault_dir):
    add_tags(vault_dir, "prod", "API_KEY", ["external"])
    tag_file = vault_dir / "prod" / ".tags.json"
    assert tag_file.exists()


def test_add_tags_merges_with_existing(vault_dir):
    add_tags(vault_dir, "prod", "API_KEY", ["external"])
    result = add_tags(vault_dir, "prod", "API_KEY", ["sensitive"])
    assert "external" in result
    assert "sensitive" in result


def test_add_tags_deduplicates(vault_dir):
    add_tags(vault_dir, "prod", "API_KEY", ["sensitive"])
    result = add_tags(vault_dir, "prod", "API_KEY", ["sensitive"])
    assert result.count("sensitive") == 1


def test_add_tags_empty_list_raises(vault_dir):
    with pytest.raises(TagError):
        add_tags(vault_dir, "prod", "API_KEY", [])


# ---------------------------------------------------------------------------
# remove_tags
# ---------------------------------------------------------------------------

def test_remove_tags_removes_specified_tag(vault_dir):
    add_tags(vault_dir, "prod", "TOKEN", ["secret", "auth"])
    result = remove_tags(vault_dir, "prod", "TOKEN", ["auth"])
    assert "auth" not in result
    assert "secret" in result


def test_remove_tags_clears_key_when_no_tags_left(vault_dir):
    add_tags(vault_dir, "prod", "TOKEN", ["temp"])
    remove_tags(vault_dir, "prod", "TOKEN", ["temp"])
    assert get_tags(vault_dir, "prod", "TOKEN") == []


def test_remove_tags_nonexistent_tag_is_noop(vault_dir):
    add_tags(vault_dir, "prod", "TOKEN", ["keep"])
    result = remove_tags(vault_dir, "prod", "TOKEN", ["ghost"])
    assert result == ["keep"]


# ---------------------------------------------------------------------------
# get_tags
# ---------------------------------------------------------------------------

def test_get_tags_returns_empty_for_unknown_key(vault_dir):
    assert get_tags(vault_dir, "staging", "MISSING") == []


def test_get_tags_returns_assigned_tags(vault_dir):
    add_tags(vault_dir, "staging", "DB_URL", ["db", "infra"])
    assert get_tags(vault_dir, "staging", "DB_URL") == ["db", "infra"]


# ---------------------------------------------------------------------------
# find_by_tag
# ---------------------------------------------------------------------------

def test_find_by_tag_returns_matching_keys(vault_dir):
    add_tags(vault_dir, "dev", "DB_PASS", ["secret"])
    add_tags(vault_dir, "dev", "API_KEY", ["secret", "external"])
    add_tags(vault_dir, "dev", "LOG_LEVEL", ["config"])
    result = find_by_tag(vault_dir, "dev", "secret")
    assert set(result) == {"DB_PASS", "API_KEY"}


def test_find_by_tag_returns_empty_when_no_match(vault_dir):
    add_tags(vault_dir, "dev", "FOO", ["bar"])
    assert find_by_tag(vault_dir, "dev", "nonexistent") == []


# ---------------------------------------------------------------------------
# list_all_tags
# ---------------------------------------------------------------------------

def test_list_all_tags_returns_full_registry(vault_dir):
    add_tags(vault_dir, "prod", "A", ["x"])
    add_tags(vault_dir, "prod", "B", ["y"])
    registry = list_all_tags(vault_dir, "prod")
    assert registry == {"A": ["x"], "B": ["y"]}


def test_list_all_tags_empty_environment(vault_dir):
    assert list_all_tags(vault_dir, "empty_env") == {}
