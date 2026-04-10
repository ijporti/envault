"""CLI subcommands for snapshot management."""

from __future__ import annotations

import argparse
import sys

from envault.cli import _get_password
from envault.snapshot import (
    SnapshotError,
    create_snapshot,
    delete_snapshot,
    list_snapshots,
    restore_snapshot,
)


def cmd_snapshot(args: argparse.Namespace) -> None:
    """Dispatch to the correct snapshot sub-action."""
    action = args.snapshot_action

    if action == "create":
        _cmd_create(args)
    elif action == "restore":
        _cmd_restore(args)
    elif action == "list":
        _cmd_list(args)
    elif action == "delete":
        _cmd_delete(args)
    else:
        print(f"Unknown snapshot action: {action}", file=sys.stderr)
        sys.exit(1)


def _cmd_create(args: argparse.Namespace) -> None:
    password = _get_password(args)
    tags = args.tags.split(",") if getattr(args, "tags", None) else []
    try:
        snap = create_snapshot(args.vault_dir, password, args.label, tags=tags)
    except SnapshotError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    env_list = ", ".join(snap.environments.keys())
    print(f"Snapshot '{snap.label}' created at {snap.created_at} ({env_list}).")


def _cmd_restore(args: argparse.Namespace) -> None:
    password = _get_password(args)
    try:
        count = restore_snapshot(args.vault_dir, password, args.label)
    except SnapshotError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Restored {count} environment(s) from snapshot '{args.label}'.")


def _cmd_list(args: argparse.Namespace) -> None:
    snaps = list_snapshots(args.vault_dir)
    if not snaps:
        print("No snapshots found.")
        return
    for snap in snaps:
        tag_str = f"  [{', '.join(snap.tags)}]" if snap.tags else ""
        envs = ", ".join(snap.environments.keys())
        print(f"{snap.label}  {snap.created_at}{tag_str}  envs: {envs}")


def _cmd_delete(args: argparse.Namespace) -> None:
    deleted = delete_snapshot(args.vault_dir, args.label)
    if deleted:
        print(f"Snapshot '{args.label}' deleted.")
    else:
        print(f"Snapshot '{args.label}' not found.", file=sys.stderr)
        sys.exit(1)


def register_snapshot_subcommand(subparsers: argparse._SubParsersAction) -> None:
    """Attach 'snapshot' command and its sub-actions to the main parser."""
    parser = subparsers.add_parser("snapshot", help="Manage environment snapshots.")
    sub = parser.add_subparsers(dest="snapshot_action", required=True)

    # create
    p_create = sub.add_parser("create", help="Capture current state as a snapshot.")
    p_create.add_argument("label", help="Unique snapshot label.")
    p_create.add_argument("--tags", default="", help="Comma-separated tags.")

    # restore
    p_restore = sub.add_parser("restore", help="Restore environments from a snapshot.")
    p_restore.add_argument("label", help="Snapshot label to restore.")

    # list
    sub.add_parser("list", help="List all snapshots.")

    # delete
    p_delete = sub.add_parser("delete", help="Delete a snapshot by label.")
    p_delete.add_argument("label", help="Snapshot label to delete.")

    parser.set_defaults(func=cmd_snapshot)
