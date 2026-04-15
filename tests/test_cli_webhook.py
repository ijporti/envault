"""Tests for envault.cli_webhook."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from envault.cli_webhook import cmd_webhook
from envault.webhook import register_webhook


class _Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def _make_args(vault_dir: Path, webhook_sub: str, **kwargs) -> _Args:
    return _Args(vault_dir=str(vault_dir), webhook_sub=webhook_sub, **kwargs)


def test_cmd_webhook_add_returns_zero(vault_dir):
    args = _make_args(vault_dir, "add", url="https://example.com/hook")
    assert cmd_webhook(args) == 0


def test_cmd_webhook_add_invalid_url_returns_one(vault_dir):
    args = _make_args(vault_dir, "add", url="ftp://bad")
    assert cmd_webhook(args) == 1


def test_cmd_webhook_list_returns_zero_empty(vault_dir):
    args = _make_args(vault_dir, "list")
    assert cmd_webhook(args) == 0


def test_cmd_webhook_list_returns_zero_with_hooks(vault_dir):
    register_webhook(vault_dir, "https://example.com/hook")
    args = _make_args(vault_dir, "list")
    assert cmd_webhook(args) == 0


def test_cmd_webhook_remove_present_returns_zero(vault_dir):
    register_webhook(vault_dir, "https://example.com/hook")
    args = _make_args(vault_dir, "remove", url="https://example.com/hook")
    assert cmd_webhook(args) == 0


def test_cmd_webhook_remove_absent_returns_one(vault_dir):
    args = _make_args(vault_dir, "remove", url="https://example.com/hook")
    assert cmd_webhook(args) == 1


def test_cmd_webhook_fire_no_hooks_returns_zero(vault_dir):
    args = _make_args(vault_dir, "fire", event="key.set")
    assert cmd_webhook(args) == 0


def test_cmd_webhook_fire_success_returns_zero(vault_dir):
    register_webhook(vault_dir, "https://example.com/hook")
    from unittest.mock import MagicMock
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: mock_resp
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        args = _make_args(vault_dir, "fire", event="key.set")
        assert cmd_webhook(args) == 0


def test_cmd_webhook_fire_failure_returns_one(vault_dir):
    import urllib.error
    register_webhook(vault_dir, "https://example.com/hook")
    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
        url="https://example.com/hook", code=500, msg="Error", hdrs=None, fp=None
    )):
        args = _make_args(vault_dir, "fire", event="key.set")
        assert cmd_webhook(args) == 1


def test_cmd_webhook_unknown_sub_returns_one(vault_dir):
    args = _make_args(vault_dir, "unknown")
    assert cmd_webhook(args) == 1
