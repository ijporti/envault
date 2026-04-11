"""Tests for envault.cli_rename."""

import argparse
import pytest

from envault.store import save_vault, load_vault
from envault.cli_rename import cmd_rename


PASSWORD = "cli-rename-pw"


class _Args(argparse.Namespace):
    def __init__(self, **kwargs):
        defaults = dict(
            vault_dir=None,
            environment="dev",
            old_key="OLD",
            new_key="NEW",
            overwrite=False,
            all_envs=False,
            password=PASSWORD,
        )
        defaults.update(kwargs)
        super().__init__(**defaults)


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _make_args(vault_dir, **kwargs):
    return _Args(vault_dir=vault_dir, **kwargs)


def test_cmd_rename_returns_zero_on_success(vault_dir):
    save_vault(vault_dir, "dev", {"OLD": "val"}, PASSWORD)
    args = _make_args(vault_dir)
    assert cmd_rename(args) == 0


def test_cmd_rename_returns_one_when_key_missing(vault_dir):
    save_vault(vault_dir, "dev", {"OTHER": "val"}, PASSWORD)
    args = _make_args(vault_dir)
    assert cmd_rename(args) == 1


def test_cmd_rename_persists_new_key(vault_dir):
    save_vault(vault_dir, "dev", {"OLD": "secret"}, PASSWORD)
    cmd_rename(_make_args(vault_dir))
    vault = load_vault(vault_dir, "dev", PASSWORD)
    assert vault.get("NEW") == "secret"
    assert "OLD" not in vault


def test_cmd_rename_conflict_returns_one(vault_dir):
    save_vault(vault_dir, "dev", {"OLD": "v1", "NEW": "v2"}, PASSWORD)
    args = _make_args(vault_dir)
    assert cmd_rename(args) == 1


def test_cmd_rename_overwrite_flag_resolves_conflict(vault_dir):
    save_vault(vault_dir, "dev", {"OLD": "v1", "NEW": "v2"}, PASSWORD)
    args = _make_args(vault_dir, overwrite=True)
    assert cmd_rename(args) == 0


def test_cmd_rename_all_envs_returns_zero(vault_dir):
    save_vault(vault_dir, "dev", {"OLD": "d"}, PASSWORD)
    save_vault(vault_dir, "prod", {"OLD": "p"}, PASSWORD)
    args = _make_args(vault_dir, all_envs=True)
    assert cmd_rename(args) == 0


def test_cmd_rename_all_envs_updates_all(vault_dir):
    save_vault(vault_dir, "dev", {"OLD": "d"}, PASSWORD)
    save_vault(vault_dir, "prod", {"OLD": "p"}, PASSWORD)
    cmd_rename(_make_args(vault_dir, all_envs=True))
    assert load_vault(vault_dir, "dev", PASSWORD).get("NEW") == "d"
    assert load_vault(vault_dir, "prod", PASSWORD).get("NEW") == "p"
