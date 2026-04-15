"""Tests for envault.cli_pipeline."""
import json
from pathlib import Path

import pytest

from envault.store import save_vault, load_vault
from envault.cli_pipeline import cmd_pipeline

PASSWORD = "cli-pipeline-pw"


class _Args:
    def __init__(self, vault_dir, environment, password=PASSWORD, steps=None, steps_file=None):
        self.vault_dir = vault_dir
        self.environment = environment
        self.password = password
        self.steps = steps
        self.steps_file = steps_file


@pytest.fixture()
def vault_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def _make_args(vault_dir, env="dev", steps=None, steps_file=None):
    return _Args(vault_dir=vault_dir, environment=env, steps=steps, steps_file=steps_file)


def _seed(vault_dir, env, data):
    save_vault(vault_dir, PASSWORD, {env: data})


def _run_steps(vault_dir, steps, env="dev"):
    """Helper: serialise *steps* to JSON, run cmd_pipeline, return the return code."""
    args = _make_args(vault_dir, env=env, steps=json.dumps(steps))
    return cmd_pipeline(args)


# ---------------------------------------------------------------------------

def test_cmd_pipeline_returns_zero_on_success(vault_dir):
    _seed(vault_dir, "dev", {"K": "v"})
    assert _run_steps(vault_dir, [{"operation": "set", "params": {"key": "NEW", "value": "1"}}]) == 0


def test_cmd_pipeline_applies_set_step(vault_dir):
    _seed(vault_dir, "dev", {})
    _run_steps(vault_dir, [{"operation": "set", "params": {"key": "FOO", "value": "bar"}}])
    vault = load_vault(vault_dir, PASSWORD)
    assert vault["dev"]["FOO"] == "bar"


def test_cmd_pipeline_loads_steps_from_file(vault_dir, tmp_path):
    _seed(vault_dir, "dev", {"X": "old"})
    steps = [{"operation": "set", "params": {"key": "X", "value": "new"}}]
    steps_file = str(tmp_path / "steps.json")
    with open(steps_file, "w") as fh:
        json.dump(steps, fh)
    args = _make_args(vault_dir, steps_file=steps_file)
    rc = cmd_pipeline(args)
    assert rc == 0
    vault = load_vault(vault_dir, PASSWORD)
    assert vault["dev"]["X"] == "new"


def test_cmd_pipeline_missing_steps_returns_one(vault_dir):
    _seed(vault_dir, "dev", {})
    args = _make_args(vault_dir)  # no steps or steps_file
    assert cmd_pipeline(args) == 1


def test_cmd_pipeline_invalid_json_returns_one(vault_dir):
    _seed(vault_dir, "dev", {})
    args = _make_args(vault_dir, steps="not-json")
    assert cmd_pipeline(args) == 1


def test_cmd_pipeline_non_array_steps_returns_one(vault_dir):
    _seed(vault_dir, "dev", {})
    args = _make_args(vault_dir, steps=json.dumps({"operation": "set"}))
    assert cmd_pipeline(args) == 1


def test_cmd_pipeline_step_missing_operation_returns_one(vault_dir):
    _seed(vault_dir, "dev", {})
    assert _run_steps(vault_dir, [{"params": {}}]) == 1


def test_cmd_pipeline_pipeline_error_returns_one(vault_dir):
    _seed(vault_dir, "dev", {})
    # 'set' without a key triggers PipelineError
    assert _run_steps(vault_dir, [{"operation": "set", "params": {"value": "oops"}}]) == 1
