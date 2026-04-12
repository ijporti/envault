"""Tests for envault.namespace."""
import pytest

from envault.namespace import (
    NamespaceError,
    NamespaceResult,
    delete_namespace,
    get_namespace_values,
    list_namespace_keys,
    set_namespace_key,
)
from envault.store import save_vault

PASSWORD = "test-pass"


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


def _seed(vault_dir, env, data):
    save_vault(vault_dir, env, data, PASSWORD)


# ---------------------------------------------------------------------------
# set_namespace_key
# ---------------------------------------------------------------------------

def test_set_namespace_key_returns_full_key(vault_dir):
    full_key = set_namespace_key(vault_dir, "dev", "db", "HOST", "localhost", PASSWORD)
    assert full_key == "db.HOST"


def test_set_namespace_key_persists_value(vault_dir):
    set_namespace_key(vault_dir, "dev", "db", "PORT", "5432", PASSWORD)
    values = get_namespace_values(vault_dir, "dev", "db", PASSWORD)
    assert values["db.PORT"] == "5432"


def test_set_namespace_key_empty_namespace_raises(vault_dir):
    with pytest.raises(NamespaceError):
        set_namespace_key(vault_dir, "dev", "", "KEY", "val", PASSWORD)


# ---------------------------------------------------------------------------
# list_namespace_keys
# ---------------------------------------------------------------------------

def test_list_namespace_keys_returns_namespace_result(vault_dir):
    _seed(vault_dir, "dev", {"app.DEBUG": "true", "app.PORT": "8000", "OTHER": "x"})
    result = list_namespace_keys(vault_dir, "dev", "app", PASSWORD)
    assert isinstance(result, NamespaceResult)


def test_list_namespace_keys_filters_by_prefix(vault_dir):
    _seed(vault_dir, "dev", {"app.DEBUG": "true", "app.PORT": "8000", "db.HOST": "localhost"})
    result = list_namespace_keys(vault_dir, "dev", "app", PASSWORD)
    assert result.keys == ["app.DEBUG", "app.PORT"]


def test_list_namespace_keys_total_keys(vault_dir):
    _seed(vault_dir, "dev", {"ns.A": "1", "ns.B": "2", "ns.C": "3"})
    result = list_namespace_keys(vault_dir, "dev", "ns", PASSWORD)
    assert result.total_keys == 3


def test_list_namespace_keys_empty_when_no_match(vault_dir):
    _seed(vault_dir, "dev", {"other.KEY": "val"})
    result = list_namespace_keys(vault_dir, "dev", "app", PASSWORD)
    assert result.keys == []


# ---------------------------------------------------------------------------
# get_namespace_values
# ---------------------------------------------------------------------------

def test_get_namespace_values_returns_dict(vault_dir):
    _seed(vault_dir, "prod", {"cfg.A": "alpha", "cfg.B": "beta", "noise": "x"})
    values = get_namespace_values(vault_dir, "prod", "cfg", PASSWORD)
    assert values == {"cfg.A": "alpha", "cfg.B": "beta"}


# ---------------------------------------------------------------------------
# delete_namespace
# ---------------------------------------------------------------------------

def test_delete_namespace_returns_namespace_result(vault_dir):
    _seed(vault_dir, "dev", {"tmp.X": "1", "tmp.Y": "2"})
    result = delete_namespace(vault_dir, "dev", "tmp", PASSWORD)
    assert isinstance(result, NamespaceResult)
    assert result.total_keys == 2


def test_delete_namespace_removes_keys(vault_dir):
    _seed(vault_dir, "dev", {"rm.A": "1", "rm.B": "2", "keep.C": "3"})
    delete_namespace(vault_dir, "dev", "rm", PASSWORD)
    remaining = get_namespace_values(vault_dir, "dev", "rm", PASSWORD)
    assert remaining == {}


def test_delete_namespace_preserves_other_keys(vault_dir):
    _seed(vault_dir, "dev", {"rm.A": "1", "keep.B": "2"})
    delete_namespace(vault_dir, "dev", "rm", PASSWORD)
    values = get_namespace_values(vault_dir, "dev", "keep", PASSWORD)
    assert values == {"keep.B": "2"}


def test_delete_namespace_no_keys_raises(vault_dir):
    _seed(vault_dir, "dev", {"other.KEY": "val"})
    with pytest.raises(NamespaceError):
        delete_namespace(vault_dir, "dev", "missing", PASSWORD)
