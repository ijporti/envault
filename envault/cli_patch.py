"""CLI sub-command: patch — apply partial key updates to an environment."""

from __future__ import annotations

import argparse
import sys

from envault.cli import _get_password
from envault.patch import PatchError, patch_env


def cmd_patch(args: argparse.Namespace) -> int:
    """Handle the ``envault patch`` sub-command."""
    password = _get_password(args)

    # Build patch dict from KEY=VALUE pairs supplied on the CLI
    patch: dict[str, str] = {}
    for pair in args.assignments:
        if "=" not in pair:
            print(f"[error] Invalid assignment '{pair}' — expected KEY=VALUE", file=sys.stderr)
            return 1
        key, _, value = pair.partition("=")
        patch[key.strip()] = value

    keys_filter = args.keys.split(",") if args.keys else None

    try:
        result = patch_env(
            args.vault_dir,
            args.environment,
            password,
            patch,
            keys=keys_filter,
            add_new=not args.no_add,
        )
    except PatchError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    if result.updated:
        print(f"Updated : {', '.join(sorted(result.updated))}")
    if result.added:
        print(f"Added   : {', '.join(sorted(result.added))}")
    if result.skipped:
        print(f"Skipped : {', '.join(sorted(result.skipped))}")
    print(f"Total changes: {result.total_changed}")
    return 0


def register_patch_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "patch",
        help="Apply partial updates to an environment",
    )
    parser.add_argument("environment", help="Target environment name")
    parser.add_argument(
        "assignments",
        nargs="+",
        metavar="KEY=VALUE",
        help="One or more key=value pairs to apply",
    )
    parser.add_argument(
        "--keys",
        default="",
        metavar="K1,K2",
        help="Comma-separated allow-list of keys to patch (others ignored)",
    )
    parser.add_argument(
        "--no-add",
        action="store_true",
        help="Do not add keys that are absent from the environment",
    )
    parser.set_defaults(func=cmd_patch)
