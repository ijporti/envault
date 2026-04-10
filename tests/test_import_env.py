"""Tests for envault.import_env module."""

import json
import os
import textwrap
from pathlib import Path

import pytest

from envault.import_env import (
    ImportError,
    import_from_file,
    import_from_os_env,
    parse_dotenv,
    parse_json_env,
)


# ---------------------------------------------------------------------------
# parse_dotenv
# ---------------------------------------------------------------------------

def test_parse_dotenv_simple():
    result = parse_dotenv("KEY=value")
    assert result == {"KEY": "value"}


def test_parse_dotenv_double_quoted():
    result = parse_dotenv('DB_URL="postgres://localhost/db"')
    assert result["DB_URL"] == "postgres://localhost/db"


def test_parse_dotenv_single_quoted():
    result = parse_dotenv("SECRET='hello world'")
    assert result["SECRET"] == "hello world"


def test_parse_dotenv_ignores_comments_and_blanks():
    text = textwrap.dedent("""
        # This is a comment

        FOO=bar
        # another comment
        BAZ=qux
    """)
    result = parse_dotenv(text)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_dotenv_escaped_double_quote():
    result = parse_dotenv('MSG="say \\"hi\\""')
    assert result["MSG"] == 'say "hi"'


def test_parse_dotenv_missing_equals_raises():
    with pytest.raises(ImportError, match="missing '='"):
        parse_dotenv("BADLINE")


def test_parse_dotenv_invalid_key_raises():
    with pytest.raises(ImportError, match="invalid key name"):
        parse_dotenv("123BAD=value")


# ---------------------------------------------------------------------------
# parse_json_env
# ---------------------------------------------------------------------------

def test_parse_json_env_valid():
    data = json.dumps({"API_KEY": "abc", "PORT": "8080"})
    result = parse_json_env(data)
    assert result == {"API_KEY": "abc", "PORT": "8080"}


def test_parse_json_env_non_string_value_raises():
    data = json.dumps({"PORT": 8080})
    with pytest.raises(ImportError, match="must be a string"):
        parse_json_env(data)


def test_parse_json_env_invalid_json_raises():
    with pytest.raises(ImportError, match="Invalid JSON"):
        parse_json_env("{not valid}")


def test_parse_json_env_non_object_raises():
    with pytest.raises(ImportError, match="root must be an object"):
        parse_json_env("[1, 2, 3]")


# ---------------------------------------------------------------------------
# import_from_file
# ---------------------------------------------------------------------------

def test_import_from_file_dotenv(tmp_path):
    f = tmp_path / ".env"
    f.write_text("HELLO=world\nFOO=bar\n")
    result, fmt = import_from_file(f)
    assert fmt == "dotenv"
    assert result == {"HELLO": "world", "FOO": "bar"}


def test_import_from_file_json(tmp_path):
    f = tmp_path / "secrets.json"
    f.write_text(json.dumps({"TOKEN": "xyz"}))
    result, fmt = import_from_file(f)
    assert fmt == "json"
    assert result == {"TOKEN": "xyz"}


# ---------------------------------------------------------------------------
# import_from_os_env
# ---------------------------------------------------------------------------

def test_import_from_os_env_no_prefix(monkeypatch):
    monkeypatch.setenv("TEST_VAR_UNIQUE", "hello")
    result = import_from_os_env()
    assert "TEST_VAR_UNIQUE" in result


def test_import_from_os_env_with_prefix(monkeypatch):
    monkeypatch.setenv("MYAPP_TOKEN", "secret")
    monkeypatch.setenv("OTHER_VAR", "noise")
    result = import_from_os_env(prefix="MYAPP_")
    assert "MYAPP_TOKEN" in result
    assert "OTHER_VAR" not in result
