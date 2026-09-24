"""Unit tests for LLM cost estimation from eval results."""

from __future__ import annotations

import os
import sys

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.llm_cost import (  # noqa: E402
    compute_results_cost,
    compute_token_cost_usd,
    format_usd,
    resolve_model_pricing,
)


def _pricing_table() -> dict:
    return {
        "gpt-4o-mini": {
            "input_cost_per_token": 0.00000015,
            "output_cost_per_token": 0.00000060,
        },
        "google/gemini-2.5-flash": {
            "input_cost_per_token": 0.00000010,
            "output_cost_per_token": 0.00000040,
        },
    }


def test_resolve_model_pricing_glm_5_1_from_overrides():
    table = {
        "z-ai/glm-5.1": {
            "input_cost_per_token": 9.8e-7,
            "output_cost_per_token": 3.08e-6,
        }
    }
    pricing = resolve_model_pricing("z-ai/glm-5.1", table)
    assert pricing is not None
    total, key = compute_token_cost_usd(
        model="z-ai/glm-5.1",
        prompt_tokens=1_000_000,
        completion_tokens=100_000,
        pricing_table=table,
    )
    assert key == "z-ai/glm-5.1"
    assert total == pytest.approx(1.288)


def test_resolve_model_pricing_matches_provider_prefixed_name():
    pricing = resolve_model_pricing("google/gemini-2.5-flash", _pricing_table())
    assert pricing is not None
    assert pricing.pricing_key == "google/gemini-2.5-flash"


def test_compute_token_cost_usd_from_pricing_table():
    total, key = compute_token_cost_usd(
        model="gpt-4o-mini",
        prompt_tokens=1_000_000,
        completion_tokens=500_000,
        pricing_table=_pricing_table(),
    )
    assert key == "gpt-4o-mini"
    assert total == pytest.approx(0.45)


def test_compute_results_cost_uses_recorded_total_cost():
    payload = {
        "run": {
            "model": "custom-model",
            "total_tasks": 2,
            "total_cost_usd": 1.25,
            "prompt_tokens": 100,
            "completion_tokens": 20,
        },
        "tests": [],
    }
    breakdown = compute_results_cost(payload, pricing_table={})
    assert breakdown.total_cost_usd == 1.25
    assert breakdown.avg_cost_per_task_usd == 0.625
    assert breakdown.source == "recorded"


def test_compute_results_cost_from_run_level_tokens():
    payload = {
        "run": {
            "model": "gpt-4o-mini",
            "total_tasks": 2,
            "prompt_tokens": 1_000_000,
            "completion_tokens": 0,
        },
        "tests": [],
    }
    breakdown = compute_results_cost(payload, pricing_table=_pricing_table())
    assert breakdown.total_cost_usd == pytest.approx(0.15)
    assert breakdown.avg_cost_per_task_usd == pytest.approx(0.075)
    assert breakdown.priced is True


def test_compute_results_cost_sums_per_task_recorded_costs():
    payload = {
        "run": {
            "model": "gpt-4o-mini",
            "total_tasks": 2,
            "prompt_tokens": 0,
            "completion_tokens": 0,
        },
        "tests": [
            {"token_usage": {"total_cost": 0.10}},
            {"token_usage": {"total_cost_usd": 0.05}},
        ],
    }
    breakdown = compute_results_cost(payload, pricing_table={})
    assert breakdown.total_cost_usd == pytest.approx(0.15)
    assert breakdown.avg_cost_per_task_usd == pytest.approx(0.075)
    assert breakdown.source == "recorded"


def test_format_usd():
    assert format_usd(None) == "—"
    assert format_usd(0) == "—"
    assert format_usd(0.0) == "—"
    assert format_usd(0.123456) == "$0.1235"


def test_compute_token_cost_usd_from_total_tokens_only():
    total, key = compute_token_cost_usd(
        model="google/gemini-2.5-flash",
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=100_000,
        pricing_table=_pricing_table(),
    )
    assert key == "google/gemini-2.5-flash"
    assert total == pytest.approx(0.01)


