"""Tests for envault.cli_promote."""

import pytest

from envault.cli_promote import cmd_promote
from envault.store import load_vault, save_vault


class _Args:
    """Minimal stand-in for argparse.Namespace."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _make_args(vault_dir, source, target, password="pass", keys=None, overwrite=False):
    return _Args(
        vault_dir=vault_dir,
        source=source,
        target=target,
        password=password,
        keys=keys or [],
        overwrite=overwrite,
    )


# ---------------------------------------------------------------------------
# Happy-path
# ---------------------------------------------------------------------------

def test_cmd_promote_returns_zero_on_success(vault_dir):
    save_vault(vault_dir, "staging", "pass", {"KEY": "val"})
    args = _make_args(vault_dir, "staging", "production")
    assert cmd_promote(args) == 0


def test_cmd_promote_copies_values(vault_dir):
    save_vault(vault_dir, "staging", "pass", {"TOKEN": "abc123"})
    args = _make_args(vault_dir, "staging", "production")
    cmd_promote(args)
    secrets = load_vault(vault_dir, "production", "pass")
    assert secrets["TOKEN"] == "abc123"


def test_cmd_promote_partial_keys(vault_dir):
    save_vault(vault_dir, "staging", "pass", {"A": "1", "B": "2"})
    args = _make_args(vault_dir, "staging", "production", keys=["A"])
    rc = cmd_promote(args)
    assert rc == 0
    secrets = load_vault(vault_dir, "production", "pass")
    assert "A" in secrets
    assert "B" not in secrets


def test_cmd_promote_overwrite_flag(vault_dir):
    save_vault(vault_dir, "staging", "pass", {"KEY": "new"})
    save_vault(vault_dir, "production", "pass", {"KEY": "old"})
    args = _make_args(vault_dir, "staging", "production", overwrite=True)
    cmd_promote(args)
    secrets = load_vault(vault_dir, "production", "pass")
    assert secrets["KEY"] == "new"


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_cmd_promote_same_env_returns_nonzero(vault_dir):
    save_vault(vault_dir, "staging", "pass", {"A": "1"})
    args = _make_args(vault_dir, "staging", "staging")
    assert cmd_promote(args) != 0


def test_cmd_promote_missing_source_returns_nonzero(vault_dir):
    args = _make_args(vault_dir, "ghost", "production")
    assert cmd_promote(args) != 0
