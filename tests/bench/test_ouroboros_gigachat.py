"""Verify GigaChat LLM routing for ouroboros harness modes."""

from __future__ import annotations

import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from bench_eval.config import EvalConfig
from bench_eval.ouroboros_config import load_ouroboros_harness_config
from bench_eval.ouroboros_cut_loop import run_ouroboros_cut_loop


@pytest.mark.asyncio
async def test_ouroboros_cut_passes_gigachat_config_to_browser_use():
    """cut mode uses WebPageBench llm_factory (ChatGigaChat), not Ouroboros server LLM."""
    seen: dict[str, str] = {}

    async def fake_browser_use(task, *, config, **kwargs):
        seen["llm_provider"] = config.llm_provider
        seen["llm_model"] = config.llm_model
        return {
            "final_result": "done",
            "steps": 1,
            "is_done": True,
            "duration_seconds": 0.1,
            "harness": "browser-use",
        }

    config = EvalConfig(
        agent_harness="ouroboros-cut",
        llm_provider="gigachat",
        llm_model="GigaChat-3-Ultra",
        llm_api_key="test-token",
        llm_max_retries=2,
    )
    ouroboros_config = load_ouroboros_harness_config("configs/ouroboros.cut.json")

    with patch(
        "bench_eval.ouroboros_cut_loop.run_browser_use_harness",
        new=AsyncMock(side_effect=fake_browser_use),
    ):
        result = await run_ouroboros_cut_loop(
            "Add any product to basket",
            config=config,
            ouroboros_config=ouroboros_config,
        )

    assert seen["llm_provider"] == "gigachat"
    assert seen["llm_model"] == "GigaChat-3-Ultra"
    assert result["harness_metadata"]["mode"] == "cut"
    assert result["harness_metadata"]["executor"] == "browser-use"


def test_ouroboros_full_modes_sync_llm_from_eval_env():
    """full_* modes push eval LLM settings into Ouroboros automatically."""
    from bench_eval.ouroboros_llm_sync import build_ouroboros_llm_settings

    settings = build_ouroboros_llm_settings(
        {
            "LLM_PROVIDER": "gigachat",
            "LLM_MODEL": "GigaChat-3-Ultra",
            "GIGACHAT_TOKEN": "auth-key",
        }
    )
    assert settings["OUROBOROS_MODEL"] == "gigachat::GigaChat-3-Ultra"
    assert settings["GIGACHAT_CREDENTIALS"] == "auth-key"
