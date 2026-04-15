"""CLI subcommand: envault pipeline — run a JSON-defined pipeline against an environment."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envault.pipeline import PipelineStep, PipelineResult, PipelineError, run_pipeline
from envault.cli import _get_password


def cmd_pipeline(args: argparse.Namespace) -> int:
    """Entry point for the `pipeline` subcommand."""
    password = _get_password(args)

    # Load steps from --steps JSON string or --steps-file
    if args.steps_file:
        try:
            with open(args.steps_file) as fh:
                raw_steps = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"error: could not read steps file: {exc}", file=sys.stderr)
            return 1
    elif args.steps:
        try:
            raw_steps = json.loads(args.steps)
        except json.JSONDecodeError as exc:
            print(f"error: invalid JSON for --steps: {exc}", file=sys.stderr)
            return 1
    else:
        print("error: provide --steps or --steps-file", file=sys.stderr)
        return 1

    if not isinstance(raw_steps, list):
        print("error: steps must be a JSON array", file=sys.stderr)
        return 1

    steps: List[PipelineStep] = []
    for item in raw_steps:
        if "operation" not in item:
            print("error: each step must have an 'operation' field", file=sys.stderr)
            return 1
        steps.append(PipelineStep(operation=item["operation"], params=item.get("params", {})))

    try:
        result: PipelineResult = run_pipeline(
            args.vault_dir, args.environment, password, steps
        )
    except PipelineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(
        f"Pipeline complete — {result.steps_applied} applied, "
        f"{result.steps_skipped} skipped ({result.environment})"
    )
    for change in result.changes:
        print(f"  • {change}")
    return 0


def register_pipeline_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "pipeline",
        help="Run a sequence of operations against an environment",
    )
    parser.add_argument("environment", help="Target environment name")
    parser.add_argument(
        "--steps",
        metavar="JSON",
        help="Inline JSON array of pipeline steps",
    )
    parser.add_argument(
        "--steps-file",
        metavar="FILE",
        help="Path to a JSON file containing pipeline steps",
    )
    parser.add_argument("--vault-dir", default=".envault", help="Vault directory")
    parser.add_argument("--password", help="Vault password (insecure; prefer env var)")
    parser.set_defaults(func=cmd_pipeline)
