"""CLI subcommand: envault validate — run validation rules against an environment."""

from __future__ import annotations

import argparse
import sys
from typing import List

from .store import load_vault
from .validate import ValidationError, validate_env


def cmd_validate(args: argparse.Namespace) -> int:
    """Entry point for the *validate* subcommand.

    Returns 0 when all checks pass, 1 when any check fails, 2 on error.
    """
    try:
        vault = load_vault(args.vault_dir, args.password)
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not load vault: {exc}", file=sys.stderr)
        return 2

    environment = args.environment
    if environment not in vault:
        print(f"error: environment '{environment}' not found", file=sys.stderr)
        return 2

    rules: List[str] | None = args.rules if args.rules else None

    try:
        results = validate_env(vault[environment], environment, rules=rules)
    except ValidationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    failures = [r for r in results if not r.passed]
    passes = [r for r in results if r.passed]

    if args.verbose or failures:
        for r in results:
            print(str(r))
    else:
        print(f"All {len(passes)} check(s) passed for environment '{environment}'.")

    if failures:
        print(
            f"\n{len(failures)} check(s) failed out of {len(results)}.",
            file=sys.stderr,
        )
        return 1

    return 0


def register_validate_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register *validate* under an existing subparsers group."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "validate",
        help="Run validation rules against secrets in an environment.",
    )
    parser.add_argument("environment", help="Environment name to validate.")
    parser.add_argument(
        "--rules",
        nargs="+",
        metavar="RULE",
        help=(
            "One or more rule names to apply "
            "(not_empty, no_whitespace_only, max_length, key_uppercase). "
            "Defaults to all rules."
        ),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print all results, not just failures.",
    )
    parser.set_defaults(func=cmd_validate)
