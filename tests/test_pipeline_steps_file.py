"""Integration-style tests for pipeline steps loaded from a JSON file."""
import json
from pathlib import Path

import pytest

from envault.store import save_vault, load_vault
from envault.pipeline import PipelineStep, run_pipeline

PASSWORD = "steps-file-pw"


@pytest.fixture()
def vault_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def _seed(vault_dir, env, data):
    save_vault(vault_dir, PASSWORD, {env: data})


def _steps_from_file(tmp_path, raw):
    """Write raw list of step dicts to a temp JSON file, return PipelineStep list."""
    p = tmp_path / "pipeline.json"
    p.write_text(json.dumps(raw))
    with open(p) as fh:
        items = json.load(fh)
    return [PipelineStep(operation=i["operation"], params=i.get("params", {})) for i in items]


def test_pipeline_file_set_and_transform(vault_dir, tmp_path):
    _seed(vault_dir, "staging", {"DB_HOST": "localhost"})
    steps = _steps_from_file(tmp_path, [
        {"operation": "set", "params": {"key": "APP_ENV", "value": "staging"}},
        {"operation": "transform", "params": {"key": "APP_ENV", "func": "upper"}},
    ])
    result = run_pipeline(vault_dir, "staging", PASSWORD, steps)
    assert result.steps_applied == 2
    vault = load_vault(vault_dir, PASSWORD)
    assert vault["staging"]["APP_ENV"] == "STAGING"


def test_pipeline_file_rename_then_delete(vault_dir, tmp_path):
    _seed(vault_dir, "prod", {"OLD_KEY": "secret", "TEMP": "x"})
    steps = _steps_from_file(tmp_path, [
        {"operation": "rename", "params": {"src": "OLD_KEY", "dst": "NEW_KEY"}},
        {"operation": "delete", "params": {"key": "TEMP"}},
    ])
    result = run_pipeline(vault_dir, "prod", PASSWORD, steps)
    assert result.steps_applied == 2
    vault = load_vault(vault_dir, PASSWORD)
    assert vault["prod"]["NEW_KEY"] == "secret"
    assert "OLD_KEY" not in vault["prod"]
    assert "TEMP" not in vault["prod"]


def test_pipeline_file_empty_steps_returns_zero_applied(vault_dir, tmp_path):
    _seed(vault_dir, "dev", {"A": "1"})
    steps = _steps_from_file(tmp_path, [])
    result = run_pipeline(vault_dir, "dev", PASSWORD, steps)
    assert result.steps_applied == 0
    assert result.steps_skipped == 0


def test_pipeline_file_changes_list_populated(vault_dir, tmp_path):
    _seed(vault_dir, "dev", {"K": "v"})
    steps = _steps_from_file(tmp_path, [
        {"operation": "set", "params": {"key": "M", "value": "n"}},
        {"operation": "delete", "params": {"key": "K"}},
    ])
    result = run_pipeline(vault_dir, "dev", PASSWORD, steps)
    assert len(result.changes) == 2
    assert any("set M" in c for c in result.changes)
    assert any("deleted K" in c for c in result.changes)


def test_pipeline_file_skipped_keys_not_in_changes(vault_dir, tmp_path):
    _seed(vault_dir, "dev", {})
    steps = _steps_from_file(tmp_path, [
        {"operation": "delete", "params": {"key": "NONEXISTENT"}},
    ])
    result = run_pipeline(vault_dir, "dev", PASSWORD, steps)
    assert result.steps_skipped == 1
    assert result.changes == []
