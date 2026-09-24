"""Unit tests for hermes-ouroboros JSON harness config."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.config import load_config
from bench_eval.hermes_config import (
    DEFAULT_HERMES_CONFIG_PATH,
    load_hermes_harness_config,
)


def test_default_json_exists():
    path = Path(_REPO_ROOT) / DEFAULT_HERMES_CONFIG_PATH
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["harness"] == "hermes-ouroboros"
    assert payload["api"]["base_url"] == "http://127.0.0.1:8000"
    assert payload["council"]["analysis_mode"] == "research"


def test_load_hermes_harness_config_from_default():
    config = load_hermes_harness_config(
        str(Path(_REPO_ROOT) / DEFAULT_HERMES_CONFIG_PATH),
        env={},
    )
    assert config.api_base_url == "http://127.0.0.1:8000"
    assert config.analysis_mode == "research"
    assert config.on_api_error == "continue_with_original_task"
    assert "mock e-commerce" in config.planning_prompt_prefix


def test_env_overrides_json(tmp_path):
    custom = tmp_path / "hermes.json"
    custom.write_text(
        json.dumps(
            {
                "api": {"base_url": "http://example:9000", "timeout_seconds": 120},
                "council": {"analysis_mode": "verify"},
            }
        ),
        encoding="utf-8",
    )
    config = load_hermes_harness_config(
        str(custom),
        env={"HERMES_BASE_URL": "http://127.0.0.1:8000", "HERMES_MODE": "red_team"},
    )
    assert config.api_base_url == "http://127.0.0.1:8000"
    assert config.analysis_mode == "red_team"
    assert config.timeout_seconds == 120.0


def test_build_planning_query():
    config = load_hermes_harness_config(
        str(Path(_REPO_ROOT) / DEFAULT_HERMES_CONFIG_PATH),
        env={},
    )
    query = config.build_planning_query("Add item to basket")
    assert "Add item to basket" in query
    assert "browser automation" in query


def test_load_config_uses_default_hermes_json(monkeypatch):
    monkeypatch.delenv("HERMES_BASE_URL", raising=False)
    monkeypatch.delenv("HERMES_MODE", raising=False)
    monkeypatch.setenv("EVAL_DATASET_PATH", "tests/evals/dataset.json")
    config = load_config()
    assert config.hermes_config_path == DEFAULT_HERMES_CONFIG_PATH
    assert config.hermes_base_url == "http://127.0.0.1:8000"
    assert config.hermes_mode == "research"
