"""CLI sub-commands for key renaming."""

from __future__ import annotations

import argparse
import sys

from .rename import RenameError, rename_key, rename_key_all_envs
from .cli import _get_password


def cmd_rename(args: argparse.Namespace) -> int:
    """Entry-point for the ``envault rename`` command."""
    password = _get_password(args)

    if args.all_envs:
        try:
            results = rename_key_all_envs(
                args.vault_dir,
                args.old_key,
                args.new_key,
                password,
                overwrite=args.overwrite,
            )
        except RenameError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

        applied = [env for env, changed in results.items() if changed]
        skipped = [env for env, changed in results.items() if not changed]
        print(f"Renamed '{args.old_key}' -> '{args.new_key}' in: {', '.join(applied) or 'none'}")
        if skipped:
            print(f"Key not found in: {', '.join(skipped)}")
        return 0

    try:
        found = rename_key(
            args.vault_dir,
            args.environment,
            args.old_key,
            args.new_key,
            password,
            overwrite=args.overwrite,
        )
    except RenameError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if found:
        print(f"Renamed '{args.old_key}' -> '{args.new_key}' in '{args.environment}'.")
    else:
        print(f"Key '{args.old_key}' not found in '{args.environment}'.")
    return 0 if found else 1


def register_rename_subcommand(subparsers) -> None:  # type: ignore[type-arg]
    """Attach the rename sub-command to *subparsers*."""
    p: argparse.ArgumentParser = subparsers.add_parser(
        "rename", help="Rename a key within an environment"
    )
    p.add_argument("old_key", help="Current key name")
    p.add_argument("new_key", help="New key name")
    p.add_argument("-e", "--environment", default="default", help="Target environment")
    p.add_argument(
        "--all-envs",
        action="store_true",
        default=False,
        help="Apply rename across all environments",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite new_key if it already exists",
    )
    p.set_defaults(func=cmd_rename)
