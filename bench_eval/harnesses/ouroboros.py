"""Decoupled ouroboros harness modes for WebPageBench eval (cut / full_isolated / full_evolving)."""

from __future__ import annotations

import time
from typing import Any, Optional

from bench_eval.config import EvalConfig
from bench_eval.harnesses.base import AgentRunResult, normalize_agent_result
from bench_eval.ouroboros_client import (
    OuroborosUnavailableError,
    check_ouroboros_available,
    run_ouroboros_full_task,
)
from bench_eval.ouroboros_config import load_ouroboros_harness_config
from bench_eval.ouroboros_cut_loop import run_ouroboros_cut_loop
from bench_eval.ouroboros_session import get_ouroboros_session


def _resolve_mode(config: EvalConfig) -> str:
    from bench_eval.harness_names import normalize_harness_name

    harness = normalize_harness_name(config.agent_harness)
    mapping = {
        "ouroboros-cut": "cut",
        "ouroboros-full-isolated": "full_isolated",
        "ouroboros-full-evolving": "full_evolving",
    }
    return mapping[harness]


async def run_ouroboros_harness(
    task: str,
    *,
    config: EvalConfig,
    task_url: Optional[str] = None,
    entry_url: Optional[str] = None,
    task_key: Optional[str] = None,
) -> AgentRunResult:
    """
    Run one of the ouroboros measurement modes.

    - cut: ouroboros shell + WebPageBench prompts + browser-use tools, per-task empty drive
    - full_isolated: full ouroboros runtime, forked drive per task, no evolution
    - full_evolving: full ouroboros runtime, shared drive, evolution between tasks
    """
    mode = _resolve_mode(config)
    ouroboros_config = load_ouroboros_harness_config(
        config.ouroboros_config_path,
        mode=mode,
    )
    session = get_ouroboros_session(config)
    task_drive = session.prepare_task_drive(task_key or "task") if session else None

    prompt = ouroboros_config.build_task_prompt(task)
    if entry_url or task_url:
        prompt = f"{prompt}\n\nStart URL: {entry_url or task_url}"

    started_at = time.perf_counter()
    harness_metadata: dict[str, Any] = {
        "mode": ouroboros_config.mode,
        "memory_mode": ouroboros_config.memory_mode,
        "include_identity": ouroboros_config.include_identity,
        "evolution_enabled": ouroboros_config.evolution_enabled,
        "shared_drive": ouroboros_config.shared_drive,
        "per_task_drive": ouroboros_config.per_task_drive,
        "config_path": ouroboros_config.config_path,
        "llm_max_retries": config.llm_max_retries,
    }
    if task_drive is not None:
        harness_metadata["drive_root"] = str(task_drive.drive_root)

    if mode == "cut":
        result = await run_ouroboros_cut_loop(
            task,
            config=config,
            ouroboros_config=ouroboros_config,
            task_url=task_url,
            entry_url=entry_url,
        )
        harness_metadata.update(result.pop("harness_metadata", {}))
    else:
        availability = check_ouroboros_available(
            ouroboros_config,
            max_retries=config.llm_max_retries,
        )
        harness_metadata["ouroboros_availability"] = availability
        if not availability.get("ok"):
            raise OuroborosUnavailableError(
                "Full ouroboros modes require a running Ouroboros server "
                f"({ouroboros_config.ouroboros_url}) or OUROBOROS_BIN on PATH. "
                f"Details: {availability.get('error') or availability}"
            )
        if task_drive is None:
            raise RuntimeError("Ouroboros session drive was not initialized")
        result = run_ouroboros_full_task(
            prompt,
            config=ouroboros_config,
            drive_root=task_drive.drive_root,
            timeout_seconds=ouroboros_config.ouroboros_timeout_seconds,
            max_retries=config.llm_max_retries,
        )
        harness_metadata.update(result.pop("harness_metadata", {}))

    if session is not None and task_drive is not None:
        session.finalize_task(task_drive, agent_summary=result)

    duration_seconds = float(result.get("duration_seconds") or 0.0)
    if duration_seconds <= 0:
        duration_seconds = time.perf_counter() - started_at

    merged = dict(result)
    merged["duration_seconds"] = duration_seconds
    merged["harness_metadata"] = harness_metadata
    harness_name = config.agent_harness.replace("_", "-")
    merged["harness"] = harness_name
    return normalize_agent_result(merged, harness=harness_name)
