"""Quota management: enforce maximum number of secrets per environment."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from envault.store import _vault_path, load_vault


class QuotaError(Exception):
    """Raised when a quota operation fails."""


@dataclass
class QuotaResult:
    environment: str
    limit: int
    current: int
    exceeded: bool = field(init=False)

    def __post_init__(self) -> None:
        self.exceeded = self.current > self.limit

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.current)

    def __str__(self) -> str:  # pragma: no cover
        status = "EXCEEDED" if self.exceeded else "OK"
        return (
            f"{self.environment}: {self.current}/{self.limit} secrets [{status}]"
        )


def _quota_path(vault_dir: Path) -> Path:
    return vault_dir / ".quotas.json"


def _load_quotas(vault_dir: Path) -> Dict[str, int]:
    path = _quota_path(vault_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_quotas(vault_dir: Path, quotas: Dict[str, int]) -> None:
    _quota_path(vault_dir).write_text(json.dumps(quotas, indent=2))


def set_quota(vault_dir: Path, environment: str, limit: int) -> int:
    """Set the maximum number of secrets allowed in *environment*."""
    if limit < 1:
        raise QuotaError("Quota limit must be a positive integer.")
    quotas = _load_quotas(vault_dir)
    quotas[environment] = limit
    _save_quotas(vault_dir, quotas)
    return limit


def remove_quota(vault_dir: Path, environment: str) -> bool:
    """Remove the quota for *environment*. Returns True if a quota existed."""
    quotas = _load_quotas(vault_dir)
    if environment not in quotas:
        return False
    del quotas[environment]
    _save_quotas(vault_dir, quotas)
    return True


def check_quota(
    vault_dir: Path,
    environment: str,
    password: str,
    *,
    default_limit: Optional[int] = None,
) -> QuotaResult:
    """Return a QuotaResult for *environment*.

    Raises QuotaError if no quota is configured and *default_limit* is None.
    """
    quotas = _load_quotas(vault_dir)
    if environment not in quotas:
        if default_limit is None:
            raise QuotaError(
                f"No quota configured for environment '{environment}'."
            )
        limit = default_limit
    else:
        limit = quotas[environment]

    vault_file = _vault_path(vault_dir, environment)
    if not vault_file.exists():
        current = 0
    else:
        secrets = load_vault(vault_dir, environment, password)
        current = len(secrets)

    return QuotaResult(environment=environment, limit=limit, current=current)
