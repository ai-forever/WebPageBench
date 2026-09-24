"""Unit tests for harness submodule metadata."""

from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.harness_submodules import (
    HARNESS_SUBMODULES,
    inspect_submodule,
    submodule_for_harness,
)


def test_harness_submodules_include_external_harnesses():
    names = {item.harness for item in HARNESS_SUBMODULES}
    assert "deepagents" in names
    assert "openhands" in names
    assert "openmanus" in names
    assert "browser-use" in names


def test_submodule_for_harness_maps_ouroboros_modes():
    assert submodule_for_harness("ouroboros-cut") is not None
    assert submodule_for_harness("ouroboros-cut").harness == "ouroboros"


def test_inspect_submodule_reports_openmanus_pin():
    meta = submodule_for_harness("openmanus")
    assert meta is not None
    status = inspect_submodule(meta)
    assert status["pinned_commit"].startswith("f616c5d")
    if status["initialized"]:
        assert status["commit_ok"] is True
