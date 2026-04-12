"""CLI subcommand: envault prune."""

from __future__ import annotations

import argparse
import sys

from envault.cli import _get_password
from envault.prune import PruneError, prune_keys, prune_empty_values


def cmd_prune(args: argparse.Namespace) -> int:
    """Entry point for the *prune* subcommand.

    Modes
    -----
    --empty   Remove all keys with empty values.
    --keys K  Remove the listed keys explicitly.
    """
    password = _get_password(args)

    try:
        if args.empty:
            result = prune_empty_values(
                vault_dir=args.vault_dir,
                environment=args.environment,
                password=password,
            )
        elif args.keys:
            result = prune_keys(
                vault_dir=args.vault_dir,
                environment=args.environment,
                password=password,
                keys_to_remove=args.keys,
            )
        else:
            print(
                "error: specify --empty or --keys KEY [KEY ...]",
                file=sys.stderr,
            )
            return 2
    except PruneError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if result.total_removed == 0:
        print(f"[{result.environment}] Nothing pruned.")
    else:
        print(
            f"[{result.environment}] Pruned {result.total_removed} key(s): "
            + ", ".join(sorted(result.removed_keys))
        )
        print(f"  {result.total_kept} key(s) remaining.")

    return 0


def register_prune_subcommand(subparsers) -> None:  # type: ignore[type-arg]
    """Attach the *prune* subcommand to *subparsers*."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "prune",
        help="Remove stale or empty keys from an environment.",
    )
    parser.add_argument("environment", help="Target environment name.")
    parser.add_argument(
        "--vault-dir",
        default=".envault",
        help="Path to the vault directory (default: .envault).",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Vault password (omit to be prompted).",
    )

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--empty",
        action="store_true",
        help="Remove all keys whose value is an empty string.",
    )
    mode.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Explicit list of keys to remove.",
    )

    parser.set_defaults(func=cmd_prune)
