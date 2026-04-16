"""Tests for envault.notify."""
import pytest
from envault.notify import (
    add_channel, remove_channel, list_channels, NotifyError, NotifyChannel
)


@pytest.fixture
def vault_dir(tmp_path):
    return str(tmp_path)


def test_add_channel_returns_notify_channel(vault_dir):
    ch = add_channel(vault_dir, "ops-slack", "slack", "https://hooks.slack.com/xxx")
    assert isinstance(ch, NotifyChannel)


def test_add_channel_persists(vault_dir):
    add_channel(vault_dir, "ops-slack", "slack", "https://hooks.slack.com/xxx")
    channels = list_channels(vault_dir)
    assert any(c.name == "ops-slack" for c in channels)


def test_add_channel_invalid_type_raises(vault_dir):
    with pytest.raises(NotifyError, match="Invalid channel type"):
        add_channel(vault_dir, "bad", "sms", "555-1234")


def test_add_channel_invalid_event_raises(vault_dir):
    with pytest.raises(NotifyError, match="Invalid events"):
        add_channel(vault_dir, "ch", "email", "a@b.com", events=["explode"])


def test_add_channel_duplicate_name_raises(vault_dir):
    add_channel(vault_dir, "ch", "email", "a@b.com")
    with pytest.raises(NotifyError, match="already exists"):
        add_channel(vault_dir, "ch", "slack", "https://x")


def test_add_channel_custom_events(vault_dir):
    ch = add_channel(vault_dir, "ch", "webhook", "https://x", events=["set", "delete"])
    assert ch.events == ["delete", "set"]


def test_add_channel_default_events_are_all(vault_dir):
    from envault.notify import VALID_EVENTS
    ch = add_channel(vault_dir, "ch", "email", "a@b.com")
    assert set(ch.events) == VALID_EVENTS


def test_remove_channel_returns_true(vault_dir):
    add_channel(vault_dir, "ch", "email", "a@b.com")
    assert remove_channel(vault_dir, "ch") is True


def test_remove_channel_removes_from_list(vault_dir):
    add_channel(vault_dir, "ch", "email", "a@b.com")
    remove_channel(vault_dir, "ch")
    assert not any(c.name == "ch" for c in list_channels(vault_dir))


def test_remove_channel_missing_returns_false(vault_dir):
    assert remove_channel(vault_dir, "ghost") is False


def test_list_channels_empty_before_add(vault_dir):
    assert list_channels(vault_dir) == []


def test_list_channels_multiple(vault_dir):
    add_channel(vault_dir, "a", "email", "a@b.com")
    add_channel(vault_dir, "b", "slack", "https://x")
    assert len(list_channels(vault_dir)) == 2
