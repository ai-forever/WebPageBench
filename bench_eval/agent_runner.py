"""Run browser agents via selectable harness adapters."""

from __future__ import annotations

from bench_eval.harness_factory import (
    available_harnesses,
    get_harness_runner,
    normalize_harness_name,
    run_agent,
    run_agent_sync,
    run_browser_agent_sync,
)
from bench_eval.harnesses.browser_use import run_browser_use_harness

__all__ = [
    "available_harnesses",
    "get_harness_runner",
    "normalize_harness_name",
    "run_agent",
    "run_agent_sync",
    "run_browser_agent_sync",
    "run_browser_use_harness",
    "run_browser_agent",
]

# Legacy async entry point.
run_browser_agent = run_browser_use_harness
