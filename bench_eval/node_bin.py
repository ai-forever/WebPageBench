"""Resolve Node.js CLI paths when npm/npx are outside default PATH."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def _executable(path: str | Path) -> bool:
    candidate = Path(path)
    return candidate.is_file() and os.access(candidate, os.X_OK)


def repo_root_from_env() -> Path | None:
    raw = os.getenv("AGENT_BENCH_ROOT", "").strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    return path if path.is_dir() else None


def repo_node_prefix(root: Path | None = None) -> Path | None:
    """Repo-local conda Node prefix (install_nodejs.sh → .conda-node)."""
    repo = root or repo_root_from_env()
    if repo is None:
        return None
    prefix = Path(os.getenv("NODE_CONDA_PREFIX", str(repo / ".conda-node"))).expanduser()
    return prefix if prefix.is_dir() else None


def resolve_npx_command() -> str | None:
    """Return an executable npx path for Playwright MCP (deepagents harness)."""
    explicit = os.getenv("PLAYWRIGHT_MCP_COMMAND")
    if explicit:
        if _executable(explicit):
            return explicit
        found = shutil.which(explicit)
        if found:
            return found

    npx_bin = os.getenv("NPX_BIN")
    if npx_bin and _executable(npx_bin):
        return npx_bin

    found = shutil.which("npx")
    if found:
        return found

    node_bin_dir = os.getenv("NODE_BIN_DIR")
    if node_bin_dir:
        candidate = Path(node_bin_dir) / "npx"
        if _executable(candidate):
            return str(candidate)

    npm_bin = os.getenv("NPM_BIN")
    if npm_bin:
        candidate = Path(npm_bin).with_name("npx")
        if _executable(candidate):
            return str(candidate)

    conda_prefix = os.getenv("CONDA_PREFIX")
    if conda_prefix:
        candidate = Path(conda_prefix) / "bin" / "npx"
        if _executable(candidate):
            return str(candidate)

    node_prefix = repo_node_prefix()
    if node_prefix is not None:
        candidate = node_prefix / "bin" / "npx"
        if _executable(candidate):
            return str(candidate)

    return None


def resolve_node_bin_dir() -> str | None:
    """Directory containing node/npx for Playwright MCP subprocess PATH."""
    explicit = os.getenv("NODE_BIN_DIR", "").strip()
    if explicit and _executable(Path(explicit) / "node"):
        return str(Path(explicit).resolve())

    npx = resolve_npx_command()
    if npx:
        candidate = Path(npx).resolve().parent
        if _executable(candidate / "node"):
            return str(candidate)

    node_prefix = repo_node_prefix()
    if node_prefix is not None:
        candidate = node_prefix / "bin"
        if _executable(candidate / "node"):
            return str(candidate)

    return None


def sanitize_subprocess_env(env: dict[str, str] | None = None) -> dict[str, str]:
    """Drop shell-only exports that break stdio MCP subprocess startup."""
    source = env if env is not None else os.environ
    cleaned: dict[str, str] = {}
    for key, value in source.items():
        if not key or "=" in key:
            continue
        if key.startswith("BASH_FUNC_"):
            continue
        if "(" in key or ")" in key or "%" in key:
            continue
        cleaned[key] = value
    return cleaned


def node_path_env() -> dict[str, str]:
    """Env vars so npx/@playwright/mcp can find a repo-local ``node``."""
    env = sanitize_subprocess_env()
    bin_dir = resolve_node_bin_dir()
    if not bin_dir:
        return env
    env["NODE_BIN_DIR"] = bin_dir
    path = env.get("PATH", "")
    parts = [p for p in path.split(":") if p]
    if bin_dir not in parts:
        env["PATH"] = f"{bin_dir}:{path}" if path else bin_dir
    return env
