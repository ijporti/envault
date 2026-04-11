"""CLI subcommands for tag management."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.store import _vault_path
from envault.tags import (
    TagError,
    add_tags,
    remove_tags,
    get_tags,
    find_by_tag,
    list_all_tags,
)


def cmd_tags(args: argparse.Namespace) -> int:
    """Dispatch to the appropriate tags sub-action."""
    vault_dir = _vault_path(args.vault).parent

    try:
        if args.tag_action == "add":
            result = add_tags(vault_dir, args.environment, args.key, args.tags)
            print(f"Tags for '{args.key}': {', '.join(result)}")

        elif args.tag_action == "remove":
            result = remove_tags(vault_dir, args.environment, args.key, args.tags)
            remaining = ", ".join(result) if result else "(none)"
            print(f"Remaining tags for '{args.key}': {remaining}")

        elif args.tag_action == "get":
            tags = get_tags(vault_dir, args.environment, args.key)
            if tags:
                print("  ".join(tags))
            else:
                print(f"No tags found for '{args.key}'.")

        elif args.tag_action == "find":
            keys = find_by_tag(vault_dir, args.environment, args.tag)
            if keys:
                for k in keys:
                    print(k)
            else:
                print(f"No keys tagged '{args.tag}' in '{args.environment}'.")

        elif args.tag_action == "list":
            registry = list_all_tags(vault_dir, args.environment)
            if not registry:
                print(f"No tags defined in '{args.environment}'.")
            else:
                for key, tags in sorted(registry.items()):
                    print(f"{key}: {', '.join(tags)}")

        else:
            print(f"Unknown tag action: {args.tag_action}", file=sys.stderr)
            return 1

    except TagError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


def register_tags_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'tags' subcommand tree onto *subparsers*."""
    tags_parser = subparsers.add_parser("tags", help="Manage tags on secrets")
    tags_parser.add_argument("-e", "--environment", required=True, help="Target environment")
    tags_parser.add_argument("--vault", default=".envault", help="Vault directory")

    tag_sub = tags_parser.add_subparsers(dest="tag_action", required=True)

    # add
    p_add = tag_sub.add_parser("add", help="Add tags to a key")
    p_add.add_argument("key", help="Secret key name")
    p_add.add_argument("tags", nargs="+", help="Tags to add")

    # remove
    p_rm = tag_sub.add_parser("remove", help="Remove tags from a key")
    p_rm.add_argument("key", help="Secret key name")
    p_rm.add_argument("tags", nargs="+", help="Tags to remove")

    # get
    p_get = tag_sub.add_parser("get", help="List tags on a key")
    p_get.add_argument("key", help="Secret key name")

    # find
    p_find = tag_sub.add_parser("find", help="Find keys by tag")
    p_find.add_argument("tag", help="Tag to search for")

    # list
    tag_sub.add_parser("list", help="List all tags in an environment")

    tags_parser.set_defaults(func=cmd_tags)
