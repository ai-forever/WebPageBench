"""Unit tests for eval result artifact paths."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.config import EvalConfig
from bench_eval.results import (
    EvalRunRecorder,
    configure_deepeval_cache_folder,
    default_deepeval_cache_dir,
    default_run_directory,
    format_run_dir_leaf,
    is_run_directory_name,
    merge_worker_results_into_final,
    parse_run_dir_timestamp,
    sanitize_model_name,
    worker_results_path,
)
from bench_eval.ui_taxonomy_report import aggregate_ui_stats, build_ui_taxonomy_report


def test_sanitize_model_name():
    assert sanitize_model_name("google/gemini-2.5-flash") == "google_gemini-2.5-flash"
    assert sanitize_model_name("  ") == "unknown_model"


def test_default_run_directory_format():
    started = datetime(2026, 6, 20, 13, 45, 30)
    path = default_run_directory("gpt-4.1-mini", "browser-use", started_at=started)
    assert path == Path("tests/eval/gpt-4.1-mini/browser-use/2026-06-20_13-45-30")


def test_default_run_directory_includes_track_suffix():
    started = datetime(2026, 6, 20, 13, 45, 30)
    path = default_run_directory(
        "gpt-4.1-mini",
        "browser-use",
        started_at=started,
        track_suffix="a1b2c3d4",
    )
    assert path == Path(
        "tests/eval/gpt-4.1-mini/browser-use/2026-06-20_13-45-30__a1b2c3d4"
    )
    assert format_run_dir_leaf(started_at=started, track_suffix="a1b2c3d4") == (
        "2026-06-20_13-45-30__a1b2c3d4"
    )


def test_configure_deepeval_cache_folder_isolates_per_run(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPEVAL_CACHE_FOLDER", raising=False)
    run_a = tmp_path / "run-a"
    run_b = tmp_path / "run-b"
    run_a.mkdir()
    run_b.mkdir()

    cache_a = configure_deepeval_cache_folder(str(run_a))
    assert cache_a == str(default_deepeval_cache_dir(run_a))
    assert os.environ["DEEPEVAL_CACHE_FOLDER"] == cache_a

    monkeypatch.delenv("DEEPEVAL_CACHE_FOLDER", raising=False)
    cache_b = configure_deepeval_cache_folder(str(run_b))
    assert cache_a != cache_b
    assert cache_b == str(default_deepeval_cache_dir(run_b))


def test_load_config_sets_deepeval_cache_folder(tmp_path, monkeypatch):
    from bench_eval.config import load_config

    monkeypatch.delenv("DEEPEVAL_CACHE_FOLDER", raising=False)
    monkeypatch.delenv("EVAL_TRACK_SUFFIX", raising=False)
    monkeypatch.setenv("EVAL_OUTPUT_DIR", str(tmp_path / "manual-run"))
    monkeypatch.setenv("EVAL_DATASET_PATH", str(tmp_path / "manual-run" / "dataset.json"))

    load_config()
    assert os.environ["DEEPEVAL_CACHE_FOLDER"] == str(
        tmp_path / "manual-run" / ".deepeval"
    )
    assert os.environ["EVAL_TRACK_SUFFIX"]


def test_run_directory_name_helpers():
    assert is_run_directory_name("2026-06-20_13-45-30")
    assert is_run_directory_name("2026-06-20_13-45-30__a1b2c3d4")
    assert not is_run_directory_name("ouroboros_drive")

    parsed = parse_run_dir_timestamp("2026-06-20_13-45-30__a1b2c3d4")
    assert parsed == datetime(2026, 6, 20, 13, 45, 30)


def test_recorder_writes_results_json(tmp_path):
    config = EvalConfig(
        llm_model="test-model",
        llm_provider="openai",
        agent_harness="hermes-ouroboros",
        eval_output_dir=str(tmp_path / "run"),
    )
    recorder = EvalRunRecorder.from_config(config)
    test_case = MagicMock()
    test_case.name = "demo_task"
    test_case.input = "do something"
    test_case.actual_output = "done"
    test_case.metadata = {
        "test_name": "demo_task",
        "track_id": "demo_task",
        "task_url": "http://localhost/demo_task",
        "dab_check": {"all_passed": True, "passed": 1, "failed": 0, "total": 1},
        "agent": {"steps": 3, "is_done": True, "token_usage": {
            "prompt_tokens": 1000,
            "completion_tokens": 200,
            "total_tokens": 1200,
            "llm_calls": 5,
        }},
        "token_usage": {
            "prompt_tokens": 1000,
            "completion_tokens": 200,
            "total_tokens": 1200,
            "llm_calls": 5,
        },
        "timing": {"duration_seconds": 12.5},
        "trajectory": {"agent": {"steps": []}, "dab_events": []},
        "agent_harness": "hermes-ouroboros",
    }

    recorder.record_test(test_case)
    payload = recorder.finalize()

    assert recorder.results_path.exists()
    assert payload["run"]["success_rate"] == 1.0
    assert payload["run"]["avg_agent_steps"] == 3.0
    assert payload["run"]["total_agent_steps"] == 3
    assert payload["run"]["total_tokens"] == 1200
    assert payload["run"]["avg_tokens_per_task"] == 1200.0
    assert payload["run"]["agent_harness"] == "hermes-ouroboros"
    saved = json.loads(recorder.results_path.read_text(encoding="utf-8"))
    assert saved["tests"][0]["success"] is True
    assert saved["tests"][0]["duration_seconds"] == 12.5
    assert saved["tests"][0]["tokens"] == 1200
    assert saved["tests"][0]["token_usage"]["prompt_tokens"] == 1000
    assert saved["tests"][0]["agent_harness"] == "hermes-ouroboros"
    assert "extended_metrics" in saved["run"]
    assert saved["tests"][0]["extended_metrics"]["agent_dab_agreement"] is True
    assert saved["extended_metrics_meta"]["enriched_by"] == "bench_eval.results"
    assert payload["run"]["extended_metrics"]["agent_completion_rate"] == 1.0


def test_build_ui_taxonomy_report_from_task(tmp_path):
    config_path = tmp_path / "task.json"
    config_path.write_text(
        json.dumps(
            {
                "test_data": {
                    "bench_first_domain": "rail",
                    "conditions": [
                        {"event_name": "select_city", "parameters": {"field": "from", "name": "Москва"}},
                        {"event_name": "basket_add", "parameters": {}},
                    ],
                    "ui_taxonomy": {
                        "primary": "BASKET",
                        "classes": ["SELECT_LIST", "BASKET"],
                    },
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    report = build_ui_taxonomy_report(
        config_path=str(config_path),
        test_name="rail_demo",
        dab_events=[
            {"event_name": "select_city", "event_data": {"field": "from", "name": "Москва"}},
            {"event_name": "state_changed", "event_data": {"new_state": "bench_rail_search"}},
        ],
    )
    assert report["checked_classes"] == ["SELECT_LIST", "BASKET"]
    assert "SELECT_LIST" in report["used_classes"]
    assert "NAV" in report["used_classes"]
    assert report["ui_patterns"]["variants"]["date"] == "popup_grid"
    assert "date:popup_grid" in report["ui_patterns"]["pattern_keys"]


def test_aggregate_ui_stats():
    tests = [
        {
            "test_name": "t1",
            "success": True,
            "ui_taxonomy": {
                "declared": {"primary": "BASKET"},
                "checked_classes": ["BASKET", "CARD"],
                "used_classes": ["BASKET", "NAV"],
                "ui_patterns": {"pattern_keys": ["text_search:standard"]},
            },
        },
        {
            "test_name": "t2",
            "success": False,
            "ui_taxonomy": {
                "declared": {"primary": "BASKET"},
                "checked_classes": ["BASKET"],
                "used_classes": ["NAV"],
                "ui_patterns": {"pattern_keys": ["text_search:standard"]},
            },
        },
    ]
    stats = aggregate_ui_stats(tests)
    assert stats["by_checked_class"]["BASKET"]["passed"] == 1
    assert stats["by_checked_class"]["BASKET"]["failed"] == 1
    assert stats["by_ui_pattern"]["text_search:standard"]["total"] == 2
    assert stats["by_ui_pattern"]["text_search:standard"]["passed"] == 1


def test_render_run_report_markdown():
    payload = {
        "run": {
            "model": "demo-model",
            "provider": "openai",
            "agent_harness": "browser-use",
            "mock": "bench",
            "started_at": "2026-06-20T10:00:00+00:00",
            "finished_at": "2026-06-20T11:00:00+00:00",
            "finished": True,
            "total_tasks": 2,
            "passed_tasks": 1,
            "failed_tasks": 1,
            "success_rate": 0.5,
            "total_duration_seconds": 30.0,
            "avg_duration_seconds": 15.0,
            "avg_agent_steps": 4.0,
            "total_tokens": 3000,
            "avg_tokens_per_task": 1500.0,
            "prompt_tokens": 2500,
            "completion_tokens": 500,
        },
        "ui_taxonomy_stats": {
            "by_checked_class": {
                "BASKET": {"passed": 1, "failed": 1, "total": 2, "success_rate": 0.5}
            }
        },
        "tests": [
            {
                "test_name": "ok_task",
                "track_id": "ok_task",
                "success": True,
                "duration_seconds": 10.0,
                "agent_steps": 3,
                "tokens": 1000,
                "token_usage": {
                    "prompt_tokens": 800,
                    "completion_tokens": 200,
                    "total_tokens": 1000,
                    "llm_calls": 4,
                },
                "agent_is_done": True,
                "dab_check": {"passed": 1, "total": 1},
                "ui_taxonomy": {"domain": "shop"},
            },
            {
                "test_name": "bad_task",
                "track_id": "bad_task",
                "success": False,
                "duration_seconds": 20.0,
                "agent_steps": 5,
                "tokens": 2000,
                "token_usage": {
                    "prompt_tokens": 1700,
                    "completion_tokens": 300,
                    "total_tokens": 2000,
                    "llm_calls": 6,
                },
                "agent_is_done": False,
                "dab_check": {"passed": 0, "total": 1, "failed_conditions": ["basket_add"]},
                "agent_error": "timeout",
                "actual_output": "failed",
                "ui_taxonomy": {
                    "domain": "shop",
                    "checked_but_not_used": ["BASKET"],
                    "ui_patterns": {"pattern_keys": ["text_search:standard"]},
                },
            },
        ],
    }
    from bench_eval.run_report import render_run_report

    md = render_run_report(payload, results_path=Path("tests/eval/demo/run/results.json"))
    assert "# Eval run report: demo-model" in md
    assert "| Harness | `browser-use` |" in md
    assert "Всего токенов" in md
    assert "Токены" in md
    assert "## Проваленные задачи" in md
    assert "`bad_task`" in md
    assert "UI taxonomy — проверяемые классы" in md
    assert "Классы UI из `conditions`" in md
    assert "| Класс | Описание | Passed |" in md
    assert "BASKET" in md
    assert "Корзина" in md


def test_ui_taxonomy_labels():
    from bench_eval.ui_taxonomy_labels import (
        taxonomy_class_description,
        ui_pattern_description,
    )

    assert "Корзина" in taxonomy_class_description("BASKET")
    assert "Навигация" in taxonomy_class_description("NAV")
    desc = ui_pattern_description("date:popup_grid")
    assert "DATE" in desc
    assert "popup_grid" in desc or "сетка" in desc


def test_write_run_report_file(tmp_path):
    run_dir = tmp_path / "demo-run"
    run_dir.mkdir()
    payload = {
        "run": {
            "model": "demo-model",
            "provider": "openai",
            "agent_harness": "browser-use",
            "mock": "bench",
            "finished": True,
            "total_tasks": 1,
            "passed_tasks": 1,
            "failed_tasks": 0,
            "success_rate": 1.0,
        },
        "tests": [
            {
                "test_name": "ok_task",
                "track_id": "ok_task",
                "success": True,
                "duration_seconds": 1.0,
                "agent_steps": 1,
                "agent_is_done": True,
                "dab_check": {"passed": 1, "total": 1},
                "ui_taxonomy": {"domain": "shop"},
            }
        ],
    }
    results_path = run_dir / "results.json"
    results_path.write_text(json.dumps(payload), encoding="utf-8")

    from bench_eval.run_report import write_run_report

    readme = write_run_report(run_dir)
    assert readme == run_dir / "README.md"
    content = readme.read_text(encoding="utf-8")
    assert content.startswith("# Eval run report")
    assert "| Harness | `browser-use` |" in content
    assert str(run_dir.resolve()) in content
    assert str(results_path.resolve()) in content
    assert str(readme.resolve()) in content


def test_progress_formatting():
    from bench_eval.progress import format_progress_result, format_progress_start

    assert format_progress_start(1, 51, "demo_task") == "[ 1/51] ▶ demo_task"
    line = format_progress_result(
        2,
        51,
        {
            "test_name": "demo_task",
            "success": True,
            "duration_seconds": 12.5,
            "agent_steps": 7,
            "dab_check": {"passed": 3, "total": 3},
            "token_usage": {"prompt_tokens": 40, "completion_tokens": 10, "total_tokens": 50, "llm_calls": 2},
            "tokens": 50,
        },
        running_success_rate=0.5,
    )
    assert "[ 2/51]" in line
    assert "PASS" in line
    assert "demo_task" in line
    assert "tokens=50" in line
    assert "success=50%" in line


def test_recorder_progress_output(tmp_path, capsys):
    config = EvalConfig(
        llm_model="demo",
        llm_provider="openai",
        eval_output_dir=str(tmp_path / "run"),
        show_progress=True,
    )
    recorder = EvalRunRecorder.from_config(config)
    recorder.set_total_tasks(1)
    recorder.print_run_header()
    recorder.on_test_start("demo_task")

    test_case = MagicMock()
    test_case.name = "demo_task"
    test_case.input = "task"
    test_case.actual_output = "ok"
    test_case.metadata = {
        "test_name": "demo_task",
        "dab_check": {"all_passed": True, "passed": 1, "total": 1},
        "agent": {"steps": 2, "is_done": True},
        "timing": {"duration_seconds": 1.0},
    }
    recorder.record_test(test_case)

    captured = capsys.readouterr()
    assert "Eval scoring" in captured.out
    assert "▶ demo_task" in captured.out
    assert "PASS" in captured.out
    assert "demo_task" in captured.out


def test_find_latest_results_scoped_by_harness(tmp_path):
    from bench_eval.run_report import find_latest_results

    browser_old = tmp_path / "demo-model" / "browser-use" / "2026-06-19_10-00-00"
    browser_new = tmp_path / "demo-model" / "browser-use" / "2026-06-20_10-00-00"
    hermes_run = tmp_path / "demo-model" / "hermes-ouroboros" / "2026-06-21_10-00-00"
    for run_dir in (browser_old, browser_new, hermes_run):
        run_dir.mkdir(parents=True)
        (run_dir / "results.json").write_text("{}", encoding="utf-8")

    latest_browser = find_latest_results(
        tmp_path,
        model="demo-model",
        harness="browser-use",
    )
    assert latest_browser == browser_new / "results.json"

    latest_any = find_latest_results(tmp_path, model="demo-model")
    assert latest_any == hermes_run / "results.json"


def test_find_latest_results_new_layout(tmp_path):
    from bench_eval.run_report import find_latest_results

    old_run = tmp_path / "demo-model" / "browser-use" / "2026-06-19_09-00-00"
    new_run = tmp_path / "demo-model" / "browser-use" / "2026-06-20_10-00-00"
    for run_dir in (old_run, new_run):
        run_dir.mkdir(parents=True)
        (run_dir / "results.json").write_text("{}", encoding="utf-8")

    latest = find_latest_results(tmp_path, model="demo-model", harness="browser-use")
    assert latest == new_run / "results.json"


def test_find_latest_results_track_suffix_layout(tmp_path):
    from bench_eval.run_report import find_latest_results

    older = tmp_path / "demo-model" / "browser-use" / "2026-06-20_10-00-00__aaaa1111"
    newer = tmp_path / "demo-model" / "browser-use" / "2026-06-20_10-00-00__bbbb2222"
    for run_dir in (older, newer):
        run_dir.mkdir(parents=True)
        (run_dir / "results.json").write_text("{}", encoding="utf-8")

    latest = find_latest_results(tmp_path, model="demo-model", harness="browser-use")
    assert latest == newer / "results.json"


def test_refactor_eval_results_layout(tmp_path):
    import importlib.util

    script_path = Path(_REPO_ROOT) / "scripts" / "refactor_eval_results_layout.py"
    spec = importlib.util.spec_from_file_location(
        "refactor_eval_results_layout",
        script_path,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    legacy = tmp_path / "gpt-4.1-mini" / "2026-06-20_13-27-37"
    legacy.mkdir(parents=True)
    payload = {
        "run": {
            "model": "gpt-4.1-mini",
            "agent_harness": "hermes-ouroboros",
            "started_at": "2026-06-20T13:27:37+00:00",
            "output_dir": str(legacy),
            "dataset_path": str(legacy / "dataset.json"),
            "results_path": str(legacy / "results.json"),
        },
        "tests": [],
    }
    (legacy / "results.json").write_text(json.dumps(payload), encoding="utf-8")
    (legacy / "dataset.json").write_text("[]", encoding="utf-8")

    plans = module.plan_moves(tmp_path, default_harness="browser-use")
    assert len(plans) == 1
    source, target, harness = plans[0]
    assert source == legacy
    assert target == tmp_path / "gpt-4.1-mini" / "hermes-ouroboros" / "2026-06-20_13-27-37"
    assert harness == "hermes-ouroboros"

    moved = module.refactor_layout(tmp_path, default_harness="browser-use")
    assert len(moved) == 1
    assert not legacy.exists()
    assert (target / "results.json").is_file()
    updated = json.loads((target / "results.json").read_text(encoding="utf-8"))
    assert updated["run"]["output_dir"] == str(target)
    assert updated["run"]["results_path"] == str(target / "results.json")


def test_worker_results_path():
    output_dir = Path("tests/eval/demo/run")
    assert worker_results_path(output_dir, "gw0") == output_dir / "results.worker-gw0.json"


def test_recorder_writes_worker_results_file(tmp_path):
    config = EvalConfig(
        llm_model="demo",
        llm_provider="openai",
        eval_output_dir=str(tmp_path / "run"),
    )
    recorder = EvalRunRecorder.from_config(config, worker_id="gw0")
    test_case = MagicMock()
    test_case.name = "task_a"
    test_case.input = "task"
    test_case.actual_output = "ok"
    test_case.metadata = {
        "test_name": "task_a",
        "dab_check": {"all_passed": True, "passed": 1, "total": 1},
        "agent": {"steps": 2, "is_done": True},
        "timing": {"duration_seconds": 5.0},
    }
    recorder.set_total_tasks(2)
    recorder.record_test(test_case)
    payload = recorder.finalize()

    worker_path = tmp_path / "run" / "results.worker-gw0.json"
    assert worker_path.exists()
    assert payload["run"]["worker_id"] == "gw0"
    assert payload["run"]["expected_total_tasks"] == 2
    assert not (tmp_path / "run" / "results.json").exists()


def test_merge_worker_results_into_final(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    config = EvalConfig(
        llm_model="demo",
        llm_provider="openai",
        eval_output_dir=str(run_dir),
    )

    worker_payloads = [
        {
            "run": {
                "worker_id": "gw0",
                "started_at": "2026-06-20T10:00:00+00:00",
                "finished_at": "2026-06-20T10:05:00+00:00",
                "expected_total_tasks": 3,
            },
            "tests": [
                {
                    "test_name": "task_b",
                    "success": False,
                    "duration_seconds": 20.0,
                    "agent_steps": 5,
                    "token_usage": {
                        "prompt_tokens": 300,
                        "completion_tokens": 50,
                        "total_tokens": 350,
                        "llm_calls": 3,
                    },
                    "tokens": 350,
                    "dab_check": {"passed": 0, "total": 1},
                    "ui_taxonomy": {"checked_classes": ["BASKET"]},
                }
            ],
        },
        {
            "run": {
                "worker_id": "gw1",
                "started_at": "2026-06-20T09:59:00+00:00",
                "finished_at": "2026-06-20T10:10:00+00:00",
                "expected_total_tasks": 3,
            },
            "tests": [
                {
                    "test_name": "task_a",
                    "success": True,
                    "duration_seconds": 10.0,
                    "agent_steps": 3,
                    "token_usage": {
                        "prompt_tokens": 100,
                        "completion_tokens": 20,
                        "total_tokens": 120,
                        "llm_calls": 2,
                    },
                    "tokens": 120,
                    "dab_check": {"passed": 1, "total": 1},
                    "ui_taxonomy": {"checked_classes": ["BASKET"]},
                },
                {
                    "test_name": "task_c",
                    "success": True,
                    "duration_seconds": 15.0,
                    "agent_steps": 4,
                    "token_usage": {
                        "prompt_tokens": 200,
                        "completion_tokens": 30,
                        "total_tokens": 230,
                        "llm_calls": 2,
                    },
                    "tokens": 230,
                    "dab_check": {"passed": 1, "total": 1},
                    "ui_taxonomy": {"checked_classes": ["NAV"]},
                },
            ],
        },
    ]

    worker_files = []
    for index, payload in enumerate(worker_payloads):
        path = run_dir / f"results.worker-gw{index}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        worker_files.append(path)

    merged = merge_worker_results_into_final(config, worker_files)
    final_path = run_dir / "results.json"

    assert final_path.exists()
    assert merged["run"]["worker_id"] is None
    assert merged["run"]["expected_total_tasks"] == 3
    assert merged["run"]["total_tasks"] == 3
    assert merged["run"]["passed_tasks"] == 2
    assert merged["run"]["failed_tasks"] == 1
    assert merged["run"]["success_rate"] == 2 / 3
    assert merged["run"]["total_tokens"] == 700
    assert merged["run"]["avg_tokens_per_task"] == 700 / 3
    assert merged["run"]["parallel"]["worker_count"] == 2
    assert merged["run"]["finished_at"] == "2026-06-20T10:10:00+00:00"
    assert [row["test_name"] for row in merged["tests"]] == ["task_a", "task_b", "task_c"]
    assert merged["ui_taxonomy_stats"]["by_checked_class"]["BASKET"]["total"] == 2
    assert merged["run"]["extended_metrics"]["false_done_count"] == 0
    assert merged["extended_metrics_meta"]["enriched_by"] == "bench_eval.results"
    assert merged["tests"][0]["extended_metrics"]["token_efficiency"] == pytest.approx(1 / 120)


def _write_results(run_dir: Path, *, model: str, harness: str, started_at: str, **overrides) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    run = {
        "model": model,
        "agent_harness": harness,
        "started_at": started_at,
        "finished": True,
        "total_tasks": 2,
        "passed_tasks": 1,
        "failed_tasks": 1,
        "success_rate": 0.5,
        "avg_duration_seconds": 10.0,
        "avg_agent_steps": 3.0,
        "avg_tokens_per_task": 100.0,
        "total_tokens": 200,
        "prompt_tokens": 1_000_000,
        "completion_tokens": 0,
        **overrides,
    }
    payload = {"run": run, "tests": []}
    (run_dir / "results.json").write_text(json.dumps(payload), encoding="utf-8")


def test_discover_latest_runs_picks_newest_per_harness_model(tmp_path):
    from bench_eval.aggregate_report import discover_latest_runs

    _write_results(
        tmp_path / "model-a" / "browser-use" / "2026-06-19_10-00-00",
        model="model-a",
        harness="browser-use",
        started_at="2026-06-19T10:00:00+00:00",
    )
    _write_results(
        tmp_path / "model-a" / "browser-use" / "2026-06-20_10-00-00",
        model="model-a",
        harness="browser-use",
        started_at="2026-06-20T10:00:00+00:00",
        success_rate=0.75,
        passed_tasks=3,
        failed_tasks=1,
        total_tasks=4,
    )
    _write_results(
        tmp_path / "model-a" / "hermes-ouroboros" / "2026-06-21_10-00-00",
        model="model-a",
        harness="hermes-ouroboros",
        started_at="2026-06-21T10:00:00+00:00",
        success_rate=1.0,
        passed_tasks=2,
        failed_tasks=0,
    )
    _write_results(
        tmp_path / "model-b" / "browser-use" / "2026-06-20_12-00-00",
        model="model-b",
        harness="browser-use",
        started_at="2026-06-20T12:00:00+00:00",
    )

    entries = discover_latest_runs(tmp_path)
    assert len(entries) == 3
    by_key = {(entry.model_dir, entry.harness): entry for entry in entries}
    assert by_key[("model-a", "browser-use")].run["success_rate"] == 0.75
    assert by_key[("model-a", "hermes-ouroboros")].run["success_rate"] == 1.0
    assert by_key[("model-b", "browser-use")].results_path.name == "results.json"


def test_render_aggregate_report_markdown(tmp_path, monkeypatch):
    from bench_eval.aggregate_report import discover_latest_runs, render_aggregate_report
    from bench_eval import llm_cost

    monkeypatch.setattr(
        llm_cost,
        "load_pricing_table",
        lambda refresh=False: {
            "model-a": {
                "input_cost_per_token": 0.000001,
                "output_cost_per_token": 0.0,
            },
            "model-b": {
                "input_cost_per_token": 0.000002,
                "output_cost_per_token": 0.0,
            },
        },
    )

    _write_results(
        tmp_path / "model-a" / "browser-use" / "2026-06-20_10-00-00",
        model="model-a",
        harness="browser-use",
        started_at="2026-06-20T10:00:00+00:00",
        success_rate=0.5,
        total_tasks=2,
        passed_tasks=1,
        failed_tasks=1,
    )
    _write_results(
        tmp_path / "model-b" / "browser-use" / "2026-06-20_11-00-00",
        model="model-b",
        harness="browser-use",
        started_at="2026-06-20T11:00:00+00:00",
        success_rate=1.0,
        total_tasks=2,
        passed_tasks=2,
        failed_tasks=0,
    )

    entries = discover_latest_runs(tmp_path)
    md = render_aggregate_report(
        entries,
        base_dir=tmp_path,
        report_path=tmp_path / "README.md",
        min_total_tasks=1,
    )
    assert "# Eval results: сводка по последним прогонам" in md
    assert "## Последний прогон каждой комбинации" in md
    assert "## Усреднение по harness" in md
    assert "## Усреднение по model" in md
    assert "`browser-use`" in md
    assert "`model-a`" in md
    assert "`model-b`" in md
    combo_section = md.split("## Последний прогон каждой комбинации", 1)[1].split("## Усреднение по harness", 1)[0]
    assert combo_section.index("`model-b`") < combo_section.index("`model-a`")
    assert "75.0%" in md
    assert "Стоимость" in md
    assert "$1.0000" in md
    assert "$2.0000" in md


def test_discover_latest_runs_skips_smoke_when_min_tasks_set(tmp_path):
    from bench_eval.aggregate_report import FULL_BENCH_MIN_TASKS, discover_latest_runs

    _write_results(
        tmp_path / "model-a" / "browser-use" / "2026-06-21_12-00-00",
        model="model-a",
        harness="browser-use",
        started_at="2026-06-21T12:00:00+00:00",
        total_tasks=1,
        passed_tasks=1,
        failed_tasks=0,
        success_rate=1.0,
    )
    _write_results(
        tmp_path / "model-a" / "browser-use" / "2026-06-20_10-00-00",
        model="model-a",
        harness="browser-use",
        started_at="2026-06-20T10:00:00+00:00",
        total_tasks=51,
        passed_tasks=40,
        failed_tasks=11,
        success_rate=40 / 51,
    )

    all_entries = discover_latest_runs(tmp_path)
    assert len(all_entries) == 1
    assert all_entries[0].total_tasks == 1

    full_entries = discover_latest_runs(tmp_path, min_total_tasks=FULL_BENCH_MIN_TASKS)
    assert len(full_entries) == 1
    assert full_entries[0].total_tasks == 51


def test_write_aggregate_report_excludes_smoke_from_aggregate_but_keeps_run_readmes(tmp_path):
    from bench_eval.aggregate_report import write_aggregate_report

    smoke_dir = tmp_path / "demo" / "browser-use" / "2026-06-21_12-00-00"
    full_dir = tmp_path / "demo" / "browser-use" / "2026-06-20_10-00-00"
    _write_results(
        smoke_dir,
        model="demo",
        harness="browser-use",
        started_at="2026-06-21T12:00:00+00:00",
        total_tasks=1,
        passed_tasks=1,
        failed_tasks=0,
        success_rate=1.0,
    )
    _write_results(
        full_dir,
        model="demo",
        harness="browser-use",
        started_at="2026-06-20T10:00:00+00:00",
        total_tasks=51,
        passed_tasks=45,
        failed_tasks=6,
        success_rate=45 / 51,
    )

    output = write_aggregate_report(tmp_path, write_run_reports=True)
    aggregate_text = output.read_text(encoding="utf-8")
    assert "51" in aggregate_text
    assert "smoke" in aggregate_text.lower() or "≥ 6" in aggregate_text
    assert (smoke_dir / "README.md").is_file()
    assert (full_dir / "README.md").is_file()


def test_write_results_archive_full_bench_layout(tmp_path):
    import zipfile

    from bench_eval.aggregate_report import (
        FULL_BENCH_MIN_TASKS,
        discover_latest_runs,
        write_aggregate_report,
        write_results_archive,
    )

    full_dir = tmp_path / "demo" / "browser-use" / "2026-06-20_10-00-00"
    _write_results(
        tmp_path / "demo" / "browser-use" / "2026-06-21_12-00-00",
        model="demo",
        harness="browser-use",
        started_at="2026-06-21T12:00:00+00:00",
        total_tasks=1,
        passed_tasks=1,
        failed_tasks=0,
        success_rate=1.0,
    )
    _write_results(
        full_dir,
        model="demo",
        harness="browser-use",
        started_at="2026-06-20T10:00:00+00:00",
        total_tasks=51,
        passed_tasks=45,
        failed_tasks=6,
        success_rate=45 / 51,
    )
    _write_results(
        tmp_path / "other" / "hermes-ouroboros" / "2026-06-20_11-00-00",
        model="other",
        harness="hermes-ouroboros",
        started_at="2026-06-20T11:00:00+00:00",
        total_tasks=51,
        passed_tasks=50,
        failed_tasks=1,
        success_rate=50 / 51,
    )

    aggregate_readme = write_aggregate_report(tmp_path, write_run_reports=True)
    entries = discover_latest_runs(tmp_path, min_total_tasks=FULL_BENCH_MIN_TASKS)
    zip_path = tmp_path / "results.zip"
    zip_path.write_bytes(b"PK\x05\x06" + b"\x00" * 18)
    old_mtime = zip_path.stat().st_mtime

    written = write_results_archive(
        entries,
        aggregate_readme=aggregate_readme,
        output_zip=zip_path,
    )
    assert written == zip_path
    assert zip_path.stat().st_mtime >= old_mtime

    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
    assert "README.md" in names
    assert "demo/browser-use/results.json" in names
    assert "demo/browser-use/README.md" in names
    assert "other/hermes-ouroboros/results.json" in names
    assert "other/hermes-ouroboros/README.md" in names
    assert "demo/browser-use/2026-06-21_12-00-00/results.json" not in names


def test_write_all_run_reports(tmp_path):
    from bench_eval.aggregate_report import write_all_run_reports

    tests = [
        {
            "test_name": "ok_task",
            "track_id": "ok_task",
            "success": True,
            "duration_seconds": 1.0,
            "agent_steps": 1,
            "agent_is_done": True,
            "dab_check": {"passed": 1, "total": 1},
        },
        {
            "test_name": "bad_task",
            "track_id": "bad_task",
            "success": False,
            "duration_seconds": 2.0,
            "agent_steps": 3,
            "agent_is_done": False,
            "dab_check": {"passed": 0, "total": 1, "failed_conditions": ["click"]},
            "agent_error": "timeout",
        },
    ]
    _write_results_with_tests(
        tmp_path / "demo" / "browser-use" / "2026-06-19_10-00-00",
        tests=tests,
    )
    _write_results_with_tests(
        tmp_path / "demo" / "browser-use" / "2026-06-20_10-00-00",
        tests=[tests[0]],
    )

    readmes = write_all_run_reports(tmp_path)
    assert len(readmes) == 2
    older = tmp_path / "demo" / "browser-use" / "2026-06-19_10-00-00" / "README.md"
    newer = tmp_path / "demo" / "browser-use" / "2026-06-20_10-00-00" / "README.md"
    assert older in readmes
    assert newer in readmes

    older_text = older.read_text(encoding="utf-8")
    assert "## Проваленные задачи" in older_text
    assert "`bad_task`" in older_text
    assert "timeout" in older_text
    assert "scripts/render_eval_aggregate.py" in older_text

    newer_text = newer.read_text(encoding="utf-8")
    assert "## Проваленные задачи" not in newer_text
    assert "Завершён" in newer_text


def test_write_aggregate_report_writes_per_run_readmes(tmp_path):
    from bench_eval.aggregate_report import write_aggregate_report

    _write_results(
        tmp_path / "demo" / "browser-use" / "2026-06-20_10-00-00",
        model="demo",
        harness="browser-use",
        started_at="2026-06-20T10:00:00+00:00",
    )

    output = write_aggregate_report(tmp_path, write_run_reports=True, min_total_tasks=1)
    assert output == tmp_path / "README.md"
    run_readme = tmp_path / "demo" / "browser-use" / "2026-06-20_10-00-00" / "README.md"
    assert run_readme.is_file()
    assert "# Eval run report: demo" in run_readme.read_text(encoding="utf-8")


def test_write_aggregate_report(tmp_path):
    from bench_eval.aggregate_report import write_aggregate_report

    _write_results(
        tmp_path / "demo" / "browser-use" / "2026-06-20_10-00-00",
        model="demo",
        harness="browser-use",
        started_at="2026-06-20T10:00:00+00:00",
    )

    output = write_aggregate_report(tmp_path, min_total_tasks=1)
    assert output == tmp_path / "README.md"
    assert output.is_file()
    text = output.read_text(encoding="utf-8")
    assert "demo" in text
    assert "## Efficiency metrics" in text

    results_path = tmp_path / "demo" / "browser-use" / "2026-06-20_10-00-00" / "results.json"
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    assert "extended_metrics" in payload["run"]
    assert payload.get("extended_metrics_meta", {}).get("schema_version") == 1
    assert payload["extended_metrics_meta"]["enriched_by"] == "render_eval_aggregate.py"


def _write_results_with_tests(run_dir: Path, *, tests: list[dict], **run_overrides) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    run = {
        "model": "demo",
        "agent_harness": "browser-use",
        "started_at": "2026-06-20T10:00:00+00:00",
        "finished": True,
        "total_tasks": len(tests),
        "passed_tasks": sum(1 for test in tests if test.get("success")),
        "failed_tasks": sum(1 for test in tests if not test.get("success")),
        "success_rate": 0.0,
        **run_overrides,
    }
    if run["total_tasks"]:
        run["success_rate"] = run["passed_tasks"] / run["total_tasks"]
    payload = {"run": run, "tests": tests}
    (run_dir / "results.json").write_text(json.dumps(payload), encoding="utf-8")


def test_extended_metrics_per_task_and_run():
    from bench_eval.extended_metrics import (
        compute_pass_at_k,
        compute_run_extended_metrics,
        compute_test_extended_metrics,
        enrich_results_payload,
    )

    test = {
        "success": True,
        "agent_is_done": True,
        "duration_seconds": 20.0,
        "token_usage": {
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "total_tokens": 1500,
            "llm_calls": 5,
        },
        "trajectory": {
            "agent": {
                "summary": {
                    "action_names": ["click", "click", "done"],
                }
            }
        },
    }
    extended = compute_test_extended_metrics(test)
    assert extended["token_efficiency"] == pytest.approx(1 / 1500)
    assert extended["avg_latency_seconds"] == pytest.approx(4.0)
    assert extended["action_redundancy"] == pytest.approx(1 / 3)
    assert extended["agent_dab_agreement"] is True
    assert extended["false_done"] is False

    run_metrics = compute_run_extended_metrics([test])
    assert run_metrics["avg_token_efficiency"] == pytest.approx(1 / 1500)
    assert run_metrics["agent_completion_rate"] == 1.0
    assert run_metrics["false_done_count"] == 0

    payload = enrich_results_payload({"run": {}, "tests": [test]})
    assert payload["tests"][0]["extended_metrics"]["token_efficiency"] == pytest.approx(1 / 1500)
    assert "enriched_at" in payload["run"]["extended_metrics"]

    pass_payloads = [
        {
            "run": {"output_dir": "run-1"},
            "tests": [
                {"test_name": "task_a", "success": True},
                {"test_name": "task_b", "success": False},
            ],
        },
        {
            "run": {"output_dir": "run-2"},
            "tests": [
                {"test_name": "task_a", "success": False},
                {"test_name": "task_b", "success": True},
            ],
        },
    ]
    pass_at_k = compute_pass_at_k(pass_payloads, k=1)
    assert pass_at_k is not None
    assert pass_at_k["run_count"] == 2
    assert pass_at_k["overall"] == pytest.approx(0.5)


def test_enrich_all_results_writes_pass_at_k(tmp_path):
    from bench_eval.aggregate_report import enrich_all_results

    tests = [{"test_name": "task_a", "success": True, "agent_is_done": True}]
    _write_results_with_tests(
        tmp_path / "demo" / "browser-use" / "2026-06-19_10-00-00",
        tests=tests,
        output_dir="run-1",
    )
    _write_results_with_tests(
        tmp_path / "demo" / "browser-use" / "2026-06-20_10-00-00",
        tests=[{"test_name": "task_a", "success": False, "agent_is_done": True}],
        output_dir="run-2",
    )

    enriched_paths = enrich_all_results(tmp_path, pass_at_k=1)
    assert len(enriched_paths) == 1
    latest = json.loads(enriched_paths[0].read_text(encoding="utf-8"))
    pass_at_k = latest["run"]["extended_metrics"]["pass_at_k"]
    assert pass_at_k["k"] == 1
    assert pass_at_k["overall"] == pytest.approx(0.5)
    assert latest["tests"][0]["extended_metrics"]["false_done"] is True
