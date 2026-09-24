"""Shared retry helpers for eval HTTP and LLM clients."""

from __future__ import annotations

_RETRYABLE_HTTP_STATUS = frozenset({408, 429, 500, 502, 503, 504})


def retry_backoff_seconds(attempt: int, *, cap: float = 30.0) -> float:
    return min(2**attempt, cap)


def is_retryable_http_status(status_code: int) -> bool:
    return status_code in _RETRYABLE_HTTP_STATUS
