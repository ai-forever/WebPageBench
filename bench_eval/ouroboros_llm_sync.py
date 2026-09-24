"""Map WebPageBench eval LLM env to Ouroboros runtime settings (full_* harness modes)."""

from __future__ import annotations

import os
import re
import shlex
from pathlib import Path
from typing import Any, Mapping, Optional

# Cheap OpenRouter defaults for WebPageBench eval (unprefixed model IDs).
OUROBOROS_OPENROUTER_MAIN_DEFAULT = "google/gemini-2.5-flash"
OUROBOROS_OPENROUTER_FALLBACKS_DEFAULT = "google/gemini-2.5-flash"
OUROBOROS_OPENROUTER_REVIEW_MODELS_DEFAULT = "google/gemini-2.5-flash"

# Every Ouroboros settings/env key that can trigger an LLM call outside the main slot.
OUROBOROS_AUXILIARY_MODEL_KEYS = (
    "OUROBOROS_REVIEW_MODELS",
    "OUROBOROS_SCOPE_REVIEW_MODELS",
    "OUROBOROS_SCOPE_REVIEW_MODEL",
    "OUROBOROS_MODEL_DEEP_SELF_REVIEW",
    "OUROBOROS_WEBSEARCH_MODEL",
)

# Review-family slots always share the same resolved review model (gemini on OpenRouter).
OUROBOROS_REVIEW_SLOT_KEYS = (
    "OUROBOROS_SCOPE_REVIEW_MODELS",
    "OUROBOROS_SCOPE_REVIEW_MODEL",
    "OUROBOROS_MODEL_DEEP_SELF_REVIEW",
)

# Keys written by build_ouroboros_llm_settings that can trigger LLM calls.
OUROBOROS_MODEL_SLOT_KEYS = (
    "OUROBOROS_MODEL",
    "OUROBOROS_MODEL_HEAVY",
    "OUROBOROS_MODEL_LIGHT",
    "OUROBOROS_MODEL_FALLBACKS",
    *OUROBOROS_AUXILIARY_MODEL_KEYS,
)

_MODEL_SLOT_ROLE_BY_KEY = {
    "OUROBOROS_MODEL": "main",
    "OUROBOROS_MODEL_HEAVY": "heavy",
    "OUROBOROS_MODEL_LIGHT": "light",
    "OUROBOROS_MODEL_FALLBACKS": "fallback",
    "OUROBOROS_REVIEW_MODELS": "review",
    "OUROBOROS_SCOPE_REVIEW_MODELS": "scope_review",
    "OUROBOROS_SCOPE_REVIEW_MODEL": "scope_review",
    "OUROBOROS_MODEL_DEEP_SELF_REVIEW": "deep_self_review",
    "OUROBOROS_WEBSEARCH_MODEL": "websearch",
}

# Substrings that must not appear in bench Ouroboros model settings (OpenRouter cost guard).
_BENCH_BLOCKED_MODEL_PATTERNS = re.compile(
    r"claude-opus|claude-sonnet|claude-4\.|gpt-5|gpt-4|gemini-3\.|gemini-3-pro|o3|o1",
    re.IGNORECASE,
)


def ouroboros_model_id(provider: str, model: str) -> str:
    """Convert eval LLM_PROVIDER + LLM_MODEL to an Ouroboros model slot value."""
    provider = (provider or "openai").strip().lower()
    model = (model or "").strip()
    if not model:
        return ""

    if "::" in model:
        return model

    if provider == "gigachat":
        return f"gigachat::{model}"
    if provider == "openrouter":
        return model
    if provider in {"openai", "azure"}:
        return f"openai::{model}"
    if provider == "vllm":
        return f"openai-compatible::{model}"
    if provider == "ollama":
        return f"openai-compatible::{model}"
    return model


