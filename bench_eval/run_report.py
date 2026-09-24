"""Render Markdown run reports from eval results.json artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from bench_eval.ui_taxonomy_labels import (
    taxonomy_class_description,
    ui_pattern_description,
)


def resolve_results_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_dir():
        results = candidate / "results.json"
        if not results.is_file():
            raise FileNotFoundError(f"results.json not found in {candidate}")
        return results
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(f"Path not found: {candidate}")


def find_latest_results(
    base_dir: str | Path = "tests/eval",
    *,
    model: str | None = None,
    harness: str | None = None,
) -> Path:
    from bench_eval.harness_names import normalize_harness_name
    from bench_eval.results import (
        _LEGACY_RUN_DIR_PATTERN,
        is_run_directory_name,
    )

    root = Path(base_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Eval results base directory not found: {root}")

    candidates: list[tuple[str, Path]] = []

    model_dirs = [root / model] if model else sorted(p for p in root.iterdir() if p.is_dir())
    for model_dir in model_dirs:
        if not model_dir.is_dir():
            continue
        for child in model_dir.iterdir():
            if not child.is_dir():
                continue

            # Legacy layout: tests/eval/<model>/<timestamp>/
            if _LEGACY_RUN_DIR_PATTERN.match(child.name):
                results = child / "results.json"
                if results.is_file():
                    candidates.append((child.name, results))
                continue

            # Current layout: tests/eval/<model>/<harness>/<date>/
            if harness and child.name != normalize_harness_name(harness):
                continue
            for run_dir in child.iterdir():
                if not run_dir.is_dir() or not is_run_directory_name(run_dir.name):
                    continue
                results = run_dir / "results.json"
                if results.is_file():
                    sort_key = f"{child.name}/{run_dir.name}"
                    candidates.append((sort_key, results))

    if not candidates:
        scope_parts = [str(root)]
        if model:
            scope_parts.append(f"model {model!r}")
        if harness:
            scope_parts.append(f"harness {harness!r}")
        raise FileNotFoundError(f"No results.json found under {' / '.join(scope_parts)}")

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def load_results(path: str | Path) -> dict[str, Any]:
    results_path = resolve_results_path(path)
    return json.loads(results_path.read_text(encoding="utf-8"))


def _abs_path(path: str | Path | None, *, base: Path | None = None) -> str:
    if path is None or path == "—":
        return "—"
    candidate = Path(path)
    if not candidate.is_absolute() and base is not None:
        candidate = base / candidate
    try:
        return str(candidate.resolve())
    except (OSError, RuntimeError):
        return str(candidate)


def _repo_root(start: Path | None = None) -> Path | None:
    cursor = start.resolve() if start else Path.cwd()
    for parent in [cursor, *cursor.parents]:
        if (parent / "docs" / "UI_TAXONOMY.md").is_file():
            return parent
    return None


def _pct(value: float | int | None) -> str:
    if value is None:
        return "—"
    return f"{float(value) * 100:.1f}%"


def _seconds(value: float | int | None) -> str:
    if value is None:
        return "—"
    return f"{float(value):.1f}s"


def _steps(value: float | int | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _tokens(value: float | int | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return str(int(round(value)))
    return str(value)


def _status_icon(success: bool | None) -> str:
    if success is True:
        return "✅"
    if success is False:
        return "❌"
    return "—"


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "_Нет данных._\n"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


UI_STATS_SECTIONS: tuple[dict[str, Any], ...] = (
    {
        "title": "UI taxonomy — проверяемые классы",
        "description": (
            "Классы UI из `conditions` и `ui_taxonomy.classes` в конфиге задачи: "
            "какие типы взаимодействий **должны** быть проверены для успеха теста "
            "(например, `BASKET` — добавление в корзину, `DATE` — выбор даты)."
        ),
        "bucket_key": "by_checked_class",
        "key_header": "Класс",
        "describe_key": taxonomy_class_description,
    },
    {
        "title": "UI taxonomy — использованные классы",
        "description": (
            "Классы UI, **фактически зафиксированные** в WebPageBench-телеметрии во время прогона "
            "(по `event_name` событий на backend). Показывает, с какими элементами интерфейса "
            "агент реально взаимодействовал."
        ),
        "bucket_key": "by_used_class",
        "key_header": "Класс",
        "describe_key": taxonomy_class_description,
    },
    {
        "title": "UI taxonomy — primary",
        "description": (
            "Главный UI-класс сценария (`ui_taxonomy.primary`): целевое взаимодействие задачи "
            "(например, `BASKET` для «добавить в корзину», `FILES` для скачивания файла)."
        ),
        "bucket_key": "by_primary",
        "key_header": "Primary",
        "describe_key": taxonomy_class_description,
    },
    {
        "title": "UI patterns",
        "description": (
            "Варианты виджетов из `domain_configs.*.ui_variants` (формат `виджет:вариант`, "
            "например `date:popup_grid`). Описывают **как именно** реализован UI для того же "
            "класса таксономии — календарь-сетка vs native input, pill-кнопки vs popup и т.д."
        ),
        "bucket_key": "by_ui_pattern",
        "key_header": "Паттерн",
        "describe_key": ui_pattern_description,
    },
)


def _render_stats_section(section: dict[str, Any], bucket: dict[str, Any]) -> str:
    if not bucket:
        return ""

    describe_key: Callable[[str], str] = section["describe_key"]
    rows = []
    for key in sorted(bucket):
        row = bucket[key]
        rows.append(
            [
                f"`{key}`",
                describe_key(key),
                str(row.get("passed", 0)),
                str(row.get("failed", 0)),
                str(row.get("total", 0)),
                _pct(row.get("success_rate")),
            ]
        )

    body = _markdown_table(
        [
            section["key_header"],
            "Описание",
            "Passed",
            "Failed",
            "Total",
            "Success rate",
        ],
        rows,
    )
    return f"### {section['title']}\n\n{section['description']}\n\n{body}\n"


def render_run_report(
    data: dict[str, Any],
    *,
    results_path: Path | None = None,
    report_path: Path | None = None,
    generated_by: str = "scripts/render_eval_report.py",
) -> str:
    run = data.get("run") or {}
    tests = data.get("tests") or []
    stats = data.get("ui_taxonomy_stats") or {}

    model = run.get("model", "unknown")
    started_at = run.get("started_at", "—")
    finished_at = run.get("finished_at") or "—"

    resolved_results = results_path.resolve() if results_path else None
    path_base = resolved_results.parent if resolved_results else None

    output_dir = _abs_path(
        run.get("output_dir") or (str(path_base) if path_base else None),
        base=path_base,
    )
    abs_results = _abs_path(
        run.get("results_path") or (str(resolved_results) if resolved_results else None),
        base=path_base,
    )
    abs_dataset = _abs_path(run.get("dataset_path"), base=path_base)
    abs_report = _abs_path(report_path, base=path_base)
    abs_ui_taxonomy_doc = _abs_path("docs/UI_TAXONOMY.md", base=_repo_root(path_base))

    lines = [
        f"# Eval run report: {model}",
        "",
        f"Каталог прогона: `{output_dir}`",
        "",
        "## Сводка",
        "",
        _markdown_table(
            ["Параметр", "Значение"],
            [
                ["Модель", f"`{model}`"],
                ["Провайдер", f"`{run.get('provider', '—')}`"],
                ["Harness", f"`{run.get('agent_harness', '—')}`"],
                ["Mock", f"`{run.get('mock', '—')}`"],
                ["Старт", str(started_at)],
                ["Завершение", str(finished_at)],
                ["Завершён", "да" if run.get("finished") else "нет"],
                ["Задач всего", str(run.get("total_tasks", len(tests)))],
                ["Успешно", str(run.get("passed_tasks", 0))],
                ["Провалено", str(run.get("failed_tasks", 0))],
                ["Success rate", _pct(run.get("success_rate"))],
                ["Суммарное время", _seconds(run.get("total_duration_seconds"))],
                ["Среднее время теста", _seconds(run.get("avg_duration_seconds"))],
                ["Среднее шагов агента", _steps(run.get("avg_agent_steps"))],
                ["Всего токенов", _tokens(run.get("total_tokens"))],
                ["Среднее токенов на задачу", _tokens(run.get("avg_tokens_per_task"))],
                ["Prompt tokens", _tokens(run.get("prompt_tokens"))],
                ["Completion tokens", _tokens(run.get("completion_tokens"))],
                ["Каталог прогона", f"`{output_dir}`"],
                ["results.json", f"`{abs_results}`"],
                ["dataset.json", f"`{abs_dataset}`"],
                ["README.md", f"`{abs_report}`"],
            ],
        ).rstrip(),
        "",
    ]

    stats_block = "".join(
        _render_stats_section(section, stats.get(section["bucket_key"]) or {})
        for section in UI_STATS_SECTIONS
    )
    if stats_block.strip():
        intro = (
            "Агрегаты по UI-таксономии и паттернам виджетов. "
            f"Справочник классов: `{abs_ui_taxonomy_doc}`."
        )
        lines.extend(["## Статистика UI", "", intro, "", stats_block.rstrip(), ""])

    task_rows = []
    for test in sorted(tests, key=lambda row: row.get("test_name") or ""):
        dab = test.get("dab_check") or {}
        task_rows.append(
            [
                _status_icon(test.get("success")),
                f"`{test.get('test_name', '—')}`",
                f"`{test.get('track_id', '—')}`",
                _seconds(test.get("duration_seconds")),
                _steps(test.get("agent_steps")),
                _tokens(test.get("tokens") or (test.get("token_usage") or {}).get("total_tokens")),
                "да" if test.get("agent_is_done") else "нет",
                f"{dab.get('passed', 0)}/{dab.get('total', 0)}",
                (test.get("ui_taxonomy") or {}).get("domain") or "—",
            ]
        )

    lines.extend(
        [
            "## Задачи",
            "",
            _markdown_table(
                [
                    "",
                    "Задача",
                    "Track ID",
                    "Время",
                    "Шаги",
                    "Токены",
                    "Done",
                    "WebPageBench",
                    "Домен",
                ],
                task_rows,
            ).rstrip(),
            "",
        ]
    )

    failed = [test for test in tests if test.get("success") is False]
    if failed:
        lines.append("## Проваленные задачи")
        lines.append("")
        for test in sorted(failed, key=lambda row: row.get("test_name") or ""):
            name = test.get("test_name", "—")
            lines.append(f"### `{name}`")
            lines.append("")
            dab = test.get("dab_check") or {}
            failed_conditions = dab.get("failed_conditions") or []
            if failed_conditions:
                lines.append("**Проваленные conditions:**")
                for item in failed_conditions:
                    lines.append(f"- `{item}`")
                lines.append("")
            if test.get("agent_error"):
                lines.append(f"**Ошибка агента:** {test['agent_error']}")
                lines.append("")
            ui = test.get("ui_taxonomy") or {}
            checked_not_used = ui.get("checked_but_not_used") or []
            if checked_not_used:
                lines.append(
                    "**Проверялись, но не зафиксированы в телеметрии:** "
                    + ", ".join(f"`{item}`" for item in checked_not_used)
                )
                lines.append("")
            patterns = (ui.get("ui_patterns") or {}).get("pattern_keys") or []
            if patterns:
                lines.append("**UI patterns:**")
                for pattern in patterns:
                    lines.append(f"- `{pattern}` — {ui_pattern_description(pattern)}")
                lines.append("")
            if test.get("actual_output"):
                output = str(test["actual_output"]).strip()
                if len(output) > 500:
                    output = output[:500] + "…"
                lines.append("**Ответ агента:**")
                lines.append("")
                lines.append(f"> {output}")
                lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        f"Сгенерировано `{generated_by}` из "
        f"`{abs_results}`."
    )
    lines.append("")
    return "\n".join(lines)


def write_run_report(
    path: str | Path,
    *,
    output_path: str | Path | None = None,
    generated_by: str = "scripts/render_eval_report.py",
) -> Path:
    results_path = resolve_results_path(path)
    data = json.loads(results_path.read_text(encoding="utf-8"))
    target = Path(output_path) if output_path else results_path.parent / "README.md"
    markdown = render_run_report(
        data,
        results_path=results_path,
        report_path=target,
        generated_by=generated_by,
    )
    target.write_text(markdown, encoding="utf-8")
    return target
