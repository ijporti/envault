"""CLI subcommands for bookmark management."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.bookmark import (
    BookmarkError,
    add_bookmark,
    remove_bookmark,
    resolve_bookmark,
    list_bookmarks,
)
from envault.cli import _get_password


def cmd_bookmark(args: argparse.Namespace) -> int:
    vault_dir = Path(args.vault_dir)
    sub = args.bookmark_sub

    if sub == "add":
        password = _get_password(args)
        try:
            entry = add_bookmark(vault_dir, args.alias, args.environment, args.key, password)
            print(f"Bookmarked: {entry}")
        except BookmarkError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    elif sub == "remove":
        removed = remove_bookmark(vault_dir, args.alias)
        if removed:
            print(f"Removed bookmark '{args.alias}'.")
        else:
            print(f"Bookmark '{args.alias}' not found.", file=sys.stderr)
            return 1

    elif sub == "get":
        password = _get_password(args)
        value = resolve_bookmark(vault_dir, args.alias, password)
        if value is None:
            print(f"No bookmark named '{args.alias}'.", file=sys.stderr)
            return 1
        print(value)

    elif sub == "list":
        entries = list_bookmarks(vault_dir)
        if not entries:
            print("No bookmarks defined.")
        else:
            for entry in entries:
                print(entry)

    return 0


def register_bookmark_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("bookmark", help="Manage key bookmarks")
    parser.add_argument("--vault-dir", default=".", dest="vault_dir")
    parser.add_argument("--password", default=None)
    bsub = parser.add_subparsers(dest="bookmark_sub", required=True)

    p_add = bsub.add_parser("add", help="Add a bookmark")
    p_add.add_argument("alias", help="Short alias for the bookmark")
    p_add.add_argument("environment", help="Environment name")
    p_add.add_argument("key", help="Secret key to bookmark")

    p_remove = bsub.add_parser("remove", help="Remove a bookmark")
    p_remove.add_argument("alias")

    p_get = bsub.add_parser("get", help="Retrieve the value of a bookmarked key")
    p_get.add_argument("alias")

    bsub.add_parser("list", help="List all bookmarks")

    parser.set_defaults(func=cmd_bookmark)
