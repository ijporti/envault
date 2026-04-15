"""Registration helper so the main CLI can include webhook subcommands."""
from __future__ import annotations

import argparse

from envault.cli_webhook import register_webhook_subcommand


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register the webhook subcommand group with the top-level parser."""
    register_webhook_subcommand(subparsers)
