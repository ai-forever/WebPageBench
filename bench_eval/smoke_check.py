"""Verify latest local evaluation artifacts for smoke matrices."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from bench_eval.harness_names import normalize_harness_name
from bench_eval.results import is_run_directory_name, sanitize_model_name
from bench_eval.run_report import find_latest_results


def _repo_root(repo_root: Path | None = None) -> Path:
    if repo_root is not None:
        return repo_root
    raw = os.getenv("AGENT_BENCH_ROOT", "").strip()
    if raw:
        path = Path(raw).expanduser()
        if path.is_dir():
            return path
    return Path(__file__).resolve().parents[1]


def resolve_model_results_dir_name(
    model: str,
    *,
    repo_root: Path | None = None,
) -> str:
    """Map notebook model key to tests/eval/<dir> (uses envs/models/*.env LLM_MODEL)."""
    short = model.strip()
    env_file = _repo_root(repo_root) / "envs" / "models" / f"{short}.env"
    if env_file.is_file():
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "LLM_MODEL":
                llm_model = value.strip().strip('"').strip("'")
                if llm_model:
                    return sanitize_model_name(llm_model)
    return sanitize_model_name(short)


@dataclass
class SmokeRunCheck:
    harness: str
    model: str
    status: str
    results_path: Path | None = None
    run_dir: Path | None = None
    total_tasks: int = 0
    passed_tasks: int = 0
    failed_tasks: int = 0
    finished: bool = False
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def _load_run_payload(results_path: Path) -> dict[str, Any]:
    return json.loads(results_path.read_text(encoding="utf-8"))


def canonical_bench_task_count(*, repo_root: Path | None = None) -> int:
    """Number of JSON tasks in ``tests/bench/tasks`` (152 in the current canon)."""
    tasks_dir = _repo_root(repo_root) / "tests" / "bench" / "tasks"
    if not tasks_dir.is_dir():
        return 152
    return sum(1 for path in tasks_dir.glob("*.json") if path.is_file()) or 152


def _iter_results_for_pair(
    harness: str,
    model: str,
    *,
    base_dir: str | Path = "tests/eval",
    repo_root: Path | None = None,
) -> list[Path]:
    """All ``results.json`` paths for one harness × model pair (any run dir)."""
    harness_name = normalize_harness_name(harness)
    model_name = resolve_model_results_dir_name(model, repo_root=repo_root)
    pair_dir = Path(base_dir) / model_name / harness_name
    if not pair_dir.is_dir():
        return []
    paths: list[Path] = []
    for run_dir in pair_dir.iterdir():
        if not run_dir.is_dir() or not is_run_directory_name(run_dir.name):
            continue
        results = run_dir / "results.json"
        if results.is_file():
            paths.append(results)
    return paths


def pair_has_completed_full_bench(
    harness: str,
    model: str,
    *,
    base_dir: str | Path = "tests/eval",
    repo_root: Path | None = None,
    min_tasks: int | None = None,
) -> tuple[bool, Path | None, int]:
    """True when any run for the pair finished with a full-bench task count.

    Looks at every run dir, not only the newest: a later smoke must not hide
    an already completed 152-task bench.
    """
    needed = canonical_bench_task_count(repo_root=repo_root) if min_tasks is None else min_tasks
    best_path: Path | None = None
    best_tasks = 0
    for results_path in _iter_results_for_pair(
        harness,
        model,
        base_dir=base_dir,
        repo_root=repo_root,
    ):
        try:
            payload = _load_run_payload(results_path)
        except (OSError, json.JSONDecodeError):
            continue
        run = payload.get("run") or {}
        if not run.get("finished"):
            continue
        total = int(run.get("total_tasks") or 0)
        if total >= needed and total >= best_tasks:
            best_path = results_path
            best_tasks = total
    return best_path is not None, best_path, best_tasks


def filter_pending_eval_jobs(
    job_specs: Iterable[dict[str, str]],
    *,
    base_dir: str | Path = "tests/eval",
    repo_root: Path | None = None,
    min_tasks: int | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Split specs into pending vs already completed full-bench pairs."""
    pending: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    needed = canonical_bench_task_count(repo_root=repo_root) if min_tasks is None else min_tasks
    for spec in job_specs:
        done, path, total = pair_has_completed_full_bench(
            spec["harness"],
            spec["model"],
            base_dir=base_dir,
            repo_root=repo_root,
            min_tasks=needed,
        )
        if done:
            skipped.append({**spec, "results_path": str(path) if path else "", "total_tasks": total})
        else:
            pending.append(dict(spec))
    return pending, skipped


def latest_eval_run_finished(
    harness: str,
    model: str,
    *,
    base_dir: str | Path = "tests/eval",
    repo_root: Path | None = None,
) -> tuple[bool, Path | None]:
    """Return whether the newest harness×model run has finished=true in results.json."""
    harness_name = normalize_harness_name(harness)
    model_name = resolve_model_results_dir_name(model, repo_root=repo_root)
    try:
        results_path = find_latest_results(
            base_dir,
            model=model_name,
            harness=harness_name,
        )
    except FileNotFoundError:
        return False, None
    try:
        payload = _load_run_payload(results_path)
    except (OSError, json.JSONDecodeError):
        return False, results_path
    finished = bool((payload.get("run") or {}).get("finished"))
    return finished, results_path


def verify_latest_smoke_run(
    harness: str,
    model: str,
    *,
    base_dir: str | Path = "tests/eval",
    repo_root: Path | None = None,
    min_tasks: int = 1,
    require_finished: bool = True,
) -> SmokeRunCheck:
    """Check the newest results.json for one harness × model combination."""
    harness_name = normalize_harness_name(harness)
    model_name = resolve_model_results_dir_name(model, repo_root=repo_root)
    check = SmokeRunCheck(harness=harness_name, model=model_name, status="missing")

    try:
        results_path = find_latest_results(
            base_dir,
            model=model_name,
            harness=harness_name,
        )
    except FileNotFoundError:
        check.errors.append(
            f"no results.json under {Path(base_dir) / model_name / harness_name}"
        )
        return check

    check.results_path = results_path
    check.run_dir = results_path.parent

    try:
        payload = _load_run_payload(results_path)
    except (OSError, json.JSONDecodeError) as exc:
        check.status = "incomplete"
        check.errors.append(f"cannot read {results_path}: {exc}")
        return check

    run = payload.get("run") or {}
    tests = payload.get("tests") or []
    check.finished = bool(run.get("finished"))
    check.total_tasks = int(run.get("total_tasks") or len(tests) or 0)
    check.passed_tasks = int(run.get("passed_tasks") or 0)
    check.failed_tasks = int(run.get("failed_tasks") or 0)

    if require_finished and not check.finished:
        check.status = "incomplete"
        check.errors.append("run not finished (results.json exists but finished=false)")
        return check

    if check.total_tasks < min_tasks:
        check.status = "incomplete"
        check.errors.append(
            f"expected at least {min_tasks} task(s), got {check.total_tasks}"
        )
        return check

    run_harness = run.get("agent_harness")
    if run_harness and normalize_harness_name(str(run_harness)) != harness_name:
        check.status = "incomplete"
        check.errors.append(
            f"latest run harness mismatch: {run_harness!r} != {harness_name!r}"
        )
        return check

    run_model = run.get("model")
    if run_model and resolve_model_results_dir_name(str(run_model), repo_root=repo_root) != model_name:
        check.status = "incomplete"
        check.errors.append(f"latest run model mismatch: {run_model!r} != {model_name!r}")
        return check

    if check.failed_tasks > 0 or check.passed_tasks < check.total_tasks:
        check.status = "failed_eval"
        check.errors.append(
            f"eval finished but task failed ({check.passed_tasks}/{check.total_tasks} passed)"
        )
        return check

    check.status = "ok"
    return check


def verify_smoke_job_results(
    job_specs: Iterable[dict[str, str]],
    *,
    base_dir: str | Path = "tests/eval",
    repo_root: Path | None = None,
    min_tasks: int = 1,
    require_finished: bool = True,
) -> list[SmokeRunCheck]:
    """Verify latest run artifacts for each submitted harness × model job."""
    checks: list[SmokeRunCheck] = []
    for spec in job_specs:
        checks.append(
            verify_latest_smoke_run(
                spec["harness"],
                spec["model"],
                base_dir=base_dir,
                repo_root=repo_root,
                min_tasks=min_tasks,
                require_finished=require_finished,
            )
        )
    return checks


def print_smoke_check_report(checks: list[SmokeRunCheck]) -> None:
    """Print a compact smoke-check table."""
    headers = (
        "Status",
        "Harness",
        "Model",
        "Tasks",
        "Passed",
        "Run dir",
        "Details",
    )
    rows: list[tuple[str, ...]] = []
    for check in checks:
        tasks = f"{check.total_tasks}" if check.total_tasks else "—"
        passed = f"{check.passed_tasks}" if check.total_tasks else "—"
        run_dir = str(check.run_dir) if check.run_dir else "—"
        details = "; ".join(check.errors) if check.errors else "OK"
        rows.append(
            (
                check.status.upper(),
                check.harness,
                check.model,
                tasks,
                passed,
                run_dir,
                details,
            )
        )

    widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def _fmt_row(cells: tuple[str, ...]) -> str:
        return "  ".join(cell.ljust(widths[idx]) for idx, cell in enumerate(cells))

    print(_fmt_row(headers))
    print(_fmt_row(tuple("-" * width for width in widths)))
    for row in rows:
        print(_fmt_row(row))

    ok = sum(1 for check in checks if check.ok)
    failed_eval = sum(1 for check in checks if check.status == "failed_eval")
    print(
        f"\nSummary: {ok}/{len(checks)} combinations passed smoke; "
        f"{failed_eval} finished with eval failures."
    )


def assert_smoke_job_results(
    job_specs: Iterable[dict[str, str]],
    *,
    base_dir: str | Path = "tests/eval",
    repo_root: Path | None = None,
    min_tasks: int = 1,
    require_finished: bool = True,
    allow_failed_eval: bool = True,
) -> list[SmokeRunCheck]:
    """Raise SystemExit when any expected smoke combination lacks a completed run."""
    checks = verify_smoke_job_results(
        job_specs,
        base_dir=base_dir,
        repo_root=repo_root,
        min_tasks=min_tasks,
        require_finished=require_finished,
    )
    print_smoke_check_report(checks)
    bad = [
        check
        for check in checks
        if check.status in {"missing", "incomplete"}
        or (check.status == "failed_eval" and not allow_failed_eval)
    ]
    if bad:
        missing = sum(1 for check in bad if check.status == "missing")
        incomplete = sum(1 for check in bad if check.status == "incomplete")
        failed_eval = sum(1 for check in bad if check.status == "failed_eval")
        raise SystemExit(
            "Smoke results check failed: "
            f"{missing} missing, {incomplete} incomplete, {failed_eval} eval failures "
            f"(of {len(checks)} harness × model combinations)."
        )
    return checks
