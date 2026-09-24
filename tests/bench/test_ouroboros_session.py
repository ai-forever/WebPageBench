"""Unit tests for ouroboros identity seeding and drive layout."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.config import EvalConfig
from bench_eval.ouroboros_session import (
    OuroborosEvalSession,
    normalize_to_memory_seed_dir,
    reset_ouroboros_session,
    resolve_identity_seed_memory_dir,
    resolve_ouroboros_drive_namespace,
)


def test_bundled_seed_memory_dir_exists():
    seed = resolve_identity_seed_memory_dir({})
    assert seed.is_dir()
    assert (seed / "identity.md").is_file()
    assert (seed / "WORLD.md").is_file()
    assert (seed / "registry.md").is_file()
    assert (seed / "knowledge" / "webpagebench-benchmark.md").is_file()


def test_normalize_accepts_data_root_and_memory_dir(tmp_path):
    data_root = tmp_path / "data"
    memory_dir = data_root / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "identity.md").write_text("seed\n", encoding="utf-8")

    assert normalize_to_memory_seed_dir(data_root) == memory_dir
    assert normalize_to_memory_seed_dir(memory_dir) == memory_dir


def test_resolve_prefers_env_seed_over_bundled(tmp_path, monkeypatch):
    custom = tmp_path / "custom-data"
    memory_dir = custom / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "identity.md").write_text("custom\n", encoding="utf-8")

    monkeypatch.delenv("OUROBOROS_REPO_DIR", raising=False)
    resolved = resolve_identity_seed_memory_dir(
        {"OUROBOROS_IDENTITY_SEED_DIR": str(custom)}
    )
    assert resolved == memory_dir


def test_full_isolated_seeds_memory_subdir(tmp_path):
    reset_ouroboros_session()
    config = EvalConfig(
        agent_harness="ouroboros-full-isolated",
        ouroboros_config_path="configs/ouroboros.full_isolated.json",
        eval_output_dir=str(tmp_path),
    )
    session = OuroborosEvalSession.from_eval_config(config)
    assert session is not None
    task_drive = session.prepare_task_drive("task_a")

    memory_dir = task_drive.drive_root / "memory"
    assert memory_dir.is_dir()
    assert (memory_dir / "identity.md").is_file()
    assert (memory_dir / "WORLD.md").is_file()
    assert (memory_dir / "registry.md").is_file()
    assert (memory_dir / "knowledge" / "webpagebench-benchmark.md").is_file()
    assert not (task_drive.drive_root / "identity.md").exists()


def test_cut_mode_does_not_seed_identity(tmp_path):
    reset_ouroboros_session()
    config = EvalConfig(
        agent_harness="ouroboros-cut",
        ouroboros_config_path="configs/ouroboros.cut.json",
        eval_output_dir=str(tmp_path),
    )
    session = OuroborosEvalSession.from_eval_config(config)
    assert session is not None
    task_drive = session.prepare_task_drive("task_a")
    assert not (task_drive.drive_root / "memory").exists()


def test_shared_drive_namespaced_by_track_suffix(tmp_path):
    reset_ouroboros_session()
    config_a = EvalConfig(
        agent_harness="ouroboros-full-evolving",
        ouroboros_config_path="configs/ouroboros.full_evolving.json",
        eval_output_dir=str(tmp_path),
        track_suffix="run_a",
    )
    config_b = EvalConfig(
        agent_harness="ouroboros-full-evolving",
        ouroboros_config_path="configs/ouroboros.full_evolving.json",
        eval_output_dir=str(tmp_path),
        track_suffix="run_b",
    )
    drive_a = OuroborosEvalSession.from_eval_config(config_a).prepare_task_drive("task_a")
    drive_b = OuroborosEvalSession.from_eval_config(config_b).prepare_task_drive("task_a")

    assert drive_a.drive_root != drive_b.drive_root
    assert drive_a.drive_root == tmp_path / "ouroboros_drive" / "run_a" / "shared"
    assert drive_b.drive_root == tmp_path / "ouroboros_drive" / "run_b" / "shared"


def test_resolve_ouroboros_drive_namespace_generates_suffix(monkeypatch):
    monkeypatch.delenv("EVAL_TRACK_SUFFIX", raising=False)
    config = EvalConfig(
        agent_harness="ouroboros-full-evolving",
        eval_output_dir="/tmp/eval",
    )
    namespace = resolve_ouroboros_drive_namespace(config)
    assert len(namespace) == 8
    assert os.environ.get("EVAL_TRACK_SUFFIX") == namespace


def test_finalize_task_waits_for_ready_after_evolution(tmp_path):
    reset_ouroboros_session()
    config = EvalConfig(
        agent_harness="ouroboros-full-evolving",
        ouroboros_config_path="configs/ouroboros.full_evolving.json",
        eval_output_dir=str(tmp_path),
        track_suffix="evolve_wait",
    )
    session = OuroborosEvalSession.from_eval_config(config)
    assert session is not None
    task_drive = session.prepare_task_drive("task_a")

    client = MagicMock()
    with patch(
        "bench_eval.ouroboros_client.OuroborosHTTPClient",
        return_value=client,
    ):
        session.finalize_task(
            task_drive,
            agent_summary={"is_done": True, "steps": 3, "final_result": "ok"},
        )

    client.set_post_task_evolution.assert_called_once_with(True)
    client.request.assert_called_once()
    client.wait_until_ready.assert_called_once()
