"""Ouroboros cut mode: base agent loop with WebPageBench browser-use tools and prompts only."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Optional

from bench_eval.config import EvalConfig
from bench_eval.harnesses.browser_use import run_browser_use_harness
from bench_eval.ouroboros_config import OuroborosHarnessConfig
from bench_eval.retry_utils import retry_backoff_seconds


async def run_ouroboros_cut_loop(
    task: str,
    *,
    config: EvalConfig,
    ouroboros_config: OuroborosHarnessConfig,
    task_url: Optional[str] = None,
    entry_url: Optional[str] = None,
) -> dict[str, Any]:
    """
    Cut measurement mode.

    Ouroboros acts only as the orchestration shell: WebPageBench task prompt + browser-use
    as the sole tool surface (Toolathlon-style external tools). No identity,
    no evolution, no ouroboros-native tool loop.
    """
    prompt = ouroboros_config.build_task_prompt(task)
    started_at = time.perf_counter()
    max_retries = config.llm_max_retries
    browser_result: dict[str, Any] | None = None
    for attempt in range(max_retries + 1):
        try:
            browser_result = dict(
                await run_browser_use_harness(
                    prompt,
                    config=config,
                    task_url=task_url,
                    entry_url=entry_url,
                )
            )
            break
        except (TimeoutError, ConnectionError, OSError) as exc:
            if attempt >= max_retries:
                raise
            await asyncio.sleep(retry_backoff_seconds(attempt))
        except Exception as exc:
            from browser_use.llm.exceptions import ModelProviderError

            if not isinstance(exc, ModelProviderError) or attempt >= max_retries:
                raise
            await asyncio.sleep(retry_backoff_seconds(attempt))

    if browser_result is None:
        raise RuntimeError("Ouroboros cut loop failed without a browser result")
    browser_result["harness_metadata"] = {
        "mode": "cut",
        "loop_engine": "ouroboros-cut",
        "tool_surface": "dab-browser-use",
        "executor": "browser-use",
        "memory_mode": "empty",
        "include_identity": False,
        "evolution_enabled": False,
        "prompt_source": "dab",
        "llm_max_retries": max_retries,
    }
    browser_result["duration_seconds"] = float(
        browser_result.get("duration_seconds") or (time.perf_counter() - started_at)
    )
    return browser_result
