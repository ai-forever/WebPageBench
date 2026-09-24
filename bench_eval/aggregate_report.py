"""Aggregate latest eval runs across models and harnesses into one Markdown report."""

from __future__ import annotations

import json
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bench_eval.extended_metrics import (
    compute_pass_at_k,
    enrich_results_payload,
)
from bench_eval.harness_names import normalize_harness_name
from bench_eval.llm_cost import compute_results_cost, format_usd
from bench_eval.results import _LEGACY_RUN_DIR_PATTERN, is_run_directory_name
from bench_eval.run_report import (
    _markdown_table,
    _pct,
    _seconds,
    _steps,
    _tokens,
    write_run_report,
)


# Smoke runs cap tasks at a small number (parallel smoke uses about five).
# Full bench is everything strictly above this threshold (51 tasks in production).
FULL_BENCH_MIN_TASKS = 6


def is_full_bench_run(run: dict[str, Any]) -> bool:
    """Return True when the run executed more than five tasks (full bench, not smoke)."""
    return int(run.get("total_tasks") or 0) >= FULL_BENCH_MIN_TASKS


@dataclass(frozen=True)
class LatestRunEntry:
    """One harness × model combination with its newest results.json."""

    model_dir: str
    harness: str
    results_path: Path
    run_dir: Path
    sort_key: str
    run: dict[str, Any]

    @property
    def model(self) -> str:
        return str(self.run.get("model") or self.model_dir)

    @property
    def finished(self) -> bool:
        return bool(self.run.get("finished"))

    @property
    def total_tasks(self) -> int:
        return int(self.run.get("total_tasks") or 0)

    @property
    def passed_tasks(self) -> int:
        return int(self.run.get("passed_tasks") or 0)

    @property
    def failed_tasks(self) -> int:
        return int(self.run.get("failed_tasks") or 0)


def _load_run(results_path: Path) -> dict[str, Any]:
    return json.loads(results_path.read_text(encoding="utf-8"))


def _run_sort_key(harness: str, run_dir_name: str) -> str:
    return f"{harness}/{run_dir_name}"


def _pick_newer(
    current: tuple[str, Path, dict[str, Any]] | None,
    candidate: tuple[str, Path, dict[str, Any]],
) -> tuple[str, Path, dict[str, Any]]:
    if current is None:
        return candidate
    return candidate if candidate[0] > current[0] else current


