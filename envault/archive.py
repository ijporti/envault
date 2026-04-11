"""Archive and restore entire vault environments."""
from __future__ import annotations

import json
import zipfile
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from envault.store import _vault_path, load_vault, save_vault


class ArchiveError(Exception):
    """Raised when an archive operation fails."""


@dataclass
class ArchiveManifest:
    created_at: str
    environments: List[str]
    envault_version: str = "1.0"

    def to_dict(self) -> dict:
        return {
            "created_at": self.created_at,
            "environments": self.environments,
            "envault_version": self.envault_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ArchiveManifest":
        return cls(
            created_at=data["created_at"],
            environments=data["environments"],
            envault_version=data.get("envault_version", "1.0"),
        )


def create_archive(vault_dir: Path, password: str, environments: List[str], dest: Path) -> ArchiveManifest:
    """Archive one or more encrypted environments into a zip file."""
    if not environments:
        raise ArchiveError("No environments specified for archiving.")

    archived = []
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for env in environments:
            vault_file = _vault_path(vault_dir, env)
            if not vault_file.exists():
                raise ArchiveError(f"Environment '{env}' does not exist.")
            # Validate password by loading
            load_vault(vault_dir, env, password)
            zf.write(vault_file, arcname=f"{env}.json")
            archived.append(env)

        manifest = ArchiveManifest(
            created_at=datetime.now(timezone.utc).isoformat(),
            environments=archived,
        )
        zf.writestr("manifest.json", json.dumps(manifest.to_dict(), indent=2))

    return manifest


def restore_archive(vault_dir: Path, password: str, src: Path, overwrite: bool = False) -> ArchiveManifest:
    """Restore environments from a zip archive."""
    if not src.exists():
        raise ArchiveError(f"Archive file not found: {src}")

    with zipfile.ZipFile(src, "r") as zf:
        names = zf.namelist()
        if "manifest.json" not in names:
            raise ArchiveError("Archive is missing manifest.json — may be corrupt.")

        manifest = ArchiveManifest.from_dict(json.loads(zf.read("manifest.json")))

        for env in manifest.environments:
            dest_file = _vault_path(vault_dir, env)
            if dest_file.exists() and not overwrite:
                raise ArchiveError(
                    f"Environment '{env}' already exists. Use overwrite=True to replace it."
                )
            vault_dir.mkdir(parents=True, exist_ok=True)
            dest_file.write_bytes(zf.read(f"{env}.json"))
            # Validate restored file is readable with given password
            load_vault(vault_dir, env, password)

    return manifest
