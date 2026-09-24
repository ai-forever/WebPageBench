"""Orchestrate one golden: create track, run agent, verify telemetry."""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from deepeval.dataset import Golden
from deepeval.test_case import LLMTestCase

from bench_eval.harness_factory import run_agent_sync
from bench_eval.config import EvalConfig, load_config
from bench_eval.ouroboros_session import get_ouroboros_session
from bench_eval.task_url import resolve_entry_url
from bench_eval.track import check_track, create_track, summarize_checks
from bench_eval.token_usage import normalize_token_usage
from bench_eval.trajectory import build_trajectory, fetch_dab_events
from bench_eval.ui_taxonomy_report import build_ui_taxonomy_report


def _metadata(golden: Golden) -> Dict[str, Any]:
    return golden.additional_metadata or {}


def run_golden(
    golden: Golden,
    config: Optional[EvalConfig] = None,
) -> LLMTestCase:
    """
    Execute a single benchmark task end-to-end.

    1. Create WebPageBench track from merged config
    2. Run selected agent harness on task URL
    3. Check telemetry conditions via agent_bench client
    """
    cfg = config or load_config()
    meta = _metadata(golden)
    test_name = meta["test_name"]
    track_id = meta["track_id"]
    config_path = meta["config_path"]
    task_url = meta.get("task_url")

    agent_summary: Dict[str, Any] = {
        "skipped": True,
        "reason": "dry_run",
    }
    check_summary: Dict[str, Any] = {
        "passed": 0,
        "failed": 0,
        "total": 0,
        "score": 0.0,
        "all_passed": False,
        "failed_conditions": [],
        "check_results": [],
    }
    track_created = False
    agent_error: Optional[str] = None
    trajectory: Dict[str, Any] = {}
    ui_taxonomy: Dict[str, Any] = {}
    dab_events: List[Dict[str, Any]] = []
    test_started_at = time.perf_counter()

    if not cfg.dry_run:
        created = create_track(
            test_name=test_name,
            track_id=track_id,
            config_path=config_path,
            api_address=cfg.api_address,
            https=cfg.https,
        )
        track_created = created is not None
        if not track_created:
            agent_error = "Failed to create track on WebPageBench backend"

        if track_created and agent_error is None:
            entry_url = resolve_entry_url(task_url, config_path) if task_url else None
            get_ouroboros_session(cfg)
            print(
                f"[eval] agent start: harness={cfg.agent_harness} "
                f"test={test_name} entry_url={entry_url}",
                flush=True,
            )
            try:
                agent_summary = dict(
                    run_agent_sync(
                        golden.input,
                        config=cfg,
                        task_url=task_url,
                        entry_url=entry_url,
                        task_key=test_name,
                    )
                )
                agent_summary["skipped"] = False
                if agent_summary.get("error"):
                    agent_error = str(agent_summary["error"])
            except Exception as exc:
                agent_error = str(exc)
                agent_summary = {
                    "skipped": False,
                    "error": agent_error,
                    "steps": 0,
                    "is_done": False,
                }
            else:
                print(
                    f"[eval] agent finished: test={test_name} "
                    f"steps={agent_summary.get('steps')} "
                    f"is_done={agent_summary.get('is_done')}",
                    flush=True,
                )

        if track_created:
            raw_checks = check_track(
                track_id, cfg.api_address, https=cfg.https
            )
            check_summary = summarize_checks(raw_checks)
            dab_events = fetch_dab_events(
                track_id, cfg.api_address, https=cfg.https
            )
            harness_trajectory = agent_summary.pop("trajectory", None)
            trajectory = build_trajectory(
                agent_history=agent_summary.pop("history", None),
                harness_trajectory=harness_trajectory,
                dab_events=dab_events,
            )
        elif "history" in agent_summary:
            agent_summary.pop("history", None)
        if "trajectory" in agent_summary:
            agent_summary.pop("trajectory", None)

    ui_taxonomy = build_ui_taxonomy_report(
        config_path=config_path,
        test_name=test_name,
        dab_events=dab_events,
    )

    test_duration_seconds = time.perf_counter() - test_started_at

    actual_output = agent_summary.get("final_result") or agent_summary.get("error")
    if actual_output is None and agent_error:
        actual_output = agent_error
    if isinstance(actual_output, (dict, list)):
        actual_output = json.dumps(actual_output, ensure_ascii=False)

    return LLMTestCase(
        input=golden.input,
        actual_output=actual_output,
        name=test_name,
        metadata={
            "mock": meta.get("mock"),
            "test_name": test_name,
            "track_id": track_id,
            "task_url": task_url,
            "entry_url": agent_summary.get("entry_url"),
            "track_created": track_created,
            "agent": agent_summary,
            "agent_harness": cfg.agent_harness,
            "dab_check": check_summary,
            "agent_error": agent_error,
            "trajectory": trajectory,
            "ui_taxonomy": ui_taxonomy,
            "timing": {
                "duration_seconds": test_duration_seconds,
                "agent_duration_seconds": agent_summary.get("duration_seconds"),
            },
            "token_usage": normalize_token_usage(agent_summary.get("token_usage")),
            "token_usage_by_model": agent_summary.get("token_usage_by_model") or {},
        },
    )
