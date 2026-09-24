"""browser-use harness: Playwright agent loop with direct LLM calls."""

from __future__ import annotations

import time
from typing import Any, Optional

from bench_eval.browser_profile import build_browser_profile
from bench_eval.browser_warmup import warmup_browser_session
from bench_eval.config import EvalConfig
from bench_eval.harnesses.base import AgentRunResult, normalize_agent_result
from bench_eval.llm_factory import create_llm
from bench_eval.token_usage import (
    extract_token_usage_by_model_from_history,
    extract_token_usage_from_history,
)
from bench_eval.trajectory import serialize_agent_history


async def run_browser_use_harness(
    task: str,
    *,
    config: EvalConfig,
    task_url: Optional[str] = None,
    entry_url: Optional[str] = None,
    task_key: Optional[str] = None,
) -> AgentRunResult:
    print("[browser-use] loading browser_use package...", flush=True)
    from browser_use import Agent, BrowserSession

    print("[browser-use] creating LLM client...", flush=True)
    llm = create_llm(config)
    print("[browser-use] building browser profile...", flush=True)
    profile = build_browser_profile(config)
    browser_session = BrowserSession(browser_profile=profile)
    navigate_url = entry_url or task_url
    warmup_summary: dict[str, Any] = {"skipped": True}

    if navigate_url:
        print(f"[browser-use] warmup {navigate_url}", flush=True)
        warmup_summary = await warmup_browser_session(
            browser_session,
            navigate_url,
            min_elements=config.agent_warmup_min_elements,
            timeout=config.agent_warmup_timeout,
            settle_seconds=config.agent_warmup_settle_seconds,
            start_timeout=config.agent_browser_start_timeout,
        )
        print(f"[browser-use] warmup done: {warmup_summary}", flush=True)

    agent = Agent(
        task=task,
        llm=llm,
        browser_session=browser_session,
        directly_open_url=False,
        calculate_cost=True,
        max_failures=config.agent_max_failures,
        llm_timeout=config.agent_llm_timeout,
    )

    started_at = time.perf_counter()
    print(
        f"[browser-use] agent.run max_steps={config.agent_max_steps}",
        flush=True,
    )
    history = await agent.run(max_steps=config.agent_max_steps)
    duration_seconds = time.perf_counter() - started_at
    final = history.final_result() if history else None
    trajectory = serialize_agent_history(history)
    token_usage = extract_token_usage_from_history(history)
    token_usage_by_model = extract_token_usage_by_model_from_history(history)
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
            "token_usage_by_model": token_usage_by_model,
        },
        harness="browser-use",
    )
