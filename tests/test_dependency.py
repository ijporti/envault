"""Tests for envault.dependency."""
import pytest
from pathlib import Path

from envault.store import save_vault
from envault.dependency import (
    add_dependency,
    remove_dependency,
    get_dependencies,
    get_dependents,
    dependency_order,
    DependencyError,
    _dep_path,
)

PASSWORD = "test-secret"


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


def _seed(vault_dir: Path, environment: str, secrets: dict) -> None:
    save_vault(vault_dir, environment, secrets, PASSWORD)


def test_add_dependency_returns_list(vault_dir):
    _seed(vault_dir, "dev", {"DB_URL": "postgres://", "DB_PASS": "s3cr3t"})
    result = add_dependency(vault_dir, "dev", "DB_URL", "DB_PASS", PASSWORD)
    assert isinstance(result, list)
    assert "DB_PASS" in result


def test_add_dependency_creates_file(vault_dir):
    _seed(vault_dir, "dev", {"A": "1", "B": "2"})
    add_dependency(vault_dir, "dev", "A", "B", PASSWORD)
    assert _dep_path(vault_dir, "dev").exists()


def test_add_dependency_deduplicates(vault_dir):
    _seed(vault_dir, "dev", {"A": "1", "B": "2"})
    add_dependency(vault_dir, "dev", "A", "B", PASSWORD)
    result = add_dependency(vault_dir, "dev", "A", "B", PASSWORD)
    assert result.count("B") == 1


def test_add_dependency_missing_key_raises(vault_dir):
    _seed(vault_dir, "dev", {"A": "1"})
    with pytest.raises(DependencyError, match="'GHOST'"):
        add_dependency(vault_dir, "dev", "GHOST", "A", PASSWORD)


def test_add_dependency_missing_dep_raises(vault_dir):
    _seed(vault_dir, "dev", {"A": "1"})
    with pytest.raises(DependencyError, match="'GHOST'"):
        add_dependency(vault_dir, "dev", "A", "GHOST", PASSWORD)


def test_add_dependency_self_raises(vault_dir):
    _seed(vault_dir, "dev", {"A": "1"})
    with pytest.raises(DependencyError, match="itself"):
        add_dependency(vault_dir, "dev", "A", "A", PASSWORD)


def test_remove_dependency(vault_dir):
    _seed(vault_dir, "dev", {"A": "1", "B": "2"})
    add_dependency(vault_dir, "dev", "A", "B", PASSWORD)
    remaining = remove_dependency(vault_dir, "dev", "A", "B")
    assert "B" not in remaining
    assert get_dependencies(vault_dir, "dev", "A") == []


def test_remove_nonexistent_dependency_is_noop(vault_dir):
    _seed(vault_dir, "dev", {"A": "1", "B": "2"})
    result = remove_dependency(vault_dir, "dev", "A", "B")
    assert result == []


def test_get_dependents(vault_dir):
    _seed(vault_dir, "dev", {"A": "1", "B": "2", "C": "3"})
    add_dependency(vault_dir, "dev", "B", "A", PASSWORD)
    add_dependency(vault_dir, "dev", "C", "A", PASSWORD)
    dependents = get_dependents(vault_dir, "dev", "A")
    assert set(dependents) == {"B", "C"}


def test_dependency_order_simple(vault_dir):
    _seed(vault_dir, "dev", {"A": "1", "B": "2", "C": "3"})
    add_dependency(vault_dir, "dev", "B", "A", PASSWORD)
    add_dependency(vault_dir, "dev", "C", "B", PASSWORD)
    order = dependency_order(vault_dir, "dev")
    assert order.index("A") < order.index("B")
    assert order.index("B") < order.index("C")


def test_dependency_order_no_deps_returns_all_keys(vault_dir):
    _seed(vault_dir, "dev", {"X": "1", "Y": "2"})
    order = dependency_order(vault_dir, "dev")
    assert set(order) == set()  # no deps recorded yet, graph is empty
