"""Pytest / deepeval: ensure repo root is importable and persist eval artifacts."""

from __future__ import annotations

import os
import sys

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.config import load_config
from bench_eval.dataset import load_or_build_dataset
from bench_eval.ouroboros_session import reset_ouroboros_session
from bench_eval.results import (
    EvalRunRecorder,
    detect_xdist_worker_id,
    get_recorder,
    is_xdist_worker,
    list_worker_result_files,
    merge_worker_results_into_final,
    reset_recorder,
    resolve_output_dir,
)


def pytest_configure(config):
    reset_recorder()
    reset_ouroboros_session()


def _golden_param_id(golden, index: int) -> str:
    meta = golden.additional_metadata or {}
    return str(meta.get("test_name") or golden.name or f"golden_{index}")


def pytest_generate_tests(metafunc):
    """Parametrize test_agent_bench_task over dataset goldens (DeepEval pattern)."""
    if "golden" not in metafunc.fixturenames:
        return
    config = load_config()
    dataset = load_or_build_dataset(config)
    goldens = list(dataset.goldens)
    ids = [_golden_param_id(g, i) for i, g in enumerate(goldens)]
    metafunc.parametrize("golden", goldens, ids=ids)


@pytest.fixture(scope="session")
def eval_config():
    config = load_config()
    recorder = get_recorder(config)
    config.dataset_path = str(recorder.dataset_path)
    return config


@pytest.fixture(scope="session", autouse=True)
def eval_run_recorder(eval_config):
    worker_id = detect_xdist_worker_id()
    recorder = get_recorder(eval_config)
    dataset = load_or_build_dataset(eval_config)
    recorder.set_total_tasks(len(dataset.goldens))
    recorder.print_run_header()
    yield recorder
    payload = recorder.finalize()
    if worker_id:
        if recorder.config.show_progress:
            print(
                f"\n=== Worker {worker_id} finished "
                f"({len(recorder.tests)} tasks) → {recorder.results_path} ===",
                flush=True,
            )
        return
    worker_files = list_worker_result_files(recorder.output_dir)
    if worker_files:
        return
    recorder.print_summary(payload)


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_sessionfinish(session, exitstatus):
    yield
    try:
        if not is_xdist_worker():
            config = load_config()
            output_dir = resolve_output_dir(config)
            worker_files = list_worker_result_files(output_dir)
            if worker_files:
                payload = merge_worker_results_into_final(config, worker_files)
                EvalRunRecorder.from_config(config).print_summary(payload)
    finally:
        from bench_eval.openhands_browser_patch import force_exit_openhands_eval

        force_exit_openhands_eval(exitstatus)
