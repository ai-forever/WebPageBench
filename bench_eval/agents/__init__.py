"""GUI (screenshot → coordinates) agent families for WebPageBench.

Unlike the DOM-based harnesses in ``bench_eval/harnesses``, these models see only
a screenshot and answer with pixel coordinates. Each family speaks its own
dialect; the shared core in :mod:`bench_eval.agents.core` normalizes those into
one action IR that a Playwright-backed executor replays in the browser.

Adding a model: register a :class:`~bench_eval.agents.core.registry.ModelSpec`
in the family package (or a new one) — see ``bench_eval/agents/README.md``.
"""

from __future__ import annotations

from bench_eval.agents.core.registry import (
    ModelSpec,
    VLLMSpec,
    list_families,
    list_models,
    models_for_family,
    register,
    resolve,
)
from bench_eval.agents.core.settings import build_agent, build_settings

__all__ = [
    "ModelSpec",
    "VLLMSpec",
    "build_agent",
    "build_settings",
    "list_families",
    "list_models",
    "models_for_family",
    "register",
    "resolve",
]
