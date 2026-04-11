"""CLI subcommands for vault archiving and restoration."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.archive import ArchiveError, create_archive, restore_archive
from envault.cli import _get_password


def cmd_archive(args: argparse.Namespace) -> int:
    """Dispatch to create or restore subcommand."""
    return args._archive_func(args)


def _cmd_create(args: argparse.Namespace) -> int:
    vault_dir = Path(args.vault_dir)
    dest = Path(args.output)
    password = _get_password(args)
    environments: list[str] = args.environments

    try:
        manifest = create_archive(vault_dir, password, environments, dest)
    except ArchiveError as exc:
        print(f"archive error: {exc}", file=sys.stderr)
        return 1

    print(f"Archived {len(manifest.environments)} environment(s) to '{dest}'.")
    for env in manifest.environments:
        print(f"  - {env}")
    return 0


def _cmd_restore(args: argparse.Namespace) -> int:
    vault_dir = Path(args.vault_dir)
    src = Path(args.input)
    password = _get_password(args)
    overwrite: bool = args.overwrite

    try:
        manifest = restore_archive(vault_dir, password, src, overwrite=overwrite)
    except ArchiveError as exc:
        print(f"archive error: {exc}", file=sys.stderr)
        return 1

    print(f"Restored {len(manifest.environments)} environment(s) from '{src}'.")
    for env in manifest.environments:
        print(f"  - {env}")
    return 0


def register_archive_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("archive", help="Archive or restore vault environments.")
    parser.add_argument("--vault-dir", default=".envault", help="Path to vault directory.")
    parser.add_argument("--password", default=None, help="Vault password (or set ENVAULT_PASSWORD).")

    sub = parser.add_subparsers(dest="archive_cmd", required=True)

    # create
    create_p = sub.add_parser("create", help="Create an archive from environments.")
    create_p.add_argument("environments", nargs="+", metavar="ENV", help="Environments to archive.")
    create_p.add_argument("-o", "--output", required=True, help="Destination zip file path.")
    create_p.set_defaults(_archive_func=_cmd_create)

    # restore
    restore_p = sub.add_parser("restore", help="Restore environments from an archive.")
    restore_p.add_argument("-i", "--input", required=True, help="Source zip file path.")
    restore_p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing environments.",
    )
    restore_p.set_defaults(_archive_func=_cmd_restore)

    parser.set_defaults(func=cmd_archive)
