"""Export latest eval results.json into liderboard/results/ (leaderboard feed)."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from src.bench_config import load_bench_config
from src.models import LeaderboardEntry, SectionStats, reconcile_success_metrics
from src.token_display import compact_token_usage_by_model, token_usage_from_run


def _sanitize_name(value: str) -> str:
    safe = re.sub(r"[^\w.\-]+", "_", value.strip())
    return safe or "unknown"


def _space_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _repo_root() -> Path:
    return _space_root().parent


def _ensure_repo_on_path() -> Path:
    root = _repo_root()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root


def _domain_for_test(test: dict[str, Any], config: dict[str, Any]) -> str | None:
    ui = test.get("ui_taxonomy") or {}
    domain = ui.get("domain")
    if domain:
        domain = str(domain)
        return "files" if domain == "gov" else domain
    patterns = ui.get("ui_patterns") or {}
    if patterns.get("domain"):
        domain = str(patterns["domain"])
        return "files" if domain == "gov" else domain
    name = test.get("test_name") or ""
    for section_id, meta in config["sections"].items():
        for task in meta["tasks"]:
            if task == name:
                return section_id
    if name.startswith("bench_hub"):
        return "hub"
    if name.startswith("digital_books"):
        return "books"
    if name.startswith("grocery") or name.startswith("bench_grocery"):
        return "grocery"
    if name.startswith("hotel"):
        return "hotels"
    if name.startswith("files"):
        return "files"
    if name.startswith("government"):
        return "files"
    if name.startswith("rail"):
        return "rail"
    if name.startswith("ecommerce"):
        return "shop"
    return None


def _section_avg_rate(sections: dict[str, SectionStats]) -> float | None:
    rates = [stats.success_rate for stats in sections.values() if stats.success_rate is not None]
    return (sum(rates) / len(rates)) if rates else None


def raw_results_path_for(entry: LeaderboardEntry, root: Path | None = None) -> Path:
    base = (root or _space_root()) / "results" / "raw"
    return base / entry.entry_id / "results.json"


def _ui_classes(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    stats = payload.get("ui_taxonomy_stats") or {}
    by_primary = stats.get("by_primary") or {}
    classes: dict[str, dict[str, Any]] = {}
    for class_id, row in by_primary.items():
        if not isinstance(row, dict):
            continue
        classes[str(class_id)] = {
            "success_rate": row.get("success_rate"),
            "passed": row.get("passed"),
            "total": row.get("total"),
            "failed": row.get("failed"),
        }
    return classes


ui_classes_from_payload = _ui_classes


def _ui_badges(payload: dict[str, Any], limit: int = 4) -> list[str]:
    stats = payload.get("ui_taxonomy_stats") or {}
    by_primary = stats.get("by_primary") or {}
    ranked: list[tuple[float, str]] = []
    for class_id, row in by_primary.items():
        if not isinstance(row, dict):
            continue
        rate = row.get("success_rate")
        if isinstance(rate, (int, float)):
            ranked.append((float(rate), str(class_id)))
    ranked.sort(reverse=True)
    return [class_id for _, class_id in ranked[:limit]]


def _cost_from_payload(payload: dict[str, Any]) -> tuple[float | None, float | None]:
    recorded = _recorded_cost_from_payload(payload)
    if recorded is not None:
        return recorded
    _ensure_repo_on_path()
    try:
        from bench_eval.llm_cost import compute_results_cost

        cost = compute_results_cost(payload)
        return cost.total_cost_usd, cost.avg_cost_per_task_usd
    except Exception:
        return None, None


def _recorded_cost_from_payload(payload: dict[str, Any]) -> tuple[float | None, float | None] | None:
    """Fast path: sum recorded cost_usd without fetching pricing tables."""
    run = payload.get("run") or {}
    tests = payload.get("tests") or []
    total_tasks = int(run.get("total_tasks") or len(tests) or 0)
    by_model = run.get("token_usage_by_model")
    if isinstance(by_model, dict) and by_model:
        total = 0.0
        priced = False
        for usage in by_model.values():
            if not isinstance(usage, dict):
                continue
            cost = usage.get("cost_usd")
            if isinstance(cost, (int, float)) and float(cost) > 0:
                total += float(cost)
                priced = True
        if priced:
            avg = (total / total_tasks) if total_tasks else None
            return total, avg

    for key in ("total_cost_usd", "total_cost", "cost_usd", "cost"):
        value = run.get(key)
        if isinstance(value, (int, float)) and float(value) > 0:
            total = float(value)
            avg = (total / total_tasks) if total_tasks else None
            return total, avg
    return None


def _needs_cost_backfill(entry: LeaderboardEntry) -> bool:
    return entry.total_cost_usd is None or entry.total_cost_usd <= 0


def backfill_summary_costs(results_dir: Path | None = None) -> int:
    """Recompute total_cost_usd in summary JSON from raw results when missing."""
    root = results_dir or (_space_root() / "results")
    if not root.is_dir():
        return 0
    updated = 0
    for path in sorted(root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "metrics" not in payload:
            continue
        entry = LeaderboardEntry.from_json(payload)
        if not _needs_cost_backfill(entry):
            continue
        raw_path = raw_results_path_for(entry, root.parent)
        if not raw_path.is_file() and entry.raw_results_path:
            raw_path = root.parent / entry.raw_results_path
        if not raw_path.is_file():
            continue
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        total_cost, avg_cost = _cost_from_payload(raw)
        if total_cost is None or total_cost <= 0:
            continue
        metrics = dict(payload.get("metrics") or {})
        metrics["total_cost_usd"] = total_cost
        metrics["avg_cost_per_task_usd"] = avg_cost
        payload["metrics"] = metrics
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        updated += 1
    return updated


def _total_agent_steps_from_payload(payload: dict[str, Any]) -> int | None:
    run = payload.get("run") or {}
    total = run.get("total_agent_steps")
    if isinstance(total, int):
        return total
    if isinstance(total, float):
        return int(total)
    tests = payload.get("tests") or []
    steps = [row["agent_steps"] for row in tests if isinstance(row.get("agent_steps"), int)]
    return sum(steps) if steps else None


def export_entry(payload: dict[str, Any], *, source_path: str | None = None) -> LeaderboardEntry:
    config = load_bench_config()
    run = payload.get("run") or {}
    tests = payload.get("tests") or []

    by_section: dict[str, dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))
    for test in tests:
        section_id = _domain_for_test(test, config)
        if section_id == "gov":
            section_id = "files"
        if not section_id:
            continue
        task = test.get("test_name") or "unknown"
        by_section[section_id][task].append(bool(test.get("success")))

    sections: dict[str, SectionStats] = {}
    for section_id, meta in config["sections"].items():
        task_map = by_section.get(section_id, {})
        tasks: dict[str, bool] = {}
        for task in meta["tasks"]:
            values = task_map.get(task)
            if values:
                tasks[task] = sum(values) / len(values) >= 0.5
        passed = sum(1 for ok in tasks.values() if ok)
        total = len(tasks)
        success_rate = (passed / total) if total else None
        sections[section_id] = SectionStats(
            section_id=section_id,
            label=meta["label"],
            success_rate=success_rate,
            passed=passed,
            total=total,
            tasks=tasks,
        )

    extended = run.get("extended_metrics") if isinstance(run.get("extended_metrics"), dict) else {}
    pass_at_k = extended.get("pass_at_k")
    pass_overall = pass_at_k.get("overall") if isinstance(pass_at_k, dict) else None
    total_cost, avg_cost = _cost_from_payload(payload)

    entry = LeaderboardEntry(
        model=str(run.get("model") or "unknown"),
        harness=str(run.get("agent_harness") or run.get("harness") or "unknown"),
        provider=run.get("provider"),
        mock=run.get("mock"),
        finished=bool(run.get("finished", True)),
        source_path=source_path,
        submitted_at=run.get("finished_at") or run.get("started_at"),
        success_rate=run.get("success_rate"),
        passed_tasks=int(run.get("passed_tasks") or 0),
        failed_tasks=int(run.get("failed_tasks") or 0),
        total_tasks=int(run.get("total_tasks") or 0),
        avg_duration_seconds=run.get("avg_duration_seconds"),
        total_duration_seconds=run.get("total_duration_seconds"),
        total_agent_steps=_total_agent_steps_from_payload(payload),
        avg_agent_steps=run.get("avg_agent_steps"),
        avg_tokens_per_task=run.get("avg_tokens_per_task"),
        total_tokens=run.get("total_tokens"),
        total_cost_usd=total_cost,
        avg_cost_per_task_usd=avg_cost,
        token_usage_by_model=token_usage_from_run(run),
        ouroboros_model_slots={
            str(slot): [str(model) for model in models]
            for slot, models in (run.get("ouroboros_model_slots") or {}).items()
            if isinstance(models, list) and models
        },
        pass_at_k=float(pass_overall) if isinstance(pass_overall, (int, float)) else None,
        agent_completion_rate=extended.get("agent_completion_rate"),
        agent_dab_agreement_rate=extended.get("agent_dab_agreement_rate"),
        sections=sections,
        ui_badges=_ui_badges(payload),
        ui_classes=_ui_classes(payload),
        section_avg_rate=_section_avg_rate(sections),
    )
    reconcile_success_metrics(entry)
    return entry


def default_output_path(entry: LeaderboardEntry, output_dir: Path) -> Path:
    model = _sanitize_name(entry.model)
    harness = _sanitize_name(entry.harness)
    return output_dir / f"{model}__{harness}.json"


def clean_results_dir(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for child in output_dir.iterdir():
        if child.name == ".gitkeep":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def export_results_file(
    results_json: Path,
    *,
    output_dir: Path,
) -> Path:
    payload = json.loads(results_json.read_text(encoding="utf-8"))
    if not payload.get("run"):
        raise ValueError(f"Not an eval results.json (missing run block): {results_json}")
    entry = export_entry(payload)
    raw_path = raw_results_path_for(entry, output_dir.parent)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(results_json, raw_path)
    entry.raw_results_path = raw_path.relative_to(output_dir.parent).as_posix()
    target = default_output_path(entry, output_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(entry.to_json(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {target}  ({results_json})")
    return target


def export_latest_runs(
    base_dir: Path,
    *,
    output_dir: Path,
    require_finished: bool = False,
    min_total_tasks: int | None = None,
    replace_all: bool = False,
) -> list[Path]:
    _ensure_repo_on_path()
    from bench_eval.aggregate_report import discover_latest_runs

    discovered = discover_latest_runs(
        base_dir,
        require_finished=require_finished,
        min_total_tasks=min_total_tasks,
    )
    if replace_all:
        clean_results_dir(output_dir)
    else:
        output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for item in discovered:
        written.append(export_results_file(item.results_path, output_dir=output_dir))
    return written


def backfill_summary_total_agent_steps(results_dir: Path | None = None) -> int:
    """Add total_agent_steps to summary JSON from copied raw results when missing."""
    root = results_dir or (_space_root() / "results")
    if not root.is_dir():
        return 0
    updated = 0
    for path in sorted(root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "metrics" not in payload:
            continue
        metrics = dict(payload.get("metrics") or {})
        if metrics.get("total_agent_steps") is not None:
            continue
        entry = LeaderboardEntry.from_json(payload)
        raw_path = raw_results_path_for(entry, root.parent)
        if not raw_path.is_file() and entry.raw_results_path:
            raw_path = root.parent / entry.raw_results_path
        if not raw_path.is_file():
            continue
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        total_steps = _total_agent_steps_from_payload(raw)
        if total_steps is None:
            continue
        metrics["total_agent_steps"] = total_steps
        payload["metrics"] = metrics
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        updated += 1
    return updated


def backfill_summary_total_duration(results_dir: Path | None = None) -> int:
    """Add total_duration_seconds to summary JSON from copied raw results when missing."""
    root = results_dir or (_space_root() / "results")
    if not root.is_dir():
        return 0
    updated = 0
    for path in sorted(root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "metrics" not in payload:
            continue
        metrics = dict(payload.get("metrics") or {})
        if metrics.get("total_duration_seconds") is not None:
            continue
        entry = LeaderboardEntry.from_json(payload)
        raw_path = raw_results_path_for(entry, root.parent)
        if not raw_path.is_file() and entry.raw_results_path:
            raw_path = root.parent / entry.raw_results_path
        if not raw_path.is_file():
            continue
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        run = raw.get("run") or {}
        total_duration = run.get("total_duration_seconds")
        if not isinstance(total_duration, (int, float)):
            continue
        metrics["total_duration_seconds"] = float(total_duration)
        payload["metrics"] = metrics
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        updated += 1
    return updated


def backfill_summary_ui_classes(results_dir: Path | None = None) -> int:
    """Write ui_classes into summary JSON from raw results when missing."""
    root = results_dir or (_space_root() / "results")
    if not root.is_dir():
        return 0
    updated = 0
    for path in sorted(root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("ui_classes"):
            continue
        if "metrics" not in payload:
            continue
        entry = LeaderboardEntry.from_json(payload)
        raw_path = raw_results_path_for(entry, root.parent)
        if not raw_path.is_file() and entry.raw_results_path:
            raw_path = root.parent / entry.raw_results_path
        if not raw_path.is_file():
            continue
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        classes = _ui_classes(raw)
        if not classes:
            continue
        entry.ui_classes = classes
        path.write_text(json.dumps(entry.to_json(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        updated += 1
    return updated


def main() -> None:
    _ensure_repo_on_path()
    from bench_eval.aggregate_report import FULL_BENCH_MIN_TASKS, discover_latest_runs

    parser = argparse.ArgumentParser(
        description=(
            "Export latest eval results.json for every harness × model "
            "into liderboard/results/ (summary + copied raw results.json)"
        ),
    )
    parser.add_argument(
        "--base-dir",
        default=os.getenv("EVAL_RESULTS_BASE_DIR", "tests/eval"),
        help="Base directory with eval runs (default: tests/eval)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Leaderboard results directory (default: liderboard/results)",
    )
    parser.add_argument(
        "--results-json",
        action="append",
        default=[],
        metavar="PATH",
        help=(
            "Export one results.json without deleting other leaderboard entries. "
            "May be repeated; intended for pull-request submissions."
        ),
    )
    parser.add_argument(
        "--replace-all",
        action="store_true",
        help=(
            "Delete existing leaderboard entries before exporting discovered runs. "
            "By default existing entries are preserved."
        ),
    )
    parser.add_argument(
        "--require-finished",
        action="store_true",
        help="Skip combinations whose latest run has finished=false",
    )
    parser.add_argument(
        "--min-tasks-for-aggregate",
        type=int,
        default=FULL_BENCH_MIN_TASKS,
        metavar="N",
        help=(
            "Include only runs with at least N tasks "
            f"(default: {FULL_BENCH_MIN_TASKS}, i.e. full bench; smoke runs excluded). "
            "Use 0 to include all runs."
        ),
    )
    parser.add_argument(
        "--backfill-ui-classes",
        action="store_true",
        help="Add ui_classes to existing summary JSON from copied raw results.json",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print discovered harness × model paths and exit without writing results",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    if not base_dir.is_absolute():
        base_dir = _repo_root() / base_dir
    min_total_tasks = args.min_tasks_for_aggregate or None
    output_dir = Path(args.output_dir) if args.output_dir else _space_root() / "results"

    if args.results_json:
        if args.backfill_ui_classes or args.list or args.replace_all:
            parser.error(
                "--results-json cannot be combined with --backfill-ui-classes, "
                "--list, or --replace-all"
            )
        written: list[Path] = []
        for raw_path in args.results_json:
            results_path = Path(raw_path)
            if not results_path.is_absolute():
                results_path = _repo_root() / results_path
            payload = json.loads(results_path.read_text(encoding="utf-8"))
            run = payload.get("run") or {}
            if args.require_finished and not bool(run.get("finished", True)):
                parser.error(f"run is not finished: {results_path}")
            total_tasks = int(run.get("total_tasks") or 0)
            if min_total_tasks is not None and total_tasks < min_total_tasks:
                parser.error(
                    f"run has {total_tasks} tasks; at least {min_total_tasks} required: {results_path}"
                )
            written.append(export_results_file(results_path, output_dir=output_dir))
        print(f"Exported {len(written)} submission(s) to {output_dir}")
        return

    if args.backfill_ui_classes:
        count = backfill_summary_ui_classes(output_dir)
        print(f"Backfilled ui_classes in {count} summary file(s) under {output_dir}")
        return

    if args.list:
        discovered = discover_latest_runs(
            base_dir,
            require_finished=args.require_finished,
            min_total_tasks=min_total_tasks,
        )
        if not discovered:
            print(f"No results under {base_dir}")
            raise SystemExit(1)
        for item in sorted(discovered, key=lambda row: (row.harness, row.model_dir)):
            status = "finished" if item.finished else "unfinished"
            print(f"{item.harness}\t{item.model}\t{status}\t{item.results_path}")
        return

    written = export_latest_runs(
        base_dir,
        output_dir=output_dir,
        require_finished=args.require_finished,
        min_total_tasks=min_total_tasks,
        replace_all=args.replace_all,
    )
    if not written:
        print(f"No runs exported from {base_dir} (min_tasks={min_total_tasks})")
        raise SystemExit(1)
    print(f"Exported {len(written)} harness × model combination(s) to {output_dir}")


if __name__ == "__main__":
    main()