def _bench_model_lock_enabled(source: Mapping[str, str]) -> bool:
    if str(source.get("DAB_OUROBOROS_BENCH_LOCK", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return True
    return str(source.get("EVAL_MOCK", "bench")).strip().lower() == "bench"


def _resolve_main_model(provider: str, model: str) -> str:
    if provider == "openrouter":
        return ouroboros_model_id(provider, model) or OUROBOROS_OPENROUTER_MAIN_DEFAULT
    return ouroboros_model_id(provider, model)


def _resolve_fallback_model(provider: str, model: str, source: Mapping[str, str]) -> str:
    explicit = str(source.get("OUROBOROS_MODEL_FALLBACKS") or "").strip()
    if explicit:
        return explicit
    if _explicit_eval_model_is_blocked(source):
        return _resolve_main_model(provider, model)
    if provider == "openrouter":
        return OUROBOROS_OPENROUTER_FALLBACKS_DEFAULT
    return _resolve_main_model(provider, model)


def _resolve_review_models(provider: str, model: str, source: Mapping[str, str]) -> str:
    explicit = str(source.get("OUROBOROS_REVIEW_MODELS") or "").strip()
    if explicit:
        return explicit
    if provider == "openrouter":
        return OUROBOROS_OPENROUTER_REVIEW_MODELS_DEFAULT
    return _resolve_main_model(provider, model)


def _apply_model_slots(
    settings: dict[str, str],
    *,
    main_model: str,
    fallbacks: Optional[str] = None,
    mirror_all_slots: bool = False,
) -> None:
    if not main_model:
        return
    settings["OUROBOROS_MODEL"] = main_model
    if mirror_all_slots:
        settings["OUROBOROS_MODEL_HEAVY"] = main_model
        settings["OUROBOROS_MODEL_LIGHT"] = main_model
        settings["OUROBOROS_MODEL_FALLBACKS"] = fallbacks or main_model
        return
    if fallbacks:
        settings["OUROBOROS_MODEL_FALLBACKS"] = fallbacks


def _apply_bench_auxiliary_models(
    settings: dict[str, str],
    *,
    cheap_model: str,
    source: Mapping[str, str],
) -> None:
    """Pin review slots to the resolved review model; websearch stays on main."""
    review_models = _resolve_review_models(
        str(source.get("LLM_PROVIDER", "openai")).strip().lower(),
        str(source.get("LLM_MODEL", "")).strip(),
        source,
    )
    settings["OUROBOROS_REVIEW_MODELS"] = review_models
    for key in OUROBOROS_AUXILIARY_MODEL_KEYS:
        if key == "OUROBOROS_REVIEW_MODELS":
            continue
        if key in OUROBOROS_REVIEW_SLOT_KEYS:
            settings[key] = review_models
            continue
        settings[key] = cheap_model


def _apply_bench_runtime_guards(settings: dict[str, str]) -> None:
    """Reduce bench-only paths that can spawn extra LLM-heavy Ouroboros features."""
    settings["OUROBOROS_ALLOW_MUTATIVE_SUBAGENTS"] = "false"
    settings["OUROBOROS_REVIEW_ENFORCEMENT"] = "advisory"


def _explicit_eval_model_is_blocked(source: Mapping[str, str]) -> bool:
    """True when LLM_MODEL intentionally selects a normally blocked frontier family."""
    model = str(source.get("LLM_MODEL") or "").strip()
    return bool(model and _BENCH_BLOCKED_MODEL_PATTERNS.search(model))


def validate_bench_safe_ouroboros_models(
    settings: Mapping[str, str],
    *,
    env: Optional[Mapping[str, str]] = None,
) -> None:
    """Raise when bench lock is on and a model slot still references a blocked family."""
    source = dict(env) if env is not None else dict(os.environ)
    if not _bench_model_lock_enabled(source):
        return
    if _explicit_eval_model_is_blocked(source):
        return
    for key, value in settings.items():
        if "MODEL" not in key.upper():
            continue
        text = str(value or "").strip()
        if not text:
            continue
        if _BENCH_BLOCKED_MODEL_PATTERNS.search(text):
            raise ValueError(
                f"Blocked model family in {key}={text!r} for WebPageBench "
                f"(set cheap models via envs/runs and ouroboros_llm_sync)"
            )


def _split_model_list(value: str) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    parts = re.split(r"[,;\n]+", text)
    return [part.strip() for part in parts if part.strip()]


def collect_ouroboros_model_slots(
    settings: Mapping[str, str],
) -> dict[str, list[str]]:
    """Return configured Ouroboros model slots (main, fallback, review, …)."""
    slots: dict[str, list[str]] = {}
    for key in OUROBOROS_MODEL_SLOT_KEYS:
        value = str(settings.get(key) or "").strip()
        if not value:
            continue
        role = _MODEL_SLOT_ROLE_BY_KEY.get(key, key.lower())
        models = _split_model_list(value)
        if not models:
            continue
        slots[role] = sorted(set(slots.get(role, [])).union(models))
    return slots


def model_roles_index(model_slots: Mapping[str, list[str]]) -> dict[str, list[str]]:
    """Invert slot map to model -> roles."""
    index: dict[str, set[str]] = {}
    for role, models in model_slots.items():
        for model in models:
            model_name = str(model or "").strip()
            if not model_name:
                continue
            index.setdefault(model_name, set()).add(role)
    return {model: sorted(roles) for model, roles in sorted(index.items())}


def build_ouroboros_llm_settings(
    env: Optional[Mapping[str, str]] = None,
) -> dict[str, str]:
    """
    Build Ouroboros /api/settings payload from eval env.

    OpenRouter: main from LLM_MODEL; review/scope/deep-self-review always default to
    google/gemini-2.5-flash unless overridden; fallback/websearch follow main unless
    overridden. Enough to set OPENROUTER_API_KEY in env.
    """
    source = dict(env) if env is not None else dict(os.environ)
    provider = str(source.get("LLM_PROVIDER", "openai")).strip().lower()
    model = str(source.get("LLM_MODEL", "")).strip()
    settings: dict[str, str] = {}
    bench_lock = _bench_model_lock_enabled(source)

    if provider == "openrouter":
        main_model = _resolve_main_model(provider, model)
        fallbacks = _resolve_fallback_model(provider, model, source)
        _apply_model_slots(
            settings,
            main_model=main_model,
            fallbacks=fallbacks,
            mirror_all_slots=bench_lock,
        )
        _apply_bench_auxiliary_models(settings, cheap_model=main_model, source=source)
        api_key = (
            str(source.get("OPENROUTER_API_KEY") or "").strip()
            or str(source.get("OPENAI_API_KEY") or "").strip()
        )
        if api_key:
            settings["OPENROUTER_API_KEY"] = api_key
        base_url = str(
            source.get("LLM_BASE_URL") or source.get("OPENAI_BASE_URL") or ""
        ).strip()
        if base_url:
            settings["OPENROUTER_BASE_URL"] = base_url
            settings["OPENAI_BASE_URL"] = base_url
    elif provider == "gigachat":
        ouro_model = _resolve_main_model(provider, model)
        _apply_model_slots(settings, main_model=ouro_model, mirror_all_slots=True)
        _apply_bench_auxiliary_models(settings, cheap_model=ouro_model, source=source)
        credentials = (
            str(source.get("GIGACHAT_CREDENTIALS") or "").strip()
            or str(source.get("GIGACHAT_TOKEN") or "").strip()
        )
        if credentials:
            settings["GIGACHAT_CREDENTIALS"] = credentials
        for key in (
            "GIGACHAT_USER",
            "GIGACHAT_PASSWORD",
            "GIGACHAT_SCOPE",
            "GIGACHAT_BASE_URL",
            "GIGACHAT_VERIFY_SSL_CERTS",
            "GIGACHAT_PROFANITY_CHECK",
        ):
            value = str(source.get(key) or "").strip()
            if value:
                settings[key] = value
    else:
        ouro_model = _resolve_main_model(provider, model)
        _apply_model_slots(settings, main_model=ouro_model, mirror_all_slots=True)
        _apply_bench_auxiliary_models(settings, cheap_model=ouro_model, source=source)
        if provider in {"openai", "azure"}:
            api_key = str(source.get("OPENAI_API_KEY") or source.get("LLM_API_KEY") or "").strip()
            if api_key:
                settings["OPENAI_API_KEY"] = api_key
        elif provider == "vllm":
            base_url = str(
                source.get("LLM_BASE_URL") or source.get("OPENAI_BASE_URL") or ""
            ).strip()
            api_key = str(source.get("OPENAI_API_KEY") or source.get("LLM_API_KEY") or "EMPTY").strip()
            if base_url:
                settings["OPENAI_COMPATIBLE_BASE_URL"] = base_url
            settings["OPENAI_COMPATIBLE_API_KEY"] = api_key

    max_retries = str(source.get("LLM_MAX_RETRIES") or "").strip()
    if max_retries:
        settings["OUROBOROS_TRANSIENT_RETRY_MAX"] = max_retries

    if bench_lock:
        _apply_bench_runtime_guards(settings)
        validate_bench_safe_ouroboros_models(settings, env=source)

    return settings


def shell_export_lines(env: Optional[Mapping[str, str]] = None) -> list[str]:
    """bash ``export`` lines for Ouroboros server / CLI subprocess env."""
    lines: list[str] = []
    for key, value in build_ouroboros_llm_settings(env).items():
        if value:
            lines.append(f"export {key}={shlex.quote(str(value))}")
    return lines


def validate_ouroboros_llm_settings(env: Optional[Mapping[str, str]] = None) -> None:
    """Raise ValueError when eval env lacks credentials for the configured provider."""
    source = dict(env) if env is not None else dict(os.environ)
    provider = str(source.get("LLM_PROVIDER", "openai")).strip().lower()
    settings = build_ouroboros_llm_settings(source)

    if provider == "openrouter":
        if not str(settings.get("OPENROUTER_API_KEY") or "").strip():
            raise ValueError(
                "OPENROUTER_API_KEY is missing for ouroboros-full-* "
                "(set it in envs/_openrouter.env)"
            )
    elif provider == "gigachat":
        if not str(settings.get("GIGACHAT_CREDENTIALS") or "").strip():
            raise ValueError(
                "GIGACHAT_TOKEN / GIGACHAT_CREDENTIALS is missing for ouroboros-full-*"
            )
    elif provider in {"openai", "azure"}:
        if not str(settings.get("OPENAI_API_KEY") or "").strip():
            raise ValueError("OPENAI_API_KEY is missing for ouroboros-full-*")
    elif not str(settings.get("OUROBOROS_MODEL") or "").strip():
        raise ValueError("OUROBOROS_MODEL could not be derived from eval LLM env")


def ouroboros_httpx_hook_dir() -> Path:
    """Directory with sitecustomize.py that gunzips stray LLM proxy bodies."""
    return Path(__file__).resolve().parents[1] / "scripts" / "ouroboros_httpx_hook"


def apply_ouroboros_httpx_hook_env(env: dict[str, str]) -> dict[str, str]:
    """Point PYTHONPATH at the gzip hook only (drop ROOT so submodule cannot shadow)."""
    hook_dir = ouroboros_httpx_hook_dir()
    if (hook_dir / "sitecustomize.py").is_file():
        env["PYTHONPATH"] = str(hook_dir)
    return env


def merge_ouroboros_llm_env(base_env: Mapping[str, str]) -> dict[str, str]:
    """Return *base_env* with eval LLM settings applied for Ouroboros subprocesses."""
    merged = dict(base_env)
    for key, value in build_ouroboros_llm_settings(merged).items():
        if value:
            merged[key] = value
    return apply_ouroboros_httpx_hook_env(merged)


def sync_ouroboros_server_llm(
    client: Any,
    *,
    env: Optional[Mapping[str, str]] = None,
) -> dict[str, str]:
    """Push eval LLM settings to a running Ouroboros server via POST /api/settings."""
    settings = build_ouroboros_llm_settings(env)
    if settings:
        client.apply_settings(settings)
    return settings
