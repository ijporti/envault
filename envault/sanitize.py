"""Sanitize environment variable keys and values before storing them."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


class SanitizeError(Exception):
    """Raised when a key or value cannot be sanitized."""


@dataclass
class SanitizeResult:
    original_key: str
    sanitized_key: str
    original_value: str
    sanitized_value: str
    key_changed: bool = False
    value_changed: bool = False
    warnings: List[str] = field(default_factory=list)

    @property
    def any_changed(self) -> bool:
        return self.key_changed or self.value_changed


_INVALID_KEY_CHARS = re.compile(r"[^A-Z0-9_]")
_LEADING_DIGIT = re.compile(r"^[0-9]")


def sanitize_key(key: str) -> Tuple[str, List[str]]:
    """Normalize an env var key to UPPER_SNAKE_CASE and strip invalid chars."""
    warnings: List[str] = []
    original = key

    sanitized = key.strip()
    if sanitized != key:
        warnings.append(f"Key '{original}' had leading/trailing whitespace stripped.")

    sanitized = sanitized.upper()
    if sanitized != key.strip():
        warnings.append(f"Key '{original}' was uppercased.")

    sanitized = sanitized.replace("-", "_").replace(" ", "_")
    sanitized = _INVALID_KEY_CHARS.sub("", sanitized)

    if _LEADING_DIGIT.match(sanitized):
        sanitized = "_" + sanitized
        warnings.append(f"Key '{original}' started with a digit; prefixed with '_'.")

    if not sanitized:
        raise SanitizeError(f"Key '{original}' is empty after sanitization.")

    return sanitized, warnings


def sanitize_value(value: str) -> Tuple[str, List[str]]:
    """Strip null bytes and trailing whitespace from a value."""
    warnings: List[str] = []
    original = value

    sanitized = value.replace("\x00", "")
    if sanitized != value:
        warnings.append("Value contained null bytes; they were removed.")

    sanitized = sanitized.rstrip()
    if sanitized != original.replace("\x00", ""):
        warnings.append("Value had trailing whitespace stripped.")

    return sanitized, warnings


def sanitize_env(env: Dict[str, str]) -> List[SanitizeResult]:
    """Sanitize all keys and values in an environment dict.

    Returns a list of SanitizeResult objects, one per entry.
    Raises SanitizeError if any key becomes empty after sanitization.
    """
    results: List[SanitizeResult] = []
    for raw_key, raw_value in env.items():
        clean_key, key_warnings = sanitize_key(raw_key)
        clean_value, value_warnings = sanitize_value(raw_value)
        results.append(
            SanitizeResult(
                original_key=raw_key,
                sanitized_key=clean_key,
                original_value=raw_value,
                sanitized_value=clean_value,
                key_changed=clean_key != raw_key,
                value_changed=clean_value != raw_value,
                warnings=key_warnings + value_warnings,
            )
        )
    return results
