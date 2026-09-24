"""Unit tests for harness compatibility helpers."""

from __future__ import annotations

import importlib
import os
import sys
from unittest.mock import patch

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.harness_compat import (
    ensure_harness_ready,
    import_harness_runner,
    inspect_all_harnesses,
    inspect_browser_use_installation,
    inspect_harness,
)


def test_inspect_all_harnesses_includes_browser_use_baseline():
    statuses = inspect_all_harnesses()
    assert "browser-use" in statuses
    assert "deepagents" in statuses
    assert "openhands" in statuses
    assert "openmanus" in statuses


def test_inspect_harness_marks_deepagents_optional():
    status = inspect_harness("deepagents")
    assert status.requires_optional is True


def test_inspect_harness_marks_browser_use_core():
    status = inspect_harness("browser-use")
    assert status.requires_optional is False


def test_ensure_harness_ready_raises_for_missing_optional_deps():
    with patch(
        "bench_eval.harness_compat._missing_optional_packages",
        return_value=["deepagents"],
    ):
        with pytest.raises(RuntimeError, match="Harness 'deepagents' is not ready"):
            ensure_harness_ready("deepagents")


def test_import_harness_runner_resolves_browser_use():
    with patch("bench_eval.harness_compat.ensure_harness_ready"):
        runner = import_harness_runner("browser-use")
    assert runner.__name__ == "run_browser_use_harness"


def test_inspect_harness_openhands_requires_python_312_on_py311():
    with patch(
        "bench_eval.harness_compat.openhands_python_supported",
        return_value=False,
    ):
        status = inspect_harness("openhands")
    assert status.ready is False
    assert any("Python >=3.12" in item for item in status.missing_packages)


def test_inspect_harness_openhands_partial_namespace_does_not_crash():
    real_import = importlib.import_module

    def fake_import(name, package=None):
        if name == "openhands.sdk":
            return object()
        if name.startswith("openhands."):
            raise ModuleNotFoundError(name)
        return real_import(name, package)

    with patch(
        "bench_eval.harness_compat.importlib.import_module",
        side_effect=fake_import,
    ):
        status = inspect_harness("openhands")
    assert status.harness == "openhands"
    assert status.ready is False
    assert any("openhands-tools" in item for item in status.missing_packages)
    assert any("install_openhands_harness_fix" in item for item in status.missing_packages)


def test_ensure_openhands_submodule_on_path_prepends_sdk_and_tools(tmp_path, monkeypatch):
    from bench_eval import harness_compat

    sdk = tmp_path / "openhands-sdk"
    tools = tmp_path / "openhands-tools"
    sdk.mkdir()
    tools.mkdir()
    monkeypatch.setattr(harness_compat, "_OPENHANDS_SDK_PATH", sdk)
    monkeypatch.setattr(harness_compat, "_OPENHANDS_TOOLS_PATH", tools)
    sys.path[:] = [p for p in sys.path if p not in {str(sdk), str(tools)}]
    harness_compat.ensure_openhands_submodule_on_path()
    assert sys.path[0] == str(tools)
    assert sys.path[1] == str(sdk)


def test_module_available_returns_false_on_find_spec_error():
    from bench_eval.harness_compat import _module_available

    with patch(
        "importlib.util.find_spec",
        side_effect=ModuleNotFoundError("openhands.tools"),
    ):
        assert _module_available("openhands.tools.browser_use") is False


def test_inspect_browser_use_installation_reports_mode():
    info = inspect_browser_use_installation()
    if info.available:
        assert info.mode in {"editable-submodule", "site-packages"}
    else:
        assert info.mode == "missing"
