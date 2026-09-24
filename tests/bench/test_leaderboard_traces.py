"""Tests for agent trace visualization."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LIDERBOARD_ROOT = _REPO_ROOT / "liderboard"
if str(_LIDERBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(_LIDERBOARD_ROOT))

from src.load_entries import load_entries  # noqa: E402
from src.traces import (  # noqa: E402
    _task_cost_usd,
    build_trace_detail,
    build_trace_js_on_load,
    build_traces_shell,
    format_duration,
    parse_trace_nav,
    trace_summaries_for_entry,
)


def test_parse_trace_nav():
    assert parse_trace_nav("traces:list:google_gemini-3.8-flash__browser-use") == (
        "list",
        "google_gemini-3.8-flash__browser-use",
        "",
    )
    assert parse_trace_nav("traces:detail:entry:bench_grocery_navigation") == (
        "detail",
        "entry",
        "bench_grocery_navigation",
    )


def test_format_duration():
    assert format_duration(45.2) == "45.20s"
    assert format_duration(125) == "2m 5s"


def test_trace_summaries_for_entry():
    entries = load_entries()
    assert entries
    summaries = trace_summaries_for_entry(entries[0])
    assert summaries
    assert "test_name" in summaries[0]
    assert "section" in summaries[0]


def test_build_traces_shell_list():
    entries = load_entries()
    html = build_traces_shell(entries, view="list", entry_id=entries[0].entry_id)
    assert "Agent Traces" in html
    assert "wab-trace-pill" in html
    assert "data-wab-trace-filter=" in html
    assert "data-wab-entry-id=" in html
    assert "wab-trace-card" in html


def test_task_cost_usd_from_token_usage_by_model():
    test = {
        "token_usage_by_model": {
            "unknown": {
                "prompt_tokens": 1000,
                "completion_tokens": 100,
                "cost_usd": 0.057951,
            }
        }
    }
    assert _task_cost_usd(test, "deepseek/deepseek-v4-flash") == 0.057951


def test_build_trace_detail():
    entries = load_entries()
    entry = entries[0]
    summaries = trace_summaries_for_entry(entry)
    html = build_trace_detail(entries, entry.entry_id, summaries[0]["test_name"])
    assert "wab-trace-detail-view" in html
    assert "data-wab-trace-tab" in html
    assert "wab-trace-split" in html
    assert "Export JSON" in html
    assert "wab-trace-back" in html
    assert 'class="wab-trace-meta-value">$' in html or 'class="wab-trace-meta-value">FREE<' in html


def test_parse_trace_nav_detail_payload():
    entry = "deepseek_deepseek-v4.1-flash__openmanus"
    test = "bench_grocery_navigation"
    assert parse_trace_nav(f"traces:detail:{entry}:{test}") == ("detail", entry, test)


def test_trace_js_on_load_registers_navigate():
    script = build_trace_js_on_load()
    assert 'trigger("navigate"' in script
    assert "data-wab-trace" in script
    assert "data-wab-trace-filter" in script
