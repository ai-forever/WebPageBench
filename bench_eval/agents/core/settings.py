"""Runtime settings for a GUI-agent run (registry defaults + env overrides)."""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Optional

from bench_eval.agents.core.client import Endpoint, SamplingParams
from bench_eval.agents.core.coordinates import CoordinateSpace
from bench_eval.agents.core.registry import ModelSpec, resolve

ENV_PREFIX = "GUI_AGENT"


def _env_str(name: str, default: Optional[str] = None) -> Optional[str]:
    raw = os.getenv(name)
    return raw.strip() if raw and raw.strip() else default


def _env_float(name: str, default: float) -> float:
    raw = _env_str(name)
    return float(raw) if raw is not None else default


def _env_int(name: str, default: int) -> int:
    raw = _env_str(name)
    return int(raw) if raw is not None else default


def _env_bool(name: str, default: bool) -> bool:
    raw = _env_str(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


@dataclass
class AgentSettings:
    """Everything the agent loop needs that is not the model weights themselves."""

    spec: ModelSpec
    endpoint: Endpoint
    coordinate_space: CoordinateSpace
    temperature: float = 0.0
    top_p: float = 0.9
    max_tokens: int = 2048
    history_n: int = 3
    resize_factor: int = 28
    max_pixels: int = 14 * 14 * 4 * 1280
    min_pixels: int = 56 * 56
    max_steps: int = 25
    max_failures: int = 5
    screen_width: int = 1280
    screen_height: int = 720
    #: Seconds the executor waits after each action for the SPA to settle.
    action_settle_seconds: float = 0.6
    wait_action_seconds: float = 3.0
    save_screenshots: bool = False
    screenshot_dir: Optional[str] = None
    #: Directory for verbatim model-call dumps; ``None`` disables them.
    dump_dir: Optional[str] = None
    #: Family-specific switches, merged from ModelSpec.options and GUI_AGENT_OPTIONS.
    options: dict[str, Any] = field(default_factory=dict)

    @property
    def screen_size(self) -> tuple[int, int]:
        return self.screen_width, self.screen_height

    def sampling(self, **overrides: Any) -> SamplingParams:
        params = SamplingParams(
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
        )
        for key, value in overrides.items():
            setattr(params, key, value)
        return params

    def option(self, key: str, default: Any = None) -> Any:
        return self.options.get(key, default)


def _options_from_env(spec: ModelSpec) -> dict[str, Any]:
    """Merge spec defaults with ``GUI_AGENT_OPTIONS`` (JSON) and per-key env vars.

    Per-key env vars use the family prefix, e.g. ``OPENCUA_COT_LEVEL=l3`` or
    ``JEDI_PLANNER_MODEL=gpt-5.5``.
    """
    import json

    options = dict(spec.options)
    raw = _env_str(f"{ENV_PREFIX}_OPTIONS")
    if raw:
        options.update(json.loads(raw))

    family_prefix = spec.family.upper().replace("-", "_")
    for key in list(options):
        env_name = f"{family_prefix}_{key.upper()}"
        value = _env_str(env_name)
        if value is None:
            continue
        current = options[key]
        if isinstance(current, bool):
            options[key] = value.lower() in {"1", "true", "yes", "on"}
        elif isinstance(current, int) and not isinstance(current, bool):
            options[key] = int(value)
        elif isinstance(current, float):
            options[key] = float(value)
        else:
            options[key] = value
    return options


def _resolve_dump_dir(eval_config: Any) -> Optional[str]:
    """Where verbatim model-call dumps go, or ``None`` when they are switched off.

    The switch is ``EvalConfig.agent_dump_enabled`` (``AGENT_DUMP_ENABLED``); a
    run that turns dumping on without naming a directory gets one inside its own
    results folder, so the calls sit next to the report they explain.
    """
    if eval_config is None:
        from bench_eval.agents.core.dump import CallDumper

        # Standalone entry points (cli/benchmark, cli/infer) have no EvalConfig.
        dumper = CallDumper.from_env()
        return str(dumper.directory) if dumper else None
    if not getattr(eval_config, "agent_dump_enabled", False):
        return None
    explicit = getattr(eval_config, "agent_dump_dir", None)
    if explicit:
        return str(explicit)
    base = (
        getattr(eval_config, "eval_output_dir", None)
        or getattr(eval_config, "eval_results_base_dir", None)
        or "tests/eval"
    )
    return str(Path(base) / "llm-calls")


def build_settings(
    model: Optional[str] = None,
    *,
    eval_config: Any = None,
    overrides: Optional[dict[str, Any]] = None,
) -> AgentSettings:
    """Resolve a model and layer registry defaults ← env ← explicit overrides."""
    name = (
        model
        or _env_str(f"{ENV_PREFIX}_MODEL_SPEC")
        or _env_str(f"{ENV_PREFIX}_MODEL")
        or _env_str("LLM_MODEL")
    )
    if not name:
        raise ValueError(
            "No GUI model selected: set GUI_AGENT_MODEL (registry name) or pass model=..."
        )
    spec = resolve(name)

    served_name = (
        _env_str(f"{ENV_PREFIX}_SERVED_MODEL")
        or (spec.vllm.served_model_name if spec.vllm else None)
        or spec.name
    )
    endpoint = Endpoint.from_env(prefix=ENV_PREFIX, model=served_name)

    coordinate_space = CoordinateSpace(
        _env_str(f"{ENV_PREFIX}_COORDINATE_SPACE", spec.coordinate_space.value)
    )

    max_steps = _env_int("AGENT_MAX_STEPS", getattr(eval_config, "agent_max_steps", 25))
    max_failures = _env_int(
        f"{ENV_PREFIX}_MAX_FAILURES", getattr(eval_config, "agent_max_failures", 5)
    )

    settings = AgentSettings(
        spec=spec,
        endpoint=endpoint,
        coordinate_space=coordinate_space,
        temperature=_env_float(f"{ENV_PREFIX}_TEMPERATURE", spec.temperature),
        top_p=_env_float(f"{ENV_PREFIX}_TOP_P", spec.top_p),
        max_tokens=_env_int(f"{ENV_PREFIX}_MAX_TOKENS", spec.max_tokens),
        history_n=_env_int(f"{ENV_PREFIX}_HISTORY_N", spec.history_n),
        resize_factor=_env_int(f"{ENV_PREFIX}_RESIZE_FACTOR", spec.resize_factor),
        max_pixels=_env_int(f"{ENV_PREFIX}_MAX_PIXELS", spec.max_pixels),
        min_pixels=_env_int(f"{ENV_PREFIX}_MIN_PIXELS", spec.min_pixels),
        max_steps=max_steps,
        max_failures=max_failures,
        screen_width=_env_int(f"{ENV_PREFIX}_SCREEN_WIDTH", 1280),
        screen_height=_env_int(f"{ENV_PREFIX}_SCREEN_HEIGHT", 720),
        action_settle_seconds=_env_float(
            f"{ENV_PREFIX}_ACTION_SETTLE",
            float(getattr(eval_config, "agent_wait_between_actions", 0.6) or 0.6),
        ),
        wait_action_seconds=_env_float(f"{ENV_PREFIX}_WAIT_SECONDS", 3.0),
        save_screenshots=_env_bool(f"{ENV_PREFIX}_SAVE_SCREENSHOTS", False),
        screenshot_dir=_env_str(f"{ENV_PREFIX}_SCREENSHOT_DIR"),
        dump_dir=_resolve_dump_dir(eval_config),
        options=_options_from_env(spec),
    )

    for key, value in (overrides or {}).items():
        setattr(settings, key, value)
    return settings


def build_agent(settings: AgentSettings) -> Any:
    """Instantiate the agent class declared by the model spec."""
    from bench_eval.agents.core.client import create_client
    from bench_eval.agents.core.dump import CallDumper

    agent_class = settings.spec.load_agent_class()
    dumper = CallDumper(Path(settings.dump_dir)) if settings.dump_dir else None
    client = create_client(settings.endpoint, dumper=dumper)
    return agent_class(settings.spec, settings, client)