def test_compute_results_cost_ignores_recorded_zero_when_tokens_present():
    payload = {
        "run": {
            "model": "google/gemini-2.5-flash",
            "total_tasks": 1,
            "token_usage_by_model": {
                "google/gemini-2.5-flash": {
                    "prompt_tokens": 100_000,
                    "completion_tokens": 41_054,
                    "total_tokens": 141_054,
                    "cost_usd": 0,
                }
            },
        },
        "tests": [],
    }
    breakdown = compute_results_cost(payload, pricing_table=_pricing_table())
    assert breakdown.total_cost_usd == pytest.approx(0.0264216)
    assert breakdown.source == "computed"
    assert breakdown.priced is True


def test_compute_results_cost_from_total_tokens_only():
    payload = {
        "run": {
            "model": "google/gemini-2.5-flash",
            "total_tasks": 1,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 50_887,
        },
        "tests": [
            {"token_usage": {"total_tokens": 50_887}},
        ],
    }
    breakdown = compute_results_cost(payload, pricing_table=_pricing_table())
    assert breakdown.total_cost_usd == pytest.approx(0.0050887)
    assert breakdown.priced is True


def test_compute_results_cost_sums_multi_model_usage():
    payload = {
        "run": {
            "model": "google/gemini-2.5-flash",
            "total_tasks": 2,
            "token_usage_by_model": {
                "google/gemini-2.5-flash": {
                    "prompt_tokens": 1_000_000,
                    "completion_tokens": 0,
                    "roles": ["main"],
                },
                "deepseek/deepseek-v4-flash": {
                    "prompt_tokens": 500_000,
                    "completion_tokens": 100_000,
                    "roles": ["fallback"],
                    "cost_usd": 0.07,
                },
            },
        },
        "tests": [],
    }
    table = {
        **_pricing_table(),
        "deepseek/deepseek-v4-flash": {
            "input_cost_per_token": 0.00000020,
            "output_cost_per_token": 0.00000080,
        },
    }
    breakdown = compute_results_cost(payload, pricing_table=table)
    assert breakdown.total_cost_usd == pytest.approx(0.17)
    assert breakdown.auxiliary_cost_usd == pytest.approx(0.07)
    assert len(breakdown.by_model) == 2
    by_name = {row.model: row for row in breakdown.by_model}
    assert by_name["deepseek/deepseek-v4-flash"].source == "recorded"
    assert by_name["google/gemini-2.5-flash"].total_cost_usd == pytest.approx(0.10)


def test_compute_results_cost_prices_unknown_ouroboros_bucket_from_primary_model():
    payload = {
        "run": {
            "model": "deepseek/deepseek-v4-flash",
            "total_tasks": 1,
            "ouroboros_model_slots": {
                "main": ["deepseek/deepseek-v4-flash"],
                "review": ["google/gemini-2.5-flash"],
            },
            "token_usage_by_model": {
                "unknown": {
                    "prompt_tokens": 1_000_000,
                    "completion_tokens": 100_000,
                    "total_tokens": 1_100_000,
                    "llm_calls": 10,
                }
            },
        },
        "tests": [],
    }
    table = {
        "deepseek/deepseek-v4-flash": {
            "input_cost_per_token": 0.00000020,
            "output_cost_per_token": 0.00000080,
        }
    }
    breakdown = compute_results_cost(payload, pricing_table=table)
    assert breakdown.total_cost_usd == pytest.approx(0.28)
    assert breakdown.priced is True
    assert breakdown.by_model[0].model == "unknown"
    assert breakdown.by_model[0].source == "computed"


def test_compute_results_cost_sums_named_ouroboros_auxiliary_models():
    payload = {
        "run": {
            "model": "google/gemini-2.5-flash",
            "total_tasks": 1,
            "token_usage_by_model": {
                "google/gemini-2.5-flash": {
                    "prompt_tokens": 1_000_000,
                    "completion_tokens": 0,
                    "roles": ["main"],
                },
                "deepseek/deepseek-v4-flash": {
                    "prompt_tokens": 500_000,
                    "completion_tokens": 100_000,
                    "roles": ["fallback"],
                    "cost_usd": 0.07,
                },
            },
        },
        "tests": [],
    }
    table = {
        **_pricing_table(),
        "deepseek/deepseek-v4-flash": {
            "input_cost_per_token": 0.00000020,
            "output_cost_per_token": 0.00000080,
        },
    }
    breakdown = compute_results_cost(payload, pricing_table=table)
    assert breakdown.total_cost_usd == pytest.approx(0.17)
    assert breakdown.auxiliary_cost_usd == pytest.approx(0.07)
