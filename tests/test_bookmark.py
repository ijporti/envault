"""Tests for envault.bookmark."""
import pytest
from pathlib import Path

from envault.store import save_vault
from envault.bookmark import (
    BookmarkError,
    BookmarkEntry,
    add_bookmark,
    remove_bookmark,
    resolve_bookmark,
    list_bookmarks,
    _bookmark_path,
)

PASSWORD = "test-password"


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    save_vault(tmp_path, "dev", {"DB_URL": "postgres://localhost/dev", "API_KEY": "abc123"}, PASSWORD)
    save_vault(tmp_path, "prod", {"DB_URL": "postgres://localhost/prod"}, PASSWORD)
    return tmp_path


def test_add_bookmark_returns_entry(vault_dir):
    entry = add_bookmark(vault_dir, "mydb", "dev", "DB_URL", PASSWORD)
    assert isinstance(entry, BookmarkEntry)
    assert entry.alias == "mydb"
    assert entry.environment == "dev"
    assert entry.key == "DB_URL"


def test_add_bookmark_creates_registry_file(vault_dir):
    add_bookmark(vault_dir, "mydb", "dev", "DB_URL", PASSWORD)
    assert _bookmark_path(vault_dir).exists()


def test_add_bookmark_nonexistent_key_raises(vault_dir):
    with pytest.raises(BookmarkError, match="not found"):
        add_bookmark(vault_dir, "ghost", "dev", "MISSING_KEY", PASSWORD)


def test_add_bookmark_empty_alias_raises(vault_dir):
    with pytest.raises(BookmarkError, match="empty"):
        add_bookmark(vault_dir, "", "dev", "DB_URL", PASSWORD)


def test_resolve_bookmark_returns_value(vault_dir):
    add_bookmark(vault_dir, "mydb", "dev", "DB_URL", PASSWORD)
    value = resolve_bookmark(vault_dir, "mydb", PASSWORD)
    assert value == "postgres://localhost/dev"


def test_resolve_bookmark_unknown_alias_returns_none(vault_dir):
    result = resolve_bookmark(vault_dir, "nonexistent", PASSWORD)
    assert result is None


def test_remove_bookmark_returns_true_when_exists(vault_dir):
    add_bookmark(vault_dir, "mydb", "dev", "DB_URL", PASSWORD)
    assert remove_bookmark(vault_dir, "mydb") is True


def test_remove_bookmark_returns_false_when_missing(vault_dir):
    assert remove_bookmark(vault_dir, "ghost") is False


def test_remove_bookmark_makes_alias_unresolvable(vault_dir):
    add_bookmark(vault_dir, "mydb", "dev", "DB_URL", PASSWORD)
    remove_bookmark(vault_dir, "mydb")
    assert resolve_bookmark(vault_dir, "mydb", PASSWORD) is None


def test_list_bookmarks_returns_all_entries(vault_dir):
    add_bookmark(vault_dir, "apikey", "dev", "API_KEY", PASSWORD)
    add_bookmark(vault_dir, "mydb", "dev", "DB_URL", PASSWORD)
    entries = list_bookmarks(vault_dir)
    assert len(entries) == 2
    aliases = [e.alias for e in entries]
    assert "apikey" in aliases
    assert "mydb" in aliases


def test_list_bookmarks_empty_when_no_file(vault_dir):
    assert list_bookmarks(vault_dir) == []


def test_bookmark_entry_str(vault_dir):
    entry = add_bookmark(vault_dir, "mydb", "dev", "DB_URL", PASSWORD)
    assert str(entry) == "mydb -> dev/DB_URL"


def test_add_bookmark_overwrites_existing_alias(vault_dir):
    add_bookmark(vault_dir, "mydb", "dev", "DB_URL", PASSWORD)
    add_bookmark(vault_dir, "mydb", "prod", "DB_URL", PASSWORD)
    entries = list_bookmarks(vault_dir)
    assert len(entries) == 1
    assert entries[0].environment == "prod"
