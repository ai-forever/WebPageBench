"""Harness dependency checks and browser-use install compatibility."""

from __future__ import annotations

import importlib
import importlib.util
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from bench_eval.harness_names import normalize_harness_name
from bench_eval.deepagents_import import deepagents_import_ok
from bench_eval.node_bin import resolve_npx_command
from bench_eval.harness_submodules import (
    HARNESS_SUBMODULES,
    inspect_submodule,
    repo_root,
    submodule_for_harness,
    submodule_path,
)

_OPENHANDS_MIN_PYTHON = (3, 12)


def openhands_python_supported() -> bool:
    return sys.version_info >= _OPENHANDS_MIN_PYTHON


_REPO_ROOT = repo_root()
_BROWSER_USE_SUBMODULE = submodule_path("browser-use")
_OPENHANDS_SDK_PATH = _REPO_ROOT / "openhands" / "openhands-sdk"
_OPENHANDS_TOOLS_PATH = _REPO_ROOT / "openhands" / "openhands-tools"
_OPENHANDS_CHECKOUT = _OPENHANDS_SDK_PATH.parent


def ensure_openhands_submodule_on_path() -> None:
    """Prefer SDK/tools trees over PYTHONPATH=ROOT binding `openhands` to the git checkout."""
    for path in (_OPENHANDS_SDK_PATH, _OPENHANDS_TOOLS_PATH):
        if not path.is_dir():
            continue
        text = str(path)
        if text in sys.path:
            sys.path.remove(text)
        sys.path.insert(0, text)
    cached = sys.modules.get("openhands")
    if cached is None:
        return
    checkout = _OPENHANDS_CHECKOUT.resolve()
    locations = [getattr(cached, "__file__", None), *list(getattr(cached, "__path__", []) or [])]
    for location in locations:
        if not location:
            continue
        resolved = Path(location).resolve()
        if resolved == checkout or resolved.parent == checkout:
            for name in list(sys.modules):
                if name == "openhands" or name.startswith("openhands."):
                    del sys.modules[name]
            break

# Harnesses that only need the core eval stack (editable browser-use submodule).
_CORE_HARNESSES = frozenset(
    {
        "browser-use",
        "hermes-ouroboros",
        "ouroboros-cut",
        "ouroboros-full-isolated",
        "ouroboros-full-evolving",
        "openmanus",
    }
)

# GUI model families run on their own Playwright executor, not on browser-use.
_GUI_HARNESSES = frozenset(
    {"gui-agent", "qwen3-vl", "uitars", "jedi", "opencua", "evocua", "fara"}
)

_GUI_HARNESS_PACKAGES: tuple[tuple[str, str], ...] = (
    ("playwright", "playwright (pip install playwright && playwright install chromium)"),
    ("httpx", "httpx (pip install httpx)"),
    ("PIL", "pillow (pip install pillow)"),
)

_OPTIONAL_HARNESS_PACKAGES: dict[str, tuple[tuple[str, str], ...]] = {
    **{harness: _GUI_HARNESS_PACKAGES for harness in _GUI_HARNESSES},
    "deepagents": (
        ("langchain_mcp_adapters", "langchain-mcp-adapters"),
        ("langchain_openai", "langchain-openai"),
        ("langchain_anthropic", "langchain-anthropic --no-deps (requirements-harnesses-deepagents.txt)"),
    ),
    "openhands": (
        ("openhands.sdk", "openhands-sdk (./scripts/install_openhands_harness_fix.sh)"),
        (
            "openhands.tools.browser_use",
            "openhands-tools (./scripts/install_openhands_harness_fix.sh)",
        ),
    ),
}

_HARNESS_ENTRYPOINTS: dict[str, str] = {
    "browser-use": "bench_eval.harnesses.browser_use:run_browser_use_harness",
    "deepagents": "bench_eval.harnesses.deepagents:run_deepagents_harness",
    "hermes-ouroboros": "bench_eval.harnesses.hermes_ouroboros:run_hermes_ouroboros_harness",
    "openhands": "bench_eval.harnesses.openhands:run_openhands_harness",
    "openmanus": "bench_eval.harnesses.openmanus:run_openmanus_harness",
    "ouroboros-cut": "bench_eval.harnesses.ouroboros:run_ouroboros_harness",
    "ouroboros-full-isolated": "bench_eval.harnesses.ouroboros:run_ouroboros_harness",
    "ouroboros-full-evolving": "bench_eval.harnesses.ouroboros:run_ouroboros_harness",
    **{
        harness: "bench_eval.agents.harness:run_gui_agent_harness"
        for harness in _GUI_HARNESSES
    },
}

