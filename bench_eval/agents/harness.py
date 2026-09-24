"""Bench harness adapter: run a registered GUI model on one benchmark task.

Registered in ``bench_eval.harness_compat`` under the family names, so the whole
existing pipeline (tracks → DeepEval → results.json → leaderboard) works with
``AGENT_HARNESS=qwen3-vl`` exactly as it does with ``AGENT_HARNESS=browser-use``.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Optional

from bench_eval.agents.core import dump
from bench_eval.agents.core.executor import BrowserComputer
from bench_eval.agents.core.loop import run_agent_loop
from bench_eval.agents.core.registry import resolve
from bench_eval.agents.core.settings import build_agent, build_settings
from bench_eval.config import EvalConfig
from bench_eval.harnesses.base import AgentRunResult, normalize_agent_result

#: AGENT_HARNESS values handled here.
GUI_HARNESSES = ("qwen3-vl", "uitars", "jedi", "opencua", "evocua", "fara", "gui-agent")

_FAMILY_BY_HARNESS = {
    "qwen3-vl": "qwen3_vl",
    "uitars": "uitars",
    "jedi": "jedi",
    "opencua": "opencua",
    "evocua": "evocua",
    "fara": "fara",
}


def resolve_model_name(config: EvalConfig) -> str:
    """Pick the registry model for this run.

    ``GUI_AGENT_MODEL`` wins; otherwise ``LLM_MODEL`` is tried (so existing
    ``envs/models/*.env`` keep working); otherwise the harness name selects the
    family default.
    """
    harness = (config.agent_harness or "").strip().lower().replace("_", "-")
    family = _FAMILY_BY_HARNESS.get(harness)

    for candidate in (os.getenv("GUI_AGENT_MODEL"), config.llm_model):
        if not candidate:
            continue
        try:
            spec = resolve(candidate)
        except KeyError:
            continue
        if family and spec.family != family:
            # LLM_MODEL points at another family: trust the harness name instead.
            continue
        return spec.name

    if family:
        return resolve(family).name
    raise ValueError(
        f"Cannot resolve a GUI model for AGENT_HARNESS={config.agent_harness!r}: "
        "set GUI_AGENT_MODEL to a registered model name "
        "(python -m bench_eval.agents.cli.models)."
    )


async def run_gui_agent_harness(
    task: str,
    *,
    config: EvalConfig,
    task_url: Optional[str] = None,
    entry_url: Optional[str] = None,
    task_key: Optional[str] = None,
) -> AgentRunResult:
    harness = (config.agent_harness or "gui-agent").strip().lower().replace("_", "-")
    model_name = resolve_model_name(config)
    dump.set_context(task_key=task_key, harness=harness, model=model_name)
    settings = build_settings(model_name, eval_config=config)
    if settings.save_screenshots and task_key:
        settings.screenshot_dir = str(
            Path(settings.screenshot_dir or _default_screenshot_root(config)) / task_key
        )

    print(
        f"[{harness}] model={model_name} endpoint={settings.endpoint.base_url} "
        f"served={settings.endpoint.model} coords={settings.coordinate_space.value} "
        f"max_steps={settings.max_steps}",
        flush=True,
    )

    agent = build_agent(settings)
    computer = BrowserComputer.from_eval_config(
        config,
        width=settings.screen_width,
        height=settings.screen_height,
    )
    computer.settle_seconds = settings.action_settle_seconds

    navigate_url = entry_url or task_url
    warmup: dict[str, Any] = {"skipped": True}
    started_at = time.perf_counter()
    error: Optional[str] = None

    try:
        await computer.start()
        if navigate_url:
            warmup_started = time.perf_counter()
            await computer.goto(
                navigate_url,
                wait_seconds=config.agent_warmup_settle_seconds,
                timeout=config.agent_warmup_timeout,
            )
            warmup = {
                "skipped": False,
                "url": navigate_url,
                "duration_seconds": round(time.perf_counter() - warmup_started, 3),
            }

        loop_result = await run_agent_loop(
            agent,
            computer,
            task,
            settings=settings,
            log_prefix=harness,
        )
    except Exception as exc:  # noqa: BLE001 - reported as a failed task, not a crash
        error = f"{type(exc).__name__}: {exc}"
        duration = time.perf_counter() - started_at
        usage, by_model = agent.ledger.snapshot()
        return normalize_agent_result(
            {
                "final_result": None,
                "steps": 0,
                "task_url": task_url,
                "entry_url": navigate_url,
                "warmup": warmup,
                "is_done": False,
                "duration_seconds": duration,
                "trajectory": {"steps": [], "summary": {"errors": [error]}},
                "token_usage": usage,
                "token_usage_by_model": by_model,
                "harness_metadata": {"model": model_name, "task_key": task_key},
                "error": error,
            },
            harness=harness,
        )
    finally:
        await computer.close()
        await agent.close()

    metadata = {
        "model": model_name,
        "family": settings.spec.family,
        "served_model": settings.endpoint.model,
        "base_url": settings.endpoint.base_url,
        "action_space": settings.spec.action_space.name,
        "coordinate_space": settings.coordinate_space.value,
        "options": settings.options,
        "task_key": task_key,
        "status": loop_result.status,
    }

    return normalize_agent_result(
        {
            "final_result": loop_result.final_result,
            "steps": loop_result.step_count,
            "task_url": task_url,
            "entry_url": navigate_url,
            "warmup": warmup,
            "is_done": loop_result.is_done,
            "duration_seconds": loop_result.duration_seconds,
            "trajectory": loop_result.trajectory(harness=harness, metadata=metadata),
            "token_usage": loop_result.token_usage,
            "token_usage_by_model": loop_result.token_usage_by_model,
            "harness_metadata": metadata,
            "error": loop_result.error,
        },
        harness=harness,
    )


def _default_screenshot_root(config: EvalConfig) -> str:
    base = config.eval_output_dir or config.eval_results_base_dir
    return str(Path(base) / "screenshots")
