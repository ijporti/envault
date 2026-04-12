"""CLI sub-command: rollback — restore an environment to a previous snapshot."""

from __future__ import annotations

import argparse
import sys

from envault.cli import _get_password
from envault.rollback import rollback_env, RollbackError
from envault.snapshot import list_snapshots


def cmd_rollback(args: argparse.Namespace) -> int:
    """Entry point for the ``rollback`` sub-command."""
    password = _get_password(args)

    # If the user asked for a listing of available snapshots, print and exit.
    if getattr(args, "list_snapshots", False):
        snapshots = list_snapshots(args.vault_dir, args.environment)
        if not snapshots:
            print(f"No snapshots found for environment '{args.environment}'.")
            return 0
        for snap in snapshots:
            tags = ", ".join(snap.tags) if snap.tags else ""
            tag_str = f"  [{tags}]" if tags else ""
            print(f"{snap.snapshot_id}  {snap.timestamp}{tag_str}")
        return 0

    if not args.snapshot_id:
        print("error: --snapshot-id is required unless --list is specified.", file=sys.stderr)
        return 1

    try:
        result = rollback_env(
            args.vault_dir,
            args.environment,
            args.snapshot_id,
            password,
            dry_run=args.dry_run,
        )
    except RollbackError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(
            f"[dry-run] Would restore {result.keys_restored} key(s) to "
            f"'{result.environment}' from snapshot {result.snapshot_id}."
        )
    else:
        print(
            f"Rolled back '{result.environment}' to snapshot {result.snapshot_id}. "
            f"Keys restored: {result.keys_restored} "
            f"(was {result.previous_key_count}, net change {result.net_change:+d})."
        )
    return 0


def register_rollback_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach the ``rollback`` sub-command to *subparsers*."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "rollback",
        help="Restore an environment to a previous snapshot.",
    )
    parser.add_argument("environment", help="Target environment name.")
    parser.add_argument(
        "--snapshot-id",
        dest="snapshot_id",
        default=None,
        help="ID of the snapshot to restore.",
    )
    parser.add_argument(
        "--list",
        dest="list_snapshots",
        action="store_true",
        help="List available snapshots for the environment.",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Preview the rollback without writing changes.",
    )
    parser.set_defaults(func=cmd_rollback)
