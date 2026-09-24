"""Unit tests for Playwright MCP preflight (deepagents harness)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval import playwright_mcp_preflight as mcp_preflight
from bench_eval.harness_llm import default_playwright_mcp_args, playwright_mcp_connection


def _write_chrome(path: Path) -> Path:
    chrome_dir = path / "chromium-1226" / "chrome-linux64"
    chrome_dir.mkdir(parents=True)
    chrome = chrome_dir / "chrome"
    chrome.write_text("", encoding="utf-8")
    chrome.chmod(0o755)
    return chrome


def test_default_mcp_browser_channel():
    assert mcp_preflight.default_mcp_browser_channel() == "chrome-for-testing"


def test_default_playwright_mcp_args_use_executable_path():
    args = default_playwright_mcp_args(executable_path="/cache/chrome")
    assert "--executable-path" in args
    assert "/cache/chrome" in args
    assert "--browser" not in args


def test_default_playwright_mcp_args_fallback_to_chrome_browser():
    args = default_playwright_mcp_args()
    assert "--browser" in args
    assert "chrome" in args
    assert "--executable-path" not in args


def test_playwright_mcp_connection_prefers_executable_path(tmp_path, monkeypatch):
    chrome = _write_chrome(tmp_path)
    npx = tmp_path / "npx"
    npx.write_text("#!/bin/sh\n", encoding="utf-8")
    npx.chmod(0o755)
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path))
    monkeypatch.setenv("PLAYWRIGHT_MCP_EXECUTABLE_PATH", str(chrome))
    monkeypatch.setenv("PLAYWRIGHT_MCP_COMMAND", str(npx))
    monkeypatch.delenv("PLAYWRIGHT_MCP_ARGS", raising=False)

    conn = playwright_mcp_connection()
    assert conn["env"]["PLAYWRIGHT_MCP_EXECUTABLE_PATH"] == str(chrome)
    assert "PLAYWRIGHT_MCP_BROWSER" not in conn["env"]
    assert "--executable-path" in conn["args"]
    assert str(chrome) in conn["args"]


def test_mcp_browser_installed_requires_executable(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path))
    (tmp_path / "chromium_headless_shell-1226").mkdir()
    assert mcp_preflight.mcp_browser_installed(tmp_path) is False

    chrome = _write_chrome(tmp_path)
    assert mcp_preflight.mcp_browser_installed(tmp_path) is True
    assert mcp_preflight.resolve_playwright_mcp_executable(browsers_path=tmp_path) == str(
        chrome
    )


def test_mcp_browser_installed_false_when_empty(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path))
    assert mcp_preflight.mcp_browser_installed(tmp_path) is False


def test_ensure_playwright_mcp_browser_skips_install_and_runs_launch(
    tmp_path: Path, monkeypatch
):
    chrome = _write_chrome(tmp_path)
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path))
    monkeypatch.delenv("PLAYWRIGHT_MCP_EXECUTABLE_PATH", raising=False)
    monkeypatch.delenv("FORCE_PLAYWRIGHT_MCP_INSTALL", raising=False)
    monkeypatch.setattr(
        mcp_preflight,
        "verify_playwright_mcp_launch",
        lambda **_kwargs: str(chrome),
    )

    result = mcp_preflight.ensure_playwright_mcp_browser(browsers_path=tmp_path)
    assert result == str(chrome)
    assert os.environ["PLAYWRIGHT_MCP_EXECUTABLE_PATH"] == str(chrome)


def test_ensure_playwright_mcp_browser_installs_when_missing(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path))
    monkeypatch.delenv("PLAYWRIGHT_MCP_EXECUTABLE_PATH", raising=False)
    monkeypatch.delenv("SKIP_PLAYWRIGHT_MCP_INSTALL", raising=False)
    monkeypatch.delenv("FORCE_PLAYWRIGHT_MCP_INSTALL", raising=False)

    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        _write_chrome(tmp_path)
        return MagicMock(returncode=0)

    chrome = tmp_path / "chromium-1226" / "chrome-linux64" / "chrome"

    monkeypatch.setattr(mcp_preflight, "resolve_npx_command", lambda: "/bin/npx")
    monkeypatch.setattr(mcp_preflight.subprocess, "run", fake_run)
    monkeypatch.setattr(
        mcp_preflight,
        "verify_playwright_mcp_launch",
        lambda **_kwargs: str(chrome),
    )

    result = mcp_preflight.ensure_playwright_mcp_browser(
        npx_command="/bin/npx",
        browsers_path=tmp_path,
    )
    assert result == str(chrome)
    assert calls
    assert calls[0][:4] == ["/bin/npx", "-y", "@playwright/mcp@latest", "install-browser"]
    assert calls[0][4] == "chrome-for-testing"


def test_ensure_playwright_mcp_browser_raises_when_skip_and_missing(
    tmp_path: Path, monkeypatch
):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path))
    monkeypatch.setenv("SKIP_PLAYWRIGHT_MCP_INSTALL", "1")
    monkeypatch.delenv("PLAYWRIGHT_MCP_EXECUTABLE_PATH", raising=False)

    with pytest.raises(SystemExit, match="SKIP_PLAYWRIGHT_MCP_INSTALL"):
        mcp_preflight.ensure_playwright_mcp_browser(browsers_path=tmp_path)


def test_mcp_chromium_launch_smoke_success(tmp_path: Path, monkeypatch):
    chrome = tmp_path / "chrome"
    chrome.write_text("#!/bin/sh\n", encoding="utf-8")
    chrome.chmod(0o755)

    def fake_run(cmd, **kwargs):
        return MagicMock(returncode=0, stdout="<html></html>", stderr="")

    monkeypatch.setattr(mcp_preflight.subprocess, "run", fake_run)
    ok, detail = mcp_preflight.mcp_chromium_launch_smoke(str(chrome))
    assert ok is True
    assert detail == ""
