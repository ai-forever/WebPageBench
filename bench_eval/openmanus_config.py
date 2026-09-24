"""OpenManus harness prompt configuration."""

from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bench_eval.harness_submodules import repo_root, submodule_path

DEFAULT_OPENMANUS_CONFIG_PATH = "configs/openmanus.default.json"


@dataclass(frozen=True)
class OpenManusHarnessConfig:
    extend_system_message: str
    integration_mode: str = "browser-use-manus-prompts"
    prompt_source: str = "configs"

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "OpenManusHarnessConfig":
        return cls(
            extend_system_message=str(payload.get("extend_system_message") or "").strip(),
            integration_mode=str(
                payload.get("integration_mode") or "browser-use-manus-prompts"
            ),
            prompt_source=str(payload.get("prompt_source") or "configs"),
        )


def _load_prompts_from_submodule() -> str | None:
    prompt_file = submodule_path("openmanus") / "app" / "prompt" / "manus.py"
    if not prompt_file.is_file():
        return None

    spec = importlib.util.spec_from_file_location(
        "dab_openmanus_prompts",
        prompt_file,
    )
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    system_prompt = getattr(module, "SYSTEM_PROMPT", "")
    next_step_prompt = getattr(module, "NEXT_STEP_PROMPT", "")
    if not system_prompt:
        return None

    if "{directory}" in system_prompt:
        system_prompt = system_prompt.format(directory=".")
    sections = [system_prompt.strip()]
    if next_step_prompt:
        sections.append(str(next_step_prompt).strip())
    sections.append(
        "File editing and shell tools are not available in this benchmark harness; "
        "use only browser actions to complete the task."
    )
    return "\n\n".join(section for section in sections if section)


def load_openmanus_harness_config(
    path: str | None = None,
) -> OpenManusHarnessConfig:
    submodule_prompt = _load_prompts_from_submodule()
    if submodule_prompt:
        return OpenManusHarnessConfig(
            extend_system_message=submodule_prompt,
            integration_mode="browser-use-manus-prompts",
            prompt_source="openmanus-submodule",
        )

    config_path = Path(path or DEFAULT_OPENMANUS_CONFIG_PATH)
    if not config_path.is_file():
        return OpenManusHarnessConfig(
            extend_system_message=(
                "You are OpenManus, a planner-executor web agent. "
                "Break complex browsing tasks into steps, use the browser to act, "
                "and finish only when the user goal is complete."
            ),
            prompt_source="builtin-fallback",
        )
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    config = OpenManusHarnessConfig.from_dict(payload)
    if config_path.is_absolute() or str(config_path).startswith(str(repo_root())):
        prompt_source = str(config_path)
    else:
        prompt_source = str(config_path)
    return OpenManusHarnessConfig(
        extend_system_message=config.extend_system_message,
        integration_mode=config.integration_mode,
        prompt_source=prompt_source,
    )
