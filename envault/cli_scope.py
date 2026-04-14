"""CLI subcommand for scope management."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.scope import ScopeError, set_scope, delete_scope, list_scopes, resolve_scope
from envault.cli import _get_password


def cmd_scope(args: argparse.Namespace) -> int:
    vault_dir = Path(args.vault_dir)
    sub = args.scope_cmd

    if sub == "set":
        try:
            envs = set_scope(vault_dir, args.scope, args.environments)
        except ScopeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"Scope '{args.scope}' set with environments: {', '.join(envs)}")
        return 0

    if sub == "delete":
        existed = delete_scope(vault_dir, args.scope)
        if existed:
            print(f"Scope '{args.scope}' deleted.")
            return 0
        print(f"error: scope '{args.scope}' not found.", file=sys.stderr)
        return 1

    if sub == "list":
        scopes = list_scopes(vault_dir)
        if not scopes:
            print("No scopes defined.")
            return 0
        for name, envs in sorted(scopes.items()):
            print(f"{name}: {', '.join(envs)}")
        return 0

    if sub == "resolve":
        password = _get_password(args)
        try:
            result = resolve_scope(
                vault_dir,
                args.scope,
                password,
                keys=args.keys or None,
            )
        except ScopeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        for env in result.environments:
            keys = result.keys_visible.get(env, [])
            print(f"[{env}] ({len(keys)} keys): {', '.join(keys) if keys else '(none)'}")
        return 0

    print(f"Unknown scope subcommand: {sub}", file=sys.stderr)
    return 1


def register_scope_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("scope", help="Manage key visibility scopes")
    p.add_argument("--vault-dir", default=".envault", metavar="DIR")
    p.add_argument("--password", default=None)
    scope_sub = p.add_subparsers(dest="scope_cmd", required=True)

    # set
    ps = scope_sub.add_parser("set", help="Define or overwrite a scope")
    ps.add_argument("scope")
    ps.add_argument("environments", nargs="+", metavar="ENV")

    # delete
    pd = scope_sub.add_parser("delete", help="Remove a scope")
    pd.add_argument("scope")

    # list
    scope_sub.add_parser("list", help="List all scopes")

    # resolve
    pr = scope_sub.add_parser("resolve", help="Show keys visible within a scope")
    pr.add_argument("scope")
    pr.add_argument("--keys", nargs="*", metavar="KEY", default=[])

    p.set_defaults(func=cmd_scope)
