"""Tests for envault.archive."""
import pytest
from pathlib import Path

from envault.store import save_vault
from envault.archive import (
    ArchiveError,
    ArchiveManifest,
    create_archive,
    restore_archive,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path / "vault"


def _seed(vault_dir: Path, env: str, password: str, data: dict) -> None:
    save_vault(vault_dir, env, password, data)


def test_create_archive_returns_manifest(vault_dir, tmp_path):
    _seed(vault_dir, "production", "pw", {"KEY": "val"})
    dest = tmp_path / "backup.zip"
    manifest = create_archive(vault_dir, "pw", ["production"], dest)
    assert isinstance(manifest, ArchiveManifest)
    assert "production" in manifest.environments


def test_create_archive_file_exists(vault_dir, tmp_path):
    _seed(vault_dir, "staging", "pw", {"A": "1"})
    dest = tmp_path / "backup.zip"
    create_archive(vault_dir, "pw", ["staging"], dest)
    assert dest.exists()


def test_create_archive_multiple_environments(vault_dir, tmp_path):
    _seed(vault_dir, "dev", "pw", {"X": "1"})
    _seed(vault_dir, "prod", "pw", {"Y": "2"})
    dest = tmp_path / "multi.zip"
    manifest = create_archive(vault_dir, "pw", ["dev", "prod"], dest)
    assert set(manifest.environments) == {"dev", "prod"}


def test_create_archive_missing_env_raises(vault_dir, tmp_path):
    dest = tmp_path / "backup.zip"
    with pytest.raises(ArchiveError, match="does not exist"):
        create_archive(vault_dir, "pw", ["ghost"], dest)


def test_create_archive_empty_list_raises(vault_dir, tmp_path):
    dest = tmp_path / "backup.zip"
    with pytest.raises(ArchiveError, match="No environments"):
        create_archive(vault_dir, "pw", [], dest)


def test_restore_archive_recovers_environment(vault_dir, tmp_path):
    _seed(vault_dir, "production", "pw", {"SECRET": "abc"})
    dest = tmp_path / "backup.zip"
    create_archive(vault_dir, "pw", ["production"], dest)

    new_vault = tmp_path / "restored_vault"
    manifest = restore_archive(new_vault, "pw", dest)
    assert "production" in manifest.environments


def test_restore_archive_values_intact(vault_dir, tmp_path):
    from envault.store import load_vault
    _seed(vault_dir, "env1", "pw", {"FOO": "bar", "BAZ": "qux"})
    dest = tmp_path / "backup.zip"
    create_archive(vault_dir, "pw", ["env1"], dest)

    new_vault = tmp_path / "rv"
    restore_archive(new_vault, "pw", dest)
    data = load_vault(new_vault, "env1", "pw")
    assert data == {"FOO": "bar", "BAZ": "qux"}


def test_restore_archive_overwrite_false_raises(vault_dir, tmp_path):
    _seed(vault_dir, "staging", "pw", {"K": "v"})
    dest = tmp_path / "backup.zip"
    create_archive(vault_dir, "pw", ["staging"], dest)
    with pytest.raises(ArchiveError, match="already exists"):
        restore_archive(vault_dir, "pw", dest, overwrite=False)


def test_restore_archive_overwrite_true_succeeds(vault_dir, tmp_path):
    _seed(vault_dir, "staging", "pw", {"K": "v"})
    dest = tmp_path / "backup.zip"
    create_archive(vault_dir, "pw", ["staging"], dest)
    manifest = restore_archive(vault_dir, "pw", dest, overwrite=True)
    assert "staging" in manifest.environments


def test_restore_archive_missing_file_raises(vault_dir, tmp_path):
    with pytest.raises(ArchiveError, match="not found"):
        restore_archive(vault_dir, "pw", tmp_path / "nonexistent.zip")
