"""OpenManus harness: Manus-style planner prompts on top of browser-use."""

from __future__ import annotations

import os
import time
from typing import Any, Optional

from bench_eval.browser_profile import build_browser_profile
from bench_eval.browser_warmup import warmup_browser_session
from bench_eval.config import EvalConfig
from bench_eval.harnesses.base import AgentRunResult, normalize_agent_result
from bench_eval.llm_factory import create_llm
from bench_eval.openmanus_config import (
    DEFAULT_OPENMANUS_CONFIG_PATH,
    load_openmanus_harness_config,
)
from bench_eval.token_usage import extract_token_usage_from_history
from bench_eval.trajectory import serialize_agent_history


async def run_openmanus_harness(
    task: str,
    *,
    config: EvalConfig,
    task_url: Optional[str] = None,
    entry_url: Optional[str] = None,
    task_key: Optional[str] = None,
) -> AgentRunResult:
    from browser_use import Agent, BrowserSession

    openmanus_config = load_openmanus_harness_config(
        os.getenv("OPENMANUS_CONFIG_PATH", DEFAULT_OPENMANUS_CONFIG_PATH)
    )
    llm = create_llm(config)
    profile = build_browser_profile(config)
    browser_session = BrowserSession(browser_profile=profile)
    navigate_url = entry_url or task_url
    warmup_summary: dict[str, Any] = {"skipped": True}

    if navigate_url:
        print(f"[openmanus] warmup {navigate_url}", flush=True)
        warmup_summary = await warmup_browser_session(
            browser_session,
            navigate_url,
            min_elements=config.agent_warmup_min_elements,
            timeout=config.agent_warmup_timeout,
            settle_seconds=config.agent_warmup_settle_seconds,
            start_timeout=config.agent_browser_start_timeout,
        )
        print(f"[openmanus] warmup done: {warmup_summary}", flush=True)

    agent = Agent(
        task=task,
        llm=llm,
        browser_session=browser_session,
        directly_open_url=False,
        calculate_cost=True,
        max_failures=config.agent_max_failures,
        llm_timeout=config.agent_llm_timeout,
        extend_system_message=openmanus_config.extend_system_message,
    )

    started_at = time.perf_counter()
    print(
        f"[openmanus] agent.run max_steps={config.agent_max_steps} "
        f"max_failures={config.agent_max_failures} "
        f"llm_timeout={config.agent_llm_timeout:.0f}s",
        flush=True,
    )
    history = await agent.run(max_steps=config.agent_max_steps)
    duration_seconds = time.perf_counter() - started_at
    final = history.final_result() if history else None
    trajectory = serialize_agent_history(history)
    token_usage = extract_token_usage_from_history(history)
    step_count = trajectory["summary"].get("step_count")
    if not step_count and history and getattr(history, "history", None):
        step_count = len(history.history)

    return normalize_agent_result(
        {
            "final_result": final,
            "steps": step_count or 0,
            "task_url": task_url,
            "entry_url": navigate_url,
            "warmup": warmup_summary,
            "is_done": bool(history and history.is_done()),
            "duration_seconds": duration_seconds,
            "trajectory": trajectory,
            "history": history,
            "token_usage": token_usage,
            "harness_metadata": {
                "integration_mode": openmanus_config.integration_mode,
                "prompt_source": openmanus_config.prompt_source,
                "config_path": os.getenv(
                    "OPENMANUS_CONFIG_PATH",
                    DEFAULT_OPENMANUS_CONFIG_PATH,
                ),
                "task_key": task_key,
            },
        },
        harness="openmanus",
    )
