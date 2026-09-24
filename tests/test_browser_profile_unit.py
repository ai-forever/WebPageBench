"""Tests for browser-use profile helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from bench_eval.browser_profile import (
    container_chromium_profile_kwargs,
    find_browser_executable,
    is_container_runtime,
    should_disable_chromium_sandbox,
)
from bench_eval.config import EvalConfig


def test_container_chromium_kwargs_when_sandbox_disabled(monkeypatch):
    monkeypatch.setenv("AGENT_CHROMIUM_NO_SANDBOX", "true")
    config = EvalConfig(agent_headless=True)
    kwargs = container_chromium_profile_kwargs(config)
    assert kwargs["chromium_sandbox"] is False
    assert "--no-sandbox" in kwargs["args"]
    assert "--disable-dev-shm-usage" in kwargs["args"]


def test_container_chromium_kwargs_off_on_local_desktop(monkeypatch):
    monkeypatch.delenv("AGENT_CHROMIUM_NO_SANDBOX", raising=False)
    monkeypatch.setattr(
        "bench_eval.browser_profile.is_container_runtime", lambda: False
    )
    config = EvalConfig(agent_headless=True)
    assert container_chromium_profile_kwargs(config) == {}


def test_should_disable_chromium_sandbox_respects_explicit_false(monkeypatch):
    monkeypatch.setenv("AGENT_CHROMIUM_NO_SANDBOX", "false")
    monkeypatch.setattr(
        "bench_eval.browser_profile.is_container_runtime", lambda: True
    )
    config = EvalConfig(agent_headless=True)
    assert should_disable_chromium_sandbox(config) is False


def test_is_container_runtime_reads_in_docker(monkeypatch):
    monkeypatch.delenv("IN_DOCKER", raising=False)
    monkeypatch.setattr(
        "bench_eval.browser_profile.Path.is_file",
        lambda self: str(self) == "/.dockerenv",
    )
    assert is_container_runtime() is True


def test_find_browser_executable_prefers_headless_shell_when_headless(tmp_path, monkeypatch):
    root = tmp_path / "ms-playwright"
    full = root / "chromium-1" / "chrome-linux64"
    shell = root / "chromium_headless_shell-1" / "chrome-headless-shell-linux64"
    full.mkdir(parents=True)
    shell.mkdir(parents=True)
    (full / "chrome").write_text("", encoding="utf-8")
    (shell / "chrome-headless-shell").write_text("", encoding="utf-8")
    (full / "chrome").chmod(0o755)
    (shell / "chrome-headless-shell").chmod(0o755)
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(root))
    config = EvalConfig(agent_headless=True, agent_downloads_enabled=False)
    assert find_browser_executable(config).endswith("chrome-headless-shell")


def test_playwright_preflight_launch_test_invokes_subprocess(monkeypatch):
    from bench_eval import playwright_preflight

    monkeypatch.setattr(
        playwright_preflight,
        "find_browser_executable",
        lambda _config=None: "/tmp/chrome",
    )
    calls: list[list[str]] = []

    class _Result:
        stdout = "<html></html>"
        stderr = ""

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return _Result()

    monkeypatch.setattr(playwright_preflight.subprocess, "run", fake_run)
    playwright_preflight.verify_chromium_launch(
        EvalConfig(agent_headless=True),
        auto_install_deps=False,
    )
    assert calls[0][0] == "/tmp/chrome"
    assert "--headless=new" in calls[0]


def test_playwright_preflight_retries_install_deps_on_missing_lib(monkeypatch):
    from bench_eval import playwright_preflight

    monkeypatch.setattr(
        playwright_preflight,
        "find_browser_executable",
        lambda _config=None: "/tmp/chrome",
    )
    monkeypatch.setenv("SKIP_PLAYWRIGHT_INSTALL_DEPS", "0")
    launch_attempts = {"n": 0}

    def fake_smoke(cfg, *, timeout_s):
        launch_attempts["n"] += 1
        if launch_attempts["n"] == 1:
            return (
                False,
                "error while loading shared libraries: libnspr4.so",
                "/tmp/chrome",
            )
        return True, "", "/tmp/chrome"

    monkeypatch.setattr(playwright_preflight, "_chromium_launch_smoke", fake_smoke)
    monkeypatch.setattr(
        playwright_preflight,
        "install_vendor_conda_libs",
        lambda root=None: True,
    )
    monkeypatch.setattr(
        playwright_preflight,
        "install_playwright_system_deps",
        lambda: False,
    )
    path = playwright_preflight.verify_chromium_launch(EvalConfig(agent_headless=True))
    assert path == "/tmp/chrome"
    assert launch_attempts["n"] == 2


def test_install_playwright_chromium_script_exists():
    text = Path("scripts/install_playwright_chromium.sh").read_text(encoding="utf-8")
    assert "shell_export_lines" in text
    assert "playwright_preflight --install --launch-test" in text
    assert "PLAYWRIGHT_BROWSERS_PATH=$AGENT_BENCH_ROOT/.cache" not in text


def test_playwright_preflight_exits_when_chromium_missing(monkeypatch):
    from bench_eval import playwright_preflight

    monkeypatch.setattr(
        playwright_preflight,
        "find_browser_executable",
        lambda _config=None: None,
    )
    with pytest.raises(SystemExit):
        playwright_preflight.verify_playwright_chromium(EvalConfig())


def test_ensure_playwright_chromium_installs_when_missing(monkeypatch):
    from bench_eval import playwright_preflight

    calls = {"n": 0}

    def fake_find(_config=None):
        calls["n"] += 1
        return "/tmp/chrome" if calls["n"] > 1 else None

    monkeypatch.setattr(playwright_preflight, "find_browser_executable", fake_find)
    monkeypatch.setattr(
        playwright_preflight.subprocess,
        "run",
        lambda *args, **kwargs: 0,
    )
    path = playwright_preflight.ensure_playwright_chromium(EvalConfig(), install=True)
    assert path == "/tmp/chrome"
    assert calls["n"] == 2
