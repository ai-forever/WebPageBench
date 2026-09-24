"""Regression tests for deepagents headless-runtime fixes."""

from __future__ import annotations

import asyncio
import os
import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.config import EvalConfig
from bench_eval.harness_llm import (
    create_langchain_chat_model,
    default_playwright_mcp_args,
    playwright_mcp_connection,
    _openhands_llm_kwargs,
)
from bench_eval.harnesses import deepagents as deepagents_harness
from bench_eval.node_bin import sanitize_subprocess_env


def test_sanitize_subprocess_env_drops_bash_func_exports():
    env = sanitize_subprocess_env(
        {
            "PATH": "/usr/bin",
            "BASH_FUNC_module%%": "() { :; }",
            "VALID": "1",
            "BAD()": "x",
        }
    )
    assert env == {"PATH": "/usr/bin", "VALID": "1"}


def test_create_langchain_chat_model_sets_request_timeout(monkeypatch):
    captured: dict = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    fake_mod = types.ModuleType("langchain_openai")
    fake_mod.ChatOpenAI = FakeChatOpenAI
    monkeypatch.setitem(sys.modules, "langchain_openai", fake_mod)
    config = EvalConfig(agent_llm_timeout=45.0, llm_api_key="test-key")
    create_langchain_chat_model(config)
    assert captured["timeout"] == 45.0
    assert captured["default_headers"] == {"Accept-Encoding": "identity"}
    assert captured["http_async_client"] is not None
    assert captured["http_client"] is not None


def test_openhands_llm_kwargs_keep_supported_header_fields():
    class FakeLLM:
        model_fields = {"model": None, "extra_headers": None, "base_url": None}

    filtered = _openhands_llm_kwargs(
        FakeLLM,
        {
            "model": "openrouter/google/gemini-2.5-flash",
            "extra_headers": {"Accept-Encoding": "identity"},
            "httpx_client": object(),
            "http_client": object(),
        },
    )
    assert filtered["extra_headers"]["Accept-Encoding"] == "identity"
    assert "httpx_client" not in filtered
    assert "http_client" not in filtered


def test_default_playwright_mcp_args_use_headless_chromium():
    args = default_playwright_mcp_args()
    assert "--browser" in args
    assert "chrome" in args
    assert "--headless" in args
    assert "--no-sandbox" in args
    assert "--executable-path" not in args


def test_default_playwright_mcp_args_with_executable_path():
    args = default_playwright_mcp_args(executable_path="/tmp/chrome")
    assert "--executable-path" in args
    assert "/tmp/chrome" in args
    assert "--browser" not in args


def test_playwright_mcp_connection_sets_default_timeouts(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    node = bin_dir / "node"
    npx = bin_dir / "npx"
    node.write_text("#!/bin/sh\n", encoding="utf-8")
    npx.write_text("#!/bin/sh\n", encoding="utf-8")
    node.chmod(0o755)
    npx.chmod(0o755)
    chrome_dir = tmp_path / "chromium-1226" / "chrome-linux64"
    chrome_dir.mkdir(parents=True)
    chrome = chrome_dir / "chrome"
    chrome.write_text("", encoding="utf-8")
    chrome.chmod(0o755)
    monkeypatch.setenv("PLAYWRIGHT_MCP_COMMAND", str(npx))
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path))
    monkeypatch.setenv("PLAYWRIGHT_MCP_EXECUTABLE_PATH", str(chrome))
    monkeypatch.delenv("PLAYWRIGHT_MCP_TIMEOUT", raising=False)
    monkeypatch.delenv("PLAYWRIGHT_MCP_ARGS", raising=False)
    conn = playwright_mcp_connection()
    assert conn["args"] == default_playwright_mcp_args(executable_path=str(chrome))
    assert conn["env"]["PLAYWRIGHT_BROWSERS_PATH"] == str(tmp_path)
    assert conn["env"]["PLAYWRIGHT_MCP_EXECUTABLE_PATH"] == str(chrome)
    assert "PLAYWRIGHT_MCP_BROWSER" not in conn["env"]
    assert conn["env"]["PLAYWRIGHT_MCP_HEADLESS"] == "true"
    assert conn["env"]["PLAYWRIGHT_TIMEOUT"] == "120000"
    assert "BASH_FUNC_" not in "".join(conn["env"])


def test_invoke_deep_agent_streams_progress_and_returns_state():
    states = [
        {"messages": [SimpleNamespace(type="human", content="go")]},
        {
            "messages": [
                SimpleNamespace(type="human", content="go"),
                SimpleNamespace(type="ai", content="ok"),
            ]
        },
    ]

    async def fake_astream(*_args, **_kwargs):
        for state in states:
            yield state

    agent = MagicMock()
    agent.astream = fake_astream

    result = asyncio.run(
        deepagents_harness._invoke_deep_agent_with_run_timeout(
            agent,
            prompt="go",
            recursion_limit=40,
            run_timeout=30.0,
        )
    )
    assert len(result["messages"]) == 2


def test_invoke_deep_agent_raises_on_run_timeout():
    async def slow_astream(*_args, **_kwargs):
        await asyncio.sleep(0.05)
        yield {"messages": []}
        await asyncio.sleep(0.2)

    agent = MagicMock()
    agent.astream = slow_astream

    with pytest.raises(TimeoutError, match="AGENT_RUN_TIMEOUT"):
        asyncio.run(
            deepagents_harness._invoke_deep_agent_with_run_timeout(
                agent,
                prompt="go",
                recursion_limit=40,
                run_timeout=0.1,
            )
        )


def test_format_agent_exception_unwraps_task_group():
    inner = TimeoutError(
        "deepagents agent exceeded AGENT_RUN_IDLE_TIMEOUT=300s (messages=4, recursion_limit=50)"
    )
    outer = ExceptionGroup("unhandled errors in a TaskGroup (1 sub-exception)", [inner])
    text = deepagents_harness.format_agent_exception(outer)
    assert "AGENT_RUN_IDLE_TIMEOUT" in text
    assert "TaskGroup" not in text


def test_invoke_deep_agent_raises_on_idle_timeout():
    async def stalled_astream(*_args, **_kwargs):
        yield {
            "messages": [
                SimpleNamespace(type="human", content="go"),
                SimpleNamespace(type="ai", content="thinking"),
            ]
        }
        await asyncio.Event().wait()

    agent = MagicMock()
    agent.astream = stalled_astream

    with pytest.raises(TimeoutError, match="AGENT_RUN_IDLE_TIMEOUT"):
        asyncio.run(
            deepagents_harness._invoke_deep_agent_with_run_timeout(
                agent,
                prompt="go",
                recursion_limit=40,
                run_timeout=30.0,
                idle_timeout=0.1,
            )
        )