def discover_all_run_paths(
    base_dir: str | Path = "tests/eval",
    *,
    require_finished: bool = False,
) -> dict[tuple[str, str], list[Path]]:
    """Map (model_dir, harness) to all results.json paths, newest first."""
    root = Path(base_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Eval results base directory not found: {root}")

    grouped: dict[tuple[str, str], list[tuple[str, Path]]] = defaultdict(list)

    for model_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for child in model_dir.iterdir():
            if not child.is_dir():
                continue

            if _LEGACY_RUN_DIR_PATTERN.match(child.name):
                results_path = child / "results.json"
                if not results_path.is_file():
                    continue
                payload = _load_run(results_path)
                run = payload.get("run") or {}
                if require_finished and not run.get("finished"):
                    continue
                harness_raw = run.get("agent_harness") or "browser-use"
                try:
                    harness = normalize_harness_name(str(harness_raw))
                except ValueError:
                    harness = str(harness_raw)
                sort_key = _run_sort_key(harness, child.name)
                grouped[(model_dir.name, harness)].append((sort_key, results_path))
                continue

            harness = child.name
            for run_dir in child.iterdir():
                if not run_dir.is_dir() or not is_run_directory_name(run_dir.name):
                    continue
                results_path = run_dir / "results.json"
                if not results_path.is_file():
                    continue
                payload = _load_run(results_path)
                run = payload.get("run") or {}
                if require_finished and not run.get("finished"):
                    continue
                sort_key = _run_sort_key(harness, run_dir.name)
                grouped[(model_dir.name, harness)].append((sort_key, results_path))

    return {
        key: [path for _, path in sorted(items, reverse=True)]
        for key, items in grouped.items()
    }


def discover_latest_runs(
    base_dir: str | Path = "tests/eval",
    *,
    require_finished: bool = False,
    min_total_tasks: int | None = None,
) -> list[LatestRunEntry]:
    """Find the newest results.json for every model × harness under ``base_dir``.

    When ``min_total_tasks`` is set, only runs with ``total_tasks`` at least that
    value are considered (use :data:`FULL_BENCH_MIN_TASKS` to skip smoke runs).
    """
    root = Path(base_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Eval results base directory not found: {root}")

    best: dict[tuple[str, str], tuple[str, Path, dict[str, Any]]] = {}

    for model_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for child in model_dir.iterdir():
            if not child.is_dir():
                continue

            if _LEGACY_RUN_DIR_PATTERN.match(child.name):
                results_path = child / "results.json"
                if not results_path.is_file():
                    continue
                payload = _load_run(results_path)
                run = payload.get("run") or {}
                if min_total_tasks is not None and int(run.get("total_tasks") or 0) < min_total_tasks:
                    continue
                harness_raw = run.get("agent_harness") or "browser-use"
                try:
                    harness = normalize_harness_name(str(harness_raw))
                except ValueError:
                    harness = str(harness_raw)
                key = (model_dir.name, harness)
                sort_key = _run_sort_key(harness, child.name)
                best[key] = _pick_newer(best.get(key), (sort_key, results_path, run))
                continue

            harness = child.name
            for run_dir in child.iterdir():
                if not run_dir.is_dir() or not is_run_directory_name(run_dir.name):
                    continue
                results_path = run_dir / "results.json"
                if not results_path.is_file():
                    continue
                payload = _load_run(results_path)
                run = payload.get("run") or {}
                if min_total_tasks is not None and int(run.get("total_tasks") or 0) < min_total_tasks:
                    continue
                key = (model_dir.name, harness)
                sort_key = _run_sort_key(harness, run_dir.name)
                best[key] = _pick_newer(best.get(key), (sort_key, results_path, run))

    entries: list[LatestRunEntry] = []
    for (model_dir, harness), (sort_key, results_path, run) in sorted(best.items()):
        if require_finished and not run.get("finished"):
            continue
        entries.append(
            LatestRunEntry(
                model_dir=model_dir,
                harness=harness,
                results_path=results_path,
                run_dir=results_path.parent,
                sort_key=sort_key,
                run=run,
            )
        )
    return entries


@dataclass(frozen=True)
class AggregateMetrics:
    label: str
    run_count: int
    total_tasks: int
    passed_tasks: int
    failed_tasks: int
    success_rate: float | None
    avg_duration_seconds: float | None
    avg_agent_steps: float | None
    avg_tokens_per_task: float | None
    total_tokens: int
    total_cost_usd: float | None
    avg_cost_per_task_usd: float | None
    priced_run_count: int
    avg_latency_per_llm_call_seconds: float | None = None
    avg_token_efficiency: float | None = None
    avg_action_redundancy: float | None = None
    agent_completion_rate: float | None = None
    agent_dab_agreement_rate: float | None = None
    false_done_rate: float | None = None
    pass_at_k: float | None = None
    pass_at_k_runs: int = 0


def _weighted_mean(values: list[tuple[float, int]]) -> float | None:
    weight = sum(weight for _, weight in values if weight > 0)
    if weight <= 0:
        return None
    return sum(value * weight for value, weight in values if weight > 0) / weight


def _extended_from_run(run: dict[str, Any]) -> dict[str, Any]:
    extended = run.get("extended_metrics")
    return extended if isinstance(extended, dict) else {}


def _efficiency_sample(
    run: dict[str, Any],
    key: str,
    weight: int,
    bucket: list[tuple[float, int]],
) -> None:
    value = _extended_from_run(run).get(key)
    if isinstance(value, (int, float)) and weight:
        bucket.append((float(value), weight))


def compute_aggregate_metrics(label: str, entries: list[LatestRunEntry]) -> AggregateMetrics:
    total_tasks = sum(entry.total_tasks for entry in entries)
    passed_tasks = sum(entry.passed_tasks for entry in entries)
    failed_tasks = sum(entry.failed_tasks for entry in entries)
    success_rate = (passed_tasks / total_tasks) if total_tasks else None

    duration_samples: list[tuple[float, int]] = []
    steps_samples: list[tuple[float, int]] = []
    token_samples: list[tuple[float, int]] = []
    cost_samples: list[tuple[float, int]] = []
    latency_samples: list[tuple[float, int]] = []
    token_efficiency_samples: list[tuple[float, int]] = []
    redundancy_samples: list[tuple[float, int]] = []
    completion_samples: list[tuple[float, int]] = []
    agreement_samples: list[tuple[float, int]] = []
    false_done_samples: list[tuple[float, int]] = []
    pass_at_k_samples: list[tuple[float, int]] = []
    pass_at_k_runs = 0
    total_tokens = 0
    total_cost_usd = 0.0
    priced_run_count = 0
    has_total_cost = False

    for entry in entries:
        run = entry.run
        weight = entry.total_tasks
        avg_duration = run.get("avg_duration_seconds")
        if isinstance(avg_duration, (int, float)) and weight:
            duration_samples.append((float(avg_duration), weight))
        avg_steps = run.get("avg_agent_steps")
        if isinstance(avg_steps, (int, float)) and weight:
            steps_samples.append((float(avg_steps), weight))
        avg_tokens = run.get("avg_tokens_per_task")
        if isinstance(avg_tokens, (int, float)) and weight:
            token_samples.append((float(avg_tokens), weight))
        task_tokens = run.get("total_tokens")
        if isinstance(task_tokens, int):
            total_tokens += task_tokens

        _efficiency_sample(run, "avg_latency_per_llm_call_seconds", weight, latency_samples)
        _efficiency_sample(run, "avg_token_efficiency", weight, token_efficiency_samples)
        _efficiency_sample(run, "avg_action_redundancy", weight, redundancy_samples)
        _efficiency_sample(run, "agent_completion_rate", weight, completion_samples)
        _efficiency_sample(run, "agent_dab_agreement_rate", weight, agreement_samples)
        _efficiency_sample(run, "false_done_rate", weight, false_done_samples)

        pass_at_k = _extended_from_run(run).get("pass_at_k")
        if isinstance(pass_at_k, dict):
            overall = pass_at_k.get("overall")
            run_count = pass_at_k.get("run_count")
            if isinstance(overall, (int, float)) and weight:
                pass_at_k_samples.append((float(overall), weight))
            if isinstance(run_count, int):
                pass_at_k_runs = max(pass_at_k_runs, run_count)

        payload = _load_run(entry.results_path)
        cost = compute_results_cost(payload)
        if cost.total_cost_usd is not None and cost.total_cost_usd > 0:
            has_total_cost = True
            total_cost_usd += cost.total_cost_usd
            priced_run_count += 1
            if cost.avg_cost_per_task_usd is not None and cost.avg_cost_per_task_usd > 0 and weight:
                cost_samples.append((cost.avg_cost_per_task_usd, weight))

    return AggregateMetrics(
        label=label,
        run_count=len(entries),
        total_tasks=total_tasks,
        passed_tasks=passed_tasks,
        failed_tasks=failed_tasks,
        success_rate=success_rate,
        avg_duration_seconds=_weighted_mean(duration_samples),
        avg_agent_steps=_weighted_mean(steps_samples),
        avg_tokens_per_task=_weighted_mean(token_samples),
        total_tokens=total_tokens,
        total_cost_usd=total_cost_usd if has_total_cost else None,
        avg_cost_per_task_usd=_weighted_mean(cost_samples),
        priced_run_count=priced_run_count,
        avg_latency_per_llm_call_seconds=_weighted_mean(latency_samples),
        avg_token_efficiency=_weighted_mean(token_efficiency_samples),
        avg_action_redundancy=_weighted_mean(redundancy_samples),
        agent_completion_rate=_weighted_mean(completion_samples),
        agent_dab_agreement_rate=_weighted_mean(agreement_samples),
        false_done_rate=_weighted_mean(false_done_samples),
        pass_at_k=_weighted_mean(pass_at_k_samples),
        pass_at_k_runs=pass_at_k_runs,
    )


def _relative_path(path: Path, *, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path.resolve())


def _entry_success_rate(entry: LatestRunEntry) -> float | None:
    rate = entry.run.get("success_rate")
    if isinstance(rate, (int, float)):
        return float(rate)
    if entry.total_tasks:
        return entry.passed_tasks / entry.total_tasks
    return None


def _quality_sort_key(rate: float | None, *tiebreakers: str) -> tuple[float, ...]:
    """Descending quality: higher success rate first; missing rate goes last."""
    return (-(rate if rate is not None else -1.0), *tiebreakers)


def _entry_quality_sort_key(entry: LatestRunEntry) -> tuple[float, ...]:
    return _quality_sort_key(
        _entry_success_rate(entry),
        entry.harness,
        entry.model_dir,
    )


def _metrics_quality_sort_key(metrics: AggregateMetrics) -> tuple[float, ...]:
    return _quality_sort_key(metrics.success_rate, metrics.label)


def _status_label(entry: LatestRunEntry) -> str:
    if not entry.finished:
        return "незавершён"
    if entry.total_tasks and entry.passed_tasks == entry.total_tasks:
        return "ok"
    if entry.total_tasks:
        return "есть провалы"
    return "—"


def _rate(value: float | int | None) -> str:
    if value is None:
        return "—"
    return _pct(value)


def _scientific(value: float | int | None) -> str:
    if value is None:
        return "—"
    return f"{float(value):.2e}"


def _efficiency_row(metrics: AggregateMetrics) -> list[str]:
    return [
        metrics.label,
        _seconds(metrics.avg_latency_per_llm_call_seconds),
        _scientific(metrics.avg_token_efficiency),
        _rate(metrics.avg_action_redundancy),
        _rate(metrics.agent_completion_rate),
        _rate(metrics.agent_dab_agreement_rate),
        _rate(metrics.false_done_rate),
        _rate(metrics.pass_at_k) if metrics.pass_at_k is not None else "—",
        str(metrics.pass_at_k_runs) if metrics.pass_at_k_runs else "—",
    ]


_EFFICIENCY_HEADERS = [
    "Группа",
    "Ср. latency/LLM",
    "Token efficiency",
    "Action redundancy",
    "Agent done rate",
    "WebPageBench agreement",
    "False done rate",
    "Pass@k",
    "Runs for Pass@k",
]


def enrich_results_file(
    results_path: Path,
    *,
    pass_at_k: dict[str, Any] | None = None,
    enriched_at: datetime | None = None,
) -> dict[str, Any]:
    """Load results.json, attach extended metrics, and write back."""
    payload = _load_run(results_path)
    enriched = enrich_results_payload(
        payload,
        pass_at_k=pass_at_k,
        enriched_at=enriched_at,
        enriched_by="render_eval_aggregate.py",
    )
    results_path.write_text(
        json.dumps(enriched, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return enriched


def enrich_all_results(
    base_dir: str | Path = "tests/eval",
    *,
    require_finished: bool = False,
    pass_at_k: int = 3,
    enriched_at: datetime | None = None,
) -> list[Path]:
    """
    Enrich every latest results.json under ``base_dir``.

    Pass@k is computed from all historical runs of the same harness × model.
    """
    moment = enriched_at or datetime.now(timezone.utc)
    all_runs = discover_all_run_paths(base_dir, require_finished=require_finished)
    enriched_paths: list[Path] = []

    for (_model_dir, _harness), paths in sorted(all_runs.items()):
        historical_payloads = [_load_run(path) for path in paths]
        pass_metrics = None
        if len(paths) >= 2 and pass_at_k >= 1:
            pass_metrics = compute_pass_at_k(historical_payloads, k=pass_at_k)

        latest_path = paths[0]
        enrich_results_file(
            latest_path,
            pass_at_k=pass_metrics,
            enriched_at=moment,
        )
        enriched_paths.append(latest_path)

    return enriched_paths


def _metrics_row(metrics: AggregateMetrics) -> list[str]:
    return [
        metrics.label,
        str(metrics.run_count),
        str(metrics.total_tasks),
        str(metrics.passed_tasks),
        str(metrics.failed_tasks),
        _pct(metrics.success_rate),
        _seconds(metrics.avg_duration_seconds),
        _steps(metrics.avg_agent_steps),
        _tokens(metrics.avg_tokens_per_task),
        _tokens(metrics.total_tokens),
        format_usd(metrics.total_cost_usd),
        format_usd(metrics.avg_cost_per_task_usd),
    ]


_METRICS_HEADERS = [
    "Группа",
    "Прогонов",
    "Задач",
    "Passed",
    "Failed",
    "Success rate",
    "Ср. время",
    "Ср. шаги",
    "Ср. токены",
    "Всего токенов",
    "Стоимость",
    "Ср. $/задачу",
]


def render_aggregate_report(
    entries: list[LatestRunEntry],
    *,
    base_dir: str | Path = "tests/eval",
    report_path: str | Path | None = None,
    generated_at: datetime | None = None,
    min_total_tasks: int | None = FULL_BENCH_MIN_TASKS,
) -> str:
    root = Path(base_dir)
    report = Path(report_path) if report_path else root / "README.md"
    report_parent = report.parent.resolve()
    moment = generated_at or datetime.now(timezone.utc)

    lines = [
        "# Eval results: сводка по последним прогонам",
        "",
        f"Сгенерировано: `{moment.isoformat()}`",
        f"Базовый каталог: `{root.resolve()}`",
        f"Комбинаций harness × model (full bench): **{len(entries)}**",
        "",
    ]
    if min_total_tasks is not None:
        lines.extend(
            [
                f"В сводку попадают только прогоны с **≥ {min_total_tasks}** задачами "
                f"(smoke с ≤ {min_total_tasks - 1} задачами исключены). "
                "Per-run README для smoke генерируется отдельно в каталоге прогона.",
                "",
            ]
        )
    lines.extend(
        [
            "Стоимость LLM оценивается по токенам из `results.json` "
            "(таблица LiteLLM, см. `scripts/compute_eval_cost.py`).",
            "",
        ]
    )

    if not entries:
        lines.extend(
            [
                (
                    f"_Нет full-bench прогонов (≥ {min_total_tasks} задач) "
                    "с `results.json` под базовым каталогом._"
                    if min_total_tasks is not None
                    else "_Нет прогонов с `results.json` под базовым каталогом._"
                ),
                "",
                "---",
                "",
                "Сгенерировано `scripts/render_eval_aggregate.py`.",
                "",
            ]
        )
        return "\n".join(lines)

    combo_rows: list[list[str]] = []
    for entry in sorted(entries, key=_entry_quality_sort_key):
        run = entry.run
        started_at = run.get("started_at") or entry.run_dir.name
        payload = _load_run(entry.results_path)
        cost = compute_results_cost(payload)
        combo_rows.append(
            [
                f"`{entry.harness}`",
                f"`{entry.model}`",
                str(entry.total_tasks),
                str(entry.passed_tasks),
                str(entry.failed_tasks),
                _pct(run.get("success_rate")),
                _seconds(run.get("avg_duration_seconds")),
                _steps(run.get("avg_agent_steps")),
                _tokens(run.get("avg_tokens_per_task")),
                format_usd(cost.total_cost_usd),
                format_usd(cost.avg_cost_per_task_usd),
                _seconds(_extended_from_run(run).get("avg_latency_per_llm_call_seconds")),
                _rate(_extended_from_run(run).get("agent_dab_agreement_rate")),
                _rate((_extended_from_run(run).get("pass_at_k") or {}).get("overall")),
                str(started_at),
                _status_label(entry),
                f"`{_relative_path(entry.run_dir, base=report_parent)}`",
            ]
        )

    lines.extend(
        [
            "## Последний прогон каждой комбинации",
            "",
            "Для каждой пары harness × model выбран самый новый каталог прогона.",
            "",
            _markdown_table(
                [
                    "Harness",
                    "Model",
                    "Задач",
                    "Passed",
                    "Failed",
                    "Success rate",
                    "Ср. время",
                    "Ср. шаги",
                    "Ср. токены",
                    "Стоимость",
                    "Ср. $/задачу",
                    "Ср. latency/LLM",
                    "WebPageBench agreement",
                    "Pass@k",
                    "Старт",
                    "Статус",
                    "Каталог",
                ],
                combo_rows,
            ).rstrip(),
            "",
        ]
    )

    by_harness: dict[str, list[LatestRunEntry]] = defaultdict(list)
    by_model: dict[str, list[LatestRunEntry]] = defaultdict(list)
    for entry in entries:
        by_harness[entry.harness].append(entry)
        by_model[entry.model_dir].append(entry)

    harness_rows = [
        _metrics_row(metrics)
        for _, metrics in sorted(
            (
                (harness, compute_aggregate_metrics(f"`{harness}`", group))
                for harness, group in by_harness.items()
            ),
            key=lambda item: _metrics_quality_sort_key(item[1]),
        )
    ]
    model_rows = [
        _metrics_row(metrics)
        for _, metrics in sorted(
            (
                (model, compute_aggregate_metrics(f"`{model}`", group))
                for model, group in by_model.items()
            ),
            key=lambda item: _metrics_quality_sort_key(item[1]),
        )
    ]
    overall = compute_aggregate_metrics("**все комбинации**", entries)

    lines.extend(
        [
            "## Усреднение по harness",
            "",
            "Метрики усреднены по всем моделям внутри harness (вес — число задач в прогоне). "
            "Стоимость — сумма по последним прогонам; ср. $/задачу — взвешенное среднее.",
            "",
            _markdown_table(_METRICS_HEADERS, harness_rows).rstrip(),
            "",
            "## Усреднение по model",
            "",
            "Метрики усреднены по всем harness внутри model (вес — число задач в прогоне). "
            "Стоимость — сумма по последним прогонам; ср. $/задачу — взвешенное среднее.",
            "",
            _markdown_table(_METRICS_HEADERS, model_rows).rstrip(),
            "",
            "## Efficiency metrics",
            "",
            "Расширенные метрики из `run.extended_metrics` в `results.json` "
            "(обогащаются при генерации отчёта). "
            "**Token efficiency** — `1 / tokens` для успешных задач; "
            "**Action redundancy** — доля повторяющихся действий в траектории; "
            "**WebPageBench agreement** — совпадение `success` и `agent_is_done`; "
            "**Pass@k** — по историческим прогонам той же пары harness × model (если ≥ 2 прогонов).",
            "",
            _markdown_table(
                _EFFICIENCY_HEADERS,
                [
                    _efficiency_row(metrics)
                    for _, metrics in sorted(
                        (
                            (harness, compute_aggregate_metrics(f"`{harness}`", group))
                            for harness, group in by_harness.items()
                        ),
                        key=lambda item: _metrics_quality_sort_key(item[1]),
                    )
                ],
            ).rstrip(),
            "",
            _markdown_table(
                _EFFICIENCY_HEADERS,
                [
                    _efficiency_row(metrics)
                    for _, metrics in sorted(
                        (
                            (model, compute_aggregate_metrics(f"`{model}`", group))
                            for model, group in by_model.items()
                        ),
                        key=lambda item: _metrics_quality_sort_key(item[1]),
                    )
                ],
            ).rstrip(),
            "",
            _markdown_table(
                _EFFICIENCY_HEADERS,
                [_efficiency_row(overall)],
            ).rstrip(),
            "",
            "## Итого",
            "",
            _markdown_table(_METRICS_HEADERS, [_metrics_row(overall)]).rstrip(),
            "",
            "---",
            "",
            "Сгенерировано `scripts/render_eval_aggregate.py` "
            f"в `{report.resolve()}`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_all_run_reports(
    base_dir: str | Path = "tests/eval",
    *,
    require_finished: bool = False,
) -> list[Path]:
    """Write README.md next to every results.json under ``base_dir``."""
    all_runs = discover_all_run_paths(base_dir, require_finished=require_finished)
    written: list[Path] = []
    seen: set[Path] = set()
    for paths in all_runs.values():
        for results_path in paths:
            resolved = results_path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            written.append(
                write_run_report(
                    results_path,
                    generated_by="scripts/render_eval_aggregate.py",
                )
            )
    return sorted(written, key=lambda path: str(path))


def write_results_archive(
    entries: list[LatestRunEntry],
    *,
    aggregate_readme: str | Path,
    output_zip: str | Path,
) -> Path:
    """Pack full-bench results into ``output_zip`` (replaces existing file).

    Layout inside the archive::

        README.md
        <model>/<harness>/results.json
        <model>/<harness>/README.md
    """
    readme_path = Path(aggregate_readme)
    if not readme_path.is_file():
        raise FileNotFoundError(f"Aggregate README not found: {readme_path}")

    zip_path = Path(output_zip)
    if zip_path.is_file():
        zip_path.unlink()
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(readme_path, arcname="README.md")
        for entry in sorted(entries, key=lambda item: (item.model_dir, item.harness)):
            prefix = f"{entry.model_dir}/{entry.harness}"
            archive.write(entry.results_path, arcname=f"{prefix}/results.json")
            run_readme = entry.run_dir / "README.md"
            if run_readme.is_file():
                archive.write(run_readme, arcname=f"{prefix}/README.md")

    return zip_path


def write_aggregate_report(
    base_dir: str | Path = "tests/eval",
    *,
    output_path: str | Path | None = None,
    require_finished: bool = False,
    enrich_results: bool = True,
    pass_at_k: int = 3,
    write_run_reports: bool = True,
    min_total_tasks: int | None = FULL_BENCH_MIN_TASKS,
) -> Path:
    root = Path(base_dir)
    target = Path(output_path) if output_path else root / "README.md"
    if enrich_results:
        enrich_all_results(
            root,
            require_finished=require_finished,
            pass_at_k=pass_at_k,
        )
    if write_run_reports:
        write_all_run_reports(root, require_finished=require_finished)
    entries = discover_latest_runs(
        root,
        require_finished=require_finished,
        min_total_tasks=min_total_tasks,
    )
    markdown = render_aggregate_report(
        entries,
        base_dir=root,
        report_path=target,
        min_total_tasks=min_total_tasks,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return target
