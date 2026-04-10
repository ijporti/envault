"""Vault store: read/write encrypted .env vault files."""

import json
import os
from pathlib import Path
from typing import Dict, Optional

from envault.crypto import encrypt, decrypt

DEFAULT_VAULT_DIR = Path(".envault")
VAULT_FILE_SUFFIX = ".vault"


def _vault_path(vault_dir: Path, environment: str) -> Path:
    return vault_dir / f"{environment}{VAULT_FILE_SUFFIX}"


def save_vault(
    secrets: Dict[str, str],
    password: str,
    environment: str = "default",
    vault_dir: Optional[Path] = None,
) -> Path:
    """Encrypt *secrets* and persist them to a vault file.

    Returns the path of the written file.
    """
    vault_dir = Path(vault_dir) if vault_dir else DEFAULT_VAULT_DIR
    vault_dir.mkdir(parents=True, exist_ok=True)

    plaintext = json.dumps(secrets)
    token = encrypt(plaintext, password)

    path = _vault_path(vault_dir, environment)
    path.write_text(token)
    return path


def load_vault(
    password: str,
    environment: str = "default",
    vault_dir: Optional[Path] = None,
) -> Dict[str, str]:
    """Decrypt and return secrets from a vault file.

    Raises FileNotFoundError if the vault does not exist.
    Raises ValueError (from crypto.decrypt) on wrong password / corruption.
    """
    vault_dir = Path(vault_dir) if vault_dir else DEFAULT_VAULT_DIR
    path = _vault_path(vault_dir, environment)

    if not path.exists():
        raise FileNotFoundError(f"Vault not found: {path}")

    token = path.read_text().strip()
    plaintext = decrypt(token, password)
    return json.loads(plaintext)


def list_environments(vault_dir: Optional[Path] = None) -> list[str]:
    """Return the names of all environments stored in *vault_dir*."""
    vault_dir = Path(vault_dir) if vault_dir else DEFAULT_VAULT_DIR
    if not vault_dir.exists():
        return []
    return [
        p.stem
        for p in sorted(vault_dir.glob(f"*{VAULT_FILE_SUFFIX}"))
    ]
