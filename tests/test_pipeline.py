"""Tests for envault.pipeline."""
import pytest
from pathlib import Path

from envault.store import save_vault, load_vault
from envault.pipeline import (
    PipelineStep,
    PipelineResult,
    PipelineError,
    run_pipeline,
)

PASSWORD = "test-pipeline-pw"


@pytest.fixture()
def vault_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def _seed(vault_dir: str, env: str, data: dict) -> None:
    vault = {env: data}
    save_vault(vault_dir, PASSWORD, vault)


# ---------------------------------------------------------------------------
# PipelineResult helpers
# ---------------------------------------------------------------------------

def test_pipeline_result_total_steps():
    r = PipelineResult(environment="dev", steps_applied=3, steps_skipped=1)
    assert r.total_steps == 4


def test_pipeline_result_total_steps_zero():
    r = PipelineResult(environment="dev", steps_applied=0, steps_skipped=0)
    assert r.total_steps == 0


# ---------------------------------------------------------------------------
# run_pipeline – set
# ---------------------------------------------------------------------------

def test_run_pipeline_set_adds_key(vault_dir):
    _seed(vault_dir, "dev", {})
    steps = [PipelineStep(operation="set", params={"key": "FOO", "value": "bar"})]
    result = run_pipeline(vault_dir, "dev", PASSWORD, steps)
    assert result.steps_applied == 1
    vault = load_vault(vault_dir, PASSWORD)
    assert vault["dev"]["FOO"] == "bar"


def test_run_pipeline_returns_pipeline_result(vault_dir):
    _seed(vault_dir, "dev", {"A": "1"})
    steps = [PipelineStep(operation="set", params={"key": "B", "value": "2"})]
    result = run_pipeline(vault_dir, "dev", PASSWORD, steps)
    assert isinstance(result, PipelineResult)
    assert result.environment == "dev"


# ---------------------------------------------------------------------------
# run_pipeline – delete
# ---------------------------------------------------------------------------

def test_run_pipeline_delete_removes_key(vault_dir):
    _seed(vault_dir, "dev", {"X": "val"})
    steps = [PipelineStep(operation="delete", params={"key": "X"})]
    result = run_pipeline(vault_dir, "dev", PASSWORD, steps)
    assert result.steps_applied == 1
    vault = load_vault(vault_dir, PASSWORD)
    assert "X" not in vault["dev"]


def test_run_pipeline_delete_missing_key_counts_as_skipped(vault_dir):
    _seed(vault_dir, "dev", {})
    steps = [PipelineStep(operation="delete", params={"key": "MISSING"})]
    result = run_pipeline(vault_dir, "dev", PASSWORD, steps)
    assert result.steps_skipped == 1
    assert result.steps_applied == 0


# ---------------------------------------------------------------------------
# run_pipeline – rename
# ---------------------------------------------------------------------------

def test_run_pipeline_rename_key(vault_dir):
    _seed(vault_dir, "dev", {"OLD": "hello"})
    steps = [PipelineStep(operation="rename", params={"src": "OLD", "dst": "NEW"})]
    result = run_pipeline(vault_dir, "dev", PASSWORD, steps)
    assert result.steps_applied == 1
    vault = load_vault(vault_dir, PASSWORD)
    assert "OLD" not in vault["dev"]
    assert vault["dev"]["NEW"] == "hello"


def test_run_pipeline_rename_missing_src_counts_as_skipped(vault_dir):
    _seed(vault_dir, "dev", {})
    steps = [PipelineStep(operation="rename", params={"src": "GHOST", "dst": "NEW"})]
    result = run_pipeline(vault_dir, "dev", PASSWORD, steps)
    assert result.steps_skipped == 1
    assert result.steps_applied == 0


# ---------------------------------------------------------------------------
# run_pipeline – unknown operation
# ---------------------------------------------------------------------------

def test_run_pipeline_unknown_operation_raises(vault_dir):
    _seed(vault_dir, "dev", {})
    steps = [PipelineStep(operation="explode", params={})]
    with pytest.raises(PipelineError):
        run_pipeline(vault_dir, "dev", PASSWORD, steps)
