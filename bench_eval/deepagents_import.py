"""Import deepagents without repo submodule namespace shadowing."""

from __future__ import annotations

import importlib
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    for key in ("AGENT_BENCH_ROOT", "EVAL_ROOT"):
        raw = os.getenv(key, "").strip()
        if raw:
            path = Path(raw).expanduser()
            if path.is_dir():
                return path.resolve()
    return Path(__file__).resolve().parents[1]


def _purge_deepagents_modules() -> None:
    for name in list(sys.modules):
        if name == "deepagents" or name.startswith("deepagents."):
            del sys.modules[name]


def import_create_deep_agent() -> Callable[..., Any]:
    """
    Return ``create_deep_agent`` from the editable pip package.

    When PYTHONPATH includes the repo root, the ``deepagents/`` git submodule
    directory is treated as a namespace package and shadows the editable install
    under ``deepagents/libs/deepagents``.
    """
    root = _repo_root()
    shadow_paths = {str(root), str(root / "deepagents")}
    editable = root / "deepagents" / "libs" / "deepagents"

    removed: list[str] = []
    for entry in list(sys.path):
        if entry in shadow_paths:
            sys.path.remove(entry)
            removed.append(entry)

    inserted = False
    if editable.is_dir():
        editable_str = str(editable)
        if editable_str not in sys.path:
            sys.path.insert(0, editable_str)
            inserted = True

    _purge_deepagents_modules()
    try:
        module = importlib.import_module("deepagents")
        return module.create_deep_agent
    finally:
        if inserted and sys.path and sys.path[0] == str(editable):
            sys.path.pop(0)
        for entry in reversed(removed):
            sys.path.insert(0, entry)


def deepagents_import_ok() -> bool:
    try:
        import_create_deep_agent()
        return True
    except Exception:
        return False
