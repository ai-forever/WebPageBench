"""Load leaderboard entries from liderboard/results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.bench_config import load_bench_config
from src.export_results import (
    _cost_from_payload,
    _recorded_cost_from_payload,
    _total_agent_steps_from_payload,
    raw_results_path_for,
    ui_classes_from_payload,
)
from src.models import LeaderboardEntry
from src.token_display import reconcile_entry_usage_totals, token_usage_from_run

_RAW_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


def space_root(root: Path | None = None) -> Path:
    return root or Path(__file__).resolve().parent.parent


def results_dir(root: Path | None = None) -> Path:
    return space_root(root) / "results"


def _resolve_raw_path(entry: LeaderboardEntry, root: Path | None = None) -> Path | None:
    base = space_root(root)
    if entry.raw_results_path:
        raw_path = base / entry.raw_results_path
        if raw_path.is_file():
            return raw_path
    fallback = raw_results_path_for(entry, base)
    if fallback.is_file():
        return fallback
    return None


def load_raw_results(entry: LeaderboardEntry, root: Path | None = None) -> dict[str, Any] | None:
    raw_path = _resolve_raw_path(entry, root)
    if raw_path is None:
        return None
    cache_key = str(raw_path.resolve())
    try:
        mtime = raw_path.stat().st_mtime
    except OSError:
        mtime = 0.0
    cached = _RAW_CACHE.get(cache_key)
    if cached is not None and cached[0] == mtime:
        return cached[1]
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    _RAW_CACHE[cache_key] = (mtime, payload)
    return payload


def _enrich_entry_from_raw(entry: LeaderboardEntry, raw: dict[str, Any]) -> None:
    run = raw.get("run") or {}
    if not entry.ui_classes:
        entry.ui_classes = ui_classes_from_payload(raw)
    if not entry.token_usage_by_model:
        entry.token_usage_by_model = token_usage_from_run(run)
    if entry.total_cost_usd is None or entry.total_cost_usd <= 0:
        recorded = _recorded_cost_from_payload(raw)
        if recorded is not None:
            total_cost, avg_cost = recorded
        else:
            total_cost, avg_cost = _cost_from_payload(raw)
        if total_cost is not None and total_cost > 0:
            entry.total_cost_usd = total_cost
            entry.avg_cost_per_task_usd = avg_cost
    if entry.total_tokens is None and isinstance(run.get("total_tokens"), (int, float)):
        entry.total_tokens = int(run["total_tokens"])
    if entry.avg_tokens_per_task is None and isinstance(run.get("avg_tokens_per_task"), (int, float)):
        entry.avg_tokens_per_task = float(run["avg_tokens_per_task"])
    if entry.total_duration_seconds is None and isinstance(run.get("total_duration_seconds"), (int, float)):
        entry.total_duration_seconds = float(run["total_duration_seconds"])
    if entry.total_agent_steps is None:
        total_steps = _total_agent_steps_from_payload(raw)
        if total_steps is not None:
            entry.total_agent_steps = total_steps
    slots = run.get("ouroboros_model_slots")
    if isinstance(slots, dict) and slots and not entry.ouroboros_model_slots:
        entry.ouroboros_model_slots = {
            str(slot): [str(model) for model in models]
            for slot, models in slots.items()
            if isinstance(models, list) and models
        }
    reconcile_entry_usage_totals(entry)


def load_entry_file(path: Path) -> LeaderboardEntry | None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "metrics" not in payload:
        return None
    entry = LeaderboardEntry.from_json(payload)
    if not entry.raw_results_path:
        raw_path = raw_results_path_for(entry, space_root(path.parent.parent))
        if raw_path.is_file():
            entry.raw_results_path = str(raw_path.relative_to(space_root(path.parent.parent)).as_posix())
    needs_raw = (
        not entry.ui_classes
        or not entry.token_usage_by_model
        or entry.total_cost_usd is None
        or entry.total_cost_usd <= 0
        or entry.total_tokens is None
        or entry.avg_tokens_per_task is None
        or entry.total_duration_seconds is None
        or entry.total_agent_steps is None
        or (entry.harness.startswith("ouroboros-full") and not entry.ouroboros_model_slots)
    )
    if needs_raw:
        raw = load_raw_results(entry, space_root(path.parent.parent))
        if raw:
            _enrich_entry_from_raw(entry, raw)
    else:
        reconcile_entry_usage_totals(entry)
    return entry


def load_entries(results_path: Path | None = None) -> list[LeaderboardEntry]:
    root = results_path or results_dir()
    if not root.is_dir():
        return []
    entries: list[LeaderboardEntry] = []
    for path in sorted(root.glob("*.json")):
        entry = load_entry_file(path)
        if entry is not None:
            entries.append(entry)
    return sorted(
        entries,
        key=lambda entry: entry.success_rate if entry.success_rate is not None else -1,
        reverse=True,
    )


def entry_label(entry: LeaderboardEntry) -> str:
    return f"{entry.model} · {entry.harness}"


def entry_choices(entries: list[LeaderboardEntry]) -> list[tuple[str, str]]:
    return [(entry_label(entry), entry.entry_id) for entry in entries]


def entry_by_id(entries: list[LeaderboardEntry], entry_id: str) -> LeaderboardEntry | None:
    for entry in entries:
        if entry.entry_id == entry_id:
            return entry
    return None


FILTER_ALL = "all"
INPUT_FILTER_ORDER = ("text", "text+image", "image")


def filter_entries(
    entries: list[LeaderboardEntry],
    *,
    input_id: str | None = FILTER_ALL,
    harness_id: str | None = FILTER_ALL,
) -> list[LeaderboardEntry]:
    filtered = entries
    if input_id and input_id != FILTER_ALL:
        filtered = [entry for entry in filtered if entry.input_modality == input_id]
    if harness_id and harness_id != FILTER_ALL:
        filtered = [entry for entry in filtered if entry.harness == harness_id]
    return filtered


def input_filter_choices(entries: list[LeaderboardEntry]) -> list[tuple[str, str]]:
    present = {entry.input_modality for entry in entries if entry.input_modality not in {"", "—"}}
    ordered = [name for name in INPUT_FILTER_ORDER if name in present]
    ordered.extend(sorted(present - set(INPUT_FILTER_ORDER)))
    return [("All inputs", FILTER_ALL), *[(name, name) for name in ordered]]


def harness_filter_choices(entries: list[LeaderboardEntry]) -> list[tuple[str, str]]:
    names = sorted({entry.harness for entry in entries if entry.harness})
    return [("All harnesses", FILTER_ALL), *[(name, name) for name in names]]


def sort_entries(entries: list[LeaderboardEntry], view_id: str) -> list[LeaderboardEntry]:
    config = load_bench_config()
    view = next((row for row in config["views"] if row["id"] == view_id), config["views"][0])
    key = view["sort_key"]
    reverse = not view.get("ascending", False)

    def sort_value(entry: LeaderboardEntry) -> float:
        value = entry.metric(key)
        if value is None:
            return float("inf") if view.get("ascending") else -1.0
        return float(value)

    return sorted(entries, key=sort_value, reverse=reverse)
