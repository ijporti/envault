"""Tests for envault.snapshot."""

import pytest

from envault.snapshot import (
    SnapshotError,
    create_snapshot,
    delete_snapshot,
    get_snapshot,
    list_snapshots,
    restore_snapshot,
)
from envault.store import load_vault, save_vault


PASSWORD = "s3cr3t"


@pytest.fixture()
def vault_dir(tmp_path):
    save_vault(str(tmp_path), "dev", PASSWORD, {"DB_URL": "postgres://dev", "DEBUG": "true"})
    save_vault(str(tmp_path), "prod", PASSWORD, {"DB_URL": "postgres://prod", "DEBUG": "false"})
    return str(tmp_path)


def test_create_snapshot_returns_snapshot(vault_dir):
    snap = create_snapshot(vault_dir, PASSWORD, "v1")
    assert snap.label == "v1"
    assert "dev" in snap.environments
    assert "prod" in snap.environments


def test_create_snapshot_captures_values(vault_dir):
    snap = create_snapshot(vault_dir, PASSWORD, "v1")
    assert snap.environments["dev"]["DB_URL"] == "postgres://dev"
    assert snap.environments["prod"]["DEBUG"] == "false"


def test_create_snapshot_has_timestamp(vault_dir):
    snap = create_snapshot(vault_dir, PASSWORD, "v1")
    assert snap.created_at  # non-empty ISO string
    assert "T" in snap.created_at  # basic ISO 8601 check


def test_create_snapshot_with_tags(vault_dir):
    snap = create_snapshot(vault_dir, PASSWORD, "tagged", tags=["release", "stable"])
    assert "release" in snap.tags


def test_duplicate_label_raises(vault_dir):
    create_snapshot(vault_dir, PASSWORD, "v1")
    with pytest.raises(SnapshotError, match="already exists"):
        create_snapshot(vault_dir, PASSWORD, "v1")


def test_list_snapshots_newest_first(vault_dir):
    create_snapshot(vault_dir, PASSWORD, "v1")
    create_snapshot(vault_dir, PASSWORD, "v2")
    snaps = list_snapshots(vault_dir)
    assert snaps[0].label == "v2"
    assert snaps[1].label == "v1"


def test_list_snapshots_empty(tmp_path):
    assert list_snapshots(str(tmp_path)) == []


def test_get_snapshot_found(vault_dir):
    create_snapshot(vault_dir, PASSWORD, "v1")
    snap = get_snapshot(vault_dir, "v1")
    assert snap is not None
    assert snap.label == "v1"


def test_get_snapshot_not_found(vault_dir):
    assert get_snapshot(vault_dir, "nonexistent") is None


def test_restore_snapshot_overwrites_current(vault_dir):
    create_snapshot(vault_dir, PASSWORD, "before-change")
    # Mutate dev environment
    save_vault(vault_dir, "dev", PASSWORD, {"DB_URL": "sqlite://", "DEBUG": "false"})
    count = restore_snapshot(vault_dir, PASSWORD, "before-change")
    assert count == 2
    restored = load_vault(vault_dir, "dev", PASSWORD)
    assert restored["DB_URL"] == "postgres://dev"


def test_restore_snapshot_missing_raises(vault_dir):
    with pytest.raises(SnapshotError, match="not found"):
        restore_snapshot(vault_dir, PASSWORD, "ghost")


def test_delete_snapshot_returns_true(vault_dir):
    create_snapshot(vault_dir, PASSWORD, "v1")
    assert delete_snapshot(vault_dir, "v1") is True
    assert get_snapshot(vault_dir, "v1") is None


def test_delete_snapshot_not_found_returns_false(vault_dir):
    assert delete_snapshot(vault_dir, "no-such") is False
