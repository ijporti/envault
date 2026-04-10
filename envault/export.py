"""Export vault secrets to various shell-compatible formats."""

from __future__ import annotations

from typing import Dict


SUPPORTED_FORMATS = ("dotenv", "shell", "json")


def export_dotenv(secrets: Dict[str, str]) -> str:
    """Render secrets as a .env file (KEY=VALUE per line)."""
    lines = []
    for key, value in sorted(secrets.items()):
        escaped = value.replace('"', '\\"')
        lines.append(f'{key}="{escaped}"')
    return "\n".join(lines) + ("\n" if lines else "")


def export_shell(secrets: Dict[str, str]) -> str:
    """Render secrets as POSIX shell export statements."""
    lines = []
    for key, value in sorted(secrets.items()):
        escaped = value.replace("'", "'\\''")
        lines.append(f"export {key}='{escaped}'")
    return "\n".join(lines) + ("\n" if lines else "")


def export_json(secrets: Dict[str, str]) -> str:
    """Render secrets as a JSON object."""
    import json
    return json.dumps(secrets, indent=2, sort_keys=True) + "\n"


def export_secrets(secrets: Dict[str, str], fmt: str) -> str:
    """Dispatch to the appropriate formatter.

    Args:
        secrets: Mapping of variable names to plaintext values.
        fmt: One of 'dotenv', 'shell', or 'json'.

    Returns:
        Formatted string ready to write to stdout or a file.

    Raises:
        ValueError: If *fmt* is not a supported format.
    """
    if fmt == "dotenv":
        return export_dotenv(secrets)
    if fmt == "shell":
        return export_shell(secrets)
    if fmt == "json":
        return export_json(secrets)
    raise ValueError(
        f"Unsupported format {fmt!r}. Choose from: {', '.join(SUPPORTED_FORMATS)}"
    )