_INSTALL_HINT = """\
Установка eval-стека (из корня репозитория):
  git submodule update --init deepeval browser-use hermes-ouroboros ouroboros \\
    deepagents openhands openmanus
  pip install -r requirements-eval.txt
  pip install -e ./deepeval -e ./browser-use -e ./hermes-ouroboros/sdk
  playwright install chromium

Harness submodules (pinned commits):
  ./scripts/install_harnesses.sh
  ./scripts/install_openhands_harness_fix.sh  # если openhands.tools не импортируется
"""


@dataclass(frozen=True)
class BrowserUseInstallInfo:
    available: bool
    mode: str
    version: Optional[str]
    path: Optional[str]
    from_submodule: bool


@dataclass(frozen=True)
class HarnessStatus:
    harness: str
    ready: bool
    requires_optional: bool
    browser_use: BrowserUseInstallInfo
    missing_packages: tuple[str, ...]
    warnings: tuple[str, ...]
    notes: tuple[str, ...]
    submodule: Optional[dict] = None


def browser_use_submodule_path() -> Path:
    return _BROWSER_USE_SUBMODULE


def _import_spec(module_name: str):
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


def inspect_browser_use_installation() -> BrowserUseInstallInfo:
    module = _import_spec("browser_use")
    if module is None:
        return BrowserUseInstallInfo(
            available=False,
            mode="missing",
            version=None,
            path=None,
            from_submodule=False,
        )

    module_path = Path(getattr(module, "__file__", "") or "").resolve()
    submodule = _BROWSER_USE_SUBMODULE.resolve()
    from_submodule = bool(module_path) and (
        module_path == submodule
        or submodule in module_path.parents
        or str(module_path).startswith(str(submodule))
    )
    version = getattr(module, "__version__", None)
    if version is None:
        try:
            from importlib.metadata import version as dist_version

            version = dist_version("browser-use")
        except Exception:
            version = None

    mode = "editable-submodule" if from_submodule else "site-packages"
    return BrowserUseInstallInfo(
        available=True,
        mode=mode,
        version=version,
        path=str(module_path) if module_path else None,
        from_submodule=from_submodule,
    )


def _module_available(module_name: str) -> bool:
    """Return True when module_name is importable; never raise on partial namespaces."""
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError, AttributeError):
        return False


def _missing_optional_packages(harness: str) -> list[str]:
    missing: list[str] = []
    meta = submodule_for_harness(harness)
    if meta is not None:
        status = inspect_submodule(meta)
        if not status["initialized"]:
            missing.append(
                f"git submodule {meta.path} "
                f"(git submodule update --init {meta.path})"
            )
        elif meta.pinned_commit and not status["commit_ok"]:
            missing.append(
                f"submodule {meta.path} commit drift "
                f"(expected {meta.pinned_commit[:12]}, got {status['current_commit'][:12] if status['current_commit'] else '?'})"
            )

    for module_name, label in _OPTIONAL_HARNESS_PACKAGES.get(harness, ()):
        if harness == "openhands":
            try:
                from bench_eval.openhands_browser_patch import prepare_openhands_runtime

                prepare_openhands_runtime()
                importlib.import_module(module_name)
            except Exception as exc:
                missing.append(f"{label} ({type(exc).__name__}: {exc})")
            continue
        if not _module_available(module_name):
            missing.append(label)

    if harness == "deepagents" and meta is not None:
        status = inspect_submodule(meta)
        if status["initialized"] and not deepagents_import_ok():
            missing.append(
                "deepagents import "
                "(./scripts/install_harnesses.sh; requirements-harnesses-deepagents.txt)"
            )

    return missing


