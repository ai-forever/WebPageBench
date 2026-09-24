"""Load WebPageBench leaderboard configuration."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


def config_path() -> Path:
    return Path(__file__).resolve().parent.parent / "bench_config.json"


@lru_cache(maxsize=1)
def load_bench_config() -> dict[str, Any]:
    return json.loads(config_path().read_text(encoding="utf-8"))


def section_order() -> list[str]:
    config = load_bench_config()
    core = [key for key, meta in config["sections"].items() if meta.get("core")]
    rest = [key for key in config["sections"] if key not in core]
    return core + rest


def section_label(section_id: str) -> str:
    return load_bench_config()["sections"][section_id]["label"]


def section_description(section_id: str) -> str:
    return load_bench_config()["sections"][section_id].get("description") or ""


def taxonomy_order() -> list[str]:
    return list(load_bench_config().get("ui_classes", {}).keys())


def taxonomy_label(class_id: str) -> str:
    meta = load_bench_config().get("ui_classes", {}).get(class_id) or {}
    return str(meta.get("label") or class_id)


def taxonomy_description(class_id: str) -> str:
    meta = load_bench_config().get("ui_classes", {}).get(class_id) or {}
    return str(meta.get("description") or "")


def task_count() -> int:
    config = load_bench_config()
    return int(config["benchmark"].get("task_count") or sum(
        len(meta["tasks"]) for meta in config["sections"].values()
    ))
