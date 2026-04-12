"""Tests for envault.watch."""

from __future__ import annotations

import pytest

from envault.store import save_vault, load_vault
from envault.watch import (
    WatchError,
    WatchEvent,
    _snapshot,
    _diff_snapshots,
    watch_env,
)

PASSWORD = "watchpass"


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _seed(vault_dir, env, data):
    save_vault(vault_dir, env, data, PASSWORD)


# --- WatchEvent ---

def test_watch_event_has_changes_true():
    ev = WatchEvent(environment="dev", added={"A": "1"})
    assert ev.has_changes is True


def test_watch_event_has_changes_false():
    ev = WatchEvent(environment="dev")
    assert ev.has_changes is False


def test_watch_event_summary_no_changes():
    ev = WatchEvent(environment="dev")
    assert ev.summary() == "no changes"


def test_watch_event_summary_all_kinds():
    ev = WatchEvent(
        environment="dev",
        added={"X": "1"},
        removed={"Y": "2"},
        changed={"Z": ("old", "new")},
    )
    summary = ev.summary()
    assert "+1 added" in summary
    assert "-1 removed" in summary
    assert "~1 changed" in summary


# --- _snapshot ---

def test_snapshot_returns_dict(vault_dir):
    _seed(vault_dir, "dev", {"FOO": "bar"})
    snap = _snapshot(vault_dir, "dev", PASSWORD)
    assert snap == {"FOO": "bar"}


def test_snapshot_missing_env_raises(vault_dir):
    with pytest.raises(WatchError, match="not found"):
        _snapshot(vault_dir, "ghost", PASSWORD)


# --- _diff_snapshots ---

def test_diff_detects_added():
    ev = _diff_snapshots("dev", {"A": "1"}, {"A": "1", "B": "2"})
    assert "B" in ev.added
    assert not ev.removed
    assert not ev.changed


def test_diff_detects_removed():
    ev = _diff_snapshots("dev", {"A": "1", "B": "2"}, {"A": "1"})
    assert "B" in ev.removed


def test_diff_detects_changed():
    ev = _diff_snapshots("dev", {"A": "old"}, {"A": "new"})
    assert "A" in ev.changed
    assert ev.changed["A"] == ("old", "new")


def test_diff_no_changes():
    ev = _diff_snapshots("dev", {"A": "1"}, {"A": "1"})
    assert not ev.has_changes


# --- watch_env ---

def test_watch_env_invalid_interval_raises(vault_dir):
    _seed(vault_dir, "dev", {})
    with pytest.raises(WatchError, match="interval"):
        watch_env(vault_dir, "dev", PASSWORD, callback=lambda e: None, interval=0)


def test_watch_env_detects_change(vault_dir):
    _seed(vault_dir, "dev", {"FOO": "bar"})
    events = []

    poll = 0

    def fake_sleep(secs):
        nonlocal poll
        poll += 1
        if poll == 1:
            _seed(vault_dir, "dev", {"FOO": "baz"})

    import envault.watch as watch_mod
    original_sleep = watch_mod.time.sleep
    watch_mod.time.sleep = fake_sleep
    try:
        count = watch_env(
            vault_dir, "dev", PASSWORD,
            callback=events.append,
            interval=0.001,
            max_polls=2,
        )
    finally:
        watch_mod.time.sleep = original_sleep

    assert count == 1
    assert len(events) == 1
    assert "FOO" in events[0].changed


def test_watch_env_no_change_emits_no_events(vault_dir):
    _seed(vault_dir, "dev", {"FOO": "bar"})
    events = []

    import envault.watch as watch_mod
    watch_mod.time.sleep = lambda s: None

    count = watch_env(
        vault_dir, "dev", PASSWORD,
        callback=events.append,
        interval=0.001,
        max_polls=3,
    )
    watch_mod.time.sleep = __import__("time").sleep

    assert count == 0
    assert events == []
