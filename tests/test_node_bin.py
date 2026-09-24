"""Unit tests for Node.js CLI path resolution."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from bench_eval.node_bin import node_path_env, resolve_node_bin_dir, resolve_npx_command


def _make_executable(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_resolve_npx_command_prefers_playwright_mcp_command(tmp_path, monkeypatch):
    npx = tmp_path / "custom-npx"
    _make_executable(npx)
    monkeypatch.delenv("NPX_BIN", raising=False)
    monkeypatch.delenv("NODE_BIN_DIR", raising=False)
    monkeypatch.delenv("NPM_BIN", raising=False)
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    monkeypatch.setenv("PLAYWRIGHT_MCP_COMMAND", str(npx))
    assert resolve_npx_command() == str(npx)


def test_resolve_npx_command_uses_node_bin_dir(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    npx = bin_dir / "npx"
    _make_executable(npx)
    monkeypatch.delenv("PLAYWRIGHT_MCP_COMMAND", raising=False)
    monkeypatch.delenv("NPX_BIN", raising=False)
    monkeypatch.delenv("NPM_BIN", raising=False)
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("NODE_BIN_DIR", str(bin_dir))
    assert resolve_npx_command() == str(npx)


def test_resolve_npx_command_derives_from_npm_bin(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    npm = bin_dir / "npm"
    npx = bin_dir / "npx"
    _make_executable(npm)
    _make_executable(npx)
    monkeypatch.delenv("PLAYWRIGHT_MCP_COMMAND", raising=False)
    monkeypatch.delenv("NPX_BIN", raising=False)
    monkeypatch.delenv("NODE_BIN_DIR", raising=False)
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("NPM_BIN", str(npm))
    assert resolve_npx_command() == str(npx)


def test_resolve_npx_command_uses_conda_prefix(tmp_path, monkeypatch):
    conda = tmp_path / "conda"
    npx = conda / "bin" / "npx"
    _make_executable(npx)
    monkeypatch.delenv("PLAYWRIGHT_MCP_COMMAND", raising=False)
    monkeypatch.delenv("NPX_BIN", raising=False)
    monkeypatch.delenv("NODE_BIN_DIR", raising=False)
    monkeypatch.delenv("NPM_BIN", raising=False)
    monkeypatch.delenv("AGENT_BENCH_ROOT", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("CONDA_PREFIX", str(conda))
    assert resolve_npx_command() == str(npx)


def test_resolve_npx_command_uses_repo_conda_node(tmp_path, monkeypatch):
    repo = tmp_path / "WebPageBench"
    repo.mkdir()
    npx = repo / ".conda-node" / "bin" / "npx"
    _make_executable(npx)
    monkeypatch.delenv("PLAYWRIGHT_MCP_COMMAND", raising=False)
    monkeypatch.delenv("NPX_BIN", raising=False)
    monkeypatch.delenv("NODE_BIN_DIR", raising=False)
    monkeypatch.delenv("NPM_BIN", raising=False)
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("AGENT_BENCH_ROOT", str(repo))
    assert resolve_npx_command() == str(npx)


def test_resolve_npx_command_returns_none_when_missing(monkeypatch):
    monkeypatch.delenv("PLAYWRIGHT_MCP_COMMAND", raising=False)
    monkeypatch.delenv("NPX_BIN", raising=False)
    monkeypatch.delenv("NODE_BIN_DIR", raising=False)
    monkeypatch.delenv("NPM_BIN", raising=False)
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    monkeypatch.delenv("AGENT_BENCH_ROOT", raising=False)
    monkeypatch.setenv("PATH", "")
    assert resolve_npx_command() is None


def test_resolve_node_bin_dir_from_npx(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    node = bin_dir / "node"
    npx = bin_dir / "npx"
    _make_executable(node)
    _make_executable(npx)
    monkeypatch.delenv("NODE_BIN_DIR", raising=False)
    monkeypatch.setenv("PLAYWRIGHT_MCP_COMMAND", str(npx))
    assert resolve_node_bin_dir() == str(bin_dir.resolve())


def test_node_path_env_prepends_node_bin_dir(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    node = bin_dir / "node"
    npx = bin_dir / "npx"
    _make_executable(node)
    _make_executable(npx)
    monkeypatch.setenv("PLAYWRIGHT_MCP_COMMAND", str(npx))
    monkeypatch.setenv("PATH", "/usr/bin")
    env = node_path_env()
    assert env["NODE_BIN_DIR"] == str(bin_dir.resolve())
    assert env["PATH"].startswith(f"{bin_dir.resolve()}:")


def test_node_path_env_filters_bash_func_exports(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    node = bin_dir / "node"
    npx = bin_dir / "npx"
    _make_executable(node)
    _make_executable(npx)
    monkeypatch.setenv("PLAYWRIGHT_MCP_COMMAND", str(npx))
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("BASH_FUNC_module%%", "() { :; }")
    env = node_path_env()
    assert "BASH_FUNC_module%%" not in env
    assert env["PATH"].startswith(f"{bin_dir.resolve()}:")


def test_playwright_mcp_connection_includes_node_path_env(tmp_path, monkeypatch):
    from bench_eval.harness_llm import playwright_mcp_connection

    bin_dir = tmp_path / "bin"
    _make_executable(bin_dir / "node")
    _make_executable(bin_dir / "npx")
    monkeypatch.setenv("PLAYWRIGHT_MCP_COMMAND", str(bin_dir / "npx"))
    monkeypatch.setenv("PATH", "/usr/bin")
    conn = playwright_mcp_connection()
    assert conn["env"]["PATH"].startswith(f"{bin_dir.resolve()}:")
    assert conn["env"]["NODE_BIN_DIR"] == str(bin_dir.resolve())
