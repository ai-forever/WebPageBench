"""Build DeepEval goldens from WebPageBench mock task configs."""

from __future__ import annotations

import copy
import json
import os
from glob import glob
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional

from bench_eval.config import EvalConfig
from bench_eval.results import resolve_dataset_path
from bench_eval.task_dates import apply_booking_dates

# deepeval is imported lazily so that build_test_configs (pure JSON merging) stays
# usable without the eval stack — see bench_eval/agents/cli/benchmark.py.
if TYPE_CHECKING:  # pragma: no cover - typing only
    from deepeval.dataset import EvaluationDataset, Golden


def merge(base: dict, update: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in update.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def build_test_configs(tests_dir: str) -> Dict[str, dict]:
    """Merge mock config with task JSON files (same logic as tests.py)."""
    test_configs = glob(os.path.join(tests_dir, "tasks", "*.json"))
    mock_config_path = os.path.join(tests_dir, "config.json")
    build_dir = os.path.join(tests_dir, "build")
    mock_config = json.load(open(mock_config_path, encoding="utf-8"))
    extends_rel = mock_config.pop("extends", None)
    if extends_rel:
        base_path = os.path.normpath(os.path.join(tests_dir, extends_rel))
        if not os.path.isfile(base_path):
            raise FileNotFoundError(f"extends: файл не найден: {base_path}")
        base_config = json.load(open(base_path, encoding="utf-8"))
        mock_config = merge(base_config, mock_config)
    os.makedirs(build_dir, exist_ok=True)
    res: Dict[str, dict] = {}
    for file in test_configs:
        test_config_data = json.load(open(file, encoding="utf-8"))
        filename = os.path.basename(file)
        merged_config = merge(mock_config, test_config_data)
        apply_booking_dates(merged_config)
        merged_config["test_data"]["test_name"] = filename.replace(".json", "")
        output_path = os.path.join(build_dir, filename)
        res[output_path] = merged_config
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(merged_config, f, ensure_ascii=False, indent=2)
    return res


def _track_id(test_name: str, *, suffix: Optional[str] = None) -> str:
    base = test_name.replace(" ", "_").lower()
    if suffix:
        return f"{base}__{suffix}"
    return base


def configs_to_goldens(
    tests_dir: str,
    *,
    frontend_host: str = "127.0.0.1:5173",
    task_filter: Optional[str] = None,
    max_tasks: Optional[int] = None,
    track_suffix: Optional[str] = None,
) -> List[Golden]:
    from deepeval.dataset import Golden

    mock_name = Path(tests_dir).name
    configs = build_test_configs(tests_dir)
    items = sorted(configs.items(), key=lambda item: item[0])
    goldens: List[Golden] = []

    for filepath, config in items:
        test_name = config["test_data"]["test_name"]
        if task_filter and task_filter not in test_name:
            continue

        track_id = _track_id(test_name, suffix=track_suffix)
        full_host = f"http://{frontend_host}/{track_id}"
        task = config["test_data"]["task"].replace("%HOST%", full_host)

        goldens.append(
            Golden(
                input=task,
                name=test_name,
                additional_metadata={
                    "mock": mock_name,
                    "test_name": test_name,
                    "track_id": track_id,
                    "config_path": filepath,
                    "task_url": full_host,
                    "conditions_count": len(
                        config.get("test_data", {}).get("conditions", [])
                    ),
                },
            )
        )
        if max_tasks is not None and len(goldens) >= max_tasks:
            break

    return goldens


def build_dataset(
    tests_dir: str,
    output_path: str,
    *,
    frontend_host: str = "127.0.0.1:5173",
    task_filter: Optional[str] = None,
    max_tasks: Optional[int] = None,
    track_suffix: Optional[str] = None,
) -> EvaluationDataset:
    from deepeval.dataset import EvaluationDataset

    goldens = configs_to_goldens(
        tests_dir,
        frontend_host=frontend_host,
        task_filter=task_filter,
        max_tasks=max_tasks,
        track_suffix=track_suffix,
    )
    path = Path(output_path)
    dataset = EvaluationDataset(goldens=goldens)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Every xdist worker rebuilds this file when EVAL_REBUILD_DATASET=true, so
    # writing in place lets one worker read what another is half-way through
    # writing (JSONDecodeError, and its whole share of the run errors at setup).
    # Build under a private name and swap it in: os.replace is atomic, so a
    # reader always sees one complete dataset or the other.
    staging = path.with_name(f"{path.stem}.{os.getpid()}.tmp")
    dataset.save_as(
        file_type="json",
        directory=str(staging.parent),
        file_name=staging.stem,
        include_test_cases=False,
    )
    written = staging.with_suffix(".json")
    try:
        os.replace(written, path)
    finally:
        written.unlink(missing_ok=True)
    return dataset


def load_or_build_dataset(
    config: EvalConfig,
) -> EvaluationDataset:
    from deepeval.dataset import EvaluationDataset

    path = Path(resolve_dataset_path(config))
    if config.rebuild_dataset or not path.exists():
        build_dataset(
            config.resolved_tests_dir(),
            str(path),
            frontend_host=config.frontend_host,
            task_filter=config.task_filter,
            max_tasks=config.max_tasks,
            track_suffix=config.track_suffix,
        )
    dataset = EvaluationDataset()
    dataset.add_goldens_from_json_file(file_path=str(path))
    goldens = list(dataset.goldens)
    if config.task_filter:
        goldens = [
            g
            for g in goldens
            if config.task_filter in (g.name or "")
            or config.task_filter in (g.additional_metadata or {}).get("test_name", "")
        ]
    if config.max_tasks is not None:
        goldens = goldens[: config.max_tasks]
    dataset._goldens = []
    for g in goldens:
        dataset._add_golden(g)
    return dataset
