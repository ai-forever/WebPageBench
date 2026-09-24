"""Shared building blocks for GUI (screenshot → coordinates) agent families."""

from __future__ import annotations

from bench_eval.agents.core.actions import (
    Action,
    ActionSpace,
    ActionType,
    PYAUTOGUI_ACTION_SPACE,
)
from bench_eval.agents.core.base import GUIAgent, Observation, Prediction
from bench_eval.agents.core.client import (
    Endpoint,
    SamplingParams,
    TokenLedger,
    VLMClient,
    image_part,
    text_part,
)
from bench_eval.agents.core.coordinates import CoordinateScaler, CoordinateSpace
from bench_eval.agents.core.executor import ActionResult, BrowserComputer
from bench_eval.agents.core.history import MemoryStep, StepMemory
from bench_eval.agents.core.images import ProcessedImage, encode_image, process_screenshot, smart_resize
from bench_eval.agents.core.loop import LoopResult, StepRecord, run_agent_loop
from bench_eval.agents.core.registry import (
    ModelSpec,
    VLLMSpec,
    derive,
    list_families,
    list_models,
    models_for_family,
    register,
    resolve,
)
from bench_eval.agents.core.settings import AgentSettings, build_agent, build_settings

__all__ = [
    "Action",
    "ActionResult",
    "ActionSpace",
    "ActionType",
    "AgentSettings",
    "BrowserComputer",
    "CoordinateScaler",
    "CoordinateSpace",
    "Endpoint",
    "GUIAgent",
    "LoopResult",
    "MemoryStep",
    "ModelSpec",
    "Observation",
    "PYAUTOGUI_ACTION_SPACE",
    "Prediction",
    "ProcessedImage",
    "SamplingParams",
    "StepMemory",
    "StepRecord",
    "TokenLedger",
    "VLLMSpec",
    "VLMClient",
    "build_agent",
    "build_settings",
    "derive",
    "encode_image",
    "image_part",
    "list_families",
    "list_models",
    "models_for_family",
    "process_screenshot",
    "register",
    "resolve",
    "run_agent_loop",
    "smart_resize",
    "text_part",
]
