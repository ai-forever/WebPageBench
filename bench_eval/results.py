"""Persist eval run artifacts under tests/eval/<model>/<harness>/<date>/."""

from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from bench_eval.config import EvalConfig
from bench_eval.extended_metrics import enrich_results_payload
from bench_eval.harness_names import normalize_harness_name
from bench_eval.progress import format_progress_result, format_progress_start
from bench_eval.token_usage import aggregate_token_usage_by_model, normalize_token_usage, tag_model_roles
from bench_eval.ui_taxonomy_report import aggregate_ui_stats


def _token_totals(tests: List[Dict[str, Any]]) -> Dict[str, float | int]:
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    llm_calls = 0
    counted_tasks = 0

    for row in tests:
        usage = row.get("token_usage") or {}
        normalized = normalize_token_usage(usage)
        task_total = normalized["total_tokens"]
        if task_total <= 0:
            continue
        counted_tasks += 1
        prompt_tokens += normalized["prompt_tokens"]
        completion_tokens += normalized["completion_tokens"]
        total_tokens += task_total
        llm_calls += normalized["llm_calls"]

    avg_tokens = (total_tokens / counted_tasks) if counted_tasks else 0.0
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "llm_calls": llm_calls,
        "avg_tokens_per_task": avg_tokens,
        "tasks_with_token_usage": counted_tasks,
    }


def sanitize_model_name(model: str) -> str:
    safe = re.sub(r"[^\w.\-]+", "_", model.strip())
    return safe or "unknown_model"


def default_deepeval_identifier(
    mock: str,
    harness: str,
    model: str,
) -> str:
    """Build DeepEval --identifier from bench mock, harness, and LLM model."""
    bench = re.sub(r"[^\w.\-]+", "_", (mock or "bench").strip()) or "bench"
    harness_name = normalize_harness_name(harness or "browser-use")
    model_name = sanitize_model_name(model or "unknown_model")
    return f"{bench}-{harness_name}-{model_name}"


def format_run_timestamp(when: Optional[datetime] = None) -> str:
    moment = when or datetime.now()
    return moment.strftime("%Y-%m-%d_%H-%M-%S")


def format_run_dir_leaf(
    *,
    started_at: Optional[datetime] = None,
    track_suffix: Optional[str] = None,
) -> str:
    """Build run directory leaf name, optionally suffixed for concurrent runs."""
    leaf = format_run_timestamp(started_at)
    if track_suffix:
        return f"{leaf}__{track_suffix}"
    return leaf


# Legacy flat layout: tests/eval/<model>/<YYYY-MM-DD_HH-MM-SS>/
_LEGACY_RUN_DIR_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$")
# Current layout leaf: tests/eval/<model>/<harness>/<YYYY-MM-DD_HH-MM-SS>[__suffix]
_RUN_TIMESTAMP_DIR_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(?:__[\w.-]+)?$"
)
# Also accept date-only dirs from earlier layout iterations.
_RUN_DATE_DIR_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}(?:_\d{2}-\d{2}-\d{2}(?:__[\w.-]+)?)?$"
)


def is_run_directory_name(name: str) -> bool:
    """Return True if ``name`` looks like an eval run directory leaf."""
    return bool(
        _LEGACY_RUN_DIR_PATTERN.match(name)
        or _RUN_TIMESTAMP_DIR_PATTERN.match(name)
        or (
            len(name) == 10
            and _RUN_DATE_DIR_PATTERN.match(name)
        )
    )


def parse_run_dir_timestamp(name: str) -> Optional[datetime]:
    """Parse the timestamp encoded in a run directory leaf name."""
    if _LEGACY_RUN_DIR_PATTERN.match(name) or _RUN_TIMESTAMP_DIR_PATTERN.match(name):
        base = name.split("__", 1)[0]
        return datetime.strptime(base, "%Y-%m-%d_%H-%M-%S")
    if len(name) == 10 and _RUN_DATE_DIR_PATTERN.match(name):
        return datetime.strptime(name, "%Y-%m-%d")
    if _RUN_DATE_DIR_PATTERN.match(name):
        base = name.split("__", 1)[0]
        return datetime.strptime(base, "%Y-%m-%d_%H-%M-%S")
    return None


