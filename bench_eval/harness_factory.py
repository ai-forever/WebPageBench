"""Select and run agent harness adapters for DeepEval."""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, Optional

from bench_eval.config import EvalConfig
from bench_eval.harness_compat import import_harness_runner
from bench_eval.harnesses.base import AgentRunResult
from bench_eval.harness_names import normalize_harness_name

HarnessRunner = Callable[..., Awaitable[AgentRunResult]]

_RUNNER_CACHE: dict[str, HarnessRunner] = {}


def normalize_harness_name(name: str) -> str:
    from bench_eval.harness_names import normalize_harness_name as _normalize

    return _normalize(name)


def available_harnesses() -> tuple[str, ...]:
    from bench_eval.harness_compat import _HARNESS_ENTRYPOINTS

    return tuple(sorted(_HARNESS_ENTRYPOINTS))


def get_harness_runner(config: EvalConfig) -> HarnessRunner:
    harness = normalize_harness_name(config.agent_harness)
    if harness not in _RUNNER_CACHE:
        _RUNNER_CACHE[harness] = import_harness_runner(harness)
    return _RUNNER_CACHE[harness]


async def run_agent(
    task: str,
    *,
    config: EvalConfig,
    task_url: Optional[str] = None,
    entry_url: Optional[str] = None,
    task_key: Optional[str] = None,
) -> AgentRunResult:
    runner = get_harness_runner(config)
    return await runner(
        task,
        config=config,
        task_url=task_url,
        entry_url=entry_url,
        task_key=task_key,
    )


def run_agent_sync(
    task: str,
    *,
    config: EvalConfig,
    task_url: Optional[str] = None,
    entry_url: Optional[str] = None,
    task_key: Optional[str] = None,
) -> AgentRunResult:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio

            nest_asyncio.apply()
            return loop.run_until_complete(
                run_agent(
                    task,
                    config=config,
                    task_url=task_url,
                    entry_url=entry_url,
                    task_key=task_key,
                )
            )
    except RuntimeError:
        pass
    return asyncio.run(
        run_agent(
            task,
            config=config,
            task_url=task_url,
            entry_url=entry_url,
            task_key=task_key,
        )
    )


# Backward-compatible alias used by older imports.
run_browser_agent_sync = run_agent_sync
