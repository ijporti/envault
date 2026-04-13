"""Tests for envault.cli_dependency."""
import pytest
from pathlib import Path
from unittest.mock import patch

from envault.store import save_vault
from envault.dependency import add_dependency
from envault.cli_dependency import cmd_dependency

PASSWORD = "cli-test-pass"


class _Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def _seed(vault_dir: Path, env: str, secrets: dict) -> None:
    save_vault(vault_dir, env, secrets, PASSWORD)


def _make_args(vault_dir: Path, dep_action: str, **kwargs) -> _Args:
    defaults = dict(
        vault_dir=str(vault_dir),
        environment="dev",
        password=PASSWORD,
        dep_action=dep_action,
    )
    defaults.update(kwargs)
    return _Args(**defaults)


def test_cmd_dependency_add_returns_zero(vault_dir):
    _seed(vault_dir, "dev", {"A": "1", "B": "2"})
    args = _make_args(vault_dir, "add", key="A", depends_on="B")
    assert cmd_dependency(args) == 0


def test_cmd_dependency_add_prints_deps(vault_dir, capsys):
    _seed(vault_dir, "dev", {"A": "1", "B": "2"})
    args = _make_args(vault_dir, "add", key="A", depends_on="B")
    cmd_dependency(args)
    out = capsys.readouterr().out
    assert "B" in out


def test_cmd_dependency_remove_returns_zero(vault_dir):
    _seed(vault_dir, "dev", {"A": "1", "B": "2"})
    add_dependency(vault_dir, "dev", "A", "B", PASSWORD)
    args = _make_args(vault_dir, "remove", key="A", depends_on="B")
    assert cmd_dependency(args) == 0


def test_cmd_dependency_list_returns_zero(vault_dir):
    _seed(vault_dir, "dev", {"A": "1", "B": "2"})
    add_dependency(vault_dir, "dev", "A", "B", PASSWORD)
    args = _make_args(vault_dir, "list", key="A")
    assert cmd_dependency(args) == 0


def test_cmd_dependency_list_prints_dep(vault_dir, capsys):
    _seed(vault_dir, "dev", {"A": "1", "B": "2"})
    add_dependency(vault_dir, "dev", "A", "B", PASSWORD)
    args = _make_args(vault_dir, "list", key="A")
    cmd_dependency(args)
    assert "B" in capsys.readouterr().out


def test_cmd_dependency_dependents_returns_zero(vault_dir):
    _seed(vault_dir, "dev", {"A": "1", "B": "2"})
    add_dependency(vault_dir, "dev", "B", "A", PASSWORD)
    args = _make_args(vault_dir, "dependents", key="A")
    assert cmd_dependency(args) == 0


def test_cmd_dependency_order_returns_zero(vault_dir):
    _seed(vault_dir, "dev", {"A": "1", "B": "2"})
    args = _make_args(vault_dir, "order")
    assert cmd_dependency(args) == 0


def test_cmd_dependency_add_bad_key_returns_one(vault_dir):
    _seed(vault_dir, "dev", {"A": "1"})
    args = _make_args(vault_dir, "add", key="MISSING", depends_on="A")
    assert cmd_dependency(args) == 1
