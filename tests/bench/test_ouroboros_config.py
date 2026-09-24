"""Unit tests for ouroboros harness mode configuration."""

from __future__ import annotations

import json
import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.config import EvalConfig, load_config
from bench_eval.ouroboros_config import load_ouroboros_harness_config
from bench_eval.ouroboros_session import OuroborosEvalSession, reset_ouroboros_session


def test_default_cut_config_values():
    cfg = load_ouroboros_harness_config("configs/ouroboros.cut.json")
    assert cfg.mode == "cut"
    assert cfg.memory_mode == "empty"
    assert cfg.include_identity is False
    assert cfg.evolution_enabled is False
    assert cfg.per_task_drive is True
    assert cfg.shared_drive is False
    assert cfg.execution_backend == "dab-cut-loop"
    assert cfg.uses_ouroboros_cli() is False


def test_full_isolated_config_values():
    cfg = load_ouroboros_harness_config("configs/ouroboros.full_isolated.json")
    assert cfg.mode == "full_isolated"
    assert cfg.memory_mode == "forked"
    assert cfg.include_identity is True
    assert cfg.evolution_enabled is False
    assert cfg.per_task_drive is True
    assert cfg.execution_backend == "ouroboros-cli"


def test_full_evolving_config_values():
    cfg = load_ouroboros_harness_config("configs/ouroboros.full_evolving.json")
    assert cfg.mode == "full_evolving"
    assert cfg.memory_mode == "shared"
    assert cfg.include_identity is True
    assert cfg.evolution_enabled is True
    assert cfg.shared_drive is True
    assert cfg.require_workers_one is True


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("OUROBOROS_MODE", "full_isolated")
    monkeypatch.setenv("OUROBOROS_MEMORY_MODE", "forked")
    monkeypatch.setenv("OUROBOROS_EVOLUTION_ENABLED", "false")
    monkeypatch.setenv("OUROBOROS_EXECUTION_BACKEND", "ouroboros-cli")
    cfg = load_ouroboros_harness_config("configs/ouroboros.cut.json")
    assert cfg.mode == "cut"
    assert cfg.memory_mode == "forked"
    assert cfg.evolution_enabled is False
    assert cfg.execution_backend == "ouroboros-cli"


def test_load_config_selects_mode_json_from_harness(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENT_HARNESS", "ouroboros-full-evolving")
    monkeypatch.setenv("EVAL_DATASET_PATH", str(tmp_path / "dataset.json"))
    (tmp_path / "dataset.json").write_text("[]", encoding="utf-8")
    config = load_config()
    assert config.agent_harness == "ouroboros-full-evolving"
    assert config.ouroboros_config_path == "configs/ouroboros.full_evolving.json"
    assert config.ouroboros_mode == "full_evolving"
    assert config.ouroboros_evolution_enabled is True


def test_session_shared_drive_reused(tmp_path):
    reset_ouroboros_session()
    config = EvalConfig(
        agent_harness="ouroboros-full-evolving",
        ouroboros_config_path="configs/ouroboros.full_evolving.json",
        eval_output_dir=str(tmp_path),
    )
    session = OuroborosEvalSession.from_eval_config(config)
    assert session is not None
    first = session.prepare_task_drive("task_a")
    second = session.prepare_task_drive("task_b")
    assert first.drive_root == second.drive_root
    assert first.drive_root.name == "shared"


def test_session_cut_uses_per_task_drive(tmp_path):
    reset_ouroboros_session()
    config = EvalConfig(
        agent_harness="ouroboros-cut",
        ouroboros_config_path="configs/ouroboros.cut.json",
        eval_output_dir=str(tmp_path),
    )
    session = OuroborosEvalSession.from_eval_config(config)
    assert session is not None
    first = session.prepare_task_drive("task_a")
    second = session.prepare_task_drive("task_b")
    assert first.drive_root != second.drive_root


def test_json_configs_declare_harness_ids():
    for path, expected in (
        ("configs/ouroboros.cut.json", "ouroboros-cut"),
        ("configs/ouroboros.full_isolated.json", "ouroboros-full-isolated"),
        ("configs/ouroboros.full_evolving.json", "ouroboros-full-evolving"),
    ):
        payload = json.loads(open(path, encoding="utf-8").read())
        assert payload["harness"] == expected
