"""Tests for leaderboard token formatting and model usage breakdown."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LIDERBOARD_ROOT = _REPO_ROOT / "liderboard"
if str(_LIDERBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(_LIDERBOARD_ROOT))

import pytest

from src.load_entries import load_entries  # noqa: E402
from src.models import LeaderboardEntry  # noqa: E402
from src.token_display import (  # noqa: E402
    compact_token_usage_by_model,
    entry_recorded_totals,
    fmt_tokens,
    format_model_usage_breakdown,
    format_task_token_usage,
    has_model_usage_split,
    sum_usage_by_model,
    token_usage_from_run,
)


def test_fmt_tokens():
    assert fmt_tokens(None) == "—"
    assert fmt_tokens(850) == "850.00"
    assert fmt_tokens(183_224) == "183.22K"
    assert fmt_tokens(21_511_581) == "21.51M"


def test_format_model_usage_breakdown_ouroboros_cut_is_hidden():
    entry = LeaderboardEntry(
        model="deepseek/deepseek-v4-flash",
        harness="ouroboros-cut",
        token_usage_by_model={
            "deepseek/deepseek-v4-flash": {
                "total_tokens": 1_200_000,
                "cost_usd": 0.42,
            }
        },
    )
    assert has_model_usage_split(entry) is False
    assert format_model_usage_breakdown(entry) == "—"


def test_format_model_usage_breakdown_unknown_only_shows_slots():
    entry = LeaderboardEntry(
        model="deepseek/deepseek-v4-flash",
        harness="ouroboros-full-isolated",
        token_usage_by_model={
            "unknown": {
                "total_tokens": 34_010_802,
                "cost_usd": 1.664,
            }
        },
        ouroboros_model_slots={
            "main": ["deepseek/deepseek-v4-flash"],
            "review": ["google/gemini-2.5-flash"],
            "fallback": ["google/gemini-2.5-flash"],
        },
    )
    assert has_model_usage_split(entry) is True
    text = format_model_usage_breakdown(entry)
    assert "deepseek-v4-flash" in text
    assert "gemini-2.5-flash" in text
    assert "fallback" in text
    assert "34.01M" in text
    assert "$1.66" in text
    assert "total" in text


def test_format_model_usage_breakdown_single_slot_model_shows_primary():
    entry = LeaderboardEntry(
        model="google/gemini-2.5-flash",
        harness="ouroboros-full-isolated",
        token_usage_by_model={
            "unknown": {
                "total_tokens": 21_511_581,
                "cost_usd": 3.04,
            }
        },
        ouroboros_model_slots={
            "main": ["google/gemini-2.5-flash"],
            "review": ["google/gemini-2.5-flash"],
            "fallback": ["google/gemini-2.5-flash"],
        },
    )
    assert has_model_usage_split(entry) is True
    assert format_model_usage_breakdown(entry) == "gemini-2.5-flash 21.51M · $3.04"


def test_format_model_usage_breakdown_auxiliary_models():
    entry = LeaderboardEntry(
        model="google/gemini-2.5-flash",
        harness="ouroboros-full-evolving",
        token_usage_by_model={
            "google/gemini-2.5-flash": {
                "total_tokens": 1_000_000,
                "roles": ["main"],
                "cost_usd": 0.10,
            },
            "deepseek/deepseek-v4-flash": {
                "total_tokens": 500_000,
                "roles": ["fallback", "review"],
                "cost_usd": 0.07,
            },
        },
    )
    assert has_model_usage_split(entry) is True
    text = format_model_usage_breakdown(entry)
    assert "gemini-2.5-flash" in text
    assert "deepseek-v4-flash" in text
    assert "fallback" in text or "review" in text
    tokens, cost = sum_usage_by_model(entry.token_usage_by_model)
    assert tokens == 1_500_000
    assert cost == pytest.approx(0.17)
    entry_tokens, entry_cost = entry_recorded_totals(entry)
    assert entry_tokens == tokens
    assert entry_cost == cost


def test_format_task_token_usage_ouroboros_cut_hidden():
    test = {
        "agent_harness": "ouroboros-cut",
        "token_usage_by_model": {
            "deepseek/deepseek-v4-flash": {
                "total_tokens": 98_372,
                "cost_usd": 0.00724906,
            }
        },
    }
    assert format_task_token_usage(test, primary_model="deepseek/deepseek-v4-flash") == "—"


def test_format_task_token_usage_unknown_only_shows_slots_for_full():
    test = {
        "agent_harness": "ouroboros-full-isolated",
        "token_usage_by_model": {
            "unknown": {
                "prompt_tokens": 1193014,
                "completion_tokens": 7186,
                "total_tokens": 1200200,
                "cost_usd": 0.057951,
            }
        },
        "agent": {
            "harness_metadata": {
                "ouroboros_llm_sync": {
                    "model_slots": {
                        "main": ["deepseek/deepseek-v4-flash"],
                        "review": ["google/gemini-2.5-flash"],
                    }
                }
            }
        },
    }
    text = format_task_token_usage(test, primary_model="deepseek/deepseek-v4-flash")
    assert "deepseek-v4-flash" in text
    assert "gemini-2.5-flash" in text


def test_token_usage_from_run():
    run = {
        "token_usage_by_model": {
            "unknown": {"total_tokens": 100, "cost_usd": 0.01, "roles": ["main"]},
        }
    }
    compact = token_usage_from_run(run)
    assert compact["unknown"]["total_tokens"] == 100
    assert compact["unknown"]["cost_usd"] == 0.01


def test_load_entries_ouroboros_cut_hides_model_usage():
    entries = load_entries(_LIDERBOARD_ROOT / "results")
    cut = [e for e in entries if e.harness == "ouroboros-cut"]
    assert cut
    for entry in cut:
        assert format_model_usage_breakdown(entry) == "—"


def test_load_entries_ouroboros_full_shows_slot_split():
    entries = load_entries(_LIDERBOARD_ROOT / "results")
    full = [e for e in entries if e.harness.startswith("ouroboros-full")]
    assert full
    for entry in full:
        text = format_model_usage_breakdown(entry)
        assert text != "—"
        assert "gemini" in text.lower()


def test_load_entries_ouroboros_full_primary_model_shown():
    entries = load_entries(_LIDERBOARD_ROOT / "results")
    full = [
        e
        for e in entries
        if e.harness.startswith("ouroboros-full") and e.model.startswith("openai/")
    ]
    assert full
    for entry in full:
        text = format_model_usage_breakdown(entry)
        assert "gpt-5.6-luna" in text
        tokens, cost = sum_usage_by_model(entry.token_usage_by_model)
        assert entry.total_tokens == tokens
        assert entry.total_cost_usd == cost
        assert fmt_tokens(entry.total_tokens) in text


def test_load_entries_model_usage_totals_match_run_totals():
    entries = load_entries(_LIDERBOARD_ROOT / "results")
    for entry in entries:
        if not has_model_usage_split(entry):
            continue
        tokens, cost = sum_usage_by_model(entry.token_usage_by_model)
        assert entry.total_tokens == tokens
        if cost is not None:
            assert entry.total_cost_usd == pytest.approx(cost)


def test_load_entries_includes_token_usage_for_ouroboros():
    entries = load_entries(_LIDERBOARD_ROOT / "results")
    ouro = [e for e in entries if "ouroboros-full" in e.harness]
    assert ouro
    assert ouro[0].total_tokens
    assert ouro[0].token_usage_by_model or ouro[0].total_tokens
