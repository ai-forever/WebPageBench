"""Pinned git submodule paths for external harness runtimes."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class HarnessSubmodule:
    harness: str
    path: str
    url: str
    pinned_commit: str
    release_label: str
    editable_install: Optional[str] = None
    notes: str = ""


HARNESS_SUBMODULES: tuple[HarnessSubmodule, ...] = (
    HarnessSubmodule(
        harness="browser-use",
        path="browser-use",
        url="https://github.com/browser-use/browser-use.git",
        pinned_commit="",  # tracked by parent repo gitlink
        release_label="submodule",
        editable_install="browser-use",
    ),
    HarnessSubmodule(
        harness="deepagents",
        path="deepagents",
        url="https://github.com/langchain-ai/deepagents.git",
        pinned_commit="f99f71259786384098a939a34868f46d47122695",
        release_label="deepagents==0.6.11",
        editable_install="deepagents/libs/deepagents",
    ),
    HarnessSubmodule(
        harness="openhands",
        path="openhands",
        url="https://github.com/OpenHands/software-agent-sdk.git",
        pinned_commit="aabf40723d308da0d5f9063008c6793cc86df282",
        release_label="openhands-sdk/tools v1.17.0",
        editable_install="openhands/openhands-sdk",
        notes="Also install openhands/openhands-tools editable (--no-deps).",
    ),
    HarnessSubmodule(
        harness="openmanus",
        path="openmanus",
        url="https://github.com/FoundationAgents/OpenManus.git",
        pinned_commit="f616c5d43d02d93ccc6e55f11666726d6645fdc2",
        release_label="v0.3.0",
        notes="Prompt source only; executor stays on ./browser-use submodule.",
    ),
    HarnessSubmodule(
        harness="hermes-ouroboros",
        path="hermes-ouroboros",
        url="https://github.com/Ridwannurudeen/hermes-ouroboros.git",
        pinned_commit="",
        release_label="submodule",
        editable_install="hermes-ouroboros/sdk",
    ),
    HarnessSubmodule(
        harness="ouroboros",
        path="ouroboros",
        url="https://github.com/razzant/ouroboros.git",
        pinned_commit="",
        release_label="submodule",
        editable_install="ouroboros",
    ),
)

_HARNESS_TO_SUBMODULE = {item.harness: item for item in HARNESS_SUBMODULES}


def repo_root() -> Path:
    return _REPO_ROOT


def submodule_path(name: str) -> Path:
    meta = _HARNESS_TO_SUBMODULE[name]
    return _REPO_ROOT / meta.path


def submodule_for_harness(harness: str) -> Optional[HarnessSubmodule]:
    normalized = harness
    if harness == "hermes":
        normalized = "hermes-ouroboros"
    if harness.startswith("ouroboros-"):
        normalized = "ouroboros"
    return _HARNESS_TO_SUBMODULE.get(normalized)


def read_submodule_commit(path: Path) -> Optional[str]:
    if not (path / ".git").exists() and not (path / ".git").is_file():
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return result.stdout.strip()


def inspect_submodule(meta: HarnessSubmodule) -> dict:
    path = _REPO_ROOT / meta.path
    initialized = path.is_dir() and (
        (path / ".git").exists() or (path / ".git").is_file()
    )
    current = read_submodule_commit(path) if initialized else None
    pinned = meta.pinned_commit or None
    commit_ok = True
    if pinned and current:
        commit_ok = current.startswith(pinned[:12]) or current == pinned
    return {
        "harness": meta.harness,
        "path": str(path),
        "initialized": initialized,
        "current_commit": current,
        "pinned_commit": pinned,
        "release_label": meta.release_label,
        "commit_ok": commit_ok if pinned else initialized,
        "editable_install": meta.editable_install,
        "notes": meta.notes,
    }


def all_submodule_statuses() -> list[dict]:
    return [inspect_submodule(meta) for meta in HARNESS_SUBMODULES]
