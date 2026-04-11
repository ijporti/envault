"""Lint environment variable keys and values for common issues."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LintIssue:
    key: str
    severity: str  # 'error' | 'warning'
    message: str
    environment: Optional[str] = None

    def __str__(self) -> str:
        env_part = f"[{self.environment}] " if self.environment else ""
        return f"{self.severity.upper()}: {env_part}{self.key} — {self.message}"


_VALID_KEY_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')
_LOWER_KEY_RE = re.compile(r'[a-z]')


def lint_keys(secrets: dict[str, str], environment: Optional[str] = None) -> List[LintIssue]:
    """Check keys for naming convention issues."""
    issues: List[LintIssue] = []
    for key in secrets:
        if not key:
            issues.append(LintIssue(key="(empty)", severity="error",
                                     message="Key must not be empty.", environment=environment))
            continue
        if _LOWER_KEY_RE.search(key):
            issues.append(LintIssue(key=key, severity="warning",
                                     message="Key contains lowercase letters; prefer ALL_CAPS.",
                                     environment=environment))
        elif not _VALID_KEY_RE.match(key):
            issues.append(LintIssue(key=key, severity="error",
                                     message="Key contains invalid characters (use A-Z, 0-9, _).",
                                     environment=environment))
    return issues


def lint_values(secrets: dict[str, str], environment: Optional[str] = None) -> List[LintIssue]:
    """Check values for common problems."""
    issues: List[LintIssue] = []
    for key, value in secrets.items():
        if value == "":
            issues.append(LintIssue(key=key, severity="warning",
                                     message="Value is empty.", environment=environment))
        elif value != value.strip():
            issues.append(LintIssue(key=key, severity="warning",
                                     message="Value has leading or trailing whitespace.",
                                     environment=environment))
    return issues


def lint_env(secrets: dict[str, str], environment: Optional[str] = None) -> List[LintIssue]:
    """Run all lint checks on a single environment's secrets."""
    return lint_keys(secrets, environment) + lint_values(secrets, environment)


def lint_all(vault: dict[str, dict[str, str]]) -> List[LintIssue]:
    """Run lint checks across every environment in the vault."""
    issues: List[LintIssue] = []
    for env_name, secrets in vault.items():
        issues.extend(lint_env(secrets, environment=env_name))
    return issues
