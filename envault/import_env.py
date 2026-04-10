"""Import environment variables from external sources into a vault."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, Optional, Tuple


class ImportError(Exception):  # noqa: A001
    """Raised when an import operation fails."""


def parse_dotenv(text: str) -> Dict[str, str]:
    """Parse a .env file content into a dictionary.

    Supports:
    - KEY=VALUE
    - KEY="VALUE" (double-quoted)
    - KEY='VALUE' (single-quoted)
    - # comments
    - blank lines
    """
    result: Dict[str, str] = {}
    for line_no, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ImportError(f"Line {line_no}: missing '=' in {line!r}")
        key, _, raw_value = line.partition("=")
        key = key.strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            raise ImportError(f"Line {line_no}: invalid key name {key!r}")
        value = raw_value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1].replace('\\"', '"')
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        result[key] = value
    return result


def parse_json_env(text: str) -> Dict[str, str]:
    """Parse a JSON object of string key-value pairs."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ImportError(f"Invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ImportError("JSON root must be an object")
    result: Dict[str, str] = {}
    for k, v in data.items():
        if not isinstance(v, str):
            raise ImportError(f"Key {k!r}: value must be a string, got {type(v).__name__}")
        result[k] = v
    return result


def import_from_file(path: Path) -> Tuple[Dict[str, str], str]:
    """Detect file format and parse it. Returns (vars_dict, format_name)."""
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json":
        return parse_json_env(text), "json"
    # Default: treat as .env
    return parse_dotenv(text), "dotenv"


def import_from_os_env(prefix: Optional[str] = None) -> Dict[str, str]:
    """Import variables from the current OS environment, optionally filtered by prefix."""
    env = dict(os.environ)
    if prefix:
        env = {k: v for k, v in env.items() if k.startswith(prefix)}
    return env
