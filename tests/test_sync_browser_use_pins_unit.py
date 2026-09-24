"""Unit tests for browser-use pip constraint normalization."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = _REPO_ROOT / "scripts" / "_sync_browser_use_pins.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("sync_pins", _MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_normalize_pip_constraint_strips_extras():
    mod = _load_module()
    assert mod.normalize_pip_constraint("httpx[socks]==0.28.1") == "httpx==0.28.1"
    assert mod.normalize_pip_constraint("openai==2.16.0") == "openai==2.16.0"


def test_normalize_pip_constraint_skips_non_pins():
    mod = _load_module()
    assert mod.normalize_pip_constraint("pydantic>=2.0") is None
    assert mod.normalize_pip_constraint("click>=8.0") is None
