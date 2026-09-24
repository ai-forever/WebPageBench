"""Shared types for agent harness adapters."""

from __future__ import annotations

from typing import Any, Optional, TypedDict

from bench_eval.token_usage import normalize_token_usage


class TokenUsageDict(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    llm_calls: int


class AgentRunResult(TypedDict, total=False):
    """Normalized result returned by every harness adapter."""

    final_result: Optional[str]
    steps: int
    task_url: Optional[str]
    entry_url: Optional[str]
    warmup: dict[str, Any]
    is_done: bool
    duration_seconds: float
    trajectory: dict[str, Any]
    history: Any
    harness: str
    harness_metadata: dict[str, Any]
    token_usage: TokenUsageDict
    token_usage_by_model: dict[str, TokenUsageDict]
    error: Optional[str]


def normalize_agent_result(
    payload: dict[str, Any],
    *,
    harness: str,
) -> AgentRunResult:
    """Ensure harness adapters expose a stable result shape."""
    result: AgentRunResult = {
        "final_result": payload.get("final_result"),
        "steps": int(payload.get("steps") or 0),
        "task_url": payload.get("task_url"),
        "entry_url": payload.get("entry_url"),
        "warmup": payload.get("warmup") or {"skipped": True},
        "is_done": bool(payload.get("is_done")),
        "duration_seconds": float(payload.get("duration_seconds") or 0.0),
        "trajectory": payload.get("trajectory") or {},
        "history": payload.get("history"),
        "harness": harness,
        "harness_metadata": payload.get("harness_metadata") or {},
        "token_usage": normalize_token_usage(payload.get("token_usage")),
        "token_usage_by_model": payload.get("token_usage_by_model") or {},
    }
    if payload.get("error"):
        result["error"] = payload.get("error")
    return result
