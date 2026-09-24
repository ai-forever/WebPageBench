"""Load JSON configuration for decoupled ouroboros eval harness modes."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

DEFAULT_OUROBOROS_CONFIG_PATH = "configs/ouroboros.cut.json"
_VALID_MODES = frozenset({"cut", "full_isolated", "full_evolving"})
_VALID_MEMORY_MODES = frozenset({"empty", "forked", "shared"})
_VALID_EXECUTION_BACKENDS = frozenset({"browser-use", "ouroboros-cli", "auto", "dab-cut-loop"})
_MODE_CONFIG_PATHS = {
    "cut": "configs/ouroboros.cut.json",
    "full_isolated": "configs/ouroboros.full_isolated.json",
    "full_evolving": "configs/ouroboros.full_evolving.json",
}


def _env_bool(name: str, default: bool, env: dict[str, str]) -> bool:
    raw = env.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class OuroborosHarnessConfig:
    """Client-side settings for bench_eval ouroboros harness modes."""

    config_path: str
    mode: str
    memory_mode: str
    include_identity: bool
    evolution_enabled: bool
    shared_drive: bool
    per_task_drive: bool
    execution_backend: str
    ouroboros_bin: str
    ouroboros_url: str
    ouroboros_repo_dir: Optional[str]
    ouroboros_timeout_seconds: float
    prompt_prefix: str
    prompt_suffix: str
    require_workers_one: bool

    def resolved_config_path(self) -> str:
        return self.config_path

    def build_task_prompt(self, task: str) -> str:
        return (
            f"{self.prompt_prefix.strip()}\n\n"
            f"{task.strip()}\n\n"
            f"{self.prompt_suffix.strip()}"
        ).strip()

    def uses_ouroboros_cli(self) -> bool:
        if self.execution_backend in {"browser-use", "dab-cut-loop"}:
            return False
        if self.execution_backend == "ouroboros-cli":
            return True
        return bool(self.ouroboros_bin or self.ouroboros_url)


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    section = data.get(name, {})
    return section if isinstance(section, dict) else {}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def resolve_mode_from_harness_name(harness_name: str) -> Optional[str]:
    normalized = harness_name.strip().lower().replace("_", "-")
    aliases = {
        "ouroboros-cut": "cut",
        "ouroboros-full-isolated": "full_isolated",
        "ouroboros-full-evolving": "full_evolving",
        "cut": "cut",
        "full-isolated": "full_isolated",
        "full-evolving": "full_evolving",
    }
    return aliases.get(normalized)


def default_config_path_for_mode(mode: str) -> str:
    if mode not in _VALID_MODES:
        raise ValueError(f"Unsupported ouroboros mode: {mode!r}")
    return _MODE_CONFIG_PATHS[mode]


def load_ouroboros_harness_config(
    config_path: Optional[str] = None,
    *,
    mode: Optional[str] = None,
    env: Optional[dict[str, str]] = None,
) -> OuroborosHarnessConfig:
    """
    Load ouroboros harness config from JSON and apply env overrides.

    Precedence (highest last):
    1. JSON defaults for the selected mode file
    2. OUROBOROS_* environment variables
    """
    env = env if env is not None else os.environ
    resolved_mode = str(
        mode or env.get("OUROBOROS_MODE", "cut")
    ).strip().lower()
    if resolved_mode not in _VALID_MODES:
        resolved_mode = "cut"

    resolved_path = (
        config_path
        or env.get("OUROBOROS_CONFIG_PATH")
        or default_config_path_for_mode(resolved_mode)
    )
    raw = _load_json(Path(resolved_path))

    root_mode = str(raw.get("mode", resolved_mode)).strip().lower()
    if root_mode in _VALID_MODES:
        resolved_mode = root_mode

    drive = _section(raw, "drive")
    execution = _section(raw, "execution")
    api = _section(raw, "api")
    prompt = _section(raw, "prompt")

    memory_mode = str(
        env.get("OUROBOROS_MEMORY_MODE", drive.get("memory_mode", "empty"))
    ).strip().lower()
    if memory_mode not in _VALID_MEMORY_MODES:
        memory_mode = "empty"

    execution_backend = str(
        env.get("OUROBOROS_EXECUTION_BACKEND", execution.get("backend", "auto"))
    ).strip().lower()
    if execution_backend not in _VALID_EXECUTION_BACKENDS:
        execution_backend = "auto"

    return OuroborosHarnessConfig(
        config_path=resolved_path,
        mode=resolved_mode,
        memory_mode=memory_mode,
        include_identity=bool(drive.get("include_identity", resolved_mode != "cut")),
        evolution_enabled=_env_bool(
            "OUROBOROS_EVOLUTION_ENABLED",
            bool(drive.get("evolution_enabled", resolved_mode == "full_evolving")),
            env,
        ),
        shared_drive=bool(drive.get("shared_drive", resolved_mode == "full_evolving")),
        per_task_drive=bool(
            drive.get("per_task_drive", resolved_mode in {"cut", "full_isolated"})
        ),
        execution_backend=execution_backend,
        ouroboros_bin=env.get("OUROBOROS_BIN", api.get("bin", "ouroboros")),
        ouroboros_url=env.get("OUROBOROS_URL", api.get("url", "http://127.0.0.1:9123")),
        ouroboros_repo_dir=env.get("OUROBOROS_REPO_DIR") or api.get("repo_dir"),
        ouroboros_timeout_seconds=float(
            env.get("OUROBOROS_TIMEOUT", api.get("timeout_seconds", 3600))
        ),
        prompt_prefix=str(
            prompt.get(
                "prefix",
                "Complete the browser automation task on the mock e-commerce site.",
            )
        ),
        prompt_suffix=str(
            prompt.get(
                "suffix",
                "Use the browser to interact with the site until the task is done.",
            )
        ),
        require_workers_one=bool(drive.get("require_workers_one", resolved_mode == "full_evolving")),
    )
