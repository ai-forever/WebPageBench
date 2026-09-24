"""Unit tests for OpenHands harness text/serialization helpers."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from bench_eval.harness_trajectory import (
    _join_openhands_content_parts,
    serialize_openhands_events,
)
from bench_eval.openhands_browser_patch import (
    apply_openhands_browser_get_state_patch,
    apply_openhands_mcp_server_patch,
    apply_openhands_async_executor_patch,
    ensure_mcp_identity_assertion_params,
    ensure_openhands_browser_executor_ready,
    is_openhands_browser_executor_alive,
    force_exit_openhands_eval,
    prepare_openhands_runtime,
    reset_openhands_browser_executor,
    shutdown_openhands_runtime,
)
from bench_eval.trajectory import build_trajectory


def test_join_openhands_content_parts_joins_list_parts():
    assert _join_openhands_content_parts(["hello", " world"]) == "hello world"


def test_join_openhands_content_parts_strips_whitespace():
    assert _join_openhands_content_parts(["  done  "]) == "done"


def test_serialize_openhands_events_action_is_json_serializable():
    pytest.importorskip("pydantic")
    sys.path.insert(0, str(_REPO_ROOT / "openhands" / "openhands-sdk"))
    sys.path.insert(0, str(_REPO_ROOT / "openhands" / "openhands-tools"))
    pytest.importorskip("openhands.tools.browser_use.definition")
    from openhands.sdk.event.llm_convertible.action import ActionEvent
    from openhands.tools.browser_use.definition import BrowserNavigateAction

    action = BrowserNavigateAction(
        url="http://127.0.0.1:5173/demo/state_shop_main/bench_catalog_main",
        new_tab=False,
    )
    events = [
        ActionEvent(
            action=action,
            tool_name="browser_navigate",
            tool_call_id="call-1",
        )
    ]

    trajectory = serialize_openhands_events(events, harness="openhands")
    json.dumps(trajectory)

    built = build_trajectory(harness_trajectory=trajectory, dab_events=[])
    json.dumps(built)

    action_step = trajectory["steps"][0]["action"]
    assert action_step["kind"] == "BrowserNavigateAction"
    assert "demo" in action_step["url"]


@pytest.mark.asyncio
async def test_openhands_browser_patch_unpacks_tuple_from_browser_use():
    pytest.importorskip("pydantic")
    sys.path.insert(0, str(_REPO_ROOT / "openhands" / "openhands-sdk"))
    sys.path.insert(0, str(_REPO_ROOT / "openhands" / "openhands-tools"))
    pytest.importorskip("openhands.tools.browser_use.impl")
    from openhands.tools.browser_use.definition import BrowserObservation
    from openhands.tools.browser_use.impl import BrowserToolExecutor

    apply_openhands_browser_get_state_patch()

    executor = BrowserToolExecutor.__new__(BrowserToolExecutor)
    executor._initialized = True
    executor.full_output_save_dir = None
    executor._server = MagicMock()
    state_payload = {
        "url": "http://127.0.0.1:5173/demo",
        "title": "Demo",
        "interactive_elements": [],
    }
    executor._server._get_browser_state = AsyncMock(
        return_value=(json.dumps(state_payload, indent=2), None)
    )

    observation = await executor.get_state(include_screenshot=False)

    assert isinstance(observation, BrowserObservation)
    assert not observation.is_error
    assert "http://127.0.0.1:5173/demo" in observation.text


def test_reset_openhands_browser_executor_is_noop_without_openhands():
    reset_openhands_browser_executor()


def test_reset_openhands_browser_executor_clears_singleton_and_closes():
    pytest.importorskip("pydantic")
    sys.path.insert(0, str(_REPO_ROOT / "openhands" / "openhands-sdk"))
    sys.path.insert(0, str(_REPO_ROOT / "openhands" / "openhands-tools"))
    pytest.importorskip("openhands.tools.browser_use.definition")
    from openhands.tools.browser_use.definition import BrowserToolSet

    mock_executor = MagicMock()
    BrowserToolSet._shared_executor = mock_executor
    try:
        reset_openhands_browser_executor()
        assert BrowserToolSet._shared_executor is None
        mock_executor._async_executor.close.assert_called()
    finally:
        BrowserToolSet._shared_executor = None


def test_reset_openhands_browser_executor_tolerates_close_errors():
    pytest.importorskip("pydantic")
    sys.path.insert(0, str(_REPO_ROOT / "openhands" / "openhands-sdk"))
    sys.path.insert(0, str(_REPO_ROOT / "openhands" / "openhands-tools"))
    pytest.importorskip("openhands.tools.browser_use.definition")
    from openhands.tools.browser_use.definition import BrowserToolSet

    mock_executor = MagicMock()
    mock_executor._async_executor.close.side_effect = RuntimeError("cleanup failed")
    BrowserToolSet._shared_executor = mock_executor
    try:
        reset_openhands_browser_executor()
        assert BrowserToolSet._shared_executor is None
    finally:
        BrowserToolSet._shared_executor = None


def test_is_openhands_browser_executor_alive_detects_cleanup():
    alive = MagicMock()
    alive._cleanup_initiated = False
    alive._async_executor = MagicMock(_portal=object())
    assert is_openhands_browser_executor_alive(alive) is True

    dead = MagicMock()
    dead._cleanup_initiated = True
    dead._async_executor = MagicMock(_portal=object())
    assert is_openhands_browser_executor_alive(dead) is False


def test_ensure_openhands_browser_executor_ready_keeps_live_executor():
    pytest.importorskip("pydantic")
    sys.path.insert(0, str(_REPO_ROOT / "openhands" / "openhands-sdk"))
    sys.path.insert(0, str(_REPO_ROOT / "openhands" / "openhands-tools"))
    pytest.importorskip("openhands.tools.browser_use.definition")
    from openhands.tools.browser_use.definition import BrowserToolSet

    mock_executor = MagicMock()
    mock_executor._cleanup_initiated = False
    mock_executor._async_executor = MagicMock(_portal=object())
    BrowserToolSet._shared_executor = mock_executor
    try:
        ensure_openhands_browser_executor_ready()
        assert BrowserToolSet._shared_executor is mock_executor
        mock_executor._async_executor.close.assert_not_called()
    finally:
        BrowserToolSet._shared_executor = None


def test_ensure_openhands_browser_executor_ready_discards_stale_executor():
    pytest.importorskip("pydantic")
    sys.path.insert(0, str(_REPO_ROOT / "openhands" / "openhands-sdk"))
    sys.path.insert(0, str(_REPO_ROOT / "openhands" / "openhands-tools"))
    pytest.importorskip("openhands.tools.browser_use.definition")
    from openhands.tools.browser_use.definition import BrowserToolSet

    mock_executor = MagicMock()
    mock_executor._cleanup_initiated = True
    mock_executor._async_executor = MagicMock(_portal=None)
    BrowserToolSet._shared_executor = mock_executor
    try:
        ensure_openhands_browser_executor_ready()
        assert BrowserToolSet._shared_executor is None
        mock_executor._async_executor.close.assert_called()
    finally:
        BrowserToolSet._shared_executor = None


def test_apply_openhands_mcp_server_patch_skips_handler_registration():
    pytest.importorskip("browser_use")
    from browser_use.mcp.server import BrowserUseServer

    original = BrowserUseServer._setup_handlers
    try:
        apply_openhands_mcp_server_patch()
        assert BrowserUseServer._setup_handlers(object()) is None
        assert BrowserUseServer._dab_skip_mcp_handlers is True
    finally:
        BrowserUseServer._setup_handlers = original
        if hasattr(BrowserUseServer, "_dab_skip_mcp_handlers"):
            delattr(BrowserUseServer, "_dab_skip_mcp_handlers")


def test_ensure_mcp_identity_assertion_params_fills_mcp_1_gap():
    pytest.importorskip("mcp")
    from bench_eval.mcp_compat import apply_mcp_fastmcp_bridge
    from mcp.server.auth import provider

    original = getattr(provider, "IdentityAssertionParams", None)
    try:
        if original is not None:
            delattr(provider, "IdentityAssertionParams")
        apply_mcp_fastmcp_bridge()
        assert getattr(provider, "IdentityAssertionParams") is not None
    finally:
        if original is None:
            if hasattr(provider, "IdentityAssertionParams"):
                delattr(provider, "IdentityAssertionParams")
        else:
            provider.IdentityAssertionParams = original


def test_shutdown_openhands_runtime_discards_shared_executor():
    pytest.importorskip("pydantic")
    sys.path.insert(0, str(_REPO_ROOT / "openhands" / "openhands-sdk"))
    sys.path.insert(0, str(_REPO_ROOT / "openhands" / "openhands-tools"))
    pytest.importorskip("openhands.tools.browser_use.definition")
    from openhands.tools.browser_use.definition import BrowserToolSet

    mock_executor = MagicMock()
    BrowserToolSet._shared_executor = mock_executor
    try:
        shutdown_openhands_runtime()
        assert BrowserToolSet._shared_executor is None
        mock_executor._async_executor.close.assert_called()
    finally:
        BrowserToolSet._shared_executor = None


def test_async_executor_close_does_not_hang_on_portal_join(monkeypatch):
    pytest.importorskip("anyio")
    sys.path.insert(0, str(_REPO_ROOT / "openhands" / "openhands-sdk"))
    pytest.importorskip("openhands.sdk.utils.async_executor")
    from bench_eval import openhands_browser_patch as patch_mod
    from openhands.sdk.utils.async_executor import AsyncExecutor

    monkeypatch.setattr(patch_mod, "_PORTAL_CLOSE_TIMEOUT_SECONDS", 0.2)
    apply_openhands_async_executor_patch()
    executor = AsyncExecutor()
    portal = MagicMock()
    portal.call.side_effect = lambda *args, **kwargs: time.sleep(30)
    executor._portal_cm = MagicMock()
    executor._portal = portal
    started = time.perf_counter()
    executor.close()
    assert time.perf_counter() - started < 5
    assert executor._portal is None
    assert executor._portal_cm is None


def test_force_exit_openhands_eval_skips_other_harnesses(monkeypatch):
    monkeypatch.setenv("AGENT_HARNESS", "browser-use")
    with patch("bench_eval.openhands_browser_patch.os._exit") as exit_mock:
        force_exit_openhands_eval(0)
    exit_mock.assert_not_called()


def test_force_exit_openhands_eval_exits_after_shutdown(monkeypatch):
    monkeypatch.setenv("AGENT_HARNESS", "openhands")
    with (
        patch("bench_eval.openhands_browser_patch._take_openhands_shared_executor") as take,
        patch("bench_eval.openhands_browser_patch._kill_chromium_children"),
        patch("bench_eval.openhands_browser_patch.os._exit") as exit_mock,
    ):
        force_exit_openhands_eval(2)
    take.assert_called_once()
    exit_mock.assert_called_once_with(2)
