"""Thin integration shim — registers the rename sub-command with the main CLI.

Import and call ``register(subparsers)`` from ``envault/cli.py`` to enable
the ``envault rename`` command.

Example
-------
::

    import argparse
    from envault.cli_rename_register import register

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register(subparsers)
"""

from __future__ import annotations

import argparse

from .cli_rename import register_rename_subcommand


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register all rename-related sub-commands with *subparsers*.

    Parameters
    ----------
    subparsers:
        The ``_SubParsersAction`` object returned by
        ``ArgumentParser.add_subparsers()``.  The rename sub-command will
        be added to this group so that it appears in the top-level help
        output alongside other envault commands.
    """
    register_rename_subcommand(subparsers)


__all__ = ["register"]
