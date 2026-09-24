"""Leaderboard entry schema for WebPageBench."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


def public_source_path(value: str | None) -> str | None:
    """Keep only portable relative paths; drop machine-local absolute paths."""
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.startswith("\\\\") or (len(text) >= 2 and text[1] == ":"):
        return None
    if text.startswith("/") and not text.startswith("results/"):
        return None
    return text.replace("\\", "/")


def entry_id_for(model: str, harness: str) -> str:
    safe = re.sub(r"[^\w.\-]+", "_", f"{model}__{harness}".strip())
    return safe or "unknown"


def reconcile_success_metrics(entry: LeaderboardEntry) -> None:
    """Primary success rate is always passed_tasks / total_tasks (WebPageBench)."""
    section_passed = sum(section.passed for section in entry.sections.values())
    section_total = sum(section.total for section in entry.sections.values())
    if section_total > 0 and entry.total_tasks <= 0:
        entry.total_tasks = section_total
        entry.passed_tasks = section_passed
        entry.failed_tasks = section_total - section_passed
    if entry.total_tasks > 0:
        entry.success_rate = entry.passed_tasks / entry.total_tasks
        entry.failed_tasks = entry.total_tasks - entry.passed_tasks


@dataclass
class SectionStats:
    section_id: str
    label: str
    success_rate: float | None
    passed: int
    total: int
    tasks: dict[str, bool] = field(default_factory=dict)


@dataclass
class LeaderboardEntry:
    model: str
    harness: str
    provider: str | None = None
    mock: str | None = None
    finished: bool = True
    source_path: str | None = None
    submitted_at: str | None = None

    success_rate: float | None = None
    passed_tasks: int = 0
    failed_tasks: int = 0
    total_tasks: int = 0

    avg_duration_seconds: float | None = None
    total_duration_seconds: float | None = None
    total_agent_steps: int | None = None
    avg_agent_steps: float | None = None
    avg_tokens_per_task: float | None = None
    total_tokens: int | None = None
    total_cost_usd: float | None = None
    avg_cost_per_task_usd: float | None = None
    token_usage_by_model: dict[str, dict[str, Any]] = field(default_factory=dict)
    ouroboros_model_slots: dict[str, list[str]] = field(default_factory=dict)

    pass_at_k: float | None = None
    agent_completion_rate: float | None = None
    agent_dab_agreement_rate: float | None = None

    sections: dict[str, SectionStats] = field(default_factory=dict)
    ui_badges: list[str] = field(default_factory=list)
    ui_classes: dict[str, dict[str, Any]] = field(default_factory=dict)
    section_avg_rate: float | None = None
    raw_results_path: str | None = None

    @property
    def entry_id(self) -> str:
        return entry_id_for(self.model, self.harness)

    @property
    def success_pct(self) -> float | None:
        if self.success_rate is None:
            return None
        return round(self.success_rate * 100, 2)

    @property
    def input_modality(self) -> str:
        from src.input_modality import harness_input

        return harness_input(self.model, self.harness)

    @property
    def full_bench_success_rate(self) -> float | None:
        from src.bench_config import task_count

        if self.total_tasks >= task_count():
            return self.success_rate
        return None

    @property
    def value_score(self) -> float | None:
        if self.success_rate is None or not self.total_cost_usd or self.total_cost_usd <= 0:
            return None
        return self.success_rate / self.total_cost_usd

    def metric(self, name: str) -> float | None:
        if name.startswith("domain:"):
            section_id = name.split(":", 1)[1]
            section = self.sections.get(section_id)
            return section.success_rate if section else None
        if name.startswith("taxonomy:"):
            class_id = name.split(":", 1)[1]
            row = self.ui_classes.get(class_id)
            if not row:
                return None
            rate = row.get("success_rate")
            return float(rate) if isinstance(rate, (int, float)) else None
        if name == "success_rate":
            return self.success_rate
        if name == "full_bench_success_rate":
            return self.full_bench_success_rate
        if name == "avg_duration_seconds":
            return self.avg_duration_seconds
        if name == "total_duration_seconds":
            return self.total_duration_seconds
        if name == "total_agent_steps":
            return float(self.total_agent_steps) if self.total_agent_steps is not None else None
        if name == "total_cost_usd":
            return self.total_cost_usd
        if name == "value_score":
            return self.value_score
        return getattr(self, name, None)

    def to_json(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "harness": self.harness,
            "provider": self.provider,
            "mock": self.mock,
            "finished": self.finished,
            "source_path": public_source_path(self.source_path),
            "submitted_at": self.submitted_at,
            "metrics": {
                "success_rate": self.success_rate,
                "passed_tasks": self.passed_tasks,
                "failed_tasks": self.failed_tasks,
                "total_tasks": self.total_tasks,
                "avg_duration_seconds": self.avg_duration_seconds,
                "total_duration_seconds": self.total_duration_seconds,
                "total_agent_steps": self.total_agent_steps,
                "avg_agent_steps": self.avg_agent_steps,
                "avg_tokens_per_task": self.avg_tokens_per_task,
                "total_tokens": self.total_tokens,
                "total_cost_usd": self.total_cost_usd,
                "avg_cost_per_task_usd": self.avg_cost_per_task_usd,
                "token_usage_by_model": self.token_usage_by_model,
                "ouroboros_model_slots": self.ouroboros_model_slots,
                "pass_at_k": self.pass_at_k,
                "agent_completion_rate": self.agent_completion_rate,
                "agent_dab_agreement_rate": self.agent_dab_agreement_rate,
                "section_avg_rate": self.section_avg_rate,
            },
            "sections": {
                section_id: {
                    "label": stats.label,
                    "success_rate": stats.success_rate,
                    "passed": stats.passed,
                    "total": stats.total,
                    "tasks": stats.tasks,
                }
                for section_id, stats in self.sections.items()
            },
            "ui_badges": self.ui_badges,
            "ui_classes": self.ui_classes,
            "section_avg_rate": self.section_avg_rate,
            "raw_results_path": self.raw_results_path,
            "entry_id": self.entry_id,
        }

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> LeaderboardEntry:
        if "metrics" in payload:
            metrics = payload.get("metrics") or {}
            sections_raw = payload.get("sections") or {}
            sections = {
                section_id: SectionStats(
                    section_id=section_id,
                    label=(data.get("label") or section_id),
                    success_rate=data.get("success_rate"),
                    passed=int(data.get("passed") or 0),
                    total=int(data.get("total") or 0),
                    tasks={k: bool(v) for k, v in (data.get("tasks") or {}).items()},
                )
                for section_id, data in sections_raw.items()
            }
            entry = cls(
                model=str(payload.get("model") or "unknown"),
                harness=str(payload.get("harness") or "unknown"),
                provider=payload.get("provider"),
                mock=payload.get("mock"),
                finished=bool(payload.get("finished", True)),
                source_path=public_source_path(payload.get("source_path")),
                submitted_at=payload.get("submitted_at"),
                success_rate=metrics.get("success_rate"),
                passed_tasks=int(metrics.get("passed_tasks") or 0),
                failed_tasks=int(metrics.get("failed_tasks") or 0),
                total_tasks=int(metrics.get("total_tasks") or 0),
                avg_duration_seconds=metrics.get("avg_duration_seconds"),
                total_duration_seconds=metrics.get("total_duration_seconds"),
                total_agent_steps=metrics.get("total_agent_steps"),
                avg_agent_steps=metrics.get("avg_agent_steps"),
                avg_tokens_per_task=metrics.get("avg_tokens_per_task"),
                total_tokens=metrics.get("total_tokens"),
                total_cost_usd=metrics.get("total_cost_usd"),
                avg_cost_per_task_usd=metrics.get("avg_cost_per_task_usd"),
                token_usage_by_model=dict(metrics.get("token_usage_by_model") or {}),
                ouroboros_model_slots={
                    slot: [str(model) for model in models]
                    for slot, models in (metrics.get("ouroboros_model_slots") or {}).items()
                    if isinstance(models, list)
                },
                pass_at_k=metrics.get("pass_at_k"),
                agent_completion_rate=metrics.get("agent_completion_rate"),
                agent_dab_agreement_rate=metrics.get("agent_dab_agreement_rate"),
                sections=sections,
                ui_badges=list(payload.get("ui_badges") or []),
                ui_classes=dict(payload.get("ui_classes") or {}),
                section_avg_rate=metrics.get("section_avg_rate") or payload.get("section_avg_rate"),
                raw_results_path=payload.get("raw_results_path"),
            )
            reconcile_success_metrics(entry)
            return entry
        entry = from_legacy_payload(payload)
        reconcile_success_metrics(entry)
        return entry


def from_legacy_payload(payload: dict[str, Any]) -> LeaderboardEntry:
    """Convert pre-refactor LIBRA-style JSON."""
    from src.bench_config import load_bench_config

    config = load_bench_config()
    sections: dict[str, SectionStats] = {}
    for section_id, meta in config["sections"].items():
        block = payload.get(section_id) or payload.get(meta["domain"]) or {}
        if not isinstance(block, dict):
            continue
        tasks = {
            task: bool(block.get(task, 0) >= 0.5)
            for task in meta["tasks"]
            if isinstance(block.get(task), (int, float))
        }
        passed = sum(1 for ok in tasks.values() if ok)
        total = len(tasks)
        domain_total = block.get("domain_total_score")
        success_rate = float(domain_total) if isinstance(domain_total, (int, float)) else None
        if success_rate is None and total:
            success_rate = passed / total
        sections[section_id] = SectionStats(
            section_id=section_id,
            label=meta["label"],
            success_rate=success_rate,
            passed=passed,
            total=total,
            tasks=tasks,
        )

    section_avg_rate = payload.get("total_score")
    if not isinstance(section_avg_rate, (int, float)) and sections:
        rates = [s.success_rate for s in sections.values() if s.success_rate is not None]
        section_avg_rate = sum(rates) / len(rates) if rates else None

    entry = LeaderboardEntry(
        model=str(payload.get("model") or "unknown"),
        harness=str(payload.get("harness") or "unknown"),
        total_tasks=sum(section.total for section in sections.values()),
        passed_tasks=sum(section.passed for section in sections.values()),
        sections=sections,
        section_avg_rate=float(section_avg_rate) if isinstance(section_avg_rate, (int, float)) else None,
    )
    reconcile_success_metrics(entry)
    return entry
