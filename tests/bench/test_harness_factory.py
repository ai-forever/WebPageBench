"""Unit tests for agent harness selection."""

from __future__ import annotations

import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.config import EvalConfig, load_config
from bench_eval.harness_factory import (
    available_harnesses,
    get_harness_runner,
    normalize_harness_name,
    run_agent_sync,
)
from bench_eval.harnesses.base import normalize_agent_result


def test_normalize_harness_name_aliases():
    assert normalize_harness_name("browser-use") == "browser-use"
    assert normalize_harness_name("browser_use") == "browser-use"
    assert normalize_harness_name("hermes") == "hermes-ouroboros"
    assert normalize_harness_name("hermes_ouroboros") == "hermes-ouroboros"
    assert normalize_harness_name("deep-agents") == "deepagents"
    assert normalize_harness_name("open-hands") == "openhands"
    assert normalize_harness_name("open-manus") == "openmanus"


def test_normalize_harness_name_rejects_unknown():
    with pytest.raises(ValueError, match="Unsupported AGENT_HARNESS"):
        normalize_harness_name("unknown-harness")


def test_available_harnesses_contains_browser_use_and_hermes():
    names = set(available_harnesses())
    assert "browser-use" in names
    assert "deepagents" in names
    assert "openhands" in names
    assert "openmanus" in names
    assert "hermes-ouroboros" in names
    assert "ouroboros-cut" in names
    assert "ouroboros-full-isolated" in names
    assert "ouroboros-full-evolving" in names


def test_normalize_ouroboros_mode_aliases():
    assert normalize_harness_name("cut") == "ouroboros-cut"
    assert normalize_harness_name("full_isolated") == "ouroboros-full-isolated"
    assert normalize_harness_name("full_evolving") == "ouroboros-full-evolving"
    assert normalize_harness_name("ouroboros_cut") == "ouroboros-cut"


def test_get_harness_runner_selects_adapter():
    from bench_eval.harness_compat import import_harness_runner

    browser_cfg = EvalConfig(agent_harness="browser-use")
    hermes_cfg = EvalConfig(agent_harness="hermes-ouroboros")

    with patch("bench_eval.harness_factory.import_harness_runner", side_effect=import_harness_runner):
        with patch("bench_eval.harness_compat.ensure_harness_ready"):
            assert get_harness_runner(browser_cfg).__name__ == "run_browser_use_harness"
            assert get_harness_runner(hermes_cfg).__name__ == "run_hermes_ouroboros_harness"
            assert get_harness_runner(EvalConfig(agent_harness="deepagents")).__name__ == "run_deepagents_harness"
            assert get_harness_runner(EvalConfig(agent_harness="openhands")).__name__ == "run_openhands_harness"
            assert get_harness_runner(EvalConfig(agent_harness="openmanus")).__name__ == "run_openmanus_harness"
            assert get_harness_runner(EvalConfig(agent_harness="ouroboros-cut")).__name__ == "run_ouroboros_harness"


def test_load_config_reads_agent_harness(monkeypatch):
    monkeypatch.setenv("AGENT_HARNESS", "hermes-ouroboros")
    monkeypatch.setenv("HERMES_MODE", "verify")
    monkeypatch.setenv("HERMES_BASE_URL", "http://localhost:8000")
    monkeypatch.setenv("EVAL_DATASET_PATH", "tests/evals/dataset.json")

    config = load_config()
    assert config.agent_harness == "hermes-ouroboros"
    assert config.hermes_mode == "verify"
    assert config.hermes_base_url == "http://localhost:8000"


def test_run_agent_sync_delegates_to_selected_harness():
    config = EvalConfig(agent_harness="browser-use")
    expected = normalize_agent_result(
        {
            "final_result": "done",
            "steps": 2,
            "is_done": True,
            "duration_seconds": 1.5,
        },
        harness="browser-use",
    )

    with patch(
        "bench_eval.harness_factory.run_agent",
        new=AsyncMock(return_value=expected),
    ) as run_agent_mock:
        result = run_agent_sync("task text", config=config, task_url="http://example")

    run_agent_mock.assert_awaited_once_with(
        "task text",
        config=config,
        task_url="http://example",
        entry_url=None,
        task_key=None,
    )
    assert result["final_result"] == "done"
    assert result["harness"] == "browser-use"
