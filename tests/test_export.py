"""Tests for envault.export module."""

import json
import pytest

from envault.export import export_secrets, export_dotenv, export_shell, export_json, SUPPORTED_FORMATS


SAMPLE = {
    "DATABASE_URL": "postgres://user:pass@localhost/db",
    "API_KEY": "abc123",
    "DEBUG": "true",
}


def test_export_dotenv_format():
    result = export_dotenv(SAMPLE)
    assert 'API_KEY="abc123"' in result
    assert 'DEBUG="true"' in result
    assert result.endswith("\n")


def test_export_dotenv_escapes_double_quotes():
    result = export_dotenv({"MSG": 'say "hello"'})
    assert 'MSG="say \\"hello\\""' in result


def test_export_shell_format():
    result = export_shell(SAMPLE)
    assert "export API_KEY='abc123'" in result
    assert "export DEBUG='true'" in result
    assert result.endswith("\n")


def test_export_shell_escapes_single_quotes():
    result = export_shell({"MSG": "it's alive"})
    assert "export MSG='it'\\''s alive'" in result


def test_export_json_valid_json():
    result = export_json(SAMPLE)
    parsed = json.loads(result)
    assert parsed["API_KEY"] == "abc123"
    assert parsed["DEBUG"] == "true"


def test_export_json_sorted_keys():
    result = export_json(SAMPLE)
    parsed = json.loads(result)
    assert list(parsed.keys()) == sorted(parsed.keys())


def test_export_secrets_dispatches_dotenv():
    result = export_secrets(SAMPLE, "dotenv")
    assert "API_KEY=" in result


def test_export_secrets_dispatches_shell():
    result = export_secrets(SAMPLE, "shell")
    assert "export API_KEY=" in result


def test_export_secrets_dispatches_json():
    result = export_secrets(SAMPLE, "json")
    assert json.loads(result)["API_KEY"] == "abc123"


def test_export_secrets_unsupported_format_raises():
    with pytest.raises(ValueError, match="Unsupported format"):
        export_secrets(SAMPLE, "xml")


def test_export_empty_secrets():
    for fmt in SUPPORTED_FORMATS:
        result = export_secrets({}, fmt)
        assert isinstance(result, str)
