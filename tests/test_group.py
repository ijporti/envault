"""Tests for envault.group."""

from __future__ import annotations

import json
import pytest

from envault.store import save_vault
from envault.group import (
    GroupError,
    add_to_group,
    remove_from_group,
    list_groups,
    get_group_keys,
    _group_path,
)

PASSWORD = "test-password"


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _seed(vault_dir, env="dev", data=None):
    if data is None:
        data = {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "abc123"}
    save_vault(vault_dir, env, data, PASSWORD)


# --- add_to_group ---

def test_add_to_group_returns_sorted_keys(vault_dir):
    _seed(vault_dir)
    result = add_to_group(vault_dir, "dev", "database", ["DB_HOST", "DB_PORT"], PASSWORD)
    assert result == ["DB_HOST", "DB_PORT"]


def test_add_to_group_creates_registry_file(vault_dir):
    _seed(vault_dir)
    add_to_group(vault_dir, "dev", "database", ["DB_HOST"], PASSWORD)
    assert _group_path(vault_dir).exists()


def test_add_to_group_merges_with_existing(vault_dir):
    _seed(vault_dir)
    add_to_group(vault_dir, "dev", "database", ["DB_HOST"], PASSWORD)
    result = add_to_group(vault_dir, "dev", "database", ["DB_PORT"], PASSWORD)
    assert "DB_HOST" in result
    assert "DB_PORT" in result


def test_add_to_group_deduplicates(vault_dir):
    _seed(vault_dir)
    add_to_group(vault_dir, "dev", "database", ["DB_HOST"], PASSWORD)
    result = add_to_group(vault_dir, "dev", "database", ["DB_HOST"], PASSWORD)
    assert result.count("DB_HOST") == 1


def test_add_to_group_missing_key_raises(vault_dir):
    _seed(vault_dir)
    with pytest.raises(GroupError, match="Keys not found"):
        add_to_group(vault_dir, "dev", "database", ["NONEXISTENT"], PASSWORD)


# --- remove_from_group ---

def test_remove_from_group_returns_remaining(vault_dir):
    _seed(vault_dir)
    add_to_group(vault_dir, "dev", "database", ["DB_HOST", "DB_PORT"], PASSWORD)
    result = remove_from_group(vault_dir, "dev", "database", ["DB_PORT"])
    assert result == ["DB_HOST"]


def test_remove_from_group_nonexistent_group_raises(vault_dir):
    _seed(vault_dir)
    with pytest.raises(GroupError, match="not found"):
        remove_from_group(vault_dir, "dev", "missing_group", ["DB_HOST"])


# --- list_groups ---

def test_list_groups_returns_all_groups(vault_dir):
    _seed(vault_dir)
    add_to_group(vault_dir, "dev", "database", ["DB_HOST"], PASSWORD)
    add_to_group(vault_dir, "dev", "api", ["API_KEY"], PASSWORD)
    groups = list_groups(vault_dir)
    assert "dev:database" in groups
    assert "dev:api" in groups


def test_list_groups_filters_by_environment(vault_dir):
    _seed(vault_dir)
    _seed(vault_dir, env="prod", data={"DB_HOST": "prod-host"})
    add_to_group(vault_dir, "dev", "database", ["DB_HOST"], PASSWORD)
    add_to_group(vault_dir, "prod", "database", ["DB_HOST"], PASSWORD)
    groups = list_groups(vault_dir, environment="dev")
    assert all(k.startswith("dev:") for k in groups)


def test_list_groups_empty_when_no_file(vault_dir):
    result = list_groups(vault_dir)
    assert result == {}


# --- get_group_keys ---

def test_get_group_keys_returns_keys(vault_dir):
    _seed(vault_dir)
    add_to_group(vault_dir, "dev", "database", ["DB_HOST", "DB_PORT"], PASSWORD)
    keys = get_group_keys(vault_dir, "dev", "database")
    assert set(keys) == {"DB_HOST", "DB_PORT"}


def test_get_group_keys_nonexistent_raises(vault_dir):
    _seed(vault_dir)
    with pytest.raises(GroupError, match="not found"):
        get_group_keys(vault_dir, "dev", "ghost")
