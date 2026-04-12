"""Value transformation utilities for envault."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from envault.store import load_vault, save_vault


class TransformError(Exception):
    """Raised when a transformation fails."""


@dataclass
class TransformResult:
    environment: str
    changed: Dict[str, str] = field(default_factory=dict)  # key -> new_value
    skipped: List[str] = field(default_factory=list)

    @property
    def total_changed(self) -> int:
        return len(self.changed)


_TRANSFORMS: Dict[str, Callable[[str], str]] = {
    "upper": str.upper,
    "lower": str.lower,
    "strip": str.strip,
    "base64_encode": lambda v: base64.b64encode(v.encode()).decode(),
    "base64_decode": lambda v: base64.b64decode(v.encode()).decode(),
    "reverse": lambda v: v[::-1],
    "trim_quotes": lambda v: v.strip("'\"" ),
}


def available_transforms() -> List[str]:
    """Return the names of all built-in transforms."""
    return sorted(_TRANSFORMS.keys())


def apply_transform(value: str, transform_name: str) -> str:
    """Apply a named transform to *value*.

    Raises TransformError for unknown transform names or decoding failures.
    """
    fn = _TRANSFORMS.get(transform_name)
    if fn is None:
        raise TransformError(
            f"Unknown transform '{transform_name}'. "
            f"Available: {', '.join(available_transforms())}"
        )
    try:
        return fn(value)
    except Exception as exc:
        raise TransformError(
            f"Transform '{transform_name}' failed on value: {exc}"
        ) from exc


def transform_env(
    vault_dir: str,
    environment: str,
    password: str,
    transform_name: str,
    keys: Optional[List[str]] = None,
) -> TransformResult:
    """Apply *transform_name* to secrets in *environment*.

    If *keys* is provided only those keys are transformed; otherwise all keys
    in the environment are processed.
    """
    secrets = load_vault(vault_dir, environment, password)
    result = TransformResult(environment=environment)

    target_keys = keys if keys is not None else list(secrets.keys())

    for key in target_keys:
        if key not in secrets:
            result.skipped.append(key)
            continue
        new_value = apply_transform(secrets[key], transform_name)
        if new_value != secrets[key]:
            secrets[key] = new_value
            result.changed[key] = new_value

    if result.changed:
        save_vault(vault_dir, environment, password, secrets)

    return result
