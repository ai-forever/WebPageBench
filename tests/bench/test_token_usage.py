"""Unit tests for LLM token usage extraction and result aggregation."""

from __future__ import annotations

import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.token_usage import (
    empty_token_usage,
    extract_token_usage_from_history,
    merge_token_usage,
    normalize_token_usage,
)


def test_empty_token_usage():
    assert empty_token_usage() == {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "llm_calls": 0,
    }


def test_normalize_token_usage_from_browser_use_summary():
    usage = normalize_token_usage(
        {
            "total_prompt_tokens": 1200,
            "total_completion_tokens": 300,
            "total_tokens": 1500,
            "entry_count": 7,
        }
    )
    assert usage == {
        "prompt_tokens": 1200,
        "completion_tokens": 300,
        "total_tokens": 1500,
        "llm_calls": 7,
    }


def test_normalize_token_usage_computes_total_when_missing():
    usage = normalize_token_usage({"prompt_tokens": 100, "completion_tokens": 25})
    assert usage["total_tokens"] == 125


def test_extract_token_usage_from_history_object():
    usage_obj = MagicMock()
    usage_obj.model_dump.return_value = {
        "total_prompt_tokens": 500,
        "total_completion_tokens": 100,
        "total_tokens": 600,
        "entry_count": 3,
    }
    history = MagicMock()
    history.usage = usage_obj

    assert extract_token_usage_from_history(history)["total_tokens"] == 600


def test_merge_token_usage():
    merged = merge_token_usage(
        {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120, "llm_calls": 2},
        {"prompt_tokens": 50, "completion_tokens": 10, "total_tokens": 60, "llm_calls": 1},
    )
    assert merged == {
        "prompt_tokens": 150,
        "completion_tokens": 30,
        "total_tokens": 180,
        "llm_calls": 3,
    }


def test_normalize_model_token_usage_ignores_zero_cost():
    from bench_eval.token_usage import normalize_model_token_usage

    usage = normalize_model_token_usage(
        {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "cost_usd": 0,
        }
    )
    assert usage["total_tokens"] == 150
    assert "cost_usd" not in usage


def test_extract_token_usage_by_model_from_history_ignores_zero_cost():
    from unittest.mock import MagicMock

    from bench_eval.token_usage import extract_token_usage_by_model_from_history

    usage_obj = MagicMock()
    usage_obj.model_dump.return_value = {
        "by_model": {
            "google/gemini-2.5-flash": {
                "model": "google/gemini-2.5-flash",
                "prompt_tokens": 1000,
                "completion_tokens": 200,
                "total_tokens": 1200,
                "invocations": 3,
                "cost": 0,
            }
        }
    }
    history = MagicMock()
    history.usage = usage_obj

    by_model = extract_token_usage_by_model_from_history(history)
    assert by_model["google/gemini-2.5-flash"]["total_tokens"] == 1200
    assert "cost_usd" not in by_model["google/gemini-2.5-flash"]


def test_token_totals_uses_prompt_and_completion_without_total_tokens():
    from bench_eval.results import _token_totals

    tests = [{"token_usage": {"prompt_tokens": 1000, "completion_tokens": 500}}]
    totals = _token_totals(tests)
    assert totals["total_tokens"] == 1500
    assert totals["avg_tokens_per_task"] == 1500.0
    assert totals["tasks_with_token_usage"] == 1


def test_extract_token_usage_from_messages_uses_response_metadata_fallback():
    from bench_eval.token_usage import extract_token_usage_from_messages

    messages = [
        SimpleNamespace(
            type="ai",
            content="ok",
            usage_metadata=None,
            response_metadata={
                "token_usage": {
                    "prompt_tokens": 11,
                    "completion_tokens": 4,
                    "total_tokens": 15,
                }
            },
        )
    ]
    assert extract_token_usage_from_messages(messages)["total_tokens"] == 15
