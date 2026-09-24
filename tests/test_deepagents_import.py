"""Unit tests for deepagents import helper."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def test_import_create_deep_agent_strips_repo_shadow_paths(monkeypatch):
    monkeypatch.setenv("AGENT_BENCH_ROOT", str(_REPO_ROOT))
    monkeypatch.setenv("EVAL_ROOT", str(_REPO_ROOT))

    fake_module = ModuleType("deepagents")

    def fake_create_deep_agent():
        return None

    fake_module.create_deep_agent = fake_create_deep_agent

    sys.path[:] = [str(_REPO_ROOT / "lib" / "src"), str(_REPO_ROOT)]
    seen: dict[str, list[str]] = {}

    def capture_import(name: str):
        seen["path"] = list(sys.path)
        return fake_module

    from bench_eval.deepagents_import import import_create_deep_agent

    with patch.object(importlib, "import_module", side_effect=capture_import):
        fn = import_create_deep_agent()

    assert fn is fake_create_deep_agent
    assert str(_REPO_ROOT) not in seen["path"]
    assert str(_REPO_ROOT / "deepagents") not in seen["path"]
    editable = str(_REPO_ROOT / "deepagents" / "libs" / "deepagents")
    assert seen["path"][0] == editable


def test_deepagents_import_ok_false_when_import_raises(monkeypatch):
    from bench_eval import deepagents_import

    monkeypatch.setattr(
        deepagents_import,
        "import_create_deep_agent",
        lambda: (_ for _ in ()).throw(ImportError("langchain_anthropic")),
    )
    assert deepagents_import.deepagents_import_ok() is False
