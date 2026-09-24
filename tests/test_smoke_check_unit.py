"""Tests for smoke-result verification."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bench_eval.smoke_check import (
    assert_smoke_job_results,
    canonical_bench_task_count,
    filter_pending_eval_jobs,
    latest_eval_run_finished,
    pair_has_completed_full_bench,
    resolve_model_results_dir_name,
    verify_latest_smoke_run,
    verify_smoke_job_results,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_finished_run(
    base: Path,
    *,
    model: str,
    harness: str,
    run_name: str,
    total_tasks: int = 1,
    passed_tasks: int = 1,
    finished: bool = True,
    llm_model: str | None = None,
) -> Path:
    run_dir = base / model / harness / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    results_path = run_dir / "results.json"
    payload = {
        "run": {
            "model": llm_model or model,
            "agent_harness": harness,
            "finished": finished,
            "total_tasks": total_tasks,
            "passed_tasks": passed_tasks,
            "failed_tasks": total_tasks - passed_tasks,
        },
        "tests": [{"test_name": f"task_{idx}", "success": idx < passed_tasks} for idx in range(total_tasks)],
    }
    results_path.write_text(json.dumps(payload), encoding="utf-8")
    return results_path


def test_resolve_model_results_dir_name_from_env_file(monkeypatch):
    monkeypatch.setenv("AGENT_BENCH_ROOT", str(_REPO_ROOT))
    assert resolve_model_results_dir_name("gemini-2.5-flash") == "google_gemini-2.5-flash"
    assert resolve_model_results_dir_name("deepseek-v4-flash") == "deepseek_deepseek-v4-flash"
    assert resolve_model_results_dir_name("gpt-5.5") == "openai_gpt-5.5"
    assert resolve_model_results_dir_name("claude-opus-4-7") == "anthropic_claude-opus-4.7"
    assert resolve_model_results_dir_name("glm-5.1") == "z-ai_glm-5.1"
    assert resolve_model_results_dir_name("glm-5.2") == "z-ai_glm-5.2"
    assert resolve_model_results_dir_name("deepseek-v4.1-flash") == "deepseek_deepseek-v4.1-flash"
    assert resolve_model_results_dir_name("gpt-5.6-luna") == "openai_gpt-5.6-luna"
    assert resolve_model_results_dir_name("minimax-m2.7") == "minimax_minimax-m2.7"
    assert resolve_model_results_dir_name("gemini-3.8-flash") == "google_gemini-3.8-flash"


def test_verify_latest_smoke_run_ok(tmp_path):
    model_dir = resolve_model_results_dir_name("gemini-2.5-flash", repo_root=_REPO_ROOT)
    _write_finished_run(
        tmp_path,
        model=model_dir,
        harness="browser-use",
        run_name="2026-06-23_03-00-00__abcd1234",
        llm_model="google/gemini-2.5-flash",
    )
    check = verify_latest_smoke_run(
        "browser-use",
        "gemini-2.5-flash",
        base_dir=tmp_path,
        repo_root=_REPO_ROOT,
    )
    assert check.ok
    assert check.total_tasks == 1
    assert check.run_dir is not None


def test_verify_latest_smoke_run_missing(tmp_path):
    check = verify_latest_smoke_run(
        "browser-use",
        "gemini-2.5-flash",
        base_dir=tmp_path,
        repo_root=_REPO_ROOT,
    )
    assert check.status == "missing"
    assert not check.ok


def test_verify_latest_smoke_run_incomplete_when_not_finished(tmp_path):
    model_dir = resolve_model_results_dir_name("gemini-2.5-flash", repo_root=_REPO_ROOT)
    _write_finished_run(
        tmp_path,
        model=model_dir,
        harness="browser-use",
        run_name="2026-06-23_03-00-00",
        finished=False,
        llm_model="google/gemini-2.5-flash",
    )
    check = verify_latest_smoke_run(
        "browser-use",
        "gemini-2.5-flash",
        base_dir=tmp_path,
        repo_root=_REPO_ROOT,
    )
    assert check.status == "incomplete"
    assert "finished=false" in check.errors[0]


def test_verify_latest_smoke_run_failed_eval(tmp_path):
    model_dir = resolve_model_results_dir_name("deepseek-v4-flash", repo_root=_REPO_ROOT)
    _write_finished_run(
        tmp_path,
        model=model_dir,
        harness="ouroboros-cut",
        run_name="2026-06-23_03-00-00__ef9de3c1",
        passed_tasks=0,
        llm_model="deepseek/deepseek-v4-flash",
    )
    check = verify_latest_smoke_run(
        "ouroboros-cut",
        "deepseek-v4-flash",
        base_dir=tmp_path,
        repo_root=_REPO_ROOT,
    )
    assert check.status == "failed_eval"
    assert not check.ok
    assert check.results_path is not None


def test_verify_smoke_job_results_picks_latest_per_combo(tmp_path):
    model_dir = resolve_model_results_dir_name("gemini-2.5-flash", repo_root=_REPO_ROOT)
    _write_finished_run(
        tmp_path,
        model=model_dir,
        harness="browser-use",
        run_name="2026-06-22_10-00-00",
        total_tasks=1,
        llm_model="google/gemini-2.5-flash",
    )
    newer = _write_finished_run(
        tmp_path,
        model=model_dir,
        harness="browser-use",
        run_name="2026-06-23_03-00-00",
        total_tasks=1,
        llm_model="google/gemini-2.5-flash",
    )
    checks = verify_smoke_job_results(
        [{"harness": "browser-use", "model": "gemini-2.5-flash"}],
        base_dir=tmp_path,
        repo_root=_REPO_ROOT,
    )
    assert len(checks) == 1
    assert checks[0].ok
    assert checks[0].results_path == newer


def test_repo_root_uses_agent_bench_root_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_BENCH_ROOT", str(tmp_path))
    from bench_eval.smoke_check import _repo_root

    assert _repo_root() == tmp_path


def test_assert_smoke_job_results_raises_on_missing(tmp_path):
    with pytest.raises(SystemExit, match="Smoke results check failed"):
        assert_smoke_job_results(
            [{"harness": "browser-use", "model": "gemini-2.5-flash"}],
            base_dir=tmp_path,
            repo_root=_REPO_ROOT,
        )


def test_assert_smoke_job_results_allows_failed_eval_by_default(tmp_path):
    model_dir = resolve_model_results_dir_name("deepseek-v4-flash", repo_root=_REPO_ROOT)
    _write_finished_run(
        tmp_path,
        model=model_dir,
        harness="ouroboros-cut",
        run_name="2026-06-23_03-00-00",
        passed_tasks=0,
        llm_model="deepseek/deepseek-v4-flash",
    )
    checks = assert_smoke_job_results(
        [{"harness": "ouroboros-cut", "model": "deepseek-v4-flash"}],
        base_dir=tmp_path,
        repo_root=_REPO_ROOT,
    )
    assert checks[0].status == "failed_eval"


def test_latest_eval_run_finished_reads_newest_run(tmp_path):
    model_dir = resolve_model_results_dir_name("gemini-2.5-flash", repo_root=_REPO_ROOT)
    _write_finished_run(
        tmp_path,
        model=model_dir,
        harness="browser-use",
        run_name="2026-06-23_02-00-00",
        finished=False,
    )
    finished_path = _write_finished_run(
        tmp_path,
        model=model_dir,
        harness="browser-use",
        run_name="2026-06-23_03-00-00",
        finished=True,
    )
    ok, path = latest_eval_run_finished(
        "browser-use",
        "gemini-2.5-flash",
        base_dir=tmp_path,
        repo_root=_REPO_ROOT,
    )
    assert ok is True
    assert path == finished_path


def test_canonical_bench_task_count_matches_tasks_dir():
    assert canonical_bench_task_count(repo_root=_REPO_ROOT) == 152


def test_filter_pending_eval_jobs_skips_completed_full_bench_not_smoke(tmp_path):
    model_dir = resolve_model_results_dir_name("gemini-3.8-flash", repo_root=_REPO_ROOT)
    _write_finished_run(
        tmp_path,
        model=model_dir,
        harness="browser-use",
        run_name="2026-06-23_02-00-00",
        total_tasks=152,
        passed_tasks=140,
        llm_model="google/gemini-3.8-flash",
    )
    _write_finished_run(
        tmp_path,
        model=model_dir,
        harness="openhands",
        run_name="2026-06-23_03-00-00",
        total_tasks=1,
        passed_tasks=1,
        llm_model="google/gemini-3.8-flash",
    )
    specs = [
        {"harness": "browser-use", "model": "gemini-3.8-flash"},
        {"harness": "openhands", "model": "gemini-3.8-flash"},
        {"harness": "openmanus", "model": "gemini-3.8-flash"},
    ]
    pending, skipped = filter_pending_eval_jobs(
        specs,
        base_dir=tmp_path,
        repo_root=_REPO_ROOT,
        min_tasks=152,
    )
    assert [spec["harness"] for spec in skipped] == ["browser-use"]
    assert [spec["harness"] for spec in pending] == ["openhands", "openmanus"]


def test_pair_has_completed_full_bench_ignores_newer_smoke(tmp_path):
    model_dir = resolve_model_results_dir_name("gpt-5.6-luna", repo_root=_REPO_ROOT)
    _write_finished_run(
        tmp_path,
        model=model_dir,
        harness="openmanus",
        run_name="2026-06-23_01-00-00",
        total_tasks=152,
        passed_tasks=152,
        llm_model="openai/gpt-5.6-luna",
    )
    _write_finished_run(
        tmp_path,
        model=model_dir,
        harness="openmanus",
        run_name="2026-06-23_09-00-00",
        total_tasks=1,
        passed_tasks=1,
        llm_model="openai/gpt-5.6-luna",
    )
    done, path, total = pair_has_completed_full_bench(
        "openmanus",
        "gpt-5.6-luna",
        base_dir=tmp_path,
        repo_root=_REPO_ROOT,
        min_tasks=152,
    )
    assert done is True
    assert total == 152
    assert path is not None
    assert "2026-06-23_01-00-00" in str(path)


def test_pair_has_completed_full_bench_false_when_unfinished(tmp_path):
    model_dir = resolve_model_results_dir_name("glm-5.2", repo_root=_REPO_ROOT)
    _write_finished_run(
        tmp_path,
        model=model_dir,
        harness="openhands",
        run_name="2026-06-23_01-00-00",
        total_tasks=152,
        passed_tasks=10,
        finished=False,
        llm_model="z-ai/glm-5.2",
    )
    done, path, total = pair_has_completed_full_bench(
        "openhands",
        "glm-5.2",
        base_dir=tmp_path,
        repo_root=_REPO_ROOT,
        min_tasks=152,
    )
    assert done is False
    assert path is None
    assert total == 0
