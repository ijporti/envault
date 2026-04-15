"""Pipeline: chain multiple transform/patch operations on an environment in sequence."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any

from envault.store import load_vault, save_vault
from envault.crypto import encrypt, decrypt


class PipelineError(Exception):
    """Raised when a pipeline step fails."""


@dataclass
class PipelineStep:
    operation: str          # 'set', 'delete', 'rename', 'transform'
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    environment: str
    steps_applied: int
    steps_skipped: int
    changes: List[str] = field(default_factory=list)

    @property
    def total_steps(self) -> int:
        return self.steps_applied + self.steps_skipped


def _apply_step(secrets: Dict[str, str], step: PipelineStep) -> tuple[Dict[str, str], str | None]:
    """Apply a single pipeline step to the secrets dict. Returns (new_secrets, change_description)."""
    op = step.operation
    p = step.params

    if op == "set":
        key, value = p.get("key"), p.get("value", "")
        if not key:
            raise PipelineError("'set' step requires 'key' param")
        secrets[key] = value
        return secrets, f"set {key}"

    elif op == "delete":
        key = p.get("key")
        if not key:
            raise PipelineError("'delete' step requires 'key' param")
        if key not in secrets:
            return secrets, None
        del secrets[key]
        return secrets, f"deleted {key}"

    elif op == "rename":
        src, dst = p.get("src"), p.get("dst")
        if not src or not dst:
            raise PipelineError("'rename' step requires 'src' and 'dst' params")
        if src not in secrets:
            return secrets, None
        secrets[dst] = secrets.pop(src)
        return secrets, f"renamed {src} -> {dst}"

    elif op == "transform":
        key, func = p.get("key"), p.get("func", "upper")
        if not key:
            raise PipelineError("'transform' step requires 'key' param")
        if key not in secrets:
            return secrets, None
        val = secrets[key]
        if func == "upper":
            secrets[key] = val.upper()
        elif func == "lower":
            secrets[key] = val.lower()
        elif func == "strip":
            secrets[key] = val.strip()
        else:
            raise PipelineError(f"Unknown transform func: {func!r}")
        return secrets, f"transform({func}) {key}"

    else:
        raise PipelineError(f"Unknown pipeline operation: {op!r}")


def run_pipeline(
    vault_dir: str,
    environment: str,
    password: str,
    steps: List[PipelineStep],
) -> PipelineResult:
    """Execute a sequence of steps against an environment and persist the result."""
    vault = load_vault(vault_dir, password)
    env_data: Dict[str, str] = vault.get(environment, {})

    applied, skipped, changes = 0, 0, []
    for step in steps:
        env_data, desc = _apply_step(env_data, step)
        if desc is not None:
            applied += 1
            changes.append(desc)
        else:
            skipped += 1

    vault[environment] = env_data
    save_vault(vault_dir, password, vault)
    return PipelineResult(
        environment=environment,
        steps_applied=applied,
        steps_skipped=skipped,
        changes=changes,
    )
