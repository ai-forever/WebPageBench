"""Unit tests for per-model token usage helpers."""

from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.token_usage import (  # noqa: E402
    aggregate_token_usage_by_model,
    merge_token_usage_by_model,
    tag_model_roles,
)


def test_merge_token_usage_by_model_sums_counters_and_cost():
    merged = merge_token_usage_by_model(
        {
            "google/gemini-2.5-flash": {
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "llm_calls": 1,
                "cost_usd": 0.01,
            }
        },
        {
            "google/gemini-2.5-flash": {
                "prompt_tokens": 50,
                "completion_tokens": 10,
                "llm_calls": 2,
            },
            "deepseek/deepseek-v4-flash": {
                "prompt_tokens": 200,
                "completion_tokens": 40,
                "llm_calls": 1,
                "cost_usd": 0.02,
            },
        },
    )
    assert merged["google/gemini-2.5-flash"]["prompt_tokens"] == 150
    assert merged["google/gemini-2.5-flash"]["cost_usd"] == 0.01
    assert merged["deepseek/deepseek-v4-flash"]["total_tokens"] == 240


def test_aggregate_token_usage_by_model_from_tests():
    tests = [
        {
            "token_usage_by_model": {
                "model-a": {"prompt_tokens": 10, "completion_tokens": 1, "llm_calls": 1},
            }
        },
        {
            "token_usage_by_model": {
                "model-a": {"prompt_tokens": 5, "completion_tokens": 2, "llm_calls": 1},
                "model-b": {"prompt_tokens": 7, "completion_tokens": 0, "llm_calls": 1},
            }
        },
    ]
    aggregated = aggregate_token_usage_by_model(tests)
    assert aggregated["model-a"]["prompt_tokens"] == 15
    assert aggregated["model-b"]["llm_calls"] == 1


def test_tag_model_roles_adds_configured_slots():
    usage = {
        "google/gemini-2.5-flash": {"prompt_tokens": 1, "completion_tokens": 0, "llm_calls": 1},
        "deepseek/deepseek-v4-flash": {"prompt_tokens": 2, "completion_tokens": 0, "llm_calls": 1},
    }
    tagged = tag_model_roles(
        usage,
        model_slots={
            "main": ["google/gemini-2.5-flash"],
            "fallback": ["deepseek/deepseek-v4-flash"],
        },
    )
    assert tagged["google/gemini-2.5-flash"]["roles"] == ["main"]
    assert tagged["deepseek/deepseek-v4-flash"]["roles"] == ["fallback"]
