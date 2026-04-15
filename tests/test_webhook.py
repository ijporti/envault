"""Tests for envault.webhook."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envault.webhook import (
    WebhookError,
    WebhookResult,
    fire_webhooks,
    list_webhooks,
    register_webhook,
    remove_webhook,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_register_webhook_returns_sorted_list(vault_dir):
    result = register_webhook(vault_dir, "https://example.com/hook")
    assert result == ["https://example.com/hook"]


def test_register_webhook_creates_file(vault_dir):
    register_webhook(vault_dir, "https://example.com/hook")
    assert (vault_dir / ".webhooks.json").exists()


def test_register_webhook_deduplicates(vault_dir):
    register_webhook(vault_dir, "https://example.com/hook")
    result = register_webhook(vault_dir, "https://example.com/hook")
    assert result.count("https://example.com/hook") == 1


def test_register_webhook_invalid_scheme_raises(vault_dir):
    with pytest.raises(WebhookError, match="Invalid URL scheme"):
        register_webhook(vault_dir, "ftp://bad.example.com")


def test_register_multiple_webhooks_sorted(vault_dir):
    register_webhook(vault_dir, "https://b.example.com")
    result = register_webhook(vault_dir, "https://a.example.com")
    assert result == ["https://a.example.com", "https://b.example.com"]


def test_remove_webhook_returns_true_when_present(vault_dir):
    register_webhook(vault_dir, "https://example.com/hook")
    assert remove_webhook(vault_dir, "https://example.com/hook") is True


def test_remove_webhook_returns_false_when_absent(vault_dir):
    assert remove_webhook(vault_dir, "https://example.com/hook") is False


def test_remove_webhook_removes_from_file(vault_dir):
    register_webhook(vault_dir, "https://example.com/hook")
    remove_webhook(vault_dir, "https://example.com/hook")
    assert list_webhooks(vault_dir) == []


def test_list_webhooks_empty_when_no_file(vault_dir):
    assert list_webhooks(vault_dir) == []


def test_fire_webhooks_returns_results(vault_dir):
    register_webhook(vault_dir, "https://example.com/hook")
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: mock_resp
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        results = fire_webhooks(vault_dir, "key.set", {"env": "prod", "key": "FOO"})
    assert len(results) == 1
    assert results[0].ok is True
    assert results[0].status_code == 200


def test_fire_webhooks_handles_http_error(vault_dir):
    import urllib.error
    register_webhook(vault_dir, "https://example.com/hook")
    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
        url="https://example.com/hook", code=500, msg="Server Error", hdrs=None, fp=None
    )):
        results = fire_webhooks(vault_dir, "key.set", {})
    assert results[0].ok is False
    assert results[0].status_code == 500


def test_fire_webhooks_no_urls_returns_empty(vault_dir):
    results = fire_webhooks(vault_dir, "key.set", {})
    assert results == []


def test_webhook_result_str_ok():
    r = WebhookResult(url="https://x.com", status_code=200, ok=True)
    assert "delivered" in str(r)
    assert "200" in str(r)


def test_webhook_result_str_error():
    r = WebhookResult(url="https://x.com", status_code=0, ok=False, error="timeout")
    assert "failed" in str(r)
    assert "timeout" in str(r)
