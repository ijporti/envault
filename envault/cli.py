"""Command-line interface for envault."""

import sys
import getpass
import argparse
from pathlib import Path

from envault.store import save_vault, load_vault, list_environments


def _get_password(prompt: str = "Vault password: ") -> str:
    return getpass.getpass(prompt)


def cmd_set(args: argparse.Namespace) -> int:
    """Set (or update) a key=value pair in the vault."""
    try:
        key, value = args.pair.split("=", 1)
    except ValueError:
        print("Error: argument must be in KEY=VALUE format.", file=sys.stderr)
        return 1

    password = _get_password()
    vault_dir = Path(args.vault_dir) if args.vault_dir else None

    try:
        secrets = load_vault(password, environment=args.env, vault_dir=vault_dir)
    except FileNotFoundError:
        secrets = {}

    secrets[key] = value
    path = save_vault(secrets, password, environment=args.env, vault_dir=vault_dir)
    print(f"Saved {key} to {path}")
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    """Print the value of a single key from the vault."""
    password = _get_password()
    vault_dir = Path(args.vault_dir) if args.vault_dir else None
    try:
        secrets = load_vault(password, environment=args.env, vault_dir=vault_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    value = secrets.get(args.key)
    if value is None:
        print(f"Key '{args.key}' not found.", file=sys.stderr)
        return 1
    print(value)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List available environments."""
    vault_dir = Path(args.vault_dir) if args.vault_dir else None
    envs = list_environments(vault_dir=vault_dir)
    if not envs:
        print("No environments found.")
    else:
        for env in envs:
            print(env)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Manage and encrypt environment variables.",
    )
    parser.add_argument("--vault-dir", default=None, help="Custom vault directory.")
    parser.add_argument("--env", default="default", help="Environment name.")

    sub = parser.add_subparsers(dest="command", required=True)

    p_set = sub.add_parser("set", help="Set a secret (KEY=VALUE).")
    p_set.add_argument("pair", metavar="KEY=VALUE")
    p_set.set_defaults(func=cmd_set)

    p_get = sub.add_parser("get", help="Get a secret by key.")
    p_get.add_argument("key", metavar="KEY")
    p_get.set_defaults(func=cmd_get)

    p_list = sub.add_parser("list", help="List environments.")
    p_list.set_defaults(func=cmd_list)

    return parser


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    main()
