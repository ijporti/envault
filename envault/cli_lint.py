"""CLI sub-command: envault lint — report issues across vault environments."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from envault.lint import lint_all, lint_env
from envault.store import load_vault


def cmd_lint(args: argparse.Namespace) -> int:
    """Entry point for the 'lint' sub-command.

    Returns an exit code: 0 = no errors found, 1 = errors present.
    """
    try:
        vault = load_vault(args.vault_dir, args.password)
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not load vault — {exc}", file=sys.stderr)
        return 2

    if args.environment:
        if args.environment not in vault:
            print(f"error: environment '{args.environment}' not found.", file=sys.stderr)
            return 2
        issues = lint_env(vault[args.environment], environment=args.environment)
    else:
        issues = lint_all(vault)

    if not issues:
        print("No lint issues found.")
        return 0

    errors = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]

    for issue in sorted(issues, key=lambda i: (i.environment or "", i.severity, i.key)):
        print(str(issue))

    summary_parts = []
    if errors:
        summary_parts.append(f"{len(errors)} error(s)")
    if warnings:
        summary_parts.append(f"{len(warnings)} warning(s)")
    print(f"\n{', '.join(summary_parts)} found.")

    return 1 if errors else 0


def register_lint_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach the 'lint' sub-command to *subparsers*."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "lint",
        help="Check environment variable keys and values for common issues.",
    )
    parser.add_argument(
        "--vault-dir",
        default=".",
        help="Directory that contains the vault files (default: current directory).",
    )
    parser.add_argument(
        "--password",
        required=True,
        help="Master password used to decrypt the vault.",
    )
    parser.add_argument(
        "--environment", "-e",
        default=None,
        metavar="ENV",
        help="Lint a single environment instead of all environments.",
    )
    parser.set_defaults(func=cmd_lint)
