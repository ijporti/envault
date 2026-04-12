"""Validation rules for environment variable keys and values."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ValidationError(Exception):
    """Raised when a validation rule cannot be applied."""


@dataclass
class ValidationResult:
    key: str
    environment: str
    passed: bool
    rule: str
    message: str

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.environment}/{self.key} ({self.rule}): {self.message}"


# Built-in rules ---------------------------------------------------------------

def _rule_not_empty(key: str, value: str) -> Optional[str]:
    """Value must not be an empty string."""
    if value == "":
        return "value is empty"
    return None


def _rule_no_whitespace_only(key: str, value: str) -> Optional[str]:
    """Value must not be whitespace only."""
    if value.strip() == "" and value != "":
        return "value contains only whitespace"
    return None


def _rule_max_length(key: str, value: str, max_len: int = 4096) -> Optional[str]:
    """Value must not exceed max_len characters."""
    if len(value) > max_len:
        return f"value exceeds {max_len} characters (length={len(value)})"
    return None


def _rule_key_uppercase(key: str, value: str) -> Optional[str]:
    """Key should be uppercase."""
    if key != key.upper():
        return f"key '{key}' is not uppercase"
    return None


_BUILTIN_RULES = {
    "not_empty": _rule_not_empty,
    "no_whitespace_only": _rule_no_whitespace_only,
    "max_length": _rule_max_length,
    "key_uppercase": _rule_key_uppercase,
}


def validate_env(
    secrets: Dict[str, str],
    environment: str,
    rules: Optional[List[str]] = None,
) -> List[ValidationResult]:
    """Run validation rules against all key/value pairs in *secrets*.

    Args:
        secrets: Plaintext key → value mapping.
        environment: Environment label (for reporting).
        rules: List of rule names to apply.  Defaults to all built-in rules.

    Returns:
        List of :class:`ValidationResult` objects, one per (key, rule) pair.
    """
    if rules is None:
        rules = list(_BUILTIN_RULES.keys())

    unknown = set(rules) - _BUILTIN_RULES.keys()
    if unknown:
        raise ValidationError(f"Unknown validation rules: {sorted(unknown)}")

    results: List[ValidationResult] = []
    for key, value in secrets.items():
        for rule_name in rules:
            fn = _BUILTIN_RULES[rule_name]
            error_msg = fn(key, value)
            passed = error_msg is None
            results.append(
                ValidationResult(
                    key=key,
                    environment=environment,
                    passed=passed,
                    rule=rule_name,
                    message=error_msg if not passed else "ok",
                )
            )
    return results
