"""Tests for leaderboard deep-link badges and navigation."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_LIDERBOARD_ROOT = _REPO_ROOT / "liderboard"
if str(_LIDERBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(_LIDERBOARD_ROOT))

from app import _parse_nav_payload  # noqa: E402
from src.models import LeaderboardEntry, SectionStats  # noqa: E402
from src.ui import _row_badges, build_board, build_highlight_picks, build_nav_js, build_shell_top, build_table  # noqa: E402


def test_row_badges_include_progress_and_nav():
    entry = LeaderboardEntry(
        model="demo/model",
        harness="browser-use",
        sections={
            "hub": SectionStats("hub", "Главная", 1.0, 4, 4),
            "shop": SectionStats("shop", "Маркет", 0.5, 6, 12),
        },
        ui_classes={
            "NAV": {"success_rate": 1.0, "passed": 4, "total": 4},
            "BASKET": {"success_rate": 0.5, "passed": 5, "total": 10},
        },
    )
    html = _row_badges(entry)
    assert "Главная" in html
    assert '<span class="wab-badge-stat">4/4</span>' in html
    assert 'data-wab-nav="sections:hub"' in html
    assert "NAV" in html
    assert 'data-wab-nav="taxonomy:NAV"' in html
    assert "wab-badge-link" in html


def test_parse_nav_payload():
    assert _parse_nav_payload("sections:hub") == ("sections", "hub")
    assert _parse_nav_payload("taxonomy:NAV") == ("taxonomy", "NAV")


def test_shell_top_has_jump_link():
    html = build_shell_top([])
    assert "wab-jump-link" in html
    assert "wab-detail-anchor" in html


def test_nav_js_uses_hidden_button():
    script = build_nav_js()
    assert "__wabPendingNav" in script
    assert "wabOpenDetailTab" in script
    assert "wab-nav-go" in script


def test_highlight_picks_always_show_three_categories():
    from src.load_entries import load_entries

    entries = load_entries()
    html = build_highlight_picks(entries)
    assert "wab-highlights" in html
    assert "Best Overall" in html
    assert "Best Budget" in html
    assert "Fastest" in html


def test_speed_table_rounds_steps():
    entry = LeaderboardEntry(
        model="demo/model",
        harness="browser-use",
        total_duration_seconds=8925.054827867076,
        avg_duration_seconds=175.00107505621716,
        total_agent_steps=1159,
        avg_agent_steps=22.725490196078432,
        success_rate=0.5,
        passed_tasks=25,
        total_tasks=51,
    )
    html = build_table([entry], "speed")
    assert "2h 28m" in html
    assert "2.92m" in html
    assert "1159" in html
    assert "22.73" not in html
    assert "22.725490196078432" not in html


def test_speed_table_sorts_by_total_duration():
    fast = LeaderboardEntry(
        model="fast/model",
        harness="browser-use",
        total_duration_seconds=1000.0,
        avg_duration_seconds=20.0,
        success_rate=0.5,
    )
    slow = LeaderboardEntry(
        model="slow/model",
        harness="browser-use",
        total_duration_seconds=5000.0,
        avg_duration_seconds=10.0,
        success_rate=0.5,
    )
    html = build_table([slow, fast], "speed")
    assert html.index("fast/model") < html.index("slow/model")


def test_board_table_excludes_quick_picks():
    from src.load_entries import load_entries

    entries = load_entries()
    for view in ("success", "speed", "cost"):
        html = build_board(entries, view)
        assert "wab-table" in html
        assert "Quick Picks" not in html
