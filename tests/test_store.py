"""Tests for envault.store (vault persistence layer)."""

import json
import pytest
from pathlib import Path

from envault.store import save_vault, load_vault, list_environments


SECRETS = {"DB_URL": "postgres://localhost/db", "SECRET_KEY": "s3cr3t"}
PASSWORD = "hunter2"


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path / "vaults"


def test_save_vault_creates_file(vault_dir):
    path = save_vault(SECRETS, PASSWORD, vault_dir=vault_dir)
    assert path.exists()
    assert path.suffix == ".vault"


def test_load_vault_roundtrip(vault_dir):
    save_vault(SECRETS, PASSWORD, vault_dir=vault_dir)
    loaded = load_vault(PASSWORD, vault_dir=vault_dir)
    assert loaded == SECRETS


def test_load_vault_wrong_password_raises(vault_dir):
    save_vault(SECRETS, PASSWORD, vault_dir=vault_dir)
    with pytest.raises(ValueError):
        load_vault("wrongpassword", vault_dir=vault_dir)


def test_load_vault_missing_raises(vault_dir):
    with pytest.raises(FileNotFoundError):
        load_vault(PASSWORD, environment="nonexistent", vault_dir=vault_dir)


def test_save_and_load_named_environment(vault_dir):
    save_vault(SECRETS, PASSWORD, environment="production", vault_dir=vault_dir)
    loaded = load_vault(PASSWORD, environment="production", vault_dir=vault_dir)
    assert loaded == SECRETS


def test_list_environments_empty(vault_dir):
    assert list_environments(vault_dir=vault_dir) == []


def test_list_environments_multiple(vault_dir):
    for env in ("default", "staging", "production"):
        save_vault(SECRETS, PASSWORD, environment=env, vault_dir=vault_dir)
    envs = list_environments(vault_dir=vault_dir)
    assert sorted(envs) == ["default", "production", "staging"]


def test_save_overwrites_existing(vault_dir):
    save_vault(SECRETS, PASSWORD, vault_dir=vault_dir)
    new_secrets = {"API_KEY": "newkey"}
    save_vault(new_secrets, PASSWORD, vault_dir=vault_dir)
    loaded = load_vault(PASSWORD, vault_dir=vault_dir)
    assert loaded == new_secrets