def default_run_directory(
    model: str,
    harness: str,
    *,
    started_at: Optional[datetime] = None,
    base_dir: str = "tests/eval",
    track_suffix: Optional[str] = None,
) -> Path:
    return (
        Path(base_dir)
        / sanitize_model_name(model)
        / normalize_harness_name(harness)
        / format_run_dir_leaf(started_at=started_at, track_suffix=track_suffix)
    )


def default_deepeval_cache_dir(output_dir: Path | str) -> Path:
    """Per-run DeepEval state directory (temp test run, cache, latest link)."""
    return Path(output_dir) / ".deepeval"


def configure_deepeval_cache_folder(output_dir: Optional[str]) -> Optional[str]:
    """
    Point DeepEval at an isolated cache dir for this eval run.

    Concurrent ``deepeval test run`` processes must not share repo-root
    ``.deepeval/`` or their test counters and temp files collide.
    """
    explicit = os.getenv("DEEPEVAL_CACHE_FOLDER")
    if explicit:
        Path(explicit).mkdir(parents=True, exist_ok=True)
        return explicit
    if not output_dir:
        return None
    cache_dir = default_deepeval_cache_dir(output_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = str(cache_dir)
    os.environ["DEEPEVAL_CACHE_FOLDER"] = path
    return path


def resolve_output_dir(config: EvalConfig) -> Path:
    if config.eval_output_dir:
        return Path(config.eval_output_dir)
    return default_run_directory(
        config.llm_model,
        config.agent_harness,
        started_at=config.run_started_at,
        base_dir=config.eval_results_base_dir,
        track_suffix=config.track_suffix,
    )


def resolve_dataset_path(config: EvalConfig) -> str:
    if config.dataset_path_explicit:
        return config.dataset_path
    return str(resolve_output_dir(config) / "dataset.json")


def detect_xdist_worker_id() -> Optional[str]:
    """Return pytest-xdist worker id (e.g. gw0) or None on controller / single process."""
    worker = os.environ.get("PYTEST_XDIST_WORKER")
    if worker and worker != "master":
        return worker
    return None


def is_xdist_worker() -> bool:
    return detect_xdist_worker_id() is not None


def worker_results_path(output_dir: Path, worker_id: str) -> Path:
    return output_dir / f"results.worker-{worker_id}.json"


def list_worker_result_files(output_dir: Path) -> List[Path]:
    return sorted(output_dir.glob("results.worker-*.json"))


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _collect_model_slots(tests: List[Dict[str, Any]]) -> dict[str, list[str]]:
    slots: dict[str, set[str]] = {}
    for row in tests:
        agent = row.get("agent") or {}
        harness_metadata = agent.get("harness_metadata") or {}
        sync = harness_metadata.get("ouroboros_llm_sync") or {}
        model_slots = sync.get("model_slots") or {}
        if not isinstance(model_slots, dict):
            continue
        for role, models in model_slots.items():
            if not isinstance(models, list):
                continue
            bucket = slots.setdefault(str(role), set())
            for model in models:
                model_name = str(model or "").strip()
                if model_name:
                    bucket.add(model_name)
    return {role: sorted(values) for role, values in sorted(slots.items())}


def _build_run_summary(
    *,
    config: EvalConfig,
    output_dir: Path,
    tests: List[Dict[str, Any]],
    started_at: datetime,
    finished: bool,
    worker_id: Optional[str] = None,
    parallel: Optional[Dict[str, Any]] = None,
    expected_total_tasks: Optional[int] = None,
) -> Dict[str, Any]:
    finished_at = datetime.now(timezone.utc)
    total = len(tests)
    passed = sum(1 for row in tests if row.get("success"))
    failed = total - passed
    durations = [
        row["duration_seconds"]
        for row in tests
        if isinstance(row.get("duration_seconds"), (int, float))
    ]
    steps = [
        row["agent_steps"]
        for row in tests
        if isinstance(row.get("agent_steps"), int)
    ]
    token_stats = _token_totals(tests)
    token_usage_by_model = aggregate_token_usage_by_model(tests)
    model_slots = _collect_model_slots(tests)
    if model_slots:
        token_usage_by_model = tag_model_roles(
            token_usage_by_model,
            model_slots=model_slots,
        )

    run: Dict[str, Any] = {
        "model": config.llm_model,
        "provider": config.llm_provider,
        "agent_harness": normalize_harness_name(config.agent_harness),
        "mock": config.mock,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat() if finished else None,
        "output_dir": str(output_dir),
        "dataset_path": str(output_dir / "dataset.json"),
        "results_path": str(output_dir / "results.json"),
        "total_tasks": total,
        "passed_tasks": passed,
        "failed_tasks": failed,
        "success_rate": (passed / total) if total else 0.0,
        "total_duration_seconds": sum(durations) if durations else 0.0,
        "avg_duration_seconds": (sum(durations) / len(durations)) if durations else 0.0,
        "total_agent_steps": sum(steps) if steps else 0,
        "avg_agent_steps": (sum(steps) / len(steps)) if steps else 0.0,
        "prompt_tokens": token_stats["prompt_tokens"],
        "completion_tokens": token_stats["completion_tokens"],
        "total_tokens": token_stats["total_tokens"],
        "avg_tokens_per_task": token_stats["avg_tokens_per_task"],
        "llm_calls": token_stats["llm_calls"],
        "token_usage_by_model": token_usage_by_model,
        "finished": finished,
        "worker_id": worker_id,
    }
    if model_slots:
        run["ouroboros_model_slots"] = model_slots
    if expected_total_tasks is not None:
        run["expected_total_tasks"] = expected_total_tasks
    if parallel:
        run["parallel"] = parallel

    return {
        "run": run,
        "ui_taxonomy_stats": aggregate_ui_stats(tests) if finished else {},
        "tests": tests,
    }


@dataclass
class EvalRunRecorder:
    """Collect per-test results and write JSON artifacts for one eval run."""

    config: EvalConfig
    output_dir: Path
    worker_id: Optional[str] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tests: List[Dict[str, Any]] = field(default_factory=list)
    total_tasks: Optional[int] = None
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @classmethod
    def from_config(
        cls,
        config: EvalConfig,
        *,
        worker_id: Optional[str] = None,
    ) -> "EvalRunRecorder":
        output_dir = resolve_output_dir(config)
        output_dir.mkdir(parents=True, exist_ok=True)
        return cls(config=config, output_dir=output_dir, worker_id=worker_id)

    @property
    def results_path(self) -> Path:
        if self.worker_id:
            return worker_results_path(self.output_dir, self.worker_id)
        return self.output_dir / "results.json"

    @property
    def dataset_path(self) -> Path:
        return self.output_dir / "dataset.json"

    def set_total_tasks(self, total: int) -> None:
        self.total_tasks = total

    def print_run_header(self) -> None:
        if not self.config.show_progress:
            return
        total_label = self.total_tasks if self.total_tasks is not None else "?"
        print("\n=== Eval scoring ===", flush=True)
        print(
            f"Model: {self.config.llm_model} ({self.config.llm_provider})",
            flush=True,
        )
        print(
            f"Harness: {normalize_harness_name(self.config.agent_harness)}",
            flush=True,
        )
        print(f"Tasks: {total_label}", flush=True)
        print(f"Output: {self.output_dir}", flush=True)
        print("", flush=True)

    def on_test_start(self, test_name: str) -> None:
        if not self.config.show_progress:
            return
        current = len(self.tests) + 1
        print(
            format_progress_start(current, self.total_tasks, test_name),
            flush=True,
        )

    def _print_test_result(self, row: Dict[str, Any], current: int) -> None:
        passed = sum(1 for item in self.tests if item.get("success"))
        running_rate = passed / current if current else 0.0
        print(
            format_progress_result(
                current,
                self.total_tasks,
                row,
                running_success_rate=running_rate,
            ),
            flush=True,
        )

    def record_test(self, test_case: Any) -> Dict[str, Any]:
        metadata = test_case.metadata or {}
        dab_check = metadata.get("dab_check") or {}
        agent = metadata.get("agent") or {}
        timing = metadata.get("timing") or {}
        token_usage = metadata.get("token_usage") or agent.get("token_usage") or {}
        token_usage_by_model = (
            metadata.get("token_usage_by_model")
            or agent.get("token_usage_by_model")
            or {}
        )
        success = bool(dab_check.get("all_passed", False))

        row = {
            "test_name": metadata.get("test_name") or test_case.name,
            "track_id": metadata.get("track_id"),
            "task_url": metadata.get("task_url"),
            "agent_harness": metadata.get("agent_harness"),
            "input": test_case.input,
            "actual_output": test_case.actual_output,
            "success": success,
            "duration_seconds": timing.get("duration_seconds"),
            "agent_steps": agent.get("steps", 0),
            "agent_is_done": agent.get("is_done"),
            "agent_error": metadata.get("agent_error") or agent.get("error"),
            "token_usage": token_usage,
            "token_usage_by_model": token_usage_by_model,
            "tokens": token_usage.get("total_tokens"),
            "dab_check": dab_check,
            "agent": agent,
            "trajectory": metadata.get("trajectory") or {},
            "ui_taxonomy": metadata.get("ui_taxonomy") or {},
        }
        with self._lock:
            self.tests.append(row)
            self._write_results(finished=False)
            if self.config.show_progress:
                self._print_test_result(row, len(self.tests))
        return row

    def build_summary(self, *, finished: bool) -> Dict[str, Any]:
        return _build_run_summary(
            config=self.config,
            output_dir=self.output_dir,
            tests=self.tests,
            started_at=self.started_at,
            finished=finished,
            worker_id=self.worker_id,
            expected_total_tasks=self.total_tasks,
        )

    def _enrich_summary(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return enrich_results_payload(payload, enriched_by="bench_eval.results")

    def _write_results(self, *, finished: bool) -> None:
        payload = self._enrich_summary(self.build_summary(finished=finished))
        self.results_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def finalize(self) -> Dict[str, Any]:
        with self._lock:
            payload = self._enrich_summary(self.build_summary(finished=True))
            self.results_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return payload

    def print_summary(self, payload: Optional[Dict[str, Any]] = None) -> None:
        data = payload or self.build_summary(finished=True)
        run = data["run"]
        print("\n=== Eval run summary ===")
        print(f"Model: {run['model']} ({run['provider']})")
        print(f"Harness: {run.get('agent_harness', '—')}")
        print(f"Output: {run['output_dir']}")
        parallel = run.get("parallel")
        if parallel:
            print(
                f"Parallel workers: {parallel.get('worker_count', 0)} "
                f"({', '.join(parallel.get('worker_ids') or [])})"
            )
        print(f"Tasks: {run['total_tasks']} | passed: {run['passed_tasks']} | failed: {run['failed_tasks']}")
        print(f"Success rate: {run['success_rate']:.1%}")
        print(f"Total duration: {run['total_duration_seconds']:.1f}s")
        print(f"Avg test duration: {run['avg_duration_seconds']:.1f}s")
        print(f"Avg agent steps: {run['avg_agent_steps']:.1f}")
        print(f"Total tokens: {run.get('total_tokens', 0)}")
        print(f"Avg tokens per task: {run.get('avg_tokens_per_task', 0.0):.1f}")
        usage_by_model = run.get("token_usage_by_model") or {}
        if usage_by_model:
            print("Token usage by model:")
            for model in sorted(usage_by_model):
                row = usage_by_model[model] or {}
                roles = row.get("roles") or []
                role_text = f" [{', '.join(roles)}]" if roles else ""
                cost = row.get("cost_usd")
                cost_text = f", cost=${float(cost):.4f}" if isinstance(cost, (int, float)) else ""
                print(
                    f"  {model}{role_text}: "
                    f"prompt={row.get('prompt_tokens', 0)}, "
                    f"completion={row.get('completion_tokens', 0)}, "
                    f"calls={row.get('llm_calls', 0)}{cost_text}"
                )
        print(f"Results JSON: {run['results_path']}")
        print(f"Dataset JSON: {run['dataset_path']}")

        stats = data.get("ui_taxonomy_stats") or {}
        self._print_ui_bucket("UI taxonomy (checked classes)", stats.get("by_checked_class") or {})
        self._print_ui_bucket("UI taxonomy (used classes)", stats.get("by_used_class") or {})
        self._print_ui_bucket("UI patterns", stats.get("by_ui_pattern") or {})

    @staticmethod
    def _print_ui_bucket(title: str, bucket: Dict[str, Any]) -> None:
        if not bucket:
            return
        print(f"\n=== {title} ===")
        for key in sorted(bucket):
            row = bucket[key]
            print(
                f"  {key}: {row['passed']}/{row['total']} passed "
                f"({row['success_rate']:.0%})"
            )


def merge_worker_results_into_final(
    config: EvalConfig,
    worker_files: Optional[List[Path]] = None,
) -> Dict[str, Any]:
    """Merge per-worker result files into a single final results.json payload."""
    output_dir = resolve_output_dir(config)
    files = worker_files or list_worker_result_files(output_dir)
    if not files:
        raise ValueError(f"No worker result files found in {output_dir}")

    payloads: List[Dict[str, Any]] = []
    for path in files:
        payloads.append(json.loads(path.read_text(encoding="utf-8")))

    all_tests: List[Dict[str, Any]] = []
    seen_names: set[str] = set()
    worker_ids: List[str] = []
    started_times: List[datetime] = []
    finished_times: List[datetime] = []
    expected_total_tasks: Optional[int] = None

    for payload in payloads:
        run = payload.get("run") or {}
        worker_id = run.get("worker_id")
        if worker_id:
            worker_ids.append(str(worker_id))
        expected = run.get("expected_total_tasks")
        if isinstance(expected, int):
            expected_total_tasks = max(expected_total_tasks or 0, expected)

        started = _parse_iso_datetime(run.get("started_at"))
        if started is not None:
            started_times.append(started)
        finished = _parse_iso_datetime(run.get("finished_at"))
        if finished is not None:
            finished_times.append(finished)

        for row in payload.get("tests") or []:
            test_name = row.get("test_name")
            if not test_name or test_name in seen_names:
                continue
            seen_names.add(test_name)
            all_tests.append(row)

    all_tests.sort(key=lambda row: row.get("test_name") or "")

    started_at = (
        min(started_times)
        if started_times
        else (config.run_started_at or datetime.now(timezone.utc))
    )
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)

    parallel = {
        "worker_count": len(files),
        "worker_ids": sorted(worker_ids),
        "worker_result_files": [str(path) for path in files],
    }

    payload = _build_run_summary(
        config=config,
        output_dir=output_dir,
        tests=all_tests,
        started_at=started_at,
        finished=True,
        worker_id=None,
        parallel=parallel,
        expected_total_tasks=expected_total_tasks,
    )

    if finished_times:
        payload["run"]["finished_at"] = max(finished_times).isoformat()

    payload = enrich_results_payload(payload, enriched_by="bench_eval.results")

    results_path = output_dir / "results.json"
    results_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


_RECORDER: Optional[EvalRunRecorder] = None
_RECORDER_LOCK = threading.Lock()


def get_recorder(config: Optional[EvalConfig] = None) -> EvalRunRecorder:
    global _RECORDER
    with _RECORDER_LOCK:
        if _RECORDER is None:
            if config is None:
                from bench_eval.config import load_config

                config = load_config()
            _RECORDER = EvalRunRecorder.from_config(
                config,
                worker_id=detect_xdist_worker_id(),
            )
        return _RECORDER


def reset_recorder() -> None:
    global _RECORDER
    with _RECORDER_LOCK:
        _RECORDER = None
