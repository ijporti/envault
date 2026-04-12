"""CLI subcommand for alias management."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.alias import AliasError, add_alias, resolve_alias, remove_alias, list_aliases
from envault.cli import _get_password


def cmd_alias(args: argparse.Namespace) -> int:
    vault_dir = Path(args.vault_dir)

    if args.alias_action == "add":
        password = _get_password(args)
        try:
            real_key = add_alias(vault_dir, args.environment, args.alias, args.key, password)
        except AliasError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"Alias '{args.alias}' -> '{real_key}' added in '{args.environment}'")
        return 0

    if args.alias_action == "resolve":
        real_key = resolve_alias(vault_dir, args.environment, args.alias)
        if real_key is None:
            print(f"Alias '{args.alias}' not found in '{args.environment}'", file=sys.stderr)
            return 1
        print(real_key)
        return 0

    if args.alias_action == "remove":
        removed = remove_alias(vault_dir, args.environment, args.alias)
        if not removed:
            print(f"Alias '{args.alias}' not found in '{args.environment}'", file=sys.stderr)
            return 1
        print(f"Alias '{args.alias}' removed from '{args.environment}'")
        return 0

    if args.alias_action == "list":
        aliases = list_aliases(vault_dir, args.environment)
        if not aliases:
            print(f"No aliases defined for '{args.environment}'")
        else:
            for alias, real_key in sorted(aliases.items()):
                print(f"{alias} -> {real_key}")
        return 0

    print(f"Unknown alias action: {args.alias_action}", file=sys.stderr)
    return 1


def register_alias_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "alias", help="Manage key aliases within an environment"
    )
    parser.add_argument("--vault-dir", default=".envault", help="Vault directory")
    parser.add_argument("-e", "--environment", required=True, help="Target environment")
    parser.add_argument("-p", "--password", default=None, help="Vault password")

    alias_sub = parser.add_subparsers(dest="alias_action", required=True)

    p_add = alias_sub.add_parser("add", help="Add an alias")
    p_add.add_argument("alias", help="Short alias name")
    p_add.add_argument("key", help="Real key the alias points to")

    p_resolve = alias_sub.add_parser("resolve", help="Resolve an alias to its real key")
    p_resolve.add_argument("alias", help="Alias to resolve")

    p_remove = alias_sub.add_parser("remove", help="Remove an alias")
    p_remove.add_argument("alias", help="Alias to remove")

    alias_sub.add_parser("list", help="List all aliases for an environment")

    parser.set_defaults(func=cmd_alias)
