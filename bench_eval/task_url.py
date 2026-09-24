"""Resolve frontend entry URLs for bench tasks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse


def _first_state_key(config: dict[str, Any]) -> Optional[str]:
    test_data = config.get("test_data") or {}
    if test_data.get("bench_first_state"):
        return test_data["bench_first_state"]

    state_keys = [key for key in config if key.startswith("state_")]
    if test_data.get("unified_bench") and "state_hub" in state_keys:
        return "state_hub"
    for key in state_keys:
        if key != "state_hub":
            return key
    return state_keys[0] if state_keys else None


def _view_type_for_state(config: dict[str, Any], state_key: str) -> Optional[str]:
    for section in config.get("bench_sections") or []:
        if section.get("state") == state_key and section.get("view_type"):
            return section["view_type"]

    state_config = config.get(state_key) or {}
    if state_config.get("view_type"):
        return state_config["view_type"]

    test_data = config.get("test_data") or {}
    domain_key = test_data.get("bench_first_domain")
    if domain_key:
        domain_slice = (config.get("domain_configs") or {}).get(domain_key) or {}
        state_config = domain_slice.get(state_key) or {}
        if state_config.get("view_type"):
            return state_config["view_type"]

    for domain_slice in (config.get("domain_configs") or {}).values():
        state_config = domain_slice.get(state_key) or {}
        if state_config.get("view_type"):
            return state_config["view_type"]

    return None


def resolve_entry_url(task_url: str, config_path: str) -> str:
    """
    Build a deep link that skips StartView and opens the first task screen.

    Example:
      http://127.0.0.1:5173/track/state_shop_main/bench_catalog_main
    """
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    first_state = _first_state_key(config)
    if not first_state:
        return task_url

    view_type = _view_type_for_state(config, first_state)
    if not view_type:
        return task_url

    base = task_url.rstrip("/")
    parsed = urlparse(base)
    track_id = parsed.path.strip("/").split("/")[0] if parsed.path.strip("/") else ""
    if not track_id:
        return task_url

    return f"{parsed.scheme}://{parsed.netloc}/{track_id}/{first_state}/{view_type}"
