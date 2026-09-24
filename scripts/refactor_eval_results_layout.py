#!/usr/bin/env python3
"""Move legacy eval runs from tests/eval/<model>/<timestamp>/ to tests/eval/<model>/<harness>/<date>/."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.harness_names import normalize_harness_name  # noqa: E402
from bench_eval.results import (  # noqa: E402
    _LEGACY_RUN_DIR_PATTERN,
    _RUN_DATE_DIR_PATTERN,
    format_run_timestamp,
    is_run_directory_name,
    parse_run_dir_timestamp,
    sanitize_model_name,
)


def _parse_started_at(run_dir: Path, payload: dict | None) -> datetime:
    if payload:
        run = payload.get("run") or {}
        started_raw = run.get("started_at")
        if started_raw:
            try:
                return datetime.fromisoformat(str(started_raw).replace("Z", "+00:00"))
            except ValueError:
                pass

    name = run_dir.name
    parsed = parse_run_dir_timestamp(name)
    if parsed is not None:
        return parsed
    if _RUN_DATE_DIR_PATTERN.match(name) and len(name) == 10:
        return datetime.strptime(name, "%Y-%m-%d")
    return datetime.fromtimestamp(run_dir.stat().st_mtime)


def _read_results(run_dir: Path) -> dict | None:
    results_path = run_dir / "results.json"
    if not results_path.is_file():
        return None
    try:
        return json.loads(results_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _resolve_harness(run_dir: Path, payload: dict | None, fallback: str) -> str:
    if payload:
        run = payload.get("run") or {}
        harness = run.get("agent_harness")
        if harness:
            return normalize_harness_name(str(harness))
        tests = payload.get("tests") or []
        for row in tests:
            test_harness = row.get("agent_harness")
            if test_harness:
                return normalize_harness_name(str(test_harness))
    return normalize_harness_name(fallback)


def _target_directory(
    base_dir: Path,
    *,
    model: str,
    harness: str,
    started_at: datetime,
) -> Path:
    parent = base_dir / sanitize_model_name(model) / normalize_harness_name(harness)
    timestamp_dir = parent / format_run_timestamp(started_at)
    if not timestamp_dir.exists():
        return timestamp_dir
    suffix = 1
    while True:
        candidate = parent / f"{format_run_timestamp(started_at)}_{suffix}"
        if not candidate.exists():
            return candidate
        suffix += 1


def _is_legacy_run_dir(path: Path) -> bool:
    return path.is_dir() and _LEGACY_RUN_DIR_PATTERN.match(path.name) is not None


def discover_legacy_runs(base_dir: Path) -> list[Path]:
    if not base_dir.is_dir():
        return []

    legacy_dirs: list[Path] = []
    for model_dir in sorted(base_dir.iterdir()):
        if not model_dir.is_dir():
            continue
        for child in model_dir.iterdir():
            if _is_legacy_run_dir(child):
                legacy_dirs.append(child)
    return legacy_dirs


def plan_moves(
    base_dir: Path,
    *,
    default_harness: str,
) -> list[tuple[Path, Path, str]]:
    plans: list[tuple[Path, Path, str]] = []
    for run_dir in discover_legacy_runs(base_dir):
        payload = _read_results(run_dir)
        model = (payload or {}).get("run", {}).get("model") or run_dir.parent.name
        harness = _resolve_harness(run_dir, payload, default_harness)
        started_at = _parse_started_at(run_dir, payload)
        target = _target_directory(
            base_dir,
            model=str(model),
            harness=harness,
            started_at=started_at,
        )
        plans.append((run_dir, target, harness))
    return plans


def _update_result_paths(payload: dict, target: Path) -> dict:
    run = payload.setdefault("run", {})
    run["output_dir"] = str(target)
    run["dataset_path"] = str(target / "dataset.json")
    run["results_path"] = str(target / "results.json")
    if run.get("agent_harness"):
        run["agent_harness"] = normalize_harness_name(str(run["agent_harness"]))
    parallel = run.get("parallel") or {}
    worker_files = parallel.get("worker_result_files") or []
    if worker_files:
        parallel["worker_result_files"] = [
            str(target / Path(path).name) for path in worker_files
        ]
        run["parallel"] = parallel
    return payload


def _relocate_run(source: Path, target: Path, *, dry_run: bool) -> None:
    if source.resolve() == target.resolve():
        return
    if target.exists():
        raise FileExistsError(f"Target already exists: {target}")

    if dry_run:
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(target))

    results_path = target / "results.json"
    if results_path.is_file():
        payload = json.loads(results_path.read_text(encoding="utf-8"))
        payload = _update_result_paths(payload, target)
        results_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    readme_path = target / "README.md"
    if readme_path.is_file():
        text = readme_path.read_text(encoding="utf-8")
        text = text.replace(str(source), str(target))
        readme_path.write_text(text, encoding="utf-8")


def refactor_layout(
    base_dir: Path,
    *,
    default_harness: str = "browser-use",
    dry_run: bool = False,
) -> list[tuple[Path, Path]]:
    moved: list[tuple[Path, Path]] = []
    for source, target, harness in plan_moves(base_dir, default_harness=default_harness):
        if source.resolve() == target.resolve():
            continue
        print(f"{source} -> {target}  (harness={harness})")
        _relocate_run(source, target, dry_run=dry_run)
        moved.append((source, target))
    return moved


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Refactor eval result directories from legacy layout "
            "tests/eval/<model>/<timestamp>/ to "
            "tests/eval/<model>/<harness>/<date>/."
        ),
    )
    parser.add_argument(
        "--base-dir",
        default=os.getenv("EVAL_RESULTS_BASE_DIR", "tests/eval"),
        help="Base directory with eval runs (default: tests/eval)",
    )
    parser.add_argument(
        "--default-harness",
        default=os.getenv("AGENT_HARNESS", "browser-use"),
        help="Harness name when results.json has no agent_harness field",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned moves without changing the filesystem",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    if not base_dir.is_dir():
        parser.error(f"Base directory not found: {base_dir}")

    moves = refactor_layout(
        base_dir,
        default_harness=args.default_harness,
        dry_run=args.dry_run,
    )
    if not moves:
        print(f"No legacy runs found under {base_dir}")
        return

    action = "Would move" if args.dry_run else "Moved"
    print(f"\n{action} {len(moves)} run(s).")


if __name__ == "__main__":
    main()
