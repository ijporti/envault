"""Redaction utilities for masking sensitive secret values in output."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class RedactError(Exception):
    """Raised when redaction configuration is invalid."""


@dataclass
class RedactResult:
    """Result of a redact operation on a dict of secrets."""

    original_count: int
    redacted_count: int
    data: Dict[str, str] = field(default_factory=dict)

    @property
    def total_visible(self) -> int:
        return self.original_count - self.redacted_count


_DEFAULT_MASK = "********"
_SENSITIVE_PATTERNS: List[re.Pattern] = [
    re.compile(r"(password|passwd|secret|token|api[_-]?key|auth|credential|private[_-]?key)", re.IGNORECASE),
]


def is_sensitive_key(key: str) -> bool:
    """Return True if *key* looks like it holds a sensitive value."""
    return any(p.search(key) for p in _SENSITIVE_PATTERNS)


def mask_value(value: str, visible_chars: int = 0, mask: str = _DEFAULT_MASK) -> str:
    """Return a masked version of *value*.

    If *visible_chars* > 0 the last N characters of the value are preserved.
    """
    if visible_chars < 0:
        raise RedactError("visible_chars must be >= 0")
    if visible_chars == 0 or len(value) <= visible_chars:
        return mask
    return mask + value[-visible_chars:]


def redact_dict(
    secrets: Dict[str, str],
    keys: Optional[List[str]] = None,
    auto_detect: bool = True,
    visible_chars: int = 0,
    mask: str = _DEFAULT_MASK,
) -> RedactResult:
    """Return a :class:`RedactResult` with sensitive values masked.

    Parameters
    ----------
    secrets:       Mapping of key -> plaintext value.
    keys:          Explicit list of keys to redact.  If *None*, only
                   auto-detection (when enabled) is used.
    auto_detect:   When *True*, keys matching :data:`_SENSITIVE_PATTERNS`
                   are also redacted.
    visible_chars: Number of trailing characters to keep visible.
    mask:          Replacement string for hidden characters.
    """
    to_redact: set[str] = set(keys or [])
    if auto_detect:
        to_redact |= {k for k in secrets if is_sensitive_key(k)}

    result: Dict[str, str] = {}
    for k, v in secrets.items():
        result[k] = mask_value(v, visible_chars=visible_chars, mask=mask) if k in to_redact else v

    return RedactResult(
        original_count=len(secrets),
        redacted_count=len(to_redact & secrets.keys()),
        data=result,
    )
