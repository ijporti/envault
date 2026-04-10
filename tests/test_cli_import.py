"""Tests for envault.cli_import module."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from envault.store import load_vault, save_vault
from envault.cli_import import cmd_import


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Args:
    """Simple namespace replacement for argparse.Namespace."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


PASSWORD = "test-secret"


@pytest.fixture()
def vault_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


def _make_args(env="test", file=None, from_os=False, prefix=None, overwrite=False):
    return _Args(env=env, file=file, from_os=from_os, prefix=prefix, overwrite=overwrite)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_import_from_dotenv_file(vault_dir, tmp_path):
    env_file = tmp_path / "sample.env"
    env_file.write_text("FOO=bar\nBAZ=qux\n")
    args = _make_args(file=str(env_file))
    with patch("envault.cli_import._get_password", return_value=PASSWORD):
        cmd_import(args)
    vault = load_vault("test", PASSWORD)
    assert vault["FOO"] == "bar"
    assert vault["BAZ"] == "qux"


def test_import_from_json_file(vault_dir, tmp_path):
    json_file = tmp_path / "secrets.json"
    json_file.write_text(json.dumps({"TOKEN": "abc123"}))
    args = _make_args(file=str(json_file))
    with patch("envault.cli_import._get_password", return_value=PASSWORD):
        cmd_import(args)
    vault = load_vault("test", PASSWORD)
    assert vault["TOKEN"] == "abc123"


def test_import_skips_existing_keys(vault_dir, tmp_path):
    save_vault("test", {"FOO": "original"}, PASSWORD)
    env_file = tmp_path / "new.env"
    env_file.write_text("FOO=overridden\nNEW=value\n")
    args = _make_args(file=str(env_file))
    with patch("envault.cli_import._get_password", return_value=PASSWORD):
        cmd_import(args)
    vault = load_vault("test", PASSWORD)
    assert vault["FOO"] == "original"  # not overwritten
    assert vault["NEW"] == "value"


def test_import_overwrite_flag(vault_dir, tmp_path):
    save_vault("test", {"FOO": "original"}, PASSWORD)
    env_file = tmp_path / "new.env"
    env_file.write_text("FOO=updated\n")
    args = _make_args(file=str(env_file), overwrite=True)
    with patch("envault.cli_import._get_password", return_value=PASSWORD):
        cmd_import(args)
    vault = load_vault("test", PASSWORD)
    assert vault["FOO"] == "updated"


def test_import_missing_file_exits(vault_dir, capsys):
    args = _make_args(file="/nonexistent/path/.env")
    with patch("envault.cli_import._get_password", return_value=PASSWORD):
        with pytest.raises(SystemExit) as exc_info:
            cmd_import(args)
    assert exc_info.value.code == 1


def test_import_from_os_env(vault_dir, monkeypatch):
    monkeypatch.setenv("MYAPP_KEY", "myvalue")
    args = _make_args(from_os=True, prefix="MYAPP_")
    with patch("envault.cli_import._get_password", return_value=PASSWORD):
        cmd_import(args)
    vault = load_vault("test", PASSWORD)
    assert vault.get("MYAPP_KEY") == "myvalue"
