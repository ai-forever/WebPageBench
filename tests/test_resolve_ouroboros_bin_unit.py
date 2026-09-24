"""Regression tests for local ouroboros CLI resolution."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RESOLVE_SH = _REPO_ROOT / "scripts" / "_resolve_ouroboros_bin.sh"
_INSTALL_HARNESSES = _REPO_ROOT / "scripts" / "install_harnesses.sh"


def _bash(script: str, *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
  import os

  merged = os.environ.copy()
  if env:
    merged.update(env)
  return subprocess.run(
    ["bash", "-c", script],
    cwd=_REPO_ROOT,
    capture_output=True,
    text=True,
    check=True,
    env=merged,
  )


def test_resolve_ouroboros_bin_uses_venv_path_without_activation():
  with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    venv = root / ".venv"
    (venv / "bin").mkdir(parents=True)
    ouroboros_bin = venv / "bin" / "ouroboros"
    ouroboros_bin.write_text("#!/bin/sh\necho ouroboros\n", encoding="utf-8")
    ouroboros_bin.chmod(0o755)

    completed = _bash(
      f"""
set -euo pipefail
source "{_RESOLVE_SH}"
export VENV_PATH="{venv}"
export PATH="/usr/bin:/bin"
export OUROBOROS_BIN=ouroboros
_resolve_ouroboros_bin "{root}"
""",
    )
    assert completed.stdout.strip() == str(ouroboros_bin)


def test_resolve_ouroboros_bin_normalizes_relative_repo_dir():
  with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    repo = root / "ouroboros"
    (repo / ".venv" / "bin").mkdir(parents=True)
    ouroboros_bin = repo / ".venv" / "bin" / "ouroboros"
    ouroboros_bin.write_text("#!/bin/sh\necho ouroboros\n", encoding="utf-8")
    ouroboros_bin.chmod(0o755)

    completed = _bash(
      f"""
set -euo pipefail
source "{_RESOLVE_SH}"
export OUROBOROS_REPO_DIR=ouroboros
export PATH="/usr/bin:/bin"
export OUROBOROS_BIN=ouroboros
_resolve_ouroboros_bin "{root}"
""",
    )
    assert completed.stdout.strip() == str(ouroboros_bin)


def test_resolve_script_exports_ouroboros_llm_sync_helper():
  text = _RESOLVE_SH.read_text(encoding="utf-8")
  assert "_sync_ouroboros_server_llm_after_start" in text


def test_install_harnesses_reinstalls_missing_ouroboros_cli():
  text = _INSTALL_HARNESSES.read_text(encoding="utf-8")
  assert "Ouroboros CLI missing after harness install" in text
  assert "install_ouroboros.sh" in text


def test_verify_ouroboros_import_checks_from_repo_root():
  text = _RESOLVE_SH.read_text(encoding="utf-8")
  assert "_verify_ouroboros_import()" in text
  assert "PYTHONSAFEPATH=1" in text
