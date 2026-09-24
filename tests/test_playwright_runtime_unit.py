"""Tests for Playwright runtime without sudo."""

from __future__ import annotations

import os
from pathlib import Path

from bench_eval.playwright_runtime import (
    apply_playwright_env_to,
    configure_chromium_library_path,
    configure_playwright_env,
    default_playwright_browsers_path,
    install_vendor_conda_libs,
    resolve_playwright_browsers_path,
    vendor_conda_lib_dir,
    vendor_lib_ready,
)


def test_resolve_playwright_browsers_path_ignores_empty_agent_root(tmp_path, monkeypatch):
    monkeypatch.delenv("PLAYWRIGHT_BROWSERS_PATH", raising=False)
    monkeypatch.setenv("AGENT_BENCH_ROOT", str(tmp_path))
    assert resolve_playwright_browsers_path(tmp_path) == tmp_path / ".cache" / "ms-playwright"


def test_resolve_playwright_browsers_path_ignores_broken_export(tmp_path, monkeypatch):
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", "/.cache/ms-playwright")
    monkeypatch.setenv("AGENT_BENCH_ROOT", str(tmp_path))
    assert resolve_playwright_browsers_path(tmp_path) == tmp_path / ".cache" / "ms-playwright"


def test_configure_chromium_library_path_prepends_conda(monkeypatch, tmp_path):
    conda_lib = tmp_path / "conda" / "lib"
    conda_lib.mkdir(parents=True)
    (conda_lib / "libnspr4.so").write_text("", encoding="utf-8")
    monkeypatch.setenv("CONDA_PREFIX", str(tmp_path / "conda"))
    monkeypatch.setenv("LD_LIBRARY_PATH", "/existing")
    joined = configure_chromium_library_path(tmp_path)
    assert str(conda_lib) in joined
    assert "/existing" in joined
    assert os.environ["LD_LIBRARY_PATH"] == joined


def test_vendor_conda_lib_dir_under_repo_cache(tmp_path):
    assert vendor_conda_lib_dir(tmp_path) == tmp_path / ".cache" / "playwright-conda-libs"
    assert default_playwright_browsers_path(tmp_path) == tmp_path / ".cache" / "ms-playwright"


def test_configure_playwright_env_sets_safe_home_and_browsers_path(tmp_path, monkeypatch):
    monkeypatch.delenv("PLAYWRIGHT_BROWSERS_PATH", raising=False)
    monkeypatch.setenv("HOME", "")
    env = configure_playwright_env(tmp_path)
    assert env["PLAYWRIGHT_BROWSERS_PATH"] == str(tmp_path / ".cache" / "ms-playwright")
    assert env["HOME"] == str(tmp_path)
    assert os.environ["HOME"] == str(tmp_path)
    assert (tmp_path / ".cache" / "ms-playwright").is_dir()


def test_configure_playwright_env_overrides_stub_home(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_BENCH_ROOT", str(tmp_path))
    monkeypatch.delenv("PLAYWRIGHT_BROWSERS_PATH", raising=False)
    monkeypatch.setenv("HOME", "/home/user")
    env = configure_playwright_env(tmp_path)
    assert env["HOME"] == str(tmp_path)
    assert env["PLAYWRIGHT_BROWSERS_PATH"] == str(tmp_path / ".cache" / "ms-playwright")


def test_install_vendor_conda_libs_uses_create_for_new_prefix(tmp_path, monkeypatch):
    prefix = vendor_conda_lib_dir(tmp_path)
    calls: list[list[str]] = []

    def fake_run(cmd, check=False, **kwargs):
        calls.append(cmd)
        (prefix / "conda-meta").mkdir(parents=True)
        lib_dir = prefix / "lib"
        lib_dir.mkdir(parents=True)
        (lib_dir / "libnspr4.so").write_text("", encoding="utf-8")
        class Result:
            returncode = 0

        return Result()

    monkeypatch.setattr("bench_eval.playwright_runtime.subprocess.run", fake_run)
    monkeypatch.setattr("bench_eval.playwright_runtime.shutil.which", lambda name: "/fake/conda")
    assert install_vendor_conda_libs(tmp_path) is True
    assert calls[0][:3] == ["/fake/conda", "create", "-y"]
    assert str(prefix) in calls[0]
    assert vendor_lib_ready(tmp_path)


def test_shell_export_lines_are_sourceable(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_BENCH_ROOT", str(tmp_path))
    monkeypatch.delenv("PLAYWRIGHT_BROWSERS_PATH", raising=False)
    from bench_eval.playwright_runtime import shell_export_lines

    lines = shell_export_lines(tmp_path, install_vendor_libs=False)
    script = "\n".join(lines)
    assert "eval" not in script
    assert "(" not in script
    assert all(line.startswith("export ") for line in lines)


def test_apply_playwright_env_to_sets_playwright_keys(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_BENCH_ROOT", str(tmp_path))
    monkeypatch.delenv("PLAYWRIGHT_BROWSERS_PATH", raising=False)
    monkeypatch.setenv("HOME", "")
    target: dict[str, str] = {"FOO": "bar"}
    apply_playwright_env_to(target, tmp_path)
    assert target["FOO"] == "bar"
    assert target["PLAYWRIGHT_BROWSERS_PATH"] == str(tmp_path / ".cache" / "ms-playwright")
    assert target["HOME"] == str(tmp_path)
    assert target["PLAYWRIGHT_INSTALL_WITH_DEPS"] == "0"
    assert target["SKIP_PLAYWRIGHT_INSTALL_DEPS"] == "1"
