"""CLI subcommand for diffing two vault environments."""

from __future__ import annotations

import sys
from typing import Optional

from envault.store import load_vault
from envault.diff import diff_envs, format_diff
from envault.audit import record


def cmd_diff(
    vault_dir: str,
    env_a: str,
    env_b: str,
    password_a: str,
    password_b: Optional[str] = None,
    show_unchanged: bool = False,
    use_color: bool = True,
) -> int:
    """Compare two environments and print a diff.  Returns exit code."""
    password_b = password_b or password_a

    try:
        secrets_a = load_vault(vault_dir, env_a, password_a)
    except Exception as exc:
        print(f"error: could not load '{env_a}': {exc}", file=sys.stderr)
        return 1

    try:
        secrets_b = load_vault(vault_dir, env_b, password_b)
    except Exception as exc:
        print(f"error: could not load '{env_b}': {exc}", file=sys.stderr)
        return 1

    entries = diff_envs(secrets_a, secrets_b, show_unchanged=show_unchanged)

    record(
        vault_dir,
        action="diff",
        environment=f"{env_a}..{env_b}",
        key=None,
        detail={"added": sum(1 for e in entries if e.status == "added"),
                "removed": sum(1 for e in entries if e.status == "removed"),
                "changed": sum(1 for e in entries if e.status == "changed")},
    )

    header = f"--- {env_a}\n+++ {env_b}"
    print(header)
    print(format_diff(entries, use_color=use_color))
    return 0


def register_diff_subcommand(subparsers) -> None:  # type: ignore[type-arg]
    """Attach the 'diff' subcommand to an existing ArgumentParser subparsers object."""
    p = subparsers.add_parser(
        "diff",
        help="Show differences between two environments",
    )
    p.add_argument("env_a", help="Source environment")
    p.add_argument("env_b", help="Target environment")
    p.add_argument(
        "--password-b",
        dest="password_b",
        default=None,
        help="Password for target environment (defaults to same as source)",
    )
    p.add_argument(
        "--show-unchanged",
        action="store_true",
        default=False,
        help="Also display keys that are identical in both environments",
    )
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI colour output",
    )
