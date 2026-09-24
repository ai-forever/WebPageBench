"""Unit tests for deepagents trajectory and token usage in eval artifacts."""

from __future__ import annotations

import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.harness_trajectory import serialize_message_trajectory
from bench_eval.token_usage import extract_token_usage_from_messages
from bench_eval.trajectory import build_trajectory


def test_extract_token_usage_from_messages_sums_ai_usage_metadata():
    messages = [
        SimpleNamespace(type="human", content="hi"),
        SimpleNamespace(
            type="ai",
            content="hello",
            usage_metadata={
                "input_tokens": 100,
                "output_tokens": 20,
                "total_tokens": 120,
            },
        ),
        SimpleNamespace(
            type="ai",
            content="done",
            usage_metadata={
                "input_tokens": 50,
                "output_tokens": 10,
                "total_tokens": 60,
            },
        ),
    ]

    usage = extract_token_usage_from_messages(messages)
    assert usage == {
        "prompt_tokens": 150,
        "completion_tokens": 30,
        "total_tokens": 180,
        "llm_calls": 2,
    }


def test_serialize_message_trajectory_includes_tool_calls():
    messages = [
        SimpleNamespace(
            type="ai",
            content="clicking",
            tool_calls=[{"id": "call_1", "name": "browser_click", "args": {"ref": "e1"}}],
        ),
        SimpleNamespace(type="tool", name="browser_click", content='{"ok": true}'),
    ]

    trajectory = serialize_message_trajectory(messages, harness="deepagents")
    assert trajectory["summary"]["step_count"] == 2
    assert trajectory["steps"][0]["tool_calls"][0]["name"] == "browser_click"
    assert trajectory["steps"][1]["name"] == "browser_click"


def test_build_trajectory_uses_harness_trajectory_for_langchain_messages():
    harness_trajectory = serialize_message_trajectory(
        [SimpleNamespace(type="human", content="task")],
        harness="deepagents",
    )
    langchain_history = [SimpleNamespace(type="ai", content="ignored by browser-use serializer")]

    trajectory = build_trajectory(
        agent_history=langchain_history,
        harness_trajectory=harness_trajectory,
        dab_events=[{"event_name": "basket_add"}],
    )

    assert len(trajectory["agent"]["steps"]) == 1
    assert trajectory["agent"]["harness"] == "deepagents"
    assert trajectory["dab_event_names"] == ["basket_add"]


def test_build_trajectory_prefers_harness_trajectory_over_browser_history():
    harness_trajectory = {
        "harness": "deepagents",
        "summary": {"step_count": 1},
        "steps": [{"index": 0, "role": "human", "content": "x"}],
    }
    browser_history = MagicMock()
    browser_history.history = [MagicMock()]

    trajectory = build_trajectory(
        agent_history=browser_history,
        harness_trajectory=harness_trajectory,
        dab_events=[],
    )

    assert trajectory["agent"]["steps"][0]["role"] == "human"
    assert trajectory["agent"]["harness"] == "deepagents"