def _harness_notes(harness: str) -> list[str]:
    notes: list[str] = []
    meta = submodule_for_harness(harness)
    if meta is not None and meta.pinned_commit:
        notes.append(
            f"submodule {meta.path} pinned at {meta.release_label} "
            f"({meta.pinned_commit[:12]})."
        )
    if harness == "deepagents":
        if resolve_npx_command() is None:
            notes.append(
                "deepagents требует npx (Node.js) для Playwright MCP; "
                "задайте NODE_BIN_DIR / NPM_BIN / NPX_BIN / PLAYWRIGHT_MCP_COMMAND."
            )
    if harness == "openhands":
        notes.append("openhands BrowserToolSet использует editable ./browser-use.")
        if not openhands_python_supported():
            notes.append(
                f"openhands-sdk v1.17.0 submodule pin требует Python >=3.12 "
                f"(текущий {sys.version_info.major}.{sys.version_info.minor})."
            )
    if harness == "openmanus":
        notes.append(
            "openmanus читает промпты из submodule openmanus/; "
            "executor — ./browser-use."
        )
    if harness in _GUI_HARNESSES:
        notes.append(
            "GUI-модель работает по скриншотам: executor — собственный Playwright "
            "(bench_eval/agents/core/executor.py), browser-use не используется."
        )
        notes.append(
            "Нужен запущенный vLLM: "
            "python -m bench_eval.agents.cli.serve <model>; "
            "затем GUI_AGENT_BASE_URL / GUI_AGENT_MODEL."
        )
    return notes


def inspect_harness(harness: str) -> HarnessStatus:
    normalized = normalize_harness_name(harness)
    browser_use = inspect_browser_use_installation()
    missing: list[str] = []
    warnings: list[str] = []

    if not browser_use.available and normalized in _CORE_HARNESSES:
        missing.append("browser-use (git submodule: pip install -e ./browser-use)")

    if normalized == "openhands" and not openhands_python_supported():
        missing.append(
            f"Python >=3.12 for openhands-sdk pin "
            f"(current {sys.version_info.major}.{sys.version_info.minor})"
        )
    elif normalized == "openhands":
        ensure_openhands_submodule_on_path()

    if normalized not in _CORE_HARNESSES or normalized in {"openhands", "openmanus"}:
        missing.extend(_missing_optional_packages(normalized))

    if normalized == "openmanus":
        meta = submodule_for_harness("openmanus")
        if meta is not None:
            status = inspect_submodule(meta)
            if not status["initialized"]:
                missing.append(
                    f"git submodule {meta.path} "
                    f"(git submodule update --init {meta.path})"
                )

    if browser_use.available and not browser_use.from_submodule:
        if normalized in {"browser-use", "openmanus", "openhands", "hermes-ouroboros"} | {
            h for h in _HARNESS_ENTRYPOINTS if h.startswith("ouroboros")
        }:
            warnings.append(
                "browser-use загружен из site-packages, не из ./browser-use submodule. "
                "Запустите: pip install -e ./browser-use"
            )

    meta = submodule_for_harness(normalized)
    submodule_status = inspect_submodule(meta) if meta is not None else None

    ready = not missing
    return HarnessStatus(
        harness=normalized,
        ready=ready,
        requires_optional=normalized not in _CORE_HARNESSES,
        browser_use=browser_use,
        missing_packages=tuple(dict.fromkeys(missing)),
        warnings=tuple(warnings),
        notes=tuple(_harness_notes(normalized)),
        submodule=submodule_status,
    )


def ensure_harness_ready(harness: str) -> None:
    """Raise RuntimeError with install instructions when harness deps are missing."""
    status = inspect_harness(harness)
    if status.ready:
        return

    lines = [
        f"Harness {status.harness!r} is not ready.",
        "Missing:",
        *[f"  - {item}" for item in status.missing_packages],
    ]
    if status.warnings:
        lines.append("Warnings:")
        lines.extend(f"  - {item}" for item in status.warnings)
    lines.append(_INSTALL_HINT)
    raise RuntimeError("\n".join(lines))


def import_harness_runner(harness: str) -> Callable:
    """Import a harness runner lazily after dependency checks."""
    normalized = normalize_harness_name(harness)
    if normalized == "openhands":
        ensure_openhands_submodule_on_path()
    ensure_harness_ready(normalized)
    entrypoint = _HARNESS_ENTRYPOINTS[normalized]
    module_name, attr = entrypoint.split(":", 1)
    module = importlib.import_module(module_name)
    runner = getattr(module, attr)
    return runner


def inspect_all_harnesses() -> dict[str, HarnessStatus]:
    return {
        harness: inspect_harness(harness)
        for harness in sorted(set(_HARNESS_ENTRYPOINTS))
    }


def list_harness_submodules() -> tuple:
    return HARNESS_SUBMODULES
