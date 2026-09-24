"""Tests for harness input modality labels."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LIDERBOARD_ROOT = _REPO_ROOT / "liderboard"
if str(_LIDERBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(_LIDERBOARD_ROOT))

from src.input_modality import harness_input  # noqa: E402
from src.load_entries import FILTER_ALL, filter_entries, harness_filter_choices, input_filter_choices  # noqa: E402
from src.models import LeaderboardEntry  # noqa: E402
from src.ui import build_table  # noqa: E402


def test_harness_input_by_harness_and_model():
    assert harness_input("openai/gpt-5.6-luna", "openhands") == "text"
    assert harness_input("openai/gpt-5.6-luna", "browser-use") == "text+image"
    assert harness_input("openai/gpt-5.6-luna", "ouroboros-full-isolated") == "text+image"
    assert harness_input("qwen3.8-27b", "qwen3-vl") == "image"
    assert harness_input("fara-1.5-9b", "fara") == "image"
    assert harness_input("deepseek/deepseek-v4.1-flash", "browser-use") == "text"
    assert harness_input("deepseek/deepseek-v4.1-flash", "openmanus") == "text"
    assert harness_input("deepseek/deepseek-v4.1-flash", "ouroboros-full-isolated") == "text+image"
    assert harness_input("minimax/minimax-m2.7", "ouroboros-full-evolving") == "text"
    assert harness_input("z-ai/glm-5.2", "openhands") == "text"


def test_entry_input_modality_property():
    entry = LeaderboardEntry(model="google/gemini-3.8-flash", harness="openmanus")
    assert entry.input_modality == "text+image"


def test_success_table_includes_input_column():
    entry = LeaderboardEntry(
        model="google/gemini-3.8-flash",
        harness="openmanus",
        success_rate=0.822,
        passed_tasks=125,
        total_tasks=152,
    )
    html = build_table([entry], "success")
    assert "<th>Input</th>" in html
    assert "text+image" in html
    assert "wab-input-text-plus-image" in html


def test_filter_entries_by_input_and_harness():
    rows = [
        LeaderboardEntry(model="openai/gpt-5.6-luna", harness="openhands"),
        LeaderboardEntry(model="openai/gpt-5.6-luna", harness="browser-use"),
        LeaderboardEntry(model="qwen3.8-27b", harness="qwen3-vl"),
        LeaderboardEntry(model="deepseek/deepseek-v4.1-flash", harness="browser-use"),
    ]
    text_only = filter_entries(rows, input_id="text")
    assert {entry.harness for entry in text_only} == {"openhands", "browser-use"}
    assert all(entry.model != "qwen3.8-27b" for entry in text_only)

    image_only = filter_entries(rows, input_id="image")
    assert [entry.harness for entry in image_only] == ["qwen3-vl"]

    bu = filter_entries(rows, harness_id="browser-use")
    assert len(bu) == 2

    both = filter_entries(rows, input_id="text", harness_id="browser-use")
    assert [entry.model for entry in both] == ["deepseek/deepseek-v4.1-flash"]

    unchanged = filter_entries(rows, input_id=FILTER_ALL, harness_id=FILTER_ALL)
    assert unchanged == rows


def test_filter_choice_lists():
    rows = [
        LeaderboardEntry(model="openai/gpt-5.6-luna", harness="openhands"),
        LeaderboardEntry(model="openai/gpt-5.6-luna", harness="browser-use"),
        LeaderboardEntry(model="qwen3.8-27b", harness="qwen3-vl"),
    ]
    assert input_filter_choices(rows)[0] == ("All inputs", FILTER_ALL)
    assert [value for _, value in input_filter_choices(rows)[1:]] == ["text", "text+image", "image"]
    assert harness_filter_choices(rows)[0] == ("All harnesses", FILTER_ALL)
    assert [value for _, value in harness_filter_choices(rows)[1:]] == [
        "browser-use",
        "openhands",
        "qwen3-vl",
    ]
