"""CLI sub-commands for locking and unlocking environments."""

from __future__ import annotations

import argparse
import sys

from envault.lock import LockError, list_locked, lock_env, unlock_env


def cmd_lock(args: argparse.Namespace) -> int:
    """Dispatch to lock / unlock / list sub-actions."""
    action = getattr(args, "lock_action", None)

    if action == "lock":
        try:
            newly_locked = lock_env(args.vault_dir, args.environment)
        except LockError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if newly_locked:
            print(f"Locked '{args.environment}'.")
        else:
            print(f"'{args.environment}' is already locked.")
        return 0

    if action == "unlock":
        was_locked = unlock_env(args.vault_dir, args.environment)
        if was_locked:
            print(f"Unlocked '{args.environment}'.")
        else:
            print(f"'{args.environment}' was not locked.")
        return 0

    if action == "list":
        locked = list_locked(args.vault_dir)
        if not locked:
            print("No environments are currently locked.")
        else:
            for env in locked:
                print(env)
        return 0

    print("error: specify a lock sub-command (lock | unlock | list)", file=sys.stderr)
    return 1


def register_lock_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser("lock", help="Lock or unlock environments.")
    parser.add_argument(
        "--vault-dir",
        default=".envault",
        help="Path to the vault directory (default: .envault).",
    )
    lock_sub = parser.add_subparsers(dest="lock_action")

    p_lock = lock_sub.add_parser("lock", help="Lock an environment.")
    p_lock.add_argument("environment", help="Environment name to lock.")

    p_unlock = lock_sub.add_parser("unlock", help="Unlock an environment.")
    p_unlock.add_argument("environment", help="Environment name to unlock.")

    lock_sub.add_parser("list", help="List all locked environments.")

    parser.set_defaults(func=cmd_lock)
