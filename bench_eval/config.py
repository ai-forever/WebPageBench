"""Environment-driven configuration for the eval pipeline."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from bench_eval.hermes_config import DEFAULT_HERMES_CONFIG_PATH, load_hermes_harness_config
from bench_eval.ouroboros_config import DEFAULT_OUROBOROS_CONFIG_PATH, load_ouroboros_harness_config


def _dump_dir_from_env() -> Optional[str]:
    """``AGENT_DUMP_DIR``, or the ``GUI_AGENT_DUMP_DIR`` this shipped with."""
    for name in ("AGENT_DUMP_DIR", "GUI_AGENT_DUMP_DIR"):
        value = (os.getenv(name) or "").strip()
        if value:
            return value
    return None


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    return int(raw)


@dataclass
class EvalConfig:
    """Runtime settings for mock evaluation."""

    mock: str = "bench"
    tests_dir: Optional[str] = None
    task_filter: Optional[str] = None
    max_tasks: Optional[int] = None

    frontend_host: str = "127.0.0.1:5173"
    api_address: str = "localhost:9000"
    https: bool = False

    llm_provider: str = "openai"
    llm_model: str = "gpt-4.1-mini"
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_temperature: float = 0.2
    llm_max_retries: int = 3

    agent_harness: str = "browser-use"
    hermes_config_path: str = "configs/hermes_ouroboros.default.json"
    hermes_api_key: Optional[str] = None
    hermes_base_url: str = "http://127.0.0.1:8000"
    hermes_mode: str = "research"
    hermes_timeout: float = 300.0
    hermes_on_api_error: str = "continue_with_original_task"

    ouroboros_config_path: str = "configs/ouroboros.cut.json"
    ouroboros_mode: str = "cut"
    ouroboros_memory_mode: str = "empty"
    ouroboros_evolution_enabled: bool = False
    ouroboros_bin: str = "ouroboros"
    ouroboros_url: str = "http://127.0.0.1:9123"
    ouroboros_timeout: float = 3600.0
    ouroboros_execution_backend: str = "auto"

    agent_max_steps: int = 25
    agent_max_failures: int = 10
    agent_llm_timeout: float = 120.0
    agent_run_timeout: float = 3600.0
    agent_run_idle_timeout: float = 0.0
    agent_headless: bool = True
    agent_page_load_wait: float = 2.0
    agent_network_idle_wait: float = 2.0
    agent_wait_between_actions: float = 0.3
    #: Client-side deadline for one browser call (click, screenshot, teardown).
    #: Playwright's own timeouts live in the Node driver and never fire when the
    #: CDP pipe wedges, so this is what keeps a stuck page from hanging a worker.
    agent_action_timeout: float = 30.0
    #: Write every model call (request as sent + full response) to disk.
    #: Off by default: the dumps carry the base64 screenshots, so a full run
    #: costs a few hundred MB.
    agent_dump_enabled: bool = False
    #: Where those dumps go; defaults to ``<eval_output_dir>/llm-calls``.
    agent_dump_dir: Optional[str] = None
    agent_browser_executable: Optional[str] = None
    # Downloads: files cabinet tasks require the agent to actually save a PDF/CSV.
    # chrome-headless-shell has no download manager, so enabling downloads also
    # forces full Chromium (see browser_profile.find_browser_executable).
    agent_downloads_enabled: bool = True
    agent_downloads_dir: Optional[str] = None
    agent_warmup_timeout: float = 30.0
    agent_warmup_min_elements: int = 3
    agent_warmup_settle_seconds: float = 2.0
    agent_browser_start_timeout: float = 120.0

    dataset_path: str = "tests/evals/dataset.json"
    dataset_path_explicit: bool = False
    rebuild_dataset: bool = False
    dry_run: bool = False

    eval_results_base_dir: str = "tests/eval"
    eval_output_dir: Optional[str] = None
    run_started_at: Optional[datetime] = None

    show_progress: bool = True

    deepeval_identifier: Optional[str] = None
    track_suffix: Optional[str] = None

    def resolved_tests_dir(self) -> str:
        return self.tests_dir or f"tests/{self.mock}"


def load_config() -> EvalConfig:
    """Load configuration from environment variables."""
    max_tasks_raw = os.getenv("EVAL_MAX_TASKS")
    max_tasks = int(max_tasks_raw) if max_tasks_raw else None

    base_url = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL")
    provider_name = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider_name == "gigachat" and not base_url:
        base_url = os.getenv("GIGACHAT_BASE_URL")
    if provider_name == "gigahf" and not base_url:
        base_url = os.getenv("GIGAHF_BASE_URL")
    api_key = (
        os.getenv("LLM_API_KEY")
        or os.getenv("OPENROUTER_API_KEY")
        or os.getenv("GIGACHAT_TOKEN")
        or os.getenv("GIGAHF_TOKEN")
        or os.getenv("OPENAI_API_KEY")
    )

    llm_model = os.getenv("LLM_MODEL", "gpt-4.1-mini")
    agent_harness = os.getenv("AGENT_HARNESS", "browser-use")
    eval_output_dir = os.getenv("EVAL_OUTPUT_DIR")
    run_started_at = datetime.now()
    dataset_path_explicit = os.getenv("EVAL_DATASET_PATH") is not None
    from bench_eval.results import (
        configure_deepeval_cache_folder,
        default_deepeval_identifier,
        default_run_directory,
    )

    track_suffix = os.getenv("EVAL_TRACK_SUFFIX")
    if not track_suffix:
        track_suffix = uuid.uuid4().hex[:8]
        os.environ["EVAL_TRACK_SUFFIX"] = track_suffix

    if dataset_path_explicit:
        dataset_path = os.getenv("EVAL_DATASET_PATH", "tests/evals/dataset.json")
    elif eval_output_dir:
        dataset_path = os.path.join(eval_output_dir, "dataset.json")
    else:
        eval_output_dir = str(
            default_run_directory(
                llm_model,
                agent_harness,
                started_at=run_started_at,
                track_suffix=track_suffix,
            )
        )
        os.environ["EVAL_OUTPUT_DIR"] = eval_output_dir
        dataset_path = f"{eval_output_dir}/dataset.json"
        os.environ.setdefault("EVAL_DATASET_PATH", dataset_path)

    configure_deepeval_cache_folder(
        eval_output_dir
        or (
            str(Path(dataset_path).parent)
            if dataset_path_explicit
            and Path(dataset_path).name == "dataset.json"
            and Path(dataset_path).parent.name != "evals"
            else None
        )
    )

    mock = os.getenv("EVAL_MOCK", "bench")
    deepeval_identifier = os.getenv("DEEPEVAL_IDENTIFIER") or default_deepeval_identifier(
        mock,
        agent_harness,
        llm_model,
    )
    os.environ.setdefault("DEEPEVAL_IDENTIFIER", deepeval_identifier)

    hermes_config_path = os.getenv("HERMES_CONFIG_PATH", DEFAULT_HERMES_CONFIG_PATH)
    hermes_harness = load_hermes_harness_config(hermes_config_path)

    ouroboros_config_path = os.getenv("OUROBOROS_CONFIG_PATH", DEFAULT_OUROBOROS_CONFIG_PATH)
    ouroboros_harness = load_ouroboros_harness_config(
        ouroboros_config_path,
        mode=os.getenv("OUROBOROS_MODE"),
    )
    if os.getenv("OUROBOROS_CONFIG_PATH") is None:
        harness_key = agent_harness.strip().lower().replace("_", "-")
        mode_paths = {
            "ouroboros-cut": "configs/ouroboros.cut.json",
            "ouroboros-full-isolated": "configs/ouroboros.full_isolated.json",
            "ouroboros-full-evolving": "configs/ouroboros.full_evolving.json",
        }
        if harness_key in mode_paths:
            ouroboros_config_path = mode_paths[harness_key]
            ouroboros_harness = load_ouroboros_harness_config(ouroboros_config_path)

    return EvalConfig(
        mock=os.getenv("EVAL_MOCK", "bench"),
        tests_dir=os.getenv("EVAL_TESTS_DIR"),
        task_filter=os.getenv("EVAL_TASK_FILTER"),
        max_tasks=max_tasks,
        frontend_host=os.getenv("EVAL_FRONTEND_HOST", "127.0.0.1:5173"),
        api_address=os.getenv("EVAL_API_ADDRESS", "localhost:9000"),
        https=_env_bool("EVAL_HTTPS", False),
        llm_provider=os.getenv("LLM_PROVIDER", "openai").lower(),
        llm_model=llm_model,
        llm_api_key=api_key,
        llm_base_url=base_url,
        llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        llm_max_retries=_env_int("LLM_MAX_RETRIES", 3),
        agent_harness=agent_harness,
        hermes_config_path=hermes_config_path,
        ouroboros_config_path=ouroboros_config_path,
        ouroboros_mode=ouroboros_harness.mode,
        ouroboros_memory_mode=ouroboros_harness.memory_mode,
        ouroboros_evolution_enabled=ouroboros_harness.evolution_enabled,
        ouroboros_bin=ouroboros_harness.ouroboros_bin,
        ouroboros_url=ouroboros_harness.ouroboros_url,
        ouroboros_timeout=ouroboros_harness.ouroboros_timeout_seconds,
        ouroboros_execution_backend=ouroboros_harness.execution_backend,
        hermes_api_key=hermes_harness.api_key,
        hermes_base_url=hermes_harness.api_base_url,
        hermes_mode=hermes_harness.analysis_mode,
        hermes_timeout=hermes_harness.timeout_seconds,
        hermes_on_api_error=hermes_harness.on_api_error,
        agent_max_steps=_env_int("AGENT_MAX_STEPS", 25),
        agent_max_failures=_env_int("AGENT_MAX_FAILURES", 10),
        agent_llm_timeout=float(os.getenv("AGENT_LLM_TIMEOUT", "120")),
        agent_run_timeout=float(
            os.getenv(
                "AGENT_RUN_TIMEOUT",
                str(
                    max(
                        600.0,
                        min(
                            7200.0,
                            _env_int("AGENT_MAX_STEPS", 25)
                            * (float(os.getenv("AGENT_LLM_TIMEOUT", "120")) + 90.0),
                        ),
                    )
                ),
            )
        ),
        agent_run_idle_timeout=float(os.getenv("AGENT_RUN_IDLE_TIMEOUT", "0")),
        agent_headless=_env_bool("AGENT_HEADLESS", True),
        agent_page_load_wait=float(os.getenv("AGENT_PAGE_LOAD_WAIT", "3.0")),
        agent_network_idle_wait=float(
            os.getenv("AGENT_NETWORK_IDLE_WAIT", "3.0")
        ),
        agent_wait_between_actions=float(
            os.getenv("AGENT_WAIT_BETWEEN_ACTIONS", "0.5")
        ),
        agent_action_timeout=float(os.getenv("AGENT_ACTION_TIMEOUT", "30.0")),
        agent_dump_enabled=_env_bool("AGENT_DUMP_ENABLED", bool(_dump_dir_from_env())),
        agent_dump_dir=_dump_dir_from_env(),
        agent_browser_executable=os.getenv("AGENT_BROWSER_EXECUTABLE")
        or os.getenv("BROWSER_EXECUTABLE_PATH"),
        agent_downloads_enabled=_env_bool("AGENT_DOWNLOADS_ENABLED", True),
        agent_downloads_dir=os.getenv("AGENT_DOWNLOADS_DIR") or None,
        agent_warmup_timeout=float(os.getenv("AGENT_WARMUP_TIMEOUT", "45")),
        agent_warmup_min_elements=_env_int("AGENT_WARMUP_MIN_ELEMENTS", 1),
        agent_warmup_settle_seconds=float(
            os.getenv("AGENT_WARMUP_SETTLE_SECONDS", "2.0")
        ),
        agent_browser_start_timeout=float(
            os.getenv("AGENT_BROWSER_START_TIMEOUT", "180")
        ),
        dataset_path=dataset_path,
        dataset_path_explicit=dataset_path_explicit,
        rebuild_dataset=_env_bool("EVAL_REBUILD_DATASET", False),
        dry_run=_env_bool("EVAL_DRY_RUN", False),
        eval_results_base_dir=os.getenv("EVAL_RESULTS_BASE_DIR", "tests/eval"),
        eval_output_dir=eval_output_dir,
        run_started_at=run_started_at,
        show_progress=_env_bool("EVAL_SHOW_PROGRESS", True),
        deepeval_identifier=deepeval_identifier,
        track_suffix=os.getenv("EVAL_TRACK_SUFFIX"),
    )
