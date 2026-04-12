"""Tests for envault.cli_group."""

from __future__ import annotations

import pytest

from envault.store import save_vault
from envault.group import add_to_group
from envault.cli_group import cmd_group

PASSWORD = "test-password"


class _Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _make_args(vault_dir, action, **kwargs):
    defaults = dict(
        vault_dir=vault_dir,
        password=PASSWORD,
        environment="dev",
        group_action=action,
    )
    defaults.update(kwargs)
    return _Args(**defaults)


def _seed(vault_dir):
    save_vault(vault_dir, "dev", {"DB_HOST": "localhost", "API_KEY": "secret"}, PASSWORD)


# --- add ---

def test_cmd_group_add_returns_zero(vault_dir):
    _seed(vault_dir)
    args = _make_args(vault_dir, "add", group="db", keys=["DB_HOST"])
    assert cmd_group(args) == 0


def test_cmd_group_add_missing_key_returns_nonzero(vault_dir):
    _seed(vault_dir)
    args = _make_args(vault_dir, "add", group="db", keys=["MISSING_KEY"])
    assert cmd_group(args) != 0


# --- remove ---

def test_cmd_group_remove_returns_zero(vault_dir):
    _seed(vault_dir)
    add_to_group(vault_dir, "dev", "db", ["DB_HOST"], PASSWORD)
    args = _make_args(vault_dir, "remove", group="db", keys=["DB_HOST"])
    assert cmd_group(args) == 0


def test_cmd_group_remove_nonexistent_group_returns_nonzero(vault_dir):
    _seed(vault_dir)
    args = _make_args(vault_dir, "remove", group="ghost", keys=["DB_HOST"])
    assert cmd_group(args) != 0


# --- list ---

def test_cmd_group_list_returns_zero_empty(vault_dir):
    args = _make_args(vault_dir, "list")
    assert cmd_group(args) == 0


def test_cmd_group_list_returns_zero_with_groups(vault_dir):
    _seed(vault_dir)
    add_to_group(vault_dir, "dev", "db", ["DB_HOST"], PASSWORD)
    args = _make_args(vault_dir, "list")
    assert cmd_group(args) == 0


# --- show ---

def test_cmd_group_show_returns_zero(vault_dir):
    _seed(vault_dir)
    add_to_group(vault_dir, "dev", "db", ["DB_HOST"], PASSWORD)
    args = _make_args(vault_dir, "show", group="db")
    assert cmd_group(args) == 0


def test_cmd_group_show_nonexistent_returns_nonzero(vault_dir):
    _seed(vault_dir)
    args = _make_args(vault_dir, "show", group="ghost")
    assert cmd_group(args) != 0


# --- unknown action ---

def test_cmd_group_no_action_returns_nonzero(vault_dir):
    args = _make_args(vault_dir, None)
    assert cmd_group(args) != 0
