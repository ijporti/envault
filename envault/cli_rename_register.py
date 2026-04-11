"""Thin integration shim — registers the rename sub-command with the main CLI.

Import and call ``register(subparsers)`` from ``envault/cli.py`` to enable
the ``envault rename`` command.
"""

from __future__ import annotations

import argparse

from .cli_rename import register_rename_subcommand


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register all rename-related sub-commands."""
    register_rename_subcommand(subparsers)


__all__ = ["register"]
