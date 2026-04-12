"""CLI subcommands for group management."""

from __future__ import annotations

import argparse
import sys

from envault.cli import _get_password
from envault.group import (
    GroupError,
    add_to_group,
    remove_from_group,
    list_groups,
    get_group_keys,
)


def cmd_group(args: argparse.Namespace) -> int:
    """Dispatch to the correct group sub-action."""
    action = getattr(args, "group_action", None)
    if action == "add":
        return _cmd_add(args)
    if action == "remove":
        return _cmd_remove(args)
    if action == "list":
        return _cmd_list(args)
    if action == "show":
        return _cmd_show(args)
    print("No group action specified. Use --help.", file=sys.stderr)
    return 1


def _cmd_add(args: argparse.Namespace) -> int:
    password = _get_password(args)
    try:
        keys = add_to_group(args.vault_dir, args.environment, args.group, args.keys, password)
        print(f"Group '{args.group}' in '{args.environment}' now contains: {', '.join(keys)}")
        return 0
    except GroupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _cmd_remove(args: argparse.Namespace) -> int:
    try:
        remaining = remove_from_group(args.vault_dir, args.environment, args.group, args.keys)
        print(f"Remaining keys in '{args.group}': {', '.join(remaining) or '(empty)'}")
        return 0
    except GroupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _cmd_list(args: argparse.Namespace) -> int:
    env = getattr(args, "environment", None)
    groups = list_groups(args.vault_dir, environment=env)
    if not groups:
        print("No groups defined.")
        return 0
    for group_key, keys in sorted(groups.items()):
        print(f"{group_key}: {', '.join(keys)}")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    try:
        keys = get_group_keys(args.vault_dir, args.environment, args.group)
        for key in keys:
            print(key)
        return 0
    except GroupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def register_group_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("group", help="Manage key groups")
    parser.add_argument("--vault-dir", default=".envault", help="Vault directory")
    parser.add_argument("--password", default=None, help="Vault password")
    parser.add_argument("--environment", "-e", default="default", help="Environment name")

    actions = parser.add_subparsers(dest="group_action")

    p_add = actions.add_parser("add", help="Add keys to a group")
    p_add.add_argument("group", help="Group name")
    p_add.add_argument("keys", nargs="+", help="Keys to add")

    p_rm = actions.add_parser("remove", help="Remove keys from a group")
    p_rm.add_argument("group", help="Group name")
    p_rm.add_argument("keys", nargs="+", help="Keys to remove")

    p_ls = actions.add_parser("list", help="List all groups")

    p_show = actions.add_parser("show", help="Show keys in a group")
    p_show.add_argument("group", help="Group name")

    parser.set_defaults(func=cmd_group)
