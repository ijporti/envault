"""Tests for envault.search."""

import os
import pytest

from envault.store import save_vault
from envault.search import SearchResult, search_keys, search_values


PASSWORD = "test-password"


@pytest.fixture()
def vault_dir(tmp_path):
    secrets = {
        "production": {
            "DATABASE_URL": "postgres://prod/db",
            "SECRET_KEY": "supersecret",
            "API_KEY": "prod-api-key",
        },
        "staging": {
            "DATABASE_URL": "postgres://staging/db",
            "DEBUG": "true",
            "API_KEY": "staging-api-key",
        },
        "development": {
            "DEBUG": "true",
            "LOCAL_PATH": "/home/dev/app",
        },
    }
    save_vault(str(tmp_path), PASSWORD, secrets)
    return str(tmp_path)


# --- search_keys ---

def test_search_keys_returns_list(vault_dir):
    results = search_keys(vault_dir, PASSWORD, "KEY")
    assert isinstance(results, list)
    assert all(isinstance(r, SearchResult) for r in results)


def test_search_keys_finds_across_environments(vault_dir):
    results = search_keys(vault_dir, PASSWORD, "API_KEY")
    envs = {r.environment for r in results}
    assert "production" in envs
    assert "staging" in envs


def test_search_keys_case_insensitive_by_default(vault_dir):
    results = search_keys(vault_dir, PASSWORD, "api_key")
    assert len(results) >= 2


def test_search_keys_case_sensitive_no_match(vault_dir):
    results = search_keys(vault_dir, PASSWORD, "api_key", case_sensitive=True)
    assert results == []


def test_search_keys_restricted_to_environment(vault_dir):
    results = search_keys(vault_dir, PASSWORD, "DEBUG", environment="development")
    assert all(r.environment == "development" for r in results)
    assert len(results) == 1


def test_search_keys_no_match_returns_empty(vault_dir):
    results = search_keys(vault_dir, PASSWORD, "NONEXISTENT_XYZ")
    assert results == []


def test_search_keys_sorted(vault_dir):
    results = search_keys(vault_dir, PASSWORD, "KEY")
    pairs = [(r.environment, r.key) for r in results]
    assert pairs == sorted(pairs)


# --- search_values ---

def test_search_values_finds_matching(vault_dir):
    results = search_values(vault_dir, PASSWORD, "postgres")
    assert len(results) == 2
    keys = {r.key for r in results}
    assert keys == {"DATABASE_URL"}


def test_search_values_case_insensitive(vault_dir):
    results = search_values(vault_dir, PASSWORD, "TRUE")
    assert len(results) >= 1


def test_search_values_restricted_to_environment(vault_dir):
    results = search_values(vault_dir, PASSWORD, "postgres", environment="production")
    assert len(results) == 1
    assert results[0].environment == "production"


def test_search_result_str(vault_dir):
    results = search_keys(vault_dir, PASSWORD, "SECRET_KEY")
    assert len(results) == 1
    text = str(results[0])
    assert "SECRET_KEY" in text
    assert "production" in text
