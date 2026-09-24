"""Tests for liderboard export and loading."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LIDERBOARD_ROOT = _REPO_ROOT / "liderboard"
if str(_LIDERBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(_LIDERBOARD_ROOT))

from src.export_results import export_entry, export_latest_runs, export_results_file, main  # noqa: E402
from src.load_entries import load_entries, load_entry_file  # noqa: E402
from src.models import LeaderboardEntry, public_source_path  # noqa: E402


def _payload(model: str, harness: str, total_tasks: int, passed: int) -> dict:
    return {
        "run": {
            "model": model,
            "provider": "openrouter",
            "agent_harness": harness,
            "mock": "bench",
            "finished": True,
            "total_tasks": total_tasks,
            "passed_tasks": passed,
            "failed_tasks": total_tasks - passed,
            "success_rate": passed / total_tasks if total_tasks else 0.0,
            "avg_duration_seconds": 120.0,
            "total_duration_seconds": 6120.0,
            "total_agent_steps": 612,
            "avg_agent_steps": 12.0,
            "avg_tokens_per_task": 1500.0,
            "total_tokens": total_tasks * 1500,
        },
        "ui_taxonomy_stats": {
            "by_primary": {
                "BASKET": {"success_rate": 0.8, "total": 10, "passed": 8, "failed": 2},
            }
        },
        "tests": [
            {
                "test_name": "ecommerce_basket_named_product",
                "success": passed > 0,
                "ui_taxonomy": {"domain": "shop"},
            }
        ],
    }


def test_export_entry_uses_run_success_rate():
    entry = export_entry(_payload("demo-model", "browser-use", 51, 40))
    assert entry.model == "demo-model"
    assert entry.harness == "browser-use"
    assert entry.success_rate == pytest.approx(40 / 51)
    assert entry.total_tasks == 51
    assert entry.total_duration_seconds == pytest.approx(6120.0)
    assert entry.total_agent_steps == 612
    assert "shop" in entry.sections
    assert entry.ui_badges == ["BASKET"]
    assert "metrics" in entry.to_json()


def test_public_source_path_drops_local_disk_paths():
    assert public_source_path(r"C:\Users\Lenovo\work\WebPageBench\tmp\results\eval_final\x\results.json") is None
    assert public_source_path("/home/jovyan/WebPageBench/tests/eval/x/results.json") is None
    assert public_source_path("results/raw/google_gemini-3.8-flash__openmanus/results.json") == (
        "results/raw/google_gemini-3.8-flash__openmanus/results.json"
    )
    entry = LeaderboardEntry(
        model="demo",
        harness="browser-use",
        source_path=r"C:\Users\Lenovo\work\WebPageBench\tmp\foo.json",
    )
    assert entry.to_json()["source_path"] is None


def test_export_latest_runs_skips_smoke_and_preserves_existing_output(tmp_path, monkeypatch):
    monkeypatch.chdir(_REPO_ROOT)

    def write_run(model: str, harness: str, run_name: str, total_tasks: int, passed: int) -> Path:
        run_dir = tmp_path / model.replace("/", "_") / harness / run_name
        run_dir.mkdir(parents=True)
        path = run_dir / "results.json"
        path.write_text(json.dumps(_payload(model, harness, total_tasks, passed)), encoding="utf-8")
        return path

    write_run("demo-model", "browser-use", "2026-06-20_10-00-00", 5, 5)
    write_run("demo-model", "browser-use", "2026-06-21_10-00-00", 51, 40)
    write_run("other-model", "ouroboros-cut", "2026-06-21_11-00-00", 51, 30)
    stale = tmp_path / "output" / "stale.json"
    stale.parent.mkdir(parents=True)
    stale.write_text("{}", encoding="utf-8")

    out_dir = tmp_path / "output"
    written = export_latest_runs(tmp_path, output_dir=out_dir, min_total_tasks=6)
    assert len(written) == 2
    assert stale.exists()
    loaded = load_entry_file(written[0])
    assert isinstance(loaded, LeaderboardEntry)
    assert loaded.success_rate is not None


def test_export_latest_runs_replace_all_removes_existing_output(tmp_path, monkeypatch):
    monkeypatch.chdir(_REPO_ROOT)
    run_dir = tmp_path / "demo-model" / "browser-use" / "2026-06-21_10-00-00"
    run_dir.mkdir(parents=True)
    (run_dir / "results.json").write_text(
        json.dumps(_payload("demo-model", "browser-use", 51, 40)),
        encoding="utf-8",
    )
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    stale = out_dir / "stale.json"
    stale.write_text("{}\n", encoding="utf-8")

    written = export_latest_runs(
        tmp_path,
        output_dir=out_dir,
        min_total_tasks=6,
        replace_all=True,
    )

    assert len(written) == 1
    assert not stale.exists()


def test_success_rate_matches_task_fraction():
    entry = export_entry(_payload("demo-model", "browser-use", 51, 30))
    assert entry.passed_tasks == 30
    assert entry.total_tasks == 51
    assert entry.success_rate == pytest.approx(30 / 51)
    assert entry.success_pct == pytest.approx(round(30 / 51 * 100, 2))


def test_export_copies_raw_results(tmp_path, monkeypatch):
    monkeypatch.chdir(_REPO_ROOT)
    payload = _payload("raw-model", "browser-use", 51, 40)
    results_path = tmp_path / "results.json"
    results_path.write_text(json.dumps(payload), encoding="utf-8")
    out_dir = tmp_path / "results"
    export_results_file(results_path, output_dir=out_dir)
    summary = load_entry_file(out_dir / "raw-model__browser-use.json")
    assert summary is not None
    raw_path = tmp_path / "results" / "raw" / summary.entry_id / "results.json"
    assert raw_path.is_file()
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    assert raw["run"]["model"] == "raw-model"
    assert summary.raw_results_path == f"results/raw/{summary.entry_id}/results.json"
    assert summary.source_path is None


def test_results_json_cli_adds_submission_without_cleaning_output(tmp_path, monkeypatch):
    payload = _payload("submit-model", "browser-use", 152, 100)
    results_path = tmp_path / "run" / "results.json"
    results_path.parent.mkdir(parents=True)
    results_path.write_text(json.dumps(payload), encoding="utf-8")

    out_dir = tmp_path / "leaderboard" / "results"
    out_dir.mkdir(parents=True)
    existing = out_dir / "existing-model__browser-use.json"
    existing.write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "export_results.py",
            "--results-json",
            str(results_path),
            "--output-dir",
            str(out_dir),
            "--require-finished",
        ],
    )
    main()

    assert existing.read_text(encoding="utf-8") == "{}\n"
    assert (out_dir / "submit-model__browser-use.json").is_file()
    assert (out_dir / "raw" / "submit-model__browser-use" / "results.json").is_file()


def test_load_entries_ignores_legacy_files(tmp_path):
    legacy = {
        "model": "legacy/model",
        "harness": "browser-use",
        "total_score": 0.5,
        "shop": {"ecommerce_basket_named_product": 1.0},
    }
    (tmp_path / "legacy.json").write_text(json.dumps(legacy), encoding="utf-8")
    assert load_entries(tmp_path) == []


def test_backfill_summary_total_duration(tmp_path, monkeypatch):
    monkeypatch.chdir(_REPO_ROOT)
    from src.export_results import backfill_summary_total_duration, export_results_file

    payload = _payload("dur-model", "browser-use", 51, 40)
    payload["run"]["total_duration_seconds"] = 9999.0
    results_path = tmp_path / "source" / "results.json"
    results_path.parent.mkdir(parents=True)
    results_path.write_text(json.dumps(payload), encoding="utf-8")
    out_dir = tmp_path / "results"
    export_results_file(results_path, output_dir=out_dir)

    summary_path = out_dir / "dur-model__browser-use.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    del summary["metrics"]["total_duration_seconds"]
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    assert backfill_summary_total_duration(out_dir) == 1
    restored = json.loads(summary_path.read_text(encoding="utf-8"))
    assert restored["metrics"]["total_duration_seconds"] == pytest.approx(9999.0)


def test_backfill_summary_ui_classes(tmp_path, monkeypatch):
    monkeypatch.chdir(_REPO_ROOT)
    from src.export_results import backfill_summary_ui_classes, export_results_file

    payload = _payload("ui-model", "browser-use", 51, 40)
    results_path = tmp_path / "source" / "results.json"
    results_path.parent.mkdir(parents=True)
    results_path.write_text(json.dumps(payload), encoding="utf-8")
    out_dir = tmp_path / "results"
    export_results_file(results_path, output_dir=out_dir)

    summary_path = out_dir / "ui-model__browser-use.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    del summary["ui_classes"]
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    assert backfill_summary_ui_classes(out_dir) == 1
    restored = json.loads(summary_path.read_text(encoding="utf-8"))
    assert restored["ui_classes"]["BASKET"]["passed"] == 8


def test_export_entry_costs_ouroboros_unknown_usage_bucket():
    payload = {
        "run": {
            "model": "deepseek/deepseek-v4-flash",
            "provider": "openrouter",
            "agent_harness": "ouroboros-full-isolated",
            "mock": "bench",
            "finished": True,
            "total_tasks": 1,
            "passed_tasks": 1,
            "failed_tasks": 0,
            "success_rate": 1.0,
            "ouroboros_model_slots": {
                "main": ["deepseek/deepseek-v4-flash"],
                "review": ["google/gemini-2.5-flash"],
            },
            "token_usage_by_model": {
                "unknown": {
                    "prompt_tokens": 1_000_000,
                    "completion_tokens": 100_000,
                    "total_tokens": 1_100_000,
                    "llm_calls": 10,
                    "cost_usd": 0.42,
                }
            },
        },
        "tests": [
            {
                "test_name": "ecommerce_basket_named_product",
                "success": True,
                "token_usage_by_model": {
                    "unknown": {
                        "prompt_tokens": 1_000_000,
                        "completion_tokens": 100_000,
                        "cost_usd": 0.42,
                    }
                },
            }
        ],
    }
    entry = export_entry(payload)
    assert entry.total_cost_usd == pytest.approx(0.42)
    assert entry.avg_cost_per_task_usd == pytest.approx(0.42)


def test_load_entry_file_backfills_missing_cost_from_raw(tmp_path, monkeypatch):
    monkeypatch.chdir(_REPO_ROOT)
    payload = {
        "run": {
            "model": "deepseek/deepseek-v4-flash",
            "provider": "openrouter",
            "agent_harness": "ouroboros-full-isolated",
            "mock": "bench",
            "finished": True,
            "total_tasks": 1,
            "passed_tasks": 1,
            "failed_tasks": 0,
            "success_rate": 1.0,
            "token_usage_by_model": {
                "unknown": {
                    "prompt_tokens": 1_000_000,
                    "completion_tokens": 0,
                    "cost_usd": 0.25,
                }
            },
        },
        "tests": [],
    }
    entry = export_entry(payload)
    entry.total_cost_usd = None
    entry.avg_cost_per_task_usd = None
    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True)
    raw_dir = results_dir / "raw" / entry.entry_id
    raw_dir.mkdir(parents=True)
    raw_path = raw_dir / "results.json"
    raw_path.write_text(json.dumps(payload), encoding="utf-8")
    entry.raw_results_path = f"results/raw/{entry.entry_id}/results.json"
    summary_path = results_dir / f"{entry.entry_id}.json"
    summary_path.write_text(json.dumps(entry.to_json()), encoding="utf-8")

    loaded = load_entry_file(summary_path)
    assert loaded is not None
    assert loaded.total_cost_usd == pytest.approx(0.25)
    assert loaded.avg_cost_per_task_usd == pytest.approx(0.25)
