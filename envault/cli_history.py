"""CLI subcommands for per-key change history."""

from __future__ import annotations

import argparse
from pathlib import Path

from envault.history import clear_history, get_history, record_change
from envault.store import _vault_path


def cmd_history(args: argparse.Namespace) -> int:
    vault_dir = _vault_path(args.vault_dir)

    if args.history_cmd == "log":
        return _cmd_log(args, vault_dir)
    if args.history_cmd == "clear":
        return _cmd_clear(args, vault_dir)
    args.parser.print_help()
    return 1


def _cmd_log(args: argparse.Namespace, vault_dir: Path) -> int:
    limit = getattr(args, "limit", None)
    entries = get_history(vault_dir, args.environment, args.key, limit=limit)
    if not entries:
        print(f"No history found for '{args.key}' in '{args.environment}'.")
        return 0
    for entry in entries:
        print(str(entry))
    return 0


def _cmd_clear(args: argparse.Namespace, vault_dir: Path) -> int:
    removed = clear_history(vault_dir, args.environment, args.key)
    print(f"Cleared {removed} history entry/entries for '{args.key}'.")
    return 0


def register_history_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "history",
        help="View or clear per-key change history",
    )
    parser.set_defaults(parser=parser)
    sub = parser.add_subparsers(dest="history_cmd")

    # log
    log_p = sub.add_parser("log", help="Show change history for a key")
    log_p.add_argument("environment", help="Environment name")
    log_p.add_argument("key", help="Secret key name")
    log_p.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Show only the N most recent entries",
    )

    # clear
    clear_p = sub.add_parser("clear", help="Remove all history for a key")
    clear_p.add_argument("environment", help="Environment name")
    clear_p.add_argument("key", help="Secret key name")

    parser.set_defaults(func=cmd_history)
