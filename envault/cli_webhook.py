"""CLI subcommands for webhook management."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.webhook import (
    WebhookError,
    fire_webhooks,
    list_webhooks,
    register_webhook,
    remove_webhook,
)


def cmd_webhook(args: argparse.Namespace) -> int:
    vault_dir = Path(args.vault_dir)
    sub = args.webhook_sub

    if sub == "add":
        return _cmd_add(vault_dir, args)
    if sub == "remove":
        return _cmd_remove(vault_dir, args)
    if sub == "list":
        return _cmd_list(vault_dir)
    if sub == "fire":
        return _cmd_fire(vault_dir, args)
    print(f"Unknown webhook subcommand: {sub}", file=sys.stderr)
    return 1


def _cmd_add(vault_dir: Path, args: argparse.Namespace) -> int:
    try:
        urls = register_webhook(vault_dir, args.url)
    except WebhookError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Registered webhook. Total: {len(urls)}")
    return 0


def _cmd_remove(vault_dir: Path, args: argparse.Namespace) -> int:
    removed = remove_webhook(vault_dir, args.url)
    if removed:
        print(f"Removed webhook: {args.url}")
        return 0
    print(f"Webhook not found: {args.url}", file=sys.stderr)
    return 1


def _cmd_list(vault_dir: Path) -> int:
    urls = list_webhooks(vault_dir)
    if not urls:
        print("No webhooks registered.")
    for url in urls:
        print(url)
    return 0


def _cmd_fire(vault_dir: Path, args: argparse.Namespace) -> int:
    results = fire_webhooks(vault_dir, args.event, {"note": "manual"})
    if not results:
        print("No webhooks to fire.")
        return 0
    code = 0
    for r in results:
        print(r)
        if not r.ok:
            code = 1
    return code


def register_webhook_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("webhook", help="Manage webhook notifications")
    p.add_argument("--vault-dir", default=".envault")
    ws = p.add_subparsers(dest="webhook_sub", required=True)

    p_add = ws.add_parser("add", help="Register a webhook URL")
    p_add.add_argument("url")

    p_rm = ws.add_parser("remove", help="Remove a webhook URL")
    p_rm.add_argument("url")

    ws.add_parser("list", help="List registered webhooks")

    p_fire = ws.add_parser("fire", help="Manually fire all webhooks")
    p_fire.add_argument("event", help="Event name to send")

    p.set_defaults(func=cmd_webhook)
