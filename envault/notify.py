"""Notification channel registry for envault events."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class NotifyError(Exception):
    pass


@dataclass
class NotifyChannel:
    name: str
    channel_type: str  # 'email' | 'slack' | 'webhook'
    target: str
    events: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "channel_type": self.channel_type,
            "target": self.target,
            "events": self.events,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "NotifyChannel":
        return cls(
            name=d["name"],
            channel_type=d["channel_type"],
            target=d["target"],
            events=d.get("events", []),
        )


VALID_TYPES = {"email", "slack", "webhook"}
VALID_EVENTS = {"set", "delete", "rotate", "lock", "unlock", "expire"}


def _notify_path(vault_dir: str) -> Path:
    return Path(vault_dir) / ".notify_channels.json"


def _load_channels(vault_dir: str) -> List[NotifyChannel]:
    p = _notify_path(vault_dir)
    if not p.exists():
        return []
    return [NotifyChannel.from_dict(d) for d in json.loads(p.read_text())]


def _save_channels(vault_dir: str, channels: List[NotifyChannel]) -> None:
    _notify_path(vault_dir).write_text(json.dumps([c.to_dict() for c in channels], indent=2))


def add_channel(vault_dir: str, name: str, channel_type: str, target: str, events: Optional[List[str]] = None) -> NotifyChannel:
    if channel_type not in VALID_TYPES:
        raise NotifyError(f"Invalid channel type '{channel_type}'. Choose from: {sorted(VALID_TYPES)}")
    events = events or list(VALID_EVENTS)
    invalid = set(events) - VALID_EVENTS
    if invalid:
        raise NotifyError(f"Invalid events: {sorted(invalid)}")
    channels = _load_channels(vault_dir)
    if any(c.name == name for c in channels):
        raise NotifyError(f"Channel '{name}' already exists.")
    ch = NotifyChannel(name=name, channel_type=channel_type, target=target, events=sorted(events))
    channels.append(ch)
    _save_channels(vault_dir, channels)
    return ch


def remove_channel(vault_dir: str, name: str) -> bool:
    channels = _load_channels(vault_dir)
    new = [c for c in channels if c.name != name]
    if len(new) == len(channels):
        return False
    _save_channels(vault_dir, new)
    return True


def list_channels(vault_dir: str) -> List[NotifyChannel]:
    return _load_channels(vault_dir)
