"""Harness name aliases shared across eval modules."""

from __future__ import annotations

_HARNESS_ALIASES = {
    "browser-use": "browser-use",
    "browser_use": "browser-use",
    "browseruse": "browser-use",
    "hermes-ouroboros": "hermes-ouroboros",
    "hermes_ouroboros": "hermes-ouroboros",
    "hermes": "hermes-ouroboros",
    "ouroboros-cut": "ouroboros-cut",
    "ouroboros_cut": "ouroboros-cut",
    "cut": "ouroboros-cut",
    "ouroboros-full-isolated": "ouroboros-full-isolated",
    "ouroboros_full_isolated": "ouroboros-full-isolated",
    "full_isolated": "ouroboros-full-isolated",
    "ouroboros-full-evolving": "ouroboros-full-evolving",
    "ouroboros_full_evolving": "ouroboros-full-evolving",
    "full_evolving": "ouroboros-full-evolving",
    "deepagents": "deepagents",
    "deep-agents": "deepagents",
    "openhands": "openhands",
    "open-hands": "openhands",
    "openmanus": "openmanus",
    "open-manus": "openmanus",
    # GUI (screenshot → coordinates) model families — see bench_eval/agents/.
    "gui-agent": "gui-agent",
    "gui_agent": "gui-agent",
    "qwen3-vl": "qwen3-vl",
    "qwen3_vl": "qwen3-vl",
    "qwen3vl": "qwen3-vl",
    "uitars": "uitars",
    "ui-tars": "uitars",
    "ui_tars": "uitars",
    "jedi": "jedi",
    "opencua": "opencua",
    "open-cua": "opencua",
    "evocua": "evocua",
    "fara": "fara",
    "fara-1.5": "fara",
    "evo-cua": "evocua",
}


def normalize_harness_name(name: str) -> str:
    key = name.strip().lower()
    if key not in _HARNESS_ALIASES:
        supported = ", ".join(sorted(set(_HARNESS_ALIASES.values())))
        raise ValueError(
            f"Unsupported AGENT_HARNESS={name!r}. Supported values: {supported}."
        )
    return _HARNESS_ALIASES[key]
