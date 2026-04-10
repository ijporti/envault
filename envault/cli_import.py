"""CLI subcommand: envault import — import env vars from a file or OS environment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from envault.audit import record
from envault.cli import _get_password
from envault.import_env import ImportError, import_from_file, import_from_os_env
from envault.store import load_vault, save_vault


def cmd_import(args: argparse.Namespace) -> None:
    """Handle the `envault import` subcommand."""
    password = _get_password(confirm=False)

    # Load existing vault (create empty if missing)
    try:
        vault = load_vault(args.env, password)
    except FileNotFoundError:
        vault = {}

    # Gather variables to import
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        try:
            new_vars, fmt = import_from_file(file_path)
        except ImportError as exc:
            print(f"Error parsing file: {exc}", file=sys.stderr)
            sys.exit(1)
        source_desc = f"{fmt} file {args.file}"
    else:
        prefix: Optional[str] = args.prefix or None
        new_vars = import_from_os_env(prefix=prefix)
        source_desc = "OS environment" + (f" (prefix={prefix})" if prefix else "")

    if not new_vars:
        print("No variables found to import.")
        return

    # Merge: skip existing keys unless --overwrite
    skipped = []
    imported = []
    for key, value in new_vars.items():
        if key in vault and not args.overwrite:
            skipped.append(key)
            continue
        vault[key] = value
        imported.append(key)

    save_vault(args.env, vault, password)

    for key in imported:
        record(args.env, "import", key)

    print(f"Imported {len(imported)} variable(s) from {source_desc}.")
    if skipped:
        print(f"Skipped {len(skipped)} existing key(s): {', '.join(skipped)}")
        print("Use --overwrite to replace existing keys.")


def register_import_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the `import` subcommand on the given subparsers object."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "import",
        help="Import environment variables from a .env / JSON file or OS environment",
    )
    parser.add_argument("env", help="Target environment name (e.g. production)")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--file", "-f", metavar="PATH",
                        help="Path to a .env or JSON file to import")
    source.add_argument("--from-os", dest="from_os", action="store_true",
                        help="Import from the current OS environment")
    parser.add_argument("--prefix", metavar="PREFIX",
                        help="Only import OS env vars with this prefix (implies --from-os)")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing keys")
    parser.set_defaults(func=cmd_import)
