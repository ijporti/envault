"""Tests for envault.cli_patch."""

import pytest

from envault.cli_patch import cmd_patch
from envault.store import load_vault, save_vault


class _Args:
    def __init__(self, vault_dir, environment, assignments, **kwargs):
        self.vault_dir = vault_dir
        self.environment = environment
        self.assignments = assignments
        self.password = kwargs.get("password", "pw")
        self.keys = kwargs.get("keys", "")
        self.no_add = kwargs.get("no_add", False)


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _make_args(vault_dir, environment, assignments, **kwargs):
    return _Args(vault_dir, environment, assignments, **kwargs)


def test_cmd_patch_returns_zero_on_success(vault_dir):
    save_vault(vault_dir, "dev", "pw", {"KEY": "old"})
    args = _make_args(vault_dir, "dev", ["KEY=new"])
    assert cmd_patch(args) == 0


def test_cmd_patch_updates_value(vault_dir):
    save_vault(vault_dir, "dev", "pw", {"FOO": "bar"})
    args = _make_args(vault_dir, "dev", ["FOO=baz"])
    cmd_patch(args)
    assert load_vault(vault_dir, "dev", "pw")["FOO"] == "baz"


def test_cmd_patch_invalid_assignment_returns_one(vault_dir, capsys):
    save_vault(vault_dir, "dev", "pw", {})
    args = _make_args(vault_dir, "dev", ["NOEQUALSSIGN"])
    rc = cmd_patch(args)
    assert rc == 1
    assert "Invalid assignment" in capsys.readouterr().err


def test_cmd_patch_missing_env_returns_one(vault_dir, capsys):
    args = _make_args(vault_dir, "ghost", ["K=v"])
    rc = cmd_patch(args)
    assert rc == 1
    assert "error" in capsys.readouterr().err.lower()


def test_cmd_patch_no_add_flag_skips_new_keys(vault_dir):
    save_vault(vault_dir, "dev", "pw", {})
    args = _make_args(vault_dir, "dev", ["NEW=val"], no_add=True)
    cmd_patch(args)
    assert "NEW" not in load_vault(vault_dir, "dev", "pw")


def test_cmd_patch_keys_filter_limits_update(vault_dir):
    save_vault(vault_dir, "dev", "pw", {"A": "1", "B": "2"})
    args = _make_args(vault_dir, "dev", ["A=X", "B=Y"], keys="A")
    cmd_patch(args)
    data = load_vault(vault_dir, "dev", "pw")
    assert data["A"] == "X"
    assert data["B"] == "2"


def test_cmd_patch_value_with_equals_sign(vault_dir):
    """Ensure values containing '=' are stored correctly (split on first '=' only)."""
    save_vault(vault_dir, "dev", "pw", {"URL": ""})
    args = _make_args(vault_dir, "dev", ["URL=http://example.com/?a=1&b=2"])
    cmd_patch(args)
    assert load_vault(vault_dir, "dev", "pw")["URL"] == "http://example.com/?a=1&b=2"
