"""CLI sub-command: envault promote."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace
from typing import List, Optional

from envault.cli import _get_password
from envault.promote import PromoteError, promote_env


def cmd_promote(args: Namespace) -> int:
    """Entry-point for the *promote* sub-command.

    Returns an exit code (0 = success, non-zero = failure).
    """
    password = _get_password(args)

    keys: Optional[List[str]] = args.keys if args.keys else None

    try:
        result = promote_env(
            vault_dir=args.vault_dir,
            source_env=args.source,
            target_env=args.target,
            password=password,
            keys=keys,
            overwrite=args.overwrite,
        )
    except PromoteError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if result.promoted:
        print(f"Promoted ({len(result.promoted)}): {', '.join(sorted(result.promoted))}")
    if result.overwritten:
        print(f"Overwritten ({len(result.overwritten)}): {', '.join(sorted(result.overwritten))}")
    if result.skipped:
        print(f"Skipped ({len(result.skipped)}): {', '.join(sorted(result.skipped))}")

    total = result.total_promoted
    print(f"\n{total} secret(s) promoted from '{args.source}' → '{args.target}'.")
    return 0


def register_promote_subcommand(subparsers) -> None:  # type: ignore[type-arg]
    """Attach the *promote* sub-command to *subparsers*."""
    parser: ArgumentParser = subparsers.add_parser(
        "promote",
        help="Promote secrets from one environment to another.",
    )
    parser.add_argument("source", help="Source environment name.")
    parser.add_argument("target", help="Target environment name.")
    parser.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Specific keys to promote (default: all).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite keys that already exist in the target environment.",
    )
    parser.add_argument(
        "--vault-dir",
        default=".",
        help="Path to the vault directory (default: current directory).",
    )
    parser.set_defaults(func=cmd_promote)
