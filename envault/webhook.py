"""Webhook notification support for envault events."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class WebhookError(Exception):
    """Raised when a webhook operation fails."""


@dataclass
class WebhookResult:
    url: str
    status_code: int
    ok: bool
    error: Optional[str] = None

    def __str__(self) -> str:
        if self.ok:
            return f"Webhook delivered to {self.url} [{self.status_code}]"
        return f"Webhook failed for {self.url}: {self.error}"


def _webhook_path(vault_dir: Path) -> Path:
    return vault_dir / ".webhooks.json"


def _load_webhooks(vault_dir: Path) -> List[str]:
    p = _webhook_path(vault_dir)
    if not p.exists():
        return []
    return json.loads(p.read_text())


def _save_webhooks(vault_dir: Path, urls: List[str]) -> None:
    _webhook_path(vault_dir).write_text(json.dumps(sorted(set(urls)), indent=2))


def register_webhook(vault_dir: Path, url: str) -> List[str]:
    """Add a webhook URL. Returns the updated list of URLs."""
    if not url.startswith(("http://", "https://")):
        raise WebhookError(f"Invalid URL scheme: {url!r}")
    urls = _load_webhooks(vault_dir)
    if url not in urls:
        urls.append(url)
    _save_webhooks(vault_dir, urls)
    return sorted(set(urls))


def remove_webhook(vault_dir: Path, url: str) -> bool:
    """Remove a webhook URL. Returns True if it was present."""
    urls = _load_webhooks(vault_dir)
    if url not in urls:
        return False
    urls.remove(url)
    _save_webhooks(vault_dir, urls)
    return True


def list_webhooks(vault_dir: Path) -> List[str]:
    return _load_webhooks(vault_dir)


def fire_webhooks(
    vault_dir: Path,
    event: str,
    payload: dict,
    timeout: int = 5,
) -> List[WebhookResult]:
    """POST a JSON payload to every registered webhook URL."""
    urls = _load_webhooks(vault_dir)
    body = json.dumps({"event": event, **payload}).encode()
    results: List[WebhookResult] = []
    for url in urls:
        try:
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                results.append(WebhookResult(url=url, status_code=resp.status, ok=True))
        except urllib.error.HTTPError as exc:
            results.append(WebhookResult(url=url, status_code=exc.code, ok=False, error=str(exc)))
        except Exception as exc:  # noqa: BLE001
            results.append(WebhookResult(url=url, status_code=0, ok=False, error=str(exc)))
    return results
