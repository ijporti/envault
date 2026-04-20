"""CLI subcommand for shield: protect keys from being overwritten."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from envault.cli import _get_password
from envault.shield import (
    ShieldError,
    is_shielded,
    list_shields,
    shield_keys,
    unshield_keys,
)


def cmd_shield(args) -> int:
    vault_dir = Path(args.vault_dir)
    sub = args.shield_cmd

    if sub == "add":
        return _cmd_add(vault_dir, args)
    if sub == "remove":
        return _cmd_remove(vault_dir, args)
    if sub == "list":
        return _cmd_list(vault_dir, args)
    if sub == "check":
        return _cmd_check(vault_dir, args)

    print(f"Unknown shield subcommand: {sub}", file=sys.stderr)
    return 1


def _cmd_add(vault_dir: Path, args) -> int:
    password = _get_password(args)
    try:
        result = shield_keys(vault_dir, args.environment, args.keys, password)
    except ShieldError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    for key in result.shielded_keys:
        print(f"Shielded: {key}")
    for key in result.already_shielded:
        print(f"Already shielded: {key}")
    return 0


def _cmd_remove(vault_dir: Path, args) -> int:
    removed = unshield_keys(vault_dir, args.environment, args.keys)
    for key in removed:
        print(f"Unshielded: {key}")
    if not removed:
        print("No matching shielded keys found.")
    return 0


def _cmd_list(vault_dir: Path, args) -> int:
    shields = list_shields(vault_dir, args.environment)
    if not shields:
        print(f"No shielded keys in '{args.environment}'.")
    for key in shields:
        print(key)
    return 0


def _cmd_check(vault_dir: Path, args) -> int:
    key = args.keys[0]
    shielded = is_shielded(vault_dir, args.environment, key)
    status = "shielded" if shielded else "not shielded"
    print(f"{key} is {status} in '{args.environment}'.")
    return 0 if shielded else 2


def register_shield_subcommand(subparsers) -> None:
    parser = subparsers.add_parser("shield", help="Protect keys from being overwritten")
    parser.add_argument("--vault-dir", default=".envault")
    parser.add_argument("--password", default=None)
    parser.add_argument("--environment", "-e", required=True)

    sub = parser.add_subparsers(dest="shield_cmd", required=True)

    add_p = sub.add_parser("add", help="Shield one or more keys")
    add_p.add_argument("keys", nargs="+")

    rem_p = sub.add_parser("remove", help="Remove shield from keys")
    rem_p.add_argument("keys", nargs="+")

    sub.add_parser("list", help="List shielded keys")

    chk_p = sub.add_parser("check", help="Check if a key is shielded")
    chk_p.add_argument("keys", nargs=1)

    parser.set_defaults(func=cmd_shield)
