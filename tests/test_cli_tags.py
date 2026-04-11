"""Integration tests for the tags CLI subcommand."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault.tags import add_tags
from envault.cli_tags import cmd_tags
from envault.store import _vault_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Args:
    """Minimal namespace mirroring argparse output."""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def _make_args(vault_dir: Path, environment: str, tag_action: str, **kwargs) -> _Args:
    return _Args(
        vault=str(vault_dir / ".envault"),
        environment=environment,
        tag_action=tag_action,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------

def test_cmd_tags_add_returns_zero(vault_dir, capsys):
    args = _make_args(vault_dir, "prod", "add", key="DB_PASS", tags=["secret"])
    assert cmd_tags(args) == 0


def test_cmd_tags_add_prints_tags(vault_dir, capsys):
    args = _make_args(vault_dir, "prod", "add", key="DB_PASS", tags=["secret", "db"])
    cmd_tags(args)
    out = capsys.readouterr().out
    assert "db" in out
    assert "secret" in out


def test_cmd_tags_add_empty_tags_returns_nonzero(vault_dir, capsys):
    args = _make_args(vault_dir, "prod", "add", key="DB_PASS", tags=[])
    assert cmd_tags(args) != 0


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------

def test_cmd_tags_remove_returns_zero(vault_dir):
    add_tags(vault_dir, "prod", "API_KEY", ["external", "sensitive"])
    args = _make_args(vault_dir, "prod", "remove", key="API_KEY", tags=["external"])
    assert cmd_tags(args) == 0


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------

def test_cmd_tags_get_prints_tags(vault_dir, capsys):
    add_tags(vault_dir, "staging", "TOKEN", ["auth"])
    args = _make_args(vault_dir, "staging", "get", key="TOKEN")
    cmd_tags(args)
    out = capsys.readouterr().out
    assert "auth" in out


def test_cmd_tags_get_missing_key_prints_message(vault_dir, capsys):
    args = _make_args(vault_dir, "staging", "get", key="GHOST")
    cmd_tags(args)
    out = capsys.readouterr().out
    assert "No tags" in out


# ---------------------------------------------------------------------------
# find
# ---------------------------------------------------------------------------

def test_cmd_tags_find_prints_matching_keys(vault_dir, capsys):
    add_tags(vault_dir, "dev", "SECRET_A", ["sensitive"])
    add_tags(vault_dir, "dev", "SECRET_B", ["sensitive"])
    args = _make_args(vault_dir, "dev", "find", tag="sensitive")
    cmd_tags(args)
    out = capsys.readouterr().out
    assert "SECRET_A" in out
    assert "SECRET_B" in out


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def test_cmd_tags_list_shows_all_entries(vault_dir, capsys):
    add_tags(vault_dir, "prod", "FOO", ["x"])
    add_tags(vault_dir, "prod", "BAR", ["y"])
    args = _make_args(vault_dir, "prod", "list")
    cmd_tags(args)
    out = capsys.readouterr().out
    assert "FOO" in out
    assert "BAR" in out


def test_cmd_tags_list_empty_env_prints_message(vault_dir, capsys):
    args = _make_args(vault_dir, "empty", "list")
    cmd_tags(args)
    out = capsys.readouterr().out
    assert "No tags" in out
