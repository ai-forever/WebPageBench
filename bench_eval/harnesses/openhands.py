"""OpenHands harness: SDK agent with BrowserToolSet (browser-use backend)."""

from __future__ import annotations

import asyncio
import os
import tempfile
import time
from typing import Any, Optional

from bench_eval.config import EvalConfig
from bench_eval.browser_profile import openhands_browser_tool_params
from bench_eval.harness_llm import create_openhands_llm
from bench_eval.openhands_browser_patch import (
    apply_openhands_browser_get_state_patch,
    apply_openhands_browser_executor_close_patch,
    prepare_openhands_runtime,
    ensure_openhands_browser_executor_ready,
)
from bench_eval.harness_trajectory import (
    openhands_content_to_text,
    serialize_openhands_events,
)
from bench_eval.harnesses.base import AgentRunResult, normalize_agent_result
from bench_eval.token_usage import empty_token_usage, normalize_token_usage


def _extract_openhands_final(events: Any) -> Optional[str]:
    from openhands.sdk.event.llm_convertible.message import MessageEvent

    for event in reversed(list(events)):
        if not isinstance(event, MessageEvent):
            continue
        if event.source != "agent":
            continue
        text = openhands_content_to_text(event.llm_message.content)
        if text:
            return text
    return None


def _extract_openhands_token_usage(conversation: Any) -> dict[str, int]:
    usage = empty_token_usage()
    stats = getattr(conversation, "conversation_stats", None)
    if stats is None:
        return usage

    prompt_tokens = 0
    completion_tokens = 0
    llm_calls = 0
    for metrics in stats.usage_to_metrics.values():
        accumulated = getattr(metrics, "accumulated_token_usage", None)
        if accumulated is None:
            continue
        prompt_tokens += int(getattr(accumulated, "prompt_tokens", 0) or 0)
        completion_tokens += int(getattr(accumulated, "completion_tokens", 0) or 0)
        llm_calls += len(getattr(metrics, "token_usages", []) or [])

    return normalize_token_usage(
        {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "llm_calls": llm_calls,
        }
    )


def _run_openhands_sync(
    task: str,
    *,
    config: EvalConfig,
    navigate_url: Optional[str],
    task_key: Optional[str],
) -> dict[str, Any]:
    os.environ.setdefault("OPENHANDS_SUPPRESS_BANNER", "1")
    prepare_openhands_runtime()

    from openhands.sdk.agent import Agent
    from openhands.sdk.conversation import Conversation
    from openhands.sdk.conversation.state import ConversationExecutionStatus
    from openhands.sdk.tool import Tool
    from openhands.tools.browser_use import BrowserToolSet

    ensure_openhands_browser_executor_ready()
    apply_openhands_browser_executor_close_patch()
    apply_openhands_browser_get_state_patch()

    prompt = task.strip()
    if navigate_url:
        prompt = f"{prompt}\n\nStart URL: {navigate_url}"

    llm = create_openhands_llm(config)
    browser_params = openhands_browser_tool_params(config)
    tools = [Tool(name=BrowserToolSet.name, params=browser_params)]
    agent = Agent(llm=llm, tools=tools)

    workspace = tempfile.mkdtemp(prefix="dab-openhands-")
    conversation = None
    try:
        conversation = Conversation(
            agent=agent,
            workspace=workspace,
            max_iteration_per_run=config.agent_max_steps,
            visualizer=None,
            # Keep the shared BrowserToolExecutor alive for the next benchmark task.
            delete_on_close=False,
        )
        print(
            f"[openhands] run max_iteration_per_run={config.agent_max_steps}",
            flush=True,
        )
        conversation.send_message(prompt)
        conversation.run()
        status = conversation.state.execution_status
        events = list(conversation.state.events)
        final = _extract_openhands_final(events)
        trajectory = serialize_openhands_events(events, harness="openhands")
        token_usage = _extract_openhands_token_usage(conversation)
        return {
            "final_result": final,
            "steps": trajectory["summary"].get("step_count", 0),
            "is_done": status == ConversationExecutionStatus.FINISHED,
            "trajectory": trajectory,
            "history": events,
            "token_usage": token_usage,
            "harness_metadata": {
                "workspace": workspace,
                "execution_status": str(status),
                "task_key": task_key,
            },
        }
    finally:
        if conversation is not None:
            close = getattr(conversation, "close", None)
            if callable(close):
                close()
        ensure_openhands_browser_executor_ready()


async def run_openhands_harness(
    task: str,
    *,
    config: EvalConfig,
    task_url: Optional[str] = None,
    entry_url: Optional[str] = None,
    task_key: Optional[str] = None,
) -> AgentRunResult:
    navigate_url = entry_url or task_url
    started_at = time.perf_counter()
    payload = await asyncio.to_thread(
        _run_openhands_sync,
        task,
        config=config,
        navigate_url=navigate_url,
        task_key=task_key,
    )
    duration_seconds = time.perf_counter() - started_at

    return normalize_agent_result(
        {
            **payload,
            "task_url": task_url,
            "entry_url": navigate_url,
            "warmup": {"skipped": True, "reason": "openhands-browser-tool-set"},
            "duration_seconds": duration_seconds,
        },
        harness="openhands",
    )
