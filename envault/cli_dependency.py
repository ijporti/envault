"""CLI subcommands for dependency management."""
from __future__ import annotations

import argparse
from pathlib import Path

from envault.dependency import (
    add_dependency,
    remove_dependency,
    get_dependencies,
    get_dependents,
    dependency_order,
    DependencyError,
)
from envault.cli import _get_password


def cmd_dependency(args: argparse.Namespace) -> int:
    vault_dir = Path(args.vault_dir)
    sub = args.dep_action

    try:
        if sub == "add":
            password = _get_password(args)
            deps = add_dependency(vault_dir, args.environment, args.key, args.depends_on, password)
            print(f"Dependencies for '{args.key}': {', '.join(deps) if deps else '(none)'}")

        elif sub == "remove":
            remaining = remove_dependency(vault_dir, args.environment, args.key, args.depends_on)
            print(f"Remaining dependencies for '{args.key}': {', '.join(remaining) if remaining else '(none)'}")

        elif sub == "list":
            deps = get_dependencies(vault_dir, args.environment, args.key)
            if deps:
                for d in deps:
                    print(d)
            else:
                print(f"No dependencies recorded for '{args.key}'.")

        elif sub == "dependents":
            dependents = get_dependents(vault_dir, args.environment, args.key)
            if dependents:
                for d in dependents:
                    print(d)
            else:
                print(f"No keys depend on '{args.key}'.")

        elif sub == "order":
            order = dependency_order(vault_dir, args.environment)
            if order:
                for k in order:
                    print(k)
            else:
                print("No dependency graph recorded.")

    except DependencyError as exc:
        print(f"Error: {exc}")
        return 1

    return 0


def register_dependency_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("dependency", help="Manage key dependencies")
    p.add_argument("--vault-dir", default=".envault", help="Vault directory")
    p.add_argument("--environment", "-e", required=True, help="Target environment")
    p.add_argument("--password", "-p", default=None, help="Vault password")

    dep_sub = p.add_subparsers(dest="dep_action", required=True)

    add_p = dep_sub.add_parser("add", help="Add a dependency edge")
    add_p.add_argument("key", help="Dependent key")
    add_p.add_argument("depends_on", help="Key that it depends on")

    rm_p = dep_sub.add_parser("remove", help="Remove a dependency edge")
    rm_p.add_argument("key", help="Dependent key")
    rm_p.add_argument("depends_on", help="Key to remove from dependencies")

    ls_p = dep_sub.add_parser("list", help="List dependencies of a key")
    ls_p.add_argument("key", help="Key to inspect")

    dt_p = dep_sub.add_parser("dependents", help="List keys that depend on a given key")
    dt_p.add_argument("key", help="Key to inspect")

    dep_sub.add_parser("order", help="Print keys in topological dependency order")

    p.set_defaults(func=cmd_dependency)
